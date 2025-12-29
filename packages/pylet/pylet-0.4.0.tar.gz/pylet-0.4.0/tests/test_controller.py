"""Unit tests for pylet.controller module."""

import pytest
import pytest_asyncio
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from pylet.controller import Controller
from pylet.schemas import (
    ResourceSpec,
    HeartbeatRequest,
    InstanceReport,
    InstanceStatus,
)


@pytest_asyncio.fixture
async def controller():
    """Create a controller with a temporary database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    ctrl = Controller(db_path)
    await ctrl.startup()
    yield ctrl
    await ctrl.shutdown()

    # Cleanup
    db_path.unlink(missing_ok=True)
    for ext in ["-wal", "-shm"]:
        Path(str(db_path) + ext).unlink(missing_ok=True)


class TestControllerStartup:
    """Tests for controller startup behavior."""

    @pytest.mark.asyncio
    async def test_startup_marks_workers_suspect(self, controller):
        """Test that startup marks all workers as SUSPECT."""
        # Register a worker first
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        # Verify it's ONLINE
        worker = await controller.get_worker("w1")
        assert worker["status"] == "ONLINE"

        # Create new controller (simulates restart)
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        ctrl2 = Controller(controller.db.db_path)
        await ctrl2.startup()

        # Worker should now be SUSPECT
        worker = await ctrl2.get_worker("w1")
        assert worker["status"] == "SUSPECT"

        await ctrl2.shutdown()


class TestWorkerRegistration:
    """Tests for worker registration."""

    @pytest.mark.asyncio
    async def test_register_new_worker(self, controller):
        """Test registering a new worker."""
        resources = ResourceSpec(cpu_cores=8, gpu_units=4, memory_mb=32768)
        token = await controller.register_worker("worker-1", "192.168.1.1", resources)

        assert token is not None
        assert len(token) > 0

        worker = await controller.get_worker("worker-1")
        assert worker is not None
        assert worker["id"] == "worker-1"
        assert worker["ip"] == "192.168.1.1"
        assert worker["status"] == "ONLINE"
        assert worker["cpu_cores"] == 8
        assert worker["gpu_units"] == 4

    @pytest.mark.asyncio
    async def test_register_worker_creates_generation(self, controller):
        """Test that registering creates generation counter."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=0, memory_mb=4096)
        await controller.register_worker("w1", "1.1.1.1", resources)

        assert "w1" in controller.desired_gen
        assert controller.desired_gen["w1"] == 0
        assert "w1" in controller.gen_events

    @pytest.mark.asyncio
    async def test_reconnect_worker_new_token(self, controller):
        """Test that reconnecting worker gets new token."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)

        token1 = await controller.register_worker("w1", "1.1.1.1", resources)
        token2 = await controller.register_worker("w1", "1.1.1.2", resources)

        # Should get different tokens
        assert token1 != token2

        # Worker should be updated
        worker = await controller.get_worker("w1")
        assert worker["ip"] == "1.1.1.2"
        assert worker["worker_token"] == token2

    @pytest.mark.asyncio
    async def test_get_all_workers(self, controller):
        """Test getting all workers."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)

        await controller.register_worker("w1", "1.1.1.1", resources)
        await controller.register_worker("w2", "2.2.2.2", resources)

        workers = await controller.get_all_workers()
        assert len(workers) == 2


class TestInstanceSubmission:
    """Tests for instance submission."""

    @pytest.mark.asyncio
    async def test_submit_instance(self, controller):
        """Test submitting an instance."""
        resources = ResourceSpec(cpu_cores=2, gpu_units=1, memory_mb=4096)

        instance_id = await controller.submit_instance(
            command="python train.py",
            resource_requirements=resources,
            name="my-instance",
        )

        assert instance_id is not None

        instance = await controller.get_instance(instance_id)
        assert instance is not None
        assert instance["command"] == "python train.py"
        assert instance["name"] == "my-instance"
        assert instance["status"] == "PENDING"

    @pytest.mark.asyncio
    async def test_submit_instance_auto_name(self, controller):
        """Test that instance gets auto-generated name if not provided."""
        resources = ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512)

        instance_id = await controller.submit_instance(
            command="echo hello",
            resource_requirements=resources,
        )

        instance = await controller.get_instance(instance_id)
        # Auto-generated name should be first 8 chars of UUID
        assert instance["name"] == instance_id[:8]

    @pytest.mark.asyncio
    async def test_submit_instance_duplicate_name_raises(self, controller):
        """Test that duplicate name raises error."""
        resources = ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512)

        await controller.submit_instance(
            command="cmd1",
            resource_requirements=resources,
            name="unique-name",
        )

        with pytest.raises(ValueError, match="already exists"):
            await controller.submit_instance(
                command="cmd2",
                resource_requirements=resources,
                name="unique-name",
            )

    @pytest.mark.asyncio
    async def test_get_instance_by_name(self, controller):
        """Test getting instance by name."""
        resources = ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512)

        instance_id = await controller.submit_instance(
            command="echo test",
            resource_requirements=resources,
            name="named-instance",
        )

        instance = await controller.get_instance_by_name("named-instance")
        assert instance is not None
        assert instance["id"] == instance_id

    @pytest.mark.asyncio
    async def test_get_instance_by_name_not_found(self, controller):
        """Test that getting non-existent name returns None."""
        instance = await controller.get_instance_by_name("no-such-name")
        assert instance is None


class TestHeartbeatProtocol:
    """Tests for heartbeat protocol."""

    @pytest.mark.asyncio
    async def test_heartbeat_validates_token(self, controller):
        """Test that heartbeat validates worker token."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        request = HeartbeatRequest(
            worker_token="invalid-token",
            boot_id="boot-123",
        )

        with pytest.raises(ValueError, match="Invalid worker token"):
            await controller.process_heartbeat("w1", request)

    @pytest.mark.asyncio
    async def test_heartbeat_validates_worker_exists(self, controller):
        """Test that heartbeat validates worker exists."""
        request = HeartbeatRequest(
            worker_token="any-token",
            boot_id="boot-123",
        )

        with pytest.raises(ValueError, match="not registered"):
            await controller.process_heartbeat("non-existent", request)

    @pytest.mark.asyncio
    @patch("pylet.controller.config.HEARTBEAT_POLL_TIMEOUT", 0.1)
    async def test_heartbeat_returns_desired_instances(self, controller):
        """Test that heartbeat returns desired instances."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        token = await controller.register_worker("w1", "1.1.1.1", resources)

        # Submit and assign an instance manually
        instance_id = await controller.submit_instance(
            command="echo hello",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        # Run scheduler to assign
        await controller._run_scheduling_cycle()

        request = HeartbeatRequest(
            worker_token=token,
            boot_id="boot-123",
        )

        response = await controller.process_heartbeat("w1", request)

        assert response.gen >= 0
        assert len(response.desired_instances) == 1
        assert response.desired_instances[0].instance_id == instance_id

    @pytest.mark.asyncio
    @patch("pylet.controller.config.HEARTBEAT_POLL_TIMEOUT", 0.1)
    async def test_heartbeat_processes_running_report(self, controller):
        """Test that heartbeat processes RUNNING reports."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        token = await controller.register_worker("w1", "1.1.1.1", resources)

        instance_id = await controller.submit_instance(
            command="server",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        # Get the attempt
        instance = await controller.get_instance(instance_id)
        attempt = instance["attempt"]

        # Report RUNNING
        request = HeartbeatRequest(
            worker_token=token,
            boot_id="boot-123",
            instances=[
                InstanceReport(
                    instance_id=instance_id,
                    attempt=attempt,
                    status="RUNNING",
                    port=15600,
                )
            ],
        )

        await controller.process_heartbeat("w1", request)

        instance = await controller.get_instance(instance_id)
        assert instance["status"] == "RUNNING"
        assert instance["port"] == 15600
        assert instance["endpoint"] == "1.1.1.1:15600"

    @pytest.mark.asyncio
    @patch("pylet.controller.config.HEARTBEAT_POLL_TIMEOUT", 0.1)
    async def test_heartbeat_processes_completed_report(self, controller):
        """Test that heartbeat processes COMPLETED reports."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        token = await controller.register_worker("w1", "1.1.1.1", resources)

        instance_id = await controller.submit_instance(
            command="echo done",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        instance = await controller.get_instance(instance_id)
        attempt = instance["attempt"]

        # Report RUNNING first
        await controller.process_heartbeat("w1", HeartbeatRequest(
            worker_token=token,
            boot_id="boot-123",
            instances=[InstanceReport(instance_id=instance_id, attempt=attempt, status="RUNNING", port=15600)],
        ))

        # Report COMPLETED
        await controller.process_heartbeat("w1", HeartbeatRequest(
            worker_token=token,
            boot_id="boot-123",
            instances=[InstanceReport(instance_id=instance_id, attempt=attempt, status="COMPLETED", exit_code=0)],
        ))

        instance = await controller.get_instance(instance_id)
        assert instance["status"] == "COMPLETED"
        assert instance["exit_code"] == 0

    @pytest.mark.asyncio
    @patch("pylet.controller.config.HEARTBEAT_POLL_TIMEOUT", 0.1)
    async def test_heartbeat_ignores_stale_attempt(self, controller):
        """Test that heartbeat ignores stale attempt reports (fencing)."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        token = await controller.register_worker("w1", "1.1.1.1", resources)

        instance_id = await controller.submit_instance(
            command="echo test",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        # Report with stale attempt (0 instead of 1)
        request = HeartbeatRequest(
            worker_token=token,
            boot_id="boot-123",
            instances=[
                InstanceReport(
                    instance_id=instance_id,
                    attempt=0,  # Stale attempt
                    status="RUNNING",
                    port=15600,
                )
            ],
        )

        await controller.process_heartbeat("w1", request)

        # Instance should still be ASSIGNED (report ignored)
        instance = await controller.get_instance(instance_id)
        assert instance["status"] == "ASSIGNED"


class TestGenerationMechanism:
    """Tests for generation-based long-poll."""

    @pytest.mark.asyncio
    async def test_increment_gen(self, controller):
        """Test incrementing generation."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        assert controller.desired_gen["w1"] == 0

        controller.increment_gen("w1")
        assert controller.desired_gen["w1"] == 1

        controller.increment_gen("w1")
        assert controller.desired_gen["w1"] == 2

    @pytest.mark.asyncio
    async def test_wait_for_gen_change_returns_immediately_if_changed(self, controller):
        """Test that wait returns immediately if gen already changed."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        controller.increment_gen("w1")

        gen = await controller._wait_for_gen_change("w1", 0, timeout=10.0)
        assert gen == 1

    @pytest.mark.asyncio
    async def test_wait_for_gen_change_times_out(self, controller):
        """Test that wait times out if no change."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        # Should timeout
        gen = await controller._wait_for_gen_change("w1", 0, timeout=0.1)
        assert gen == 0


class TestCancellation:
    """Tests for instance cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_pending_instance(self, controller):
        """Test cancelling a PENDING instance."""
        resources = ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512)
        instance_id = await controller.submit_instance(
            command="sleep 100",
            resource_requirements=resources,
        )

        success = await controller.request_cancellation(instance_id)
        assert success is True

        instance = await controller.get_instance(instance_id)
        assert instance["status"] == "CANCELLED"

    @pytest.mark.asyncio
    async def test_cancel_running_instance_sets_timestamp(self, controller):
        """Test that cancelling a RUNNING instance sets timestamp."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        token = await controller.register_worker("w1", "1.1.1.1", resources)

        instance_id = await controller.submit_instance(
            command="sleep 100",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        # Make it RUNNING
        instance = await controller.get_instance(instance_id)
        await controller.db.update_instance_running(
            instance_id, instance["attempt"], 15600, "1.1.1.1:15600"
        )

        success = await controller.request_cancellation(instance_id)
        assert success is True

        instance = await controller.get_instance(instance_id)
        # Status should still be RUNNING, but cancel_requested_at should be set
        assert instance["status"] == "RUNNING"
        assert instance["cancel_requested_at"] is not None

    @pytest.mark.asyncio
    async def test_cancel_terminal_instance_fails(self, controller):
        """Test that cancelling a terminal instance fails."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        instance_id = await controller.submit_instance(
            command="exit 0",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        instance = await controller.get_instance(instance_id)
        await controller.db.transition_to_terminal(
            instance_id, instance["attempt"], "COMPLETED", 0
        )

        success = await controller.request_cancellation(instance_id)
        assert success is False

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_instance(self, controller):
        """Test that cancelling non-existent instance fails."""
        success = await controller.request_cancellation("no-such-instance")
        assert success is False

    @pytest.mark.asyncio
    async def test_cancel_idempotent(self, controller):
        """Test that cancellation is idempotent."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        instance_id = await controller.submit_instance(
            command="sleep 100",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        # Make it RUNNING
        instance = await controller.get_instance(instance_id)
        await controller.db.update_instance_running(
            instance_id, instance["attempt"], 15600, "1.1.1.1:15600"
        )

        # Cancel twice
        success1 = await controller.request_cancellation(instance_id)
        success2 = await controller.request_cancellation(instance_id)

        assert success1 is True
        assert success2 is True  # Idempotent


class TestScheduler:
    """Tests for scheduler logic."""

    @pytest.mark.asyncio
    async def test_scheduler_assigns_to_online_worker(self, controller):
        """Test that scheduler assigns instances to online workers."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        instance_id = await controller.submit_instance(
            command="echo hello",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        instance = await controller.get_instance(instance_id)
        assert instance["status"] == "ASSIGNED"
        assert instance["assigned_worker"] == "w1"
        assert instance["attempt"] == 1

    @pytest.mark.asyncio
    async def test_scheduler_skips_offline_worker(self, controller):
        """Test that scheduler skips offline workers."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        # Mark worker offline
        await controller.db.update_worker_status("w1", "OFFLINE")

        instance_id = await controller.submit_instance(
            command="echo hello",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        instance = await controller.get_instance(instance_id)
        assert instance["status"] == "PENDING"  # Not assigned

    @pytest.mark.asyncio
    async def test_scheduler_respects_gpu_availability(self, controller):
        """Test that scheduler respects GPU availability."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        # Submit instance requiring 2 GPUs
        id1 = await controller.submit_instance(
            command="cmd1",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=2, memory_mb=512),
        )

        # Submit another requiring 1 GPU
        id2 = await controller.submit_instance(
            command="cmd2",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        inst1 = await controller.get_instance(id1)
        inst2 = await controller.get_instance(id2)

        # First should be assigned (uses all 2 GPUs)
        assert inst1["status"] == "ASSIGNED"
        # Second should remain pending (no GPUs left)
        assert inst2["status"] == "PENDING"

    @pytest.mark.asyncio
    async def test_scheduler_allocates_gpus(self, controller):
        """Test that scheduler allocates specific GPU indices."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=4, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        instance_id = await controller.submit_instance(
            command="train",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=2, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        instance = await controller.get_instance(instance_id)
        allocations = await controller.db.get_instance_allocations(instance_id, instance["attempt"])

        assert len(allocations) == 2
        gpu_indices = {a["gpu_index"] for a in allocations}
        assert gpu_indices.issubset({0, 1, 2, 3})

    @pytest.mark.asyncio
    async def test_scheduler_increments_gen_on_assignment(self, controller):
        """Test that scheduler increments generation when assigning."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        initial_gen = controller.desired_gen["w1"]

        await controller.submit_instance(
            command="cmd",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        assert controller.desired_gen["w1"] > initial_gen


class TestLivenessEvaluation:
    """Tests for worker liveness evaluation."""

    @pytest.mark.asyncio
    @patch("pylet.controller.config.SUSPECT_THRESHOLD_SECONDS", 0)
    async def test_mark_stale_workers_suspect(self, controller):
        """Test marking stale workers as SUSPECT."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        # Worker should be ONLINE initially
        worker = await controller.get_worker("w1")
        assert worker["status"] == "ONLINE"

        # With threshold 0, worker should be marked SUSPECT
        await controller.evaluate_liveness()

        worker = await controller.get_worker("w1")
        assert worker["status"] == "SUSPECT"

    @pytest.mark.asyncio
    @patch("pylet.controller.config.SUSPECT_THRESHOLD_SECONDS", 0)
    @patch("pylet.controller.config.OFFLINE_THRESHOLD_SECONDS", 0)
    async def test_mark_worker_offline(self, controller):
        """Test marking worker as OFFLINE."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        await controller.evaluate_liveness()

        worker = await controller.get_worker("w1")
        assert worker["status"] == "OFFLINE"

    @pytest.mark.asyncio
    @patch("pylet.controller.config.SUSPECT_THRESHOLD_SECONDS", 0)
    @patch("pylet.controller.config.OFFLINE_THRESHOLD_SECONDS", 0)
    async def test_worker_offline_marks_instances_unknown(self, controller):
        """Test that worker going offline marks instances as UNKNOWN."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        await controller.register_worker("w1", "1.1.1.1", resources)

        instance_id = await controller.submit_instance(
            command="cmd",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        # Make instance RUNNING
        instance = await controller.get_instance(instance_id)
        await controller.db.update_instance_running(
            instance_id, instance["attempt"], 15600, "1.1.1.1:15600"
        )

        # Worker goes offline
        await controller.evaluate_liveness()

        instance = await controller.get_instance(instance_id)
        assert instance["status"] == "UNKNOWN"


class TestNotFoundHandling:
    """Tests for NOT_FOUND report handling."""

    @pytest.mark.asyncio
    @patch("pylet.controller.config.HEARTBEAT_POLL_TIMEOUT", 0.1)
    async def test_not_found_marks_instance_failed(self, controller):
        """Test that NOT_FOUND report marks instance as FAILED."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        token = await controller.register_worker("w1", "1.1.1.1", resources)

        instance_id = await controller.submit_instance(
            command="cmd",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        instance = await controller.get_instance(instance_id)
        attempt = instance["attempt"]

        # Make it RUNNING first (NOT_FOUND only handled for non-ASSIGNED)
        await controller.db.update_instance_running(
            instance_id, attempt, 15600, "1.1.1.1:15600"
        )

        # Report NOT_FOUND
        request = HeartbeatRequest(
            worker_token=token,
            boot_id="boot-123",
            instances=[
                InstanceReport(
                    instance_id=instance_id,
                    attempt=attempt,
                    status="NOT_FOUND",
                )
            ],
        )

        await controller.process_heartbeat("w1", request)

        instance = await controller.get_instance(instance_id)
        assert instance["status"] == "FAILED"
        assert instance["failure_reason"] == "LOST_AFTER_REJOIN"


class TestCancelledReportHandling:
    """Tests for CANCELLED report handling."""

    @pytest.mark.asyncio
    @patch("pylet.controller.config.HEARTBEAT_POLL_TIMEOUT", 0.1)
    async def test_cancelled_with_request_becomes_cancelled(self, controller):
        """Test that CANCELLED report with cancel request becomes CANCELLED."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        token = await controller.register_worker("w1", "1.1.1.1", resources)

        instance_id = await controller.submit_instance(
            command="sleep 100",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        instance = await controller.get_instance(instance_id)
        attempt = instance["attempt"]

        # Make it RUNNING
        await controller.db.update_instance_running(
            instance_id, attempt, 15600, "1.1.1.1:15600"
        )

        # Request cancellation
        await controller.request_cancellation(instance_id)

        # Report CANCELLED
        request = HeartbeatRequest(
            worker_token=token,
            boot_id="boot-123",
            instances=[
                InstanceReport(
                    instance_id=instance_id,
                    attempt=attempt,
                    status="CANCELLED",
                )
            ],
        )

        await controller.process_heartbeat("w1", request)

        instance = await controller.get_instance(instance_id)
        assert instance["status"] == "CANCELLED"

    @pytest.mark.asyncio
    @patch("pylet.controller.config.HEARTBEAT_POLL_TIMEOUT", 0.1)
    async def test_cancelled_without_request_becomes_failed(self, controller):
        """Test that CANCELLED report without cancel request becomes FAILED."""
        resources = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        token = await controller.register_worker("w1", "1.1.1.1", resources)

        instance_id = await controller.submit_instance(
            command="cmd",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=512),
        )

        await controller._run_scheduling_cycle()

        instance = await controller.get_instance(instance_id)
        attempt = instance["attempt"]

        # Make it RUNNING
        await controller.db.update_instance_running(
            instance_id, attempt, 15600, "1.1.1.1:15600"
        )

        # Report CANCELLED without requesting cancellation
        request = HeartbeatRequest(
            worker_token=token,
            boot_id="boot-123",
            instances=[
                InstanceReport(
                    instance_id=instance_id,
                    attempt=attempt,
                    status="CANCELLED",
                )
            ],
        )

        await controller.process_heartbeat("w1", request)

        instance = await controller.get_instance(instance_id)
        assert instance["status"] == "FAILED"
        assert instance["failure_reason"] == "KILLED_BY_WORKER"


class TestPokeScheduler:
    """Tests for poke scheduler mechanism."""

    @pytest.mark.asyncio
    async def test_poke_scheduler_sets_event(self, controller):
        """Test that poke_scheduler sets the event."""
        controller.scheduler_event.clear()

        controller.poke_scheduler()

        assert controller.scheduler_event.is_set()
