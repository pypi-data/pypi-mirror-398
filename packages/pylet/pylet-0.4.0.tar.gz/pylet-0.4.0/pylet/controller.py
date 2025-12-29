"""
PyLet Controller - Core scheduling and state management.

Uses SQLite for persistence. Implements:
- Worker liveness model (ONLINE/SUSPECT/OFFLINE)
- Generation-based long-poll for worker communication
- Attempt-based fencing for correctness
"""

import asyncio
import secrets
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pylet import config
from pylet.db import Database
from pylet.logger import logger
from pylet.schemas import (
    DesiredInstance,
    HeartbeatRequest,
    HeartbeatResponse,
    Instance,
    InstanceReport,
    InstanceStatus,
    ResourceSpec,
    Worker,
    WorkerStatus,
    is_terminal,
    validate_transition,
)


class Controller:
    """
    Controller manages instance scheduling and worker coordination.

    All state is persisted to SQLite. Workers communicate via a
    generation-based long-poll heartbeat protocol.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db = Database(db_path)
        self.lock = asyncio.Lock()

        # Generation counters for long-poll (in-memory, per worker)
        self.desired_gen: Dict[str, int] = {}
        self.gen_events: Dict[str, asyncio.Event] = {}

        # Scheduler poke event
        self.scheduler_event = asyncio.Event()

    async def startup(self) -> None:
        """Initialize controller on startup."""
        await self.db.connect()

        # Mark all workers SUSPECT on startup (controller crash recovery)
        await self.db.mark_all_workers_suspect()
        logger.info("Controller startup: marked all workers SUSPECT")

    async def shutdown(self) -> None:
        """Clean shutdown."""
        await self.db.close()

    # ========== Worker Management ==========

    async def register_worker(
        self,
        worker_id: str,
        host: str,
        resources: ResourceSpec,
        boot_id: Optional[str] = None,
    ) -> str:
        """
        Register a worker and return its token.

        If worker already exists, this is a reconnection - issue new token.
        """
        token = secrets.token_urlsafe(32)

        async with self.lock:
            existing = await self.db.get_worker(worker_id)

            if existing:
                # Reconnection - update worker with new token
                await self.db.update_worker_on_reconnect(
                    worker_id=worker_id,
                    ip=host,
                    cpu_cores=resources.cpu_cores,
                    gpu_units=resources.gpu_units,
                    memory_mb=resources.memory_mb,
                    worker_token=token,
                )
                logger.info(f"Worker {worker_id} ({host}) reconnected")
            else:
                # New worker
                await self.db.insert_worker(
                    worker_id=worker_id,
                    ip=host,
                    cpu_cores=resources.cpu_cores,
                    gpu_units=resources.gpu_units,
                    memory_mb=resources.memory_mb,
                    worker_token=token,
                )
                logger.info(
                    f"Worker {worker_id} ({host}) registered with resources: {resources}"
                )

            # Initialize generation counter
            self.desired_gen[worker_id] = 0
            self.gen_events[worker_id] = asyncio.Event()

        return token

    async def get_worker(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Get worker by ID."""
        return await self.db.get_worker(worker_id)

    async def get_all_workers(self) -> List[Dict[str, Any]]:
        """Get all workers."""
        return await self.db.get_all_workers()

    # ========== Heartbeat Protocol (Phase 3) ==========

    async def process_heartbeat(
        self, worker_id: str, request: HeartbeatRequest
    ) -> HeartbeatResponse:
        """
        Process worker heartbeat with long-poll.

        1. Validate token
        2. Update liveness
        3. Process instance reports (with fencing)
        4. Wait for gen change or timeout (long-poll)
        5. Return desired state
        """
        # 1. Validate token
        worker = await self.db.get_worker(worker_id)
        if not worker:
            raise ValueError(f"Worker {worker_id} not registered")
        if worker["worker_token"] != request.worker_token:
            raise ValueError("Invalid worker token")

        # 2. Update liveness (and detect restart via boot_id)
        if worker["last_boot_id"] and worker["last_boot_id"] != request.boot_id:
            logger.info(f"Worker {worker_id} restarted (new boot_id)")

        await self.db.update_worker_heartbeat(worker_id, request.boot_id)

        # 3. Process instance reports (attempt-fenced)
        for report in request.instances:
            await self._process_instance_report(worker_id, report)

        # 4. Wait for gen change or timeout (long-poll)
        gen = await self._wait_for_gen_change(
            worker_id, request.last_seen_gen, config.HEARTBEAT_POLL_TIMEOUT
        )

        # 5. Return desired state
        desired = await self._get_desired_instances(worker_id)
        return HeartbeatResponse(gen=gen, desired_instances=desired)

    async def _wait_for_gen_change(
        self, worker_id: str, last_seen: int, timeout: float
    ) -> int:
        """Wait for generation to change or timeout."""
        current = self.desired_gen.get(worker_id, 0)
        if current > last_seen:
            return current

        event = self.gen_events.setdefault(worker_id, asyncio.Event())
        event.clear()

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass

        return self.desired_gen.get(worker_id, 0)

    def increment_gen(self, worker_id: str) -> None:
        """Increment generation and wake long-poll."""
        self.desired_gen[worker_id] = self.desired_gen.get(worker_id, 0) + 1
        if worker_id in self.gen_events:
            self.gen_events[worker_id].set()

    async def _get_desired_instances(self, worker_id: str) -> List[DesiredInstance]:
        """Get instances that should be running on this worker."""
        import json

        rows = await self.db.get_desired_instances_for_worker(worker_id)
        worker = await self.db.get_worker(worker_id)
        worker_ip = worker["ip"] if worker else "127.0.0.1"

        desired = []
        for row in rows:
            gpu_indices = []
            if row["gpu_indices"]:
                gpu_indices = [int(x) for x in row["gpu_indices"].split(",")]

            # Parse env from JSON
            env = {}
            if row.get("env"):
                try:
                    env = json.loads(row["env"])
                except (json.JSONDecodeError, TypeError):
                    pass

            desired.append(
                DesiredInstance(
                    instance_id=row["id"],
                    attempt=row["attempt"],
                    command=row["command"],
                    gpu_indices=gpu_indices,
                    env=env,
                    venv=row.get("venv"),
                    expected_status=row["status"],
                )
            )

        return desired

    # ========== Instance Report Processing (Phase 4: Fencing) ==========

    async def _process_instance_report(
        self, worker_id: str, report: InstanceReport
    ) -> None:
        """Process instance report with attempt fencing."""
        instance = await self.db.get_instance(report.instance_id)

        if not instance:
            logger.warning(f"Report for unknown instance: {report.instance_id}")
            return

        # FENCING CHECK: Reject stale attempts
        if report.attempt != instance["attempt"]:
            logger.info(
                f"Ignoring stale report for {report.instance_id}: "
                f"report attempt={report.attempt}, current={instance['attempt']}"
            )
            return

        # Verify worker ownership
        if instance["assigned_worker"] != worker_id:
            logger.warning(
                f"Report from wrong worker: {worker_id} for instance "
                f"assigned to {instance['assigned_worker']}"
            )
            return

        # Apply the report
        await self._apply_instance_report(instance, report, worker_id)

    async def _apply_instance_report(
        self, instance: Dict[str, Any], report: InstanceReport, worker_id: str
    ) -> None:
        """Apply a validated (attempt-fenced) report."""
        current_status = instance["status"]

        if report.status == "RUNNING":
            if current_status in ("ASSIGNED", "UNKNOWN"):
                worker = await self.db.get_worker(worker_id)
                worker_ip = worker["ip"] if worker else "127.0.0.1"
                endpoint = f"{worker_ip}:{report.port}" if report.port else None

                success = await self.db.update_instance_running(
                    instance["id"], report.attempt, report.port or 0, endpoint or ""
                )
                if success:
                    logger.info(
                        f"Instance {instance['id']} {current_status} -> RUNNING "
                        f"(endpoint={endpoint})"
                    )

        elif report.status == "COMPLETED":
            if current_status in ("RUNNING", "UNKNOWN"):
                success = await self.db.transition_to_terminal(
                    instance["id"], report.attempt, "COMPLETED", report.exit_code
                )
                if success:
                    logger.info(f"Instance {instance['id']} -> COMPLETED")
                    self.poke_scheduler()

        elif report.status == "FAILED":
            if current_status in ("ASSIGNED", "RUNNING", "UNKNOWN"):
                success = await self.db.transition_to_terminal(
                    instance["id"], report.attempt, "FAILED", report.exit_code
                )
                if success:
                    logger.info(
                        f"Instance {instance['id']} -> FAILED (exit_code={report.exit_code})"
                    )
                    self.poke_scheduler()

        elif report.status == "NOT_FOUND":
            await self._handle_not_found(instance, report)

        elif report.status == "CANCELLED":
            if current_status in ("ASSIGNED", "RUNNING", "UNKNOWN"):
                # Check if cancellation was requested to determine terminal state
                cancel_requested = instance.get("cancel_requested_at") is not None

                if cancel_requested:
                    # User-initiated cancellation confirmed
                    success = await self.db.transition_to_terminal(
                        instance["id"], report.attempt, "CANCELLED"
                    )
                    if success:
                        logger.info(f"Instance {instance['id']} cancellation confirmed")
                        self.poke_scheduler()
                else:
                    # Worker killed it without cancel request (e.g., rescheduled)
                    # Mark as FAILED since it wasn't user-initiated
                    success = await self.db.transition_to_terminal(
                        instance["id"], report.attempt, "FAILED",
                        failure_reason="KILLED_BY_WORKER"
                    )
                    if success:
                        logger.info(f"Instance {instance['id']} -> FAILED (killed by worker)")
                        self.poke_scheduler()

    async def _handle_not_found(
        self, instance: Dict[str, Any], report: InstanceReport
    ) -> None:
        """Handle NOT_FOUND report - worker has no evidence of this attempt."""
        current_status = instance["status"]

        if current_status not in ("ASSIGNED", "RUNNING", "UNKNOWN"):
            logger.debug(f"Ignoring NOT_FOUND for terminal instance {instance['id']}")
            return

        if report.attempt != instance["attempt"]:
            logger.debug("Ignoring NOT_FOUND for stale attempt")
            return

        logger.warning(
            f"Instance {instance['id']} attempt {report.attempt} NOT_FOUND - "
            f"marking as FAILED (LOST_AFTER_REJOIN)"
        )

        await self.db.transition_to_terminal(
            instance["id"],
            report.attempt,
            "FAILED",
            exit_code=None,
            failure_reason="LOST_AFTER_REJOIN",
        )
        self.poke_scheduler()

    # ========== Instance Management ==========

    async def submit_instance(
        self,
        command: str,
        resource_requirements: ResourceSpec,
        name: Optional[str] = None,
        # SLLM support parameters
        target_worker: Optional[str] = None,
        gpu_indices: Optional[List[int]] = None,
        exclusive: bool = True,
        labels: Optional[Dict[str, str]] = None,
        env: Optional[Dict[str, str]] = None,
        # Venv support
        venv: Optional[str] = None,
    ) -> str:
        """Submit a new instance for execution."""
        async with self.lock:
            instance_id = str(uuid.uuid4())

            # Auto-generate name if not provided
            if name is None:
                name = instance_id[:8]

            # Check for duplicate names
            existing = await self.db.get_instance_by_name(name)
            if existing:
                raise ValueError(f"An instance with name '{name}' already exists.")

            # Determine effective GPU count
            effective_gpu_units = resource_requirements.gpu_units
            if gpu_indices is not None:
                effective_gpu_units = len(gpu_indices)

            await self.db.insert_instance(
                instance_id=instance_id,
                name=name,
                command=command,
                cpu_cores=resource_requirements.cpu_cores,
                gpu_units=effective_gpu_units,
                memory_mb=resource_requirements.memory_mb,
                exclusive=exclusive,
                labels=labels or {},
                env=env or {},
                target_worker=target_worker,
                gpu_indices=gpu_indices,
                venv=venv,
            )

            logger.info(
                f"Instance {instance_id} ('{name}') submitted: "
                f"target_worker={target_worker}, gpu_indices={gpu_indices}, "
                f"exclusive={exclusive}, labels={labels}"
            )

        # Poke scheduler
        self.poke_scheduler()

        return instance_id

    async def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get instance by ID."""
        return await self.db.get_instance(instance_id)

    async def get_instance_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get instance by name."""
        return await self.db.get_instance_by_name(name)

    async def get_all_instances(
        self,
        status: Optional[str] = None,
        label_filters: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all instances, optionally filtered by status and labels.

        Args:
            status: Optional status filter (e.g., "RUNNING", "PENDING")
            label_filters: Optional dict of label key:value filters (AND logic)

        Returns:
            List of instance dicts
        """
        return await self.db.get_all_instances(status, label_filters)

    async def request_cancellation(self, instance_id: str) -> bool:
        """
        Request cancellation of an instance.

        Sets cancellation_requested_at timestamp if not already set.
        Idempotent - multiple requests return True without error.
        """
        instance = await self.db.get_instance(instance_id)
        if not instance:
            return False

        current_status = instance["status"]
        if current_status in ("COMPLETED", "FAILED", "CANCELLED"):
            logger.warning(f"Cannot cancel {instance_id} - already in terminal state")
            return False

        # Check if already requested (idempotent)
        if instance.get("cancel_requested_at") is not None:
            logger.info(f"Instance {instance_id} already has cancellation requested")
            return True

        # For PENDING instances, cancel immediately (no worker involved)
        if current_status == "PENDING":
            await self.db.transition_to_terminal(
                instance_id, instance["attempt"], "CANCELLED"
            )
            logger.info(f"Instance {instance_id} cancelled (was PENDING)")
            self.poke_scheduler()
            return True

        # Set cancellation timestamp
        rows_affected = await self.db.request_cancellation(instance_id)

        if rows_affected > 0:
            logger.info(f"Instance {instance_id} cancellation requested")
            self.poke_scheduler()

            # Wake worker's long-poll if assigned
            if instance["assigned_worker"]:
                self.increment_gen(instance["assigned_worker"])

            return True

        logger.warning(
            f"Could not cancel {instance_id} - not in cancellable state"
        )
        return False

    # ========== Liveness Evaluation (Phase 2) ==========

    async def evaluate_liveness(self) -> None:
        """Update worker statuses based on heartbeat age."""
        # ONLINE -> SUSPECT
        await self.db.mark_stale_workers_suspect(config.SUSPECT_THRESHOLD_SECONDS)

        # SUSPECT/ONLINE -> OFFLINE
        workers_going_offline = await self.db.get_workers_exceeding_threshold(
            config.OFFLINE_THRESHOLD_SECONDS
        )

        for worker in workers_going_offline:
            await self._mark_worker_offline(worker["id"])

    async def _mark_worker_offline(self, worker_id: str) -> None:
        """Mark worker offline and transition instances to UNKNOWN."""
        await self.db.update_worker_status(worker_id, "OFFLINE")

        # Non-terminal instances -> UNKNOWN
        affected = await self.db.mark_instances_unknown(worker_id)

        if affected > 0:
            logger.warning(
                f"Worker {worker_id} -> OFFLINE, {affected} instances -> UNKNOWN"
            )
        else:
            logger.info(f"Worker {worker_id} -> OFFLINE")

        self.poke_scheduler()

    async def liveness_loop(self) -> None:
        """Periodic loop to evaluate worker liveness."""
        while True:
            await asyncio.sleep(config.LIVENESS_CHECK_INTERVAL)
            try:
                await self.evaluate_liveness()
            except Exception as e:
                logger.error(f"Liveness evaluation error: {e}")

    # ========== Scheduler (Phase 7: in-process for now) ==========

    def poke_scheduler(self) -> None:
        """Wake scheduler to run a scheduling cycle."""
        self.scheduler_event.set()

    async def scheduler_loop(self) -> None:
        """Background scheduler loop."""
        while True:
            # Wait for poke or periodic interval
            try:
                await asyncio.wait_for(
                    self.scheduler_event.wait(), timeout=config.SCHEDULER_INTERVAL
                )
            except asyncio.TimeoutError:
                pass

            self.scheduler_event.clear()

            try:
                await self._run_scheduling_cycle()
            except Exception as e:
                logger.error(f"Scheduling cycle error: {e}")

    async def _run_scheduling_cycle(self) -> None:
        """Execute one scheduling cycle."""
        # Get online workers
        workers = await self.db.get_online_workers()
        if not workers:
            return

        # Calculate available resources per worker
        # Only count EXCLUSIVE allocations for availability
        available = {}
        for worker in workers:
            used_gpus = await self.db.get_used_gpus_for_worker(
                worker["id"], exclusive_only=True
            )
            total_gpus = worker["gpu_units"] or 0
            available[worker["id"]] = {
                "total_gpus": total_gpus,
                "used_gpus": set(used_gpus),
                "free_gpus": total_gpus - len(used_gpus),
                "worker": worker,
            }

        # Get pending instances
        pending = await self.db.get_pending_instances()

        for instance in pending:
            assignment = await self._try_assign_instance(instance, available)

            if assignment:
                worker_id, gpu_indices = assignment

                # Update tracking (only for exclusive)
                if instance.get("exclusive", True):
                    available[worker_id]["used_gpus"].update(gpu_indices)
                    available[worker_id]["free_gpus"] -= len(gpu_indices)

                # Wake worker's long-poll
                self.increment_gen(worker_id)

    def _parse_gpu_indices(self, raw: Optional[str]) -> Optional[List[int]]:
        """Parse JSON-encoded gpu_indices from database."""
        if not raw:
            return None
        try:
            import json
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    async def _try_assign_instance(
        self,
        instance: Dict[str, Any],
        available: Dict[str, Dict],
    ) -> Optional[Tuple[str, List[int]]]:
        """
        Try to assign an instance to a worker.

        Returns (worker_id, gpu_indices) if successful, None otherwise.
        """
        needed_gpus = instance.get("gpu_units") or 0
        exclusive = instance.get("exclusive", True)
        target_worker = instance.get("target_worker")
        requested_gpu_indices = self._parse_gpu_indices(instance.get("requested_gpu_indices"))

        # Case 1: Specific worker + specific GPUs
        if target_worker and requested_gpu_indices:
            return await self._assign_specific(
                instance, target_worker, requested_gpu_indices, exclusive, available
            )

        # Case 2: Specific worker, auto-allocate GPUs
        if target_worker:
            return await self._assign_to_worker(
                instance, target_worker, needed_gpus, exclusive, available
            )

        # Case 3: Any worker, auto-allocate GPUs
        return await self._assign_any_worker(
            instance, needed_gpus, exclusive, available
        )

    async def _assign_specific(
        self,
        instance: Dict[str, Any],
        target_worker: str,
        gpu_indices: List[int],
        exclusive: bool,
        available: Dict[str, Dict],
    ) -> Optional[Tuple[str, List[int]]]:
        """Assign to specific worker with specific GPUs."""

        if target_worker not in available:
            logger.warning(
                f"Instance {instance['id']}: target_worker {target_worker} not available"
            )
            return None

        worker_info = available[target_worker]

        # Validate GPU indices are within range
        if any(idx >= worker_info["total_gpus"] for idx in gpu_indices):
            logger.warning(
                f"Instance {instance['id']}: gpu_indices {gpu_indices} invalid "
                f"for worker {target_worker} (has {worker_info['total_gpus']} GPUs)"
            )
            return None

        # Check for exclusive overlap (only if this request is exclusive)
        if exclusive:
            overlap = set(gpu_indices) & worker_info["used_gpus"]
            if overlap:
                logger.info(
                    f"Instance {instance['id']}: GPUs {overlap} already exclusively "
                    f"allocated on {target_worker}, waiting..."
                )
                return None

        # Assign
        new_attempt = (instance.get("attempt") or 0) + 1
        success = await self.db.assign_instance(
            instance_id=instance["id"],
            worker_id=target_worker,
            new_attempt=new_attempt,
            gpu_indices=gpu_indices,
            exclusive=exclusive,
        )

        if success:
            logger.info(
                f"Assigned {instance['id']} attempt {new_attempt} to {target_worker} "
                f"(gpus={gpu_indices}, exclusive={exclusive})"
            )
            return (target_worker, gpu_indices)

        return None

    async def _assign_to_worker(
        self,
        instance: Dict[str, Any],
        target_worker: str,
        needed_gpus: int,
        exclusive: bool,
        available: Dict[str, Dict],
    ) -> Optional[Tuple[str, List[int]]]:
        """Assign to specific worker, auto-allocating GPUs."""

        if target_worker not in available:
            logger.warning(
                f"Instance {instance['id']}: target_worker {target_worker} not available"
            )
            return None

        worker_info = available[target_worker]

        # For exclusive requests, check availability
        if exclusive:
            if worker_info["free_gpus"] < needed_gpus:
                logger.info(
                    f"Instance {instance['id']}: {target_worker} has {worker_info['free_gpus']} "
                    f"free GPUs, need {needed_gpus}, waiting..."
                )
                return None

        # Select GPUs
        all_gpus = set(range(worker_info["total_gpus"]))

        if exclusive:
            # Pick from free GPUs
            free = all_gpus - worker_info["used_gpus"]
            gpu_indices = sorted(free)[:needed_gpus]
        else:
            # Non-exclusive: just pick first N GPUs (they share)
            gpu_indices = list(range(min(needed_gpus, worker_info["total_gpus"])))

        if len(gpu_indices) < needed_gpus:
            logger.warning(
                f"Instance {instance['id']}: cannot allocate {needed_gpus} GPUs on {target_worker}"
            )
            return None

        # Assign
        new_attempt = (instance.get("attempt") or 0) + 1
        success = await self.db.assign_instance(
            instance_id=instance["id"],
            worker_id=target_worker,
            new_attempt=new_attempt,
            gpu_indices=gpu_indices,
            exclusive=exclusive,
        )

        if success:
            logger.info(
                f"Assigned {instance['id']} attempt {new_attempt} to {target_worker} "
                f"(gpus={gpu_indices}, exclusive={exclusive})"
            )
            return (target_worker, gpu_indices)

        return None

    async def _assign_any_worker(
        self,
        instance: Dict[str, Any],
        needed_gpus: int,
        exclusive: bool,
        available: Dict[str, Dict],
    ) -> Optional[Tuple[str, List[int]]]:
        """Assign to any suitable worker, auto-allocating GPUs."""

        for worker_id, worker_info in available.items():
            # For exclusive, need enough free GPUs
            if exclusive and worker_info["free_gpus"] < needed_gpus:
                continue

            # For non-exclusive, just need enough total GPUs
            if not exclusive and worker_info["total_gpus"] < needed_gpus:
                continue

            # Select GPUs
            all_gpus = set(range(worker_info["total_gpus"]))

            if exclusive:
                free = all_gpus - worker_info["used_gpus"]
                gpu_indices = sorted(free)[:needed_gpus]
            else:
                gpu_indices = list(range(min(needed_gpus, worker_info["total_gpus"])))

            if len(gpu_indices) < needed_gpus:
                continue

            # Assign
            new_attempt = (instance.get("attempt") or 0) + 1
            success = await self.db.assign_instance(
                instance_id=instance["id"],
                worker_id=worker_id,
                new_attempt=new_attempt,
                gpu_indices=gpu_indices,
                exclusive=exclusive,
            )

            if success:
                logger.info(
                    f"Assigned {instance['id']} attempt {new_attempt} to {worker_id} "
                    f"(gpus={gpu_indices}, exclusive={exclusive})"
                )
                return (worker_id, gpu_indices)

        return None

    # ========== Legacy API compatibility ==========

    async def update_worker_heartbeat(self, worker_id: str) -> None:
        """Legacy heartbeat update (simple, no token)."""
        worker = await self.db.get_worker(worker_id)
        if not worker:
            raise ValueError("Worker not registered")
        await self.db.update_worker_heartbeat(worker_id)

    async def set_instance_endpoint(
        self, instance_id: str, host: str, port: int
    ) -> None:
        """Set endpoint for an instance (legacy API)."""
        instance = await self.db.get_instance(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found")

        endpoint = f"{host}:{port}"
        await self.db.set_instance_endpoint(instance_id, endpoint, port)
        logger.info(f"Instance {instance_id} endpoint set to {endpoint}")

    async def report_instance_result(
        self,
        worker_id: str,
        instance_id: str,
        success: bool,
        result_data: Any,
    ) -> None:
        """Report instance result (legacy API)."""
        instance = await self.db.get_instance(instance_id)
        if not instance:
            raise ValueError("Instance not found")
        if instance["assigned_worker"] != worker_id:
            raise ValueError("Worker not assigned to this instance")

        exit_code = 0 if success else 1
        status = "COMPLETED" if success else "FAILED"

        await self.db.transition_to_terminal(
            instance_id, instance["attempt"], status, exit_code
        )

        logger.info(f"Instance {instance_id} {status} by worker {worker_id}")
        self.poke_scheduler()

    async def update_instance_status(
        self, worker_id: str, instance_id: str, status_update: Dict[str, Any]
    ) -> None:
        """Update instance status (legacy API)."""
        instance = await self.db.get_instance(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} does not exist.")
        if instance["assigned_worker"] != worker_id:
            raise ValueError(f"Instance {instance_id} is not assigned to worker {worker_id}.")

        # Handle RUNNING status
        if status_update.get("status") == "RUNNING":
            port = status_update.get("port")
            worker = await self.db.get_worker(worker_id)
            worker_ip = worker["ip"] if worker else "127.0.0.1"
            endpoint = f"{worker_ip}:{port}" if port else None

            await self.db.update_instance_running_legacy(instance_id, port, endpoint)
            logger.info(f"Instance {instance_id} is now RUNNING on worker {worker_id}")
