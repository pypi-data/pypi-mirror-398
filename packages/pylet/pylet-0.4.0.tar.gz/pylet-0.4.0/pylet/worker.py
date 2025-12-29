"""
PyLet Worker - Declarative reconciliation-based worker node.

Implements:
- Process group management for clean termination
- Local state persistence for crash recovery
- Generation-based heartbeat with cancel-and-reissue
- Full reconciliation of desired vs actual state
"""

import asyncio
import json
import os
import shlex
import signal
import socket
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

from pylet import config
from pylet.logger import logger
from pylet.schemas import DesiredInstance, HeartbeatRequest, HeartbeatResponse, InstanceReport
from pylet import worker_http


@dataclass
class ProcessInfo:
    """Information about a running process."""
    pid: int
    pgid: int
    instance_id: str
    attempt: int
    port: int
    status: str = "RUNNING"  # RUNNING, STOPPING, COMPLETED, FAILED, CANCELLED
    exit_code: Optional[int] = None
    process: Optional[asyncio.subprocess.Process] = None
    stop_deadline: Optional[float] = None  # time.time() when SIGKILL should be sent


class LocalStateManager:
    """Persists minimal process state to disk for crash recovery."""

    def __init__(self, state_dir: Optional[Path] = None):
        self.state_dir = state_dir or config.RUN_DIR
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save_state(
        self,
        instance_id: str,
        attempt: int,
        pgid: int,
        port: int,
    ) -> None:
        """Persist process state to disk."""
        state_file = self.state_dir / f"{instance_id}.{attempt}.state"
        state_file.write_text(
            json.dumps({
                "instance_id": instance_id,
                "attempt": attempt,
                "pgid": pgid,
                "port": port,
            })
        )

    def load_all_states(self) -> List[Dict[str, Any]]:
        """Load all persisted states."""
        states = []
        for state_file in self.state_dir.glob("*.state"):
            try:
                states.append(json.loads(state_file.read_text()))
            except Exception as e:
                logger.error(f"Failed to load {state_file}: {e}")
        return states

    def remove_state(self, instance_id: str, attempt: int) -> None:
        """Remove state file."""
        state_file = self.state_dir / f"{instance_id}.{attempt}.state"
        state_file.unlink(missing_ok=True)

    def clear_all(self) -> None:
        """Remove all state files."""
        for state_file in self.state_dir.glob("*.state"):
            state_file.unlink()


def kill_process_group(pgid: int) -> None:
    """Kill entire process group forcefully (used for startup cleanup)."""
    try:
        os.killpg(pgid, signal.SIGTERM)
        # Give processes time to cleanup
        time.sleep(0.5)
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # Already dead
    except ProcessLookupError:
        pass  # Already dead
    except Exception as e:
        logger.warning(f"Error killing process group {pgid}: {e}")


def send_sigterm(pgid: int) -> bool:
    """Send SIGTERM to process group. Returns True if signal was sent."""
    try:
        os.killpg(pgid, signal.SIGTERM)
        return True
    except ProcessLookupError:
        return False  # Already dead
    except Exception as e:
        logger.warning(f"Error sending SIGTERM to process group {pgid}: {e}")
        return False


def send_sigkill(pgid: int) -> bool:
    """Send SIGKILL to process group. Returns True if signal was sent."""
    try:
        os.killpg(pgid, signal.SIGKILL)
        return True
    except ProcessLookupError:
        return False  # Already dead
    except Exception as e:
        logger.warning(f"Error sending SIGKILL to process group {pgid}: {e}")
        return False


# ========== Worker ==========

class Worker:
    """
    Worker node that executes instances via declarative reconciliation.

    Workers don't receive imperative commands. Instead, they:
    1. Send heartbeats with local state
    2. Receive desired state in response
    3. Reconcile local state with desired state
    """

    def __init__(
        self,
        head_address: str,
        cpu_cores: int = 4,
        gpu_units: int = 0,
        memory_mb: int = 4096,
    ):
        self.worker_id = str(uuid.uuid4())
        self.head_address = head_address
        # Handle both "host:port" and "http://host:port" formats
        if head_address.startswith("http://") or head_address.startswith("https://"):
            self.api_server_url = head_address
        else:
            self.api_server_url = f"http://{head_address}"
        self.host = socket.gethostbyname(socket.gethostname())

        self.total_resources = {
            "cpu_cores": cpu_cores,
            "gpu_units": gpu_units,
            "memory_mb": memory_mb,
        }

        # State
        self.worker_token: Optional[str] = None
        self.boot_id = str(uuid.uuid4())
        self.last_seen_gen = 0

        # Local instances: (instance_id, attempt) -> ProcessInfo
        self.local_instances: Dict[Tuple[str, int], ProcessInfo] = {}

        # Last desired state from controller (used to infer NOT_FOUND)
        self.last_desired: List[DesiredInstance] = []

        # Port allocation
        self.port_range = (config.WORKER_PORT_MIN, config.WORKER_PORT_MAX)
        self.used_ports: Set[int] = set()

        # State persistence
        self.state_manager = LocalStateManager()

        # Heartbeat control
        self.inflight_heartbeat: Optional[asyncio.Task] = None
        self.heartbeat_event = asyncio.Event()

    async def run(self) -> None:
        """Main worker loop."""
        # Clean slate on startup
        await self._startup_cleanup()

        # Ensure log directory exists
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(timeout=60.0) as client:
            self.client = client

            # Register with controller
            if not await self._register():
                return

            # Start background tasks
            heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            monitor_task = asyncio.create_task(self._monitor_processes())
            http_task = asyncio.create_task(self._run_http_server())

            try:
                await asyncio.gather(heartbeat_task, monitor_task, http_task)
            except asyncio.CancelledError:
                pass
            finally:
                heartbeat_task.cancel()
                monitor_task.cancel()
                http_task.cancel()

    async def _startup_cleanup(self) -> None:
        """Clean slate on worker start - kill orphaned processes."""
        old_states = self.state_manager.load_all_states()
        for state in old_states:
            pgid = state.get("pgid")
            if pgid:
                logger.info(f"Killing orphaned process group: pgid={pgid}")
                kill_process_group(pgid)

        self.state_manager.clear_all()
        self.local_instances = {}
        logger.info(f"Worker startup cleanup complete")

    async def _register(self) -> bool:
        """Register with the controller and obtain token."""
        try:
            response = await self.client.post(
                f"{self.api_server_url}/workers",
                json={
                    "worker_id": self.worker_id,
                    "host": self.host,
                    "resources": self.total_resources,
                    "boot_id": self.boot_id,
                },
            )
            response.raise_for_status()
            data = response.json()

            # Get token from response
            self.worker_token = data.get("worker_token")
            if not self.worker_token:
                # Legacy server - generate placeholder token
                self.worker_token = "legacy"

            logger.info(
                f"Worker {self.worker_id} ({self.host}) registered with "
                f"resources: {self.total_resources}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to register worker {self.worker_id}: {e}")
            return False

    # ========== Heartbeat Protocol ==========

    async def _heartbeat_loop(self) -> None:
        """
        Heartbeat loop with cancel-and-reissue pattern.

        When local state changes, the in-flight heartbeat is cancelled
        and a new one is issued immediately with updated state.
        """
        while True:
            self.inflight_heartbeat = asyncio.create_task(self._do_heartbeat())
            try:
                response = await self.inflight_heartbeat
                if response:
                    self.last_seen_gen = response.gen
                    self.last_desired = response.desired_instances
                    await self._reconcile(response.desired_instances)
            except asyncio.CancelledError:
                # Local state changed, reissue immediately
                continue
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)  # Backoff on error

    async def _do_heartbeat(self) -> Optional[HeartbeatResponse]:
        """Execute a single heartbeat."""
        try:
            request = HeartbeatRequest(
                worker_token=self.worker_token,
                boot_id=self.boot_id,
                last_seen_gen=self.last_seen_gen,
                instances=self._get_instance_reports(),
            )

            response = await self.client.post(
                f"{self.api_server_url}/workers/{self.worker_id}/heartbeat",
                json=request.model_dump(),
                timeout=35.0,  # Slightly longer than server poll timeout
            )
            response.raise_for_status()
            return HeartbeatResponse(**response.json())
        except httpx.TimeoutException:
            # Normal timeout from long-poll
            return None
        except Exception as e:
            logger.error(f"Heartbeat request failed: {e}")
            raise

    def _get_instance_reports(self) -> List[InstanceReport]:
        """Generate reports for all local instances."""
        reports = []
        for (instance_id, attempt), proc in self.local_instances.items():
            reports.append(
                InstanceReport(
                    instance_id=instance_id,
                    attempt=attempt,
                    status=proc.status,
                    port=proc.port,
                    exit_code=proc.exit_code,
                )
            )
        # Report NOT_FOUND for desired instances we don't have evidence for.
        for inst in self.last_desired:
            key = (inst.instance_id, inst.attempt)
            if inst.expected_status != "ASSIGNED" and key not in self.local_instances:
                reports.append(
                    InstanceReport(
                        instance_id=inst.instance_id,
                        attempt=inst.attempt,
                        status="NOT_FOUND",
                    )
                )
        return reports

    def _trigger_heartbeat(self) -> None:
        """Cancel in-flight heartbeat to trigger immediate reissue."""
        if self.inflight_heartbeat and not self.inflight_heartbeat.done():
            self.inflight_heartbeat.cancel()

    # ========== Reconciliation ==========

    async def _reconcile(self, desired: List[DesiredInstance]) -> None:
        """
        Reconcile local state with desired state.

        1. Start graceful stop for anything not in desired state
        2. Start anything desired but not running
        3. Report NOT_FOUND for instances we don't have
        """
        desired_keys = {(d.instance_id, d.attempt) for d in desired}

        # Phase 1: Start graceful stop for unwanted instances
        for key in list(self.local_instances.keys()):
            if key not in desired_keys:
                proc = self.local_instances[key]
                if proc.status == "RUNNING":
                    # Start graceful shutdown - send SIGTERM and set deadline
                    logger.info(f"Starting graceful stop for instance: {key}")
                    send_sigterm(proc.pgid)
                    proc.status = "STOPPING"
                    proc.stop_deadline = time.time() + config.DEFAULT_GRACE_PERIOD_SECONDS
                    # Don't trigger heartbeat yet - monitor will handle status transition
                    continue

                # STOPPING instances are handled by monitor loop
                if proc.status == "STOPPING":
                    continue

                # Clean up terminal instances that are no longer desired
                # (these have already been reported in a previous heartbeat)
                if proc.status in ("COMPLETED", "FAILED", "CANCELLED"):
                    self.state_manager.remove_state(*key)
                    self._release_port(proc.port)
                    del self.local_instances[key]

        # Phase 2: Start or report NOT_FOUND for desired instances
        for inst in desired:
            key = (inst.instance_id, inst.attempt)
            if key not in self.local_instances:
                # We don't have this instance
                if inst.expected_status == "ASSIGNED":
                    # Fresh assignment - start it
                    await self._start_instance(inst)
                else:
                    # Controller thinks it should be running but we don't have it.
                    # NOT_FOUND is reported via heartbeats from last_desired.
                    logger.warning(f"Instance {key} expected but not found")

    async def _run_http_server(self) -> None:
        """Run the worker HTTP server for log retrieval."""
        try:
            await worker_http.run_server()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Worker HTTP server error: {e}")

    async def _start_instance(self, inst: DesiredInstance) -> None:
        """Start an instance process in its own session with log capture."""
        key = (inst.instance_id, inst.attempt)
        port = self._allocate_port()

        if port is None:
            logger.error(f"No available port for instance {inst.instance_id}")
            return

        # Prepare environment
        # Order matters: user env first, then Pylet-managed vars (PORT, CUDA_VISIBLE_DEVICES)
        # to ensure users cannot override resource allocation and service discovery
        env = os.environ.copy()
        for k, v in inst.env.items():
            env[k] = v
        # Pylet-managed vars always override user values
        env["PORT"] = str(port)
        if inst.gpu_indices:
            env["CUDA_VISIBLE_DEVICES"] = ",".join(str(i) for i in inst.gpu_indices)

        # Build shell command with log sidecar
        # Uses pipefail to get user command exit code, not sidecar's
        # Uses trap "" PIPE to let task continue if sidecar crashes
        log_dir = str(config.LOG_DIR)
        escaped_cmd = inst.command.replace("'", "'\"'\"'")  # Escape single quotes

        # Activate venv if specified (before user command, not sidecar)
        if inst.venv:
            # Use double quotes inside the single-quoted bash command to handle spaces
            # Escape any double quotes or backslashes in the path
            safe_venv = inst.venv.replace("\\", "\\\\").replace('"', '\\"')
            venv_activate = f'source "{safe_venv}/bin/activate" && '
        else:
            venv_activate = ""

        shell_cmd = (
            f"/bin/bash -c 'set -o pipefail; trap \"\" PIPE; "
            f"({venv_activate}{escaped_cmd}) 2>&1 | "
            f"python3 -m pylet.log_sidecar {shlex.quote(log_dir)} "
            f"{shlex.quote(inst.instance_id)}'"
        )

        try:
            # Start process in new session (setsid for isolation)
            process = await asyncio.create_subprocess_shell(
                shell_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                env=env,
                start_new_session=True,  # Equivalent to setsid
            )

            # Get pgid - use pid if process exited very quickly
            try:
                pgid = os.getpgid(process.pid)
            except ProcessLookupError:
                # Process already exited - use pid as pgid (it was leader)
                pgid = process.pid

            proc_info = ProcessInfo(
                pid=process.pid,
                pgid=pgid,
                instance_id=inst.instance_id,
                attempt=inst.attempt,
                port=port,
                status="RUNNING",
                process=process,
            )

            # Persist state
            self.state_manager.save_state(inst.instance_id, inst.attempt, pgid, port)

            # Track locally
            self.local_instances[key] = proc_info

            logger.info(
                f"Started instance {inst.instance_id} attempt {inst.attempt} "
                f"(pid={process.pid}, pgid={pgid}, port={port})"
            )

            # Trigger immediate heartbeat to report RUNNING
            self._trigger_heartbeat()

        except Exception as e:
            logger.error(f"Failed to start instance {inst.instance_id}: {e}")
            self._release_port(port)

    # ========== Process Monitoring ==========

    async def _monitor_processes(self) -> None:
        """Background task to monitor process exits and handle graceful stops."""
        while True:
            for key, proc in list(self.local_instances.items()):
                if proc.status == "STOPPING" and proc.process:
                    # Check if process exited during grace period
                    ret = proc.process.returncode
                    if ret is not None:
                        # Process exited gracefully
                        proc.exit_code = ret
                        proc.status = "CANCELLED"
                        logger.info(
                            f"Instance {key} stopped gracefully, exit_code={ret}"
                        )
                        self._trigger_heartbeat()
                    elif proc.stop_deadline and time.time() > proc.stop_deadline:
                        # Grace period expired, force kill
                        logger.warning(
                            f"Instance {key} grace period expired, sending SIGKILL"
                        )
                        send_sigkill(proc.pgid)
                        proc.exit_code = -9  # Indicate killed by SIGKILL
                        proc.status = "CANCELLED"
                        self._trigger_heartbeat()

                elif proc.status == "RUNNING" and proc.process:
                    # Check if process has exited normally
                    try:
                        ret = proc.process.returncode
                        if ret is not None:
                            proc.exit_code = ret
                            proc.status = "COMPLETED" if ret == 0 else "FAILED"
                            logger.info(
                                f"Instance {key} exited with code {ret}"
                            )
                            self._trigger_heartbeat()
                    except Exception as e:
                        logger.error(f"Error checking process {key}: {e}")

            await asyncio.sleep(0.5)

    # ========== Port Allocation ==========

    def _allocate_port(self) -> Optional[int]:
        """Allocate a free port."""
        for port in range(self.port_range[0], self.port_range[1] + 1):
            if port not in self.used_ports:
                self.used_ports.add(port)
                return port
        return None

    def _release_port(self, port: int) -> None:
        """Release a port."""
        self.used_ports.discard(port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PyLet Worker")
    parser.add_argument("head_address", type=str, help="Address of the head node")
    parser.add_argument("--cpu-cores", type=int, default=4, help="Number of CPU cores")
    parser.add_argument("--gpu-units", type=int, default=0, help="Number of GPU units")
    parser.add_argument("--memory-mb", type=int, default=4096, help="Memory in MB")
    args = parser.parse_args()

    worker = Worker(
        args.head_address, args.cpu_cores, args.gpu_units, args.memory_mb
    )
    asyncio.run(worker.run())
