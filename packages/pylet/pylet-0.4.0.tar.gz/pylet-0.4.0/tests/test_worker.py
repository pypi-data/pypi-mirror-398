"""Unit tests for pylet.worker module."""

import pytest
import pytest_asyncio
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from pylet.worker import (
    ProcessInfo,
    LocalStateManager,
    Worker,
    kill_process_group,
    send_sigterm,
    send_sigkill,
)
from pylet.schemas import DesiredInstance, InstanceReport


class TestProcessInfo:
    """Tests for ProcessInfo dataclass."""

    def test_create_process_info(self):
        """Test creating ProcessInfo with required fields."""
        info = ProcessInfo(
            pid=1234,
            pgid=1234,
            instance_id="inst-1",
            attempt=1,
            port=15600,
        )
        assert info.pid == 1234
        assert info.pgid == 1234
        assert info.instance_id == "inst-1"
        assert info.attempt == 1
        assert info.port == 15600
        assert info.status == "RUNNING"  # Default
        assert info.exit_code is None
        assert info.process is None
        assert info.stop_deadline is None

    def test_create_process_info_with_all_fields(self):
        """Test creating ProcessInfo with all fields."""
        info = ProcessInfo(
            pid=5678,
            pgid=5678,
            instance_id="inst-2",
            attempt=3,
            port=15601,
            status="STOPPING",
            exit_code=0,
            process=None,
            stop_deadline=1234567890.0,
        )
        assert info.status == "STOPPING"
        assert info.exit_code == 0
        assert info.stop_deadline == 1234567890.0


class TestLocalStateManager:
    """Tests for LocalStateManager class."""

    @pytest.fixture
    def state_dir(self):
        """Create a temporary state directory."""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    def test_save_and_load_state(self, state_dir):
        """Test saving and loading state."""
        manager = LocalStateManager(state_dir)

        manager.save_state(
            instance_id="inst-1",
            attempt=1,
            pgid=1234,
            port=15600,
        )

        states = manager.load_all_states()
        assert len(states) == 1
        assert states[0]["instance_id"] == "inst-1"
        assert states[0]["attempt"] == 1
        assert states[0]["pgid"] == 1234
        assert states[0]["port"] == 15600

    def test_save_multiple_states(self, state_dir):
        """Test saving multiple states."""
        manager = LocalStateManager(state_dir)

        manager.save_state("inst-1", 1, 1234, 15600)
        manager.save_state("inst-2", 1, 5678, 15601)
        manager.save_state("inst-1", 2, 9012, 15602)  # New attempt

        states = manager.load_all_states()
        assert len(states) == 3

    def test_remove_state(self, state_dir):
        """Test removing a state file."""
        manager = LocalStateManager(state_dir)

        manager.save_state("inst-1", 1, 1234, 15600)
        manager.save_state("inst-2", 1, 5678, 15601)

        manager.remove_state("inst-1", 1)

        states = manager.load_all_states()
        assert len(states) == 1
        assert states[0]["instance_id"] == "inst-2"

    def test_remove_nonexistent_state(self, state_dir):
        """Test removing a non-existent state file doesn't raise."""
        manager = LocalStateManager(state_dir)
        manager.remove_state("nonexistent", 99)  # Should not raise

    def test_clear_all(self, state_dir):
        """Test clearing all state files."""
        manager = LocalStateManager(state_dir)

        manager.save_state("inst-1", 1, 1234, 15600)
        manager.save_state("inst-2", 1, 5678, 15601)

        manager.clear_all()

        states = manager.load_all_states()
        assert len(states) == 0

    def test_load_all_states_empty(self, state_dir):
        """Test loading from empty directory."""
        manager = LocalStateManager(state_dir)
        states = manager.load_all_states()
        assert states == []

    def test_load_handles_corrupt_file(self, state_dir):
        """Test that load handles corrupt state files gracefully."""
        manager = LocalStateManager(state_dir)

        # Create valid state
        manager.save_state("inst-1", 1, 1234, 15600)

        # Create corrupt state file
        corrupt_file = state_dir / "corrupt.1.state"
        corrupt_file.write_text("not valid json")

        states = manager.load_all_states()
        # Should only load the valid one
        assert len(states) == 1
        assert states[0]["instance_id"] == "inst-1"


class TestSignalFunctions:
    """Tests for signal sending functions."""

    def test_send_sigterm_process_not_found(self):
        """Test send_sigterm returns False for non-existent process."""
        # Use a very large PGID that shouldn't exist
        result = send_sigterm(999999999)
        assert result is False

    def test_send_sigkill_process_not_found(self):
        """Test send_sigkill returns False for non-existent process."""
        result = send_sigkill(999999999)
        assert result is False

    def test_kill_process_group_handles_not_found(self):
        """Test kill_process_group handles non-existent process group."""
        # Should not raise
        kill_process_group(999999999)


class TestWorkerPortAllocation:
    """Tests for Worker port allocation."""

    @pytest.fixture
    def worker(self):
        """Create a worker instance for testing."""
        worker = Worker(
            head_address="localhost:8000",
            cpu_cores=4,
            gpu_units=2,
            memory_mb=8192,
        )
        return worker

    def test_allocate_port(self, worker):
        """Test allocating a port."""
        port = worker._allocate_port()
        assert port is not None
        assert port >= worker.port_range[0]
        assert port <= worker.port_range[1]
        assert port in worker.used_ports

    def test_allocate_multiple_ports(self, worker):
        """Test allocating multiple ports."""
        port1 = worker._allocate_port()
        port2 = worker._allocate_port()

        assert port1 != port2
        assert len(worker.used_ports) == 2

    def test_release_port(self, worker):
        """Test releasing a port."""
        port = worker._allocate_port()
        assert port in worker.used_ports

        worker._release_port(port)
        assert port not in worker.used_ports

    def test_release_port_not_in_use(self, worker):
        """Test releasing a port that's not in use doesn't raise."""
        worker._release_port(99999)  # Should not raise

    def test_allocate_port_exhaustion(self, worker):
        """Test that port allocation returns None when exhausted."""
        # Allocate all ports
        worker.port_range = (15600, 15602)  # Small range for test
        worker.used_ports = set()

        ports = []
        for _ in range(3):
            port = worker._allocate_port()
            if port:
                ports.append(port)

        # All ports should be allocated
        assert len(ports) == 3

        # Next allocation should fail
        port = worker._allocate_port()
        assert port is None


class TestWorkerInstanceReports:
    """Tests for Worker instance report generation."""

    @pytest.fixture
    def worker(self):
        """Create a worker instance for testing."""
        worker = Worker(
            head_address="localhost:8000",
            cpu_cores=4,
            gpu_units=2,
            memory_mb=8192,
        )
        return worker

    def test_get_instance_reports_empty(self, worker):
        """Test getting reports when no instances running."""
        reports = worker._get_instance_reports()
        assert reports == []

    def test_get_instance_reports_running(self, worker):
        """Test getting reports for running instances."""
        worker.local_instances[("inst-1", 1)] = ProcessInfo(
            pid=1234,
            pgid=1234,
            instance_id="inst-1",
            attempt=1,
            port=15600,
            status="RUNNING",
        )

        reports = worker._get_instance_reports()
        assert len(reports) == 1
        assert reports[0].instance_id == "inst-1"
        assert reports[0].attempt == 1
        assert reports[0].status == "RUNNING"
        assert reports[0].port == 15600

    def test_get_instance_reports_completed(self, worker):
        """Test getting reports for completed instances."""
        worker.local_instances[("inst-1", 1)] = ProcessInfo(
            pid=1234,
            pgid=1234,
            instance_id="inst-1",
            attempt=1,
            port=15600,
            status="COMPLETED",
            exit_code=0,
        )

        reports = worker._get_instance_reports()
        assert len(reports) == 1
        assert reports[0].status == "COMPLETED"
        assert reports[0].exit_code == 0

    def test_get_instance_reports_not_found(self, worker):
        """Test generating NOT_FOUND reports for missing instances."""
        # Set last desired state
        worker.last_desired = [
            DesiredInstance(
                instance_id="inst-1",
                attempt=1,
                command="cmd",
                expected_status="RUNNING",  # Controller expects RUNNING
            )
        ]

        # But we don't have it locally
        reports = worker._get_instance_reports()

        assert len(reports) == 1
        assert reports[0].instance_id == "inst-1"
        assert reports[0].status == "NOT_FOUND"

    def test_get_instance_reports_no_not_found_for_assigned(self, worker):
        """Test that NOT_FOUND is not generated for ASSIGNED instances."""
        # Set last desired state with ASSIGNED (controller wants us to start it)
        worker.last_desired = [
            DesiredInstance(
                instance_id="inst-1",
                attempt=1,
                command="cmd",
                expected_status="ASSIGNED",  # Fresh assignment
            )
        ]

        reports = worker._get_instance_reports()
        # Should not report NOT_FOUND for ASSIGNED instances
        assert len(reports) == 0


class TestWorkerTriggerHeartbeat:
    """Tests for heartbeat triggering."""

    @pytest.fixture
    def worker(self):
        """Create a worker instance for testing."""
        worker = Worker(
            head_address="localhost:8000",
            cpu_cores=4,
            gpu_units=2,
            memory_mb=8192,
        )
        return worker

    def test_trigger_heartbeat_cancels_inflight(self, worker):
        """Test that trigger_heartbeat cancels in-flight heartbeat."""
        # Create a mock task
        mock_task = MagicMock()
        mock_task.done.return_value = False
        worker.inflight_heartbeat = mock_task

        worker._trigger_heartbeat()

        mock_task.cancel.assert_called_once()

    def test_trigger_heartbeat_no_inflight(self, worker):
        """Test trigger_heartbeat when no in-flight heartbeat."""
        worker.inflight_heartbeat = None
        worker._trigger_heartbeat()  # Should not raise

    def test_trigger_heartbeat_already_done(self, worker):
        """Test trigger_heartbeat when heartbeat already done."""
        mock_task = MagicMock()
        mock_task.done.return_value = True
        worker.inflight_heartbeat = mock_task

        worker._trigger_heartbeat()

        mock_task.cancel.assert_not_called()


class TestWorkerReconciliation:
    """Tests for worker reconciliation logic."""

    @pytest.fixture
    def worker(self):
        """Create a worker instance for testing."""
        worker = Worker(
            head_address="localhost:8000",
            cpu_cores=4,
            gpu_units=2,
            memory_mb=8192,
        )
        # Mock the state manager
        worker.state_manager = MagicMock()
        return worker

    @pytest.mark.asyncio
    async def test_reconcile_starts_new_instance(self, worker):
        """Test that reconciliation starts new instances."""
        desired = [
            DesiredInstance(
                instance_id="inst-1",
                attempt=1,
                command="echo hello",
                expected_status="ASSIGNED",
            )
        ]

        # Mock _start_instance
        worker._start_instance = AsyncMock()

        await worker._reconcile(desired)

        worker._start_instance.assert_called_once()
        call_args = worker._start_instance.call_args[0][0]
        assert call_args.instance_id == "inst-1"

    @pytest.mark.asyncio
    async def test_reconcile_stops_unwanted_instance(self, worker):
        """Test that reconciliation stops unwanted instances."""
        # Add a local instance
        worker.local_instances[("inst-1", 1)] = ProcessInfo(
            pid=1234,
            pgid=1234,
            instance_id="inst-1",
            attempt=1,
            port=15600,
            status="RUNNING",
        )

        # Desired state is empty - instance should be stopped
        with patch("pylet.worker.send_sigterm") as mock_sigterm:
            mock_sigterm.return_value = True
            await worker._reconcile([])

        # Instance should be marked STOPPING
        assert worker.local_instances[("inst-1", 1)].status == "STOPPING"
        assert worker.local_instances[("inst-1", 1)].stop_deadline is not None

    @pytest.mark.asyncio
    async def test_reconcile_cleans_up_terminal(self, worker):
        """Test that reconciliation cleans up terminal instances not in desired state."""
        # Add a completed instance
        worker.local_instances[("inst-1", 1)] = ProcessInfo(
            pid=1234,
            pgid=1234,
            instance_id="inst-1",
            attempt=1,
            port=15600,
            status="COMPLETED",
            exit_code=0,
        )
        worker.used_ports = {15600}

        # Empty desired state
        await worker._reconcile([])

        # Instance should be removed
        assert ("inst-1", 1) not in worker.local_instances
        assert 15600 not in worker.used_ports
        worker.state_manager.remove_state.assert_called_once_with("inst-1", 1)

    @pytest.mark.asyncio
    async def test_reconcile_keeps_desired_running_instance(self, worker):
        """Test that reconciliation keeps instances in desired state."""
        # Add a running instance
        worker.local_instances[("inst-1", 1)] = ProcessInfo(
            pid=1234,
            pgid=1234,
            instance_id="inst-1",
            attempt=1,
            port=15600,
            status="RUNNING",
        )

        # Instance is in desired state
        desired = [
            DesiredInstance(
                instance_id="inst-1",
                attempt=1,
                command="cmd",
                expected_status="RUNNING",
            )
        ]

        await worker._reconcile(desired)

        # Instance should still be there and RUNNING
        assert ("inst-1", 1) in worker.local_instances
        assert worker.local_instances[("inst-1", 1)].status == "RUNNING"

    @pytest.mark.asyncio
    async def test_reconcile_logs_warning_for_missing_expected_running(self, worker):
        """Test that reconciliation logs warning for missing expected-running instances."""
        desired = [
            DesiredInstance(
                instance_id="inst-1",
                attempt=1,
                command="cmd",
                expected_status="RUNNING",  # Expected to be running
            )
        ]

        worker._start_instance = AsyncMock()

        # Should not try to start since expected_status != ASSIGNED
        await worker._reconcile(desired)

        worker._start_instance.assert_not_called()


class TestWorkerInit:
    """Tests for Worker initialization."""

    def test_worker_init(self):
        """Test Worker initialization."""
        worker = Worker(
            head_address="192.168.1.1:8000",
            cpu_cores=8,
            gpu_units=4,
            memory_mb=65536,
        )

        assert worker.head_address == "192.168.1.1:8000"
        assert worker.api_server_url == "http://192.168.1.1:8000"
        assert worker.total_resources["cpu_cores"] == 8
        assert worker.total_resources["gpu_units"] == 4
        assert worker.total_resources["memory_mb"] == 65536
        assert worker.worker_token is None
        assert worker.last_seen_gen == 0
        assert worker.local_instances == {}
        assert worker.last_desired == []

    def test_worker_has_unique_ids(self):
        """Test that workers get unique IDs and boot IDs."""
        worker1 = Worker("localhost:8000")
        worker2 = Worker("localhost:8000")

        assert worker1.worker_id != worker2.worker_id
        assert worker1.boot_id != worker2.boot_id


class TestWorkerStartupCleanup:
    """Tests for worker startup cleanup."""

    @pytest.mark.asyncio
    async def test_startup_cleanup_kills_orphans(self):
        """Test that startup cleanup kills orphaned processes."""
        with tempfile.TemporaryDirectory() as state_dir:
            state_path = Path(state_dir)

            worker = Worker("localhost:8000")
            worker.state_manager = LocalStateManager(state_path)

            # Save some state files (simulating crash)
            worker.state_manager.save_state("inst-1", 1, 999999999, 15600)

            with patch("pylet.worker.kill_process_group") as mock_kill:
                await worker._startup_cleanup()

                # Should have tried to kill the orphaned process
                mock_kill.assert_called_once_with(999999999)

            # State files should be cleared
            states = worker.state_manager.load_all_states()
            assert len(states) == 0

            # Local instances should be empty
            assert worker.local_instances == {}


class TestWorkerEnvMerging:
    """Tests for environment variable merging in _start_instance."""

    @pytest.fixture
    def worker(self):
        """Create a worker instance for testing."""
        worker = Worker(
            head_address="localhost:8000",
            cpu_cores=4,
            gpu_units=4,
            memory_mb=8192,
        )
        worker.state_manager = MagicMock()
        return worker

    @pytest.mark.asyncio
    async def test_pylet_vars_override_user_env(self, worker):
        """Test that Pylet-managed vars (PORT, CUDA_VISIBLE_DEVICES) override user env."""
        # User tries to override Pylet-managed vars
        inst = DesiredInstance(
            instance_id="inst-1",
            attempt=1,
            command="echo test",
            expected_status="ASSIGNED",
            gpu_indices=[0, 1],
            env={
                "PORT": "9999",  # User tries to set PORT
                "CUDA_VISIBLE_DEVICES": "99",  # User tries to set CUDA
                "MODEL_PATH": "/models/llama",  # User's custom var - should be preserved
            },
        )

        captured_env = None

        async def mock_create_subprocess(*args, **kwargs):
            nonlocal captured_env
            captured_env = kwargs.get("env", {})
            # Return a mock process
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            return mock_proc

        with patch("asyncio.create_subprocess_shell", side_effect=mock_create_subprocess):
            with patch("os.getpgid", return_value=12345):
                await worker._start_instance(inst)

        # Verify Pylet-managed vars override user values
        assert captured_env is not None
        assert captured_env["PORT"] != "9999", "PORT should be overridden by Pylet"
        assert captured_env["PORT"] == "15600", "PORT should be Pylet-allocated port"
        assert captured_env["CUDA_VISIBLE_DEVICES"] == "0,1", "CUDA should match gpu_indices"
        # User's custom var should be preserved
        assert captured_env["MODEL_PATH"] == "/models/llama"

    @pytest.mark.asyncio
    async def test_user_env_preserved_for_non_managed_vars(self, worker):
        """Test that user env vars are preserved for non-Pylet-managed keys."""
        inst = DesiredInstance(
            instance_id="inst-2",
            attempt=1,
            command="echo test",
            expected_status="ASSIGNED",
            env={
                "MY_VAR": "my_value",
                "BATCH_SIZE": "32",
                "MODEL_NAME": "llama2-7b",
            },
        )

        captured_env = None

        async def mock_create_subprocess(*args, **kwargs):
            nonlocal captured_env
            captured_env = kwargs.get("env", {})
            mock_proc = MagicMock()
            mock_proc.pid = 12346
            return mock_proc

        with patch("asyncio.create_subprocess_shell", side_effect=mock_create_subprocess):
            with patch("os.getpgid", return_value=12346):
                await worker._start_instance(inst)

        # All user vars should be preserved
        assert captured_env["MY_VAR"] == "my_value"
        assert captured_env["BATCH_SIZE"] == "32"
        assert captured_env["MODEL_NAME"] == "llama2-7b"
        # PORT should still be set by Pylet
        assert captured_env["PORT"] == "15600"

    @pytest.mark.asyncio
    async def test_cuda_not_set_without_gpu_indices(self, worker):
        """Test that CUDA_VISIBLE_DEVICES is not set when gpu_indices is empty."""
        inst = DesiredInstance(
            instance_id="inst-3",
            attempt=1,
            command="echo test",
            expected_status="ASSIGNED",
            gpu_indices=[],  # No GPUs
            env={
                "CUDA_VISIBLE_DEVICES": "0,1,2,3",  # User tries to set
            },
        )

        captured_env = None
        original_cuda = None

        async def mock_create_subprocess(*args, **kwargs):
            nonlocal captured_env, original_cuda
            captured_env = kwargs.get("env", {})
            # Check if CUDA was in original os.environ
            original_cuda = os.environ.get("CUDA_VISIBLE_DEVICES")
            mock_proc = MagicMock()
            mock_proc.pid = 12347
            return mock_proc

        with patch("asyncio.create_subprocess_shell", side_effect=mock_create_subprocess):
            with patch("os.getpgid", return_value=12347):
                await worker._start_instance(inst)

        # With empty gpu_indices, user's CUDA value should be preserved
        # (Pylet only overrides when gpu_indices is set)
        assert captured_env["CUDA_VISIBLE_DEVICES"] == "0,1,2,3"
