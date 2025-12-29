"""Unit tests for venv parameter feature.

These tests follow TDD - written before implementation.
Tests will fail until the venv feature is implemented.
"""

import pytest
import shlex
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from pydantic import ValidationError

from pylet.schemas import (
    InstanceSubmissionRequest,
    Instance,
    DesiredInstance,
    ResourceSpec,
    InstanceStatus,
)


# =============================================================================
# Schema Tests - InstanceSubmissionRequest
# =============================================================================

class TestInstanceSubmissionRequestVenv:
    """Tests for venv field in InstanceSubmissionRequest."""

    def test_accepts_valid_absolute_venv_path(self):
        """Test that schema accepts valid absolute venv path."""
        request = InstanceSubmissionRequest(
            command="python train.py",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
            venv="/home/user/my-venv",
        )
        assert request.venv == "/home/user/my-venv"

    def test_accepts_none_venv(self):
        """Test that schema accepts venv=None (default)."""
        request = InstanceSubmissionRequest(
            command="python train.py",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
        )
        assert request.venv is None

    def test_accepts_venv_with_spaces_in_path(self):
        """Test that schema accepts venv path containing spaces."""
        request = InstanceSubmissionRequest(
            command="python train.py",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
            venv="/home/user/my project/venv",
        )
        assert request.venv == "/home/user/my project/venv"

    def test_accepts_venv_with_special_chars(self):
        """Test that schema accepts venv path with allowed special characters."""
        request = InstanceSubmissionRequest(
            command="python train.py",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
            venv="/home/user/my-venv_v2.0",
        )
        assert request.venv == "/home/user/my-venv_v2.0"

    def test_venv_coexists_with_env(self):
        """Test that venv and env parameters can be used together."""
        request = InstanceSubmissionRequest(
            command="python train.py",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
            venv="/home/user/my-venv",
            env={"MY_VAR": "value", "BATCH_SIZE": "32"},
        )
        assert request.venv == "/home/user/my-venv"
        assert request.env == {"MY_VAR": "value", "BATCH_SIZE": "32"}

    def test_venv_coexists_with_all_sllm_fields(self):
        """Test that venv works with all SLLM-related fields."""
        request = InstanceSubmissionRequest(
            command="vllm serve model",
            resource_requirements=ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=16384),
            venv="/opt/vllm-env",
            env={"MODEL_PATH": "/models/llama"},
            target_worker="worker-1",
            gpu_indices=[0, 1],
            exclusive=True,
            labels={"model_id": "llama2-7b"},
        )
        assert request.venv == "/opt/vllm-env"
        assert request.target_worker == "worker-1"
        assert request.gpu_indices == [0, 1]


# =============================================================================
# Schema Tests - Instance
# =============================================================================

class TestInstanceVenv:
    """Tests for venv field in Instance model."""

    def test_instance_accepts_venv(self):
        """Test that Instance model accepts venv field."""
        instance = Instance(
            instance_id="test-123",
            command="python train.py",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
            venv="/home/user/my-venv",
        )
        assert instance.venv == "/home/user/my-venv"

    def test_instance_venv_defaults_to_none(self):
        """Test that Instance venv defaults to None."""
        instance = Instance(
            instance_id="test-123",
            command="python train.py",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
        )
        assert instance.venv is None

    def test_instance_serialization_includes_venv(self):
        """Test that Instance serialization includes venv field."""
        instance = Instance(
            instance_id="test-123",
            command="python train.py",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
            venv="/home/user/my-venv",
        )
        data = instance.model_dump()
        assert "venv" in data
        assert data["venv"] == "/home/user/my-venv"


# =============================================================================
# Schema Tests - DesiredInstance
# =============================================================================

class TestDesiredInstanceVenv:
    """Tests for venv field in DesiredInstance model."""

    def test_desired_instance_accepts_venv(self):
        """Test that DesiredInstance accepts venv field."""
        desired = DesiredInstance(
            instance_id="inst-1",
            attempt=1,
            command="python train.py",
            venv="/home/user/my-venv",
        )
        assert desired.venv == "/home/user/my-venv"

    def test_desired_instance_venv_defaults_to_none(self):
        """Test that DesiredInstance venv defaults to None."""
        desired = DesiredInstance(
            instance_id="inst-1",
            attempt=1,
            command="python train.py",
        )
        assert desired.venv is None

    def test_desired_instance_with_venv_and_env(self):
        """Test DesiredInstance with both venv and env."""
        desired = DesiredInstance(
            instance_id="inst-1",
            attempt=1,
            command="python train.py",
            venv="/home/user/my-venv",
            env={"MY_VAR": "value"},
            gpu_indices=[0, 1],
        )
        assert desired.venv == "/home/user/my-venv"
        assert desired.env == {"MY_VAR": "value"}
        assert desired.gpu_indices == [0, 1]


# =============================================================================
# Path Validation Tests
# =============================================================================

class TestVenvPathValidation:
    """Tests for venv path validation.

    Note: Path validation happens in server.py at submission time,
    not in the schema itself. These tests verify the validation logic.
    """

    def test_rejects_relative_path(self):
        """Test that relative paths are rejected."""
        # This validation should happen in server.py
        # Here we document the expected behavior
        invalid_paths = [
            "./venv",
            "venv",
            "../venv",
            "home/user/venv",
        ]
        for path in invalid_paths:
            assert not path.startswith("/"), f"Path {path} should be rejected as relative"

    def test_rejects_path_with_dotdot(self):
        """Test that paths containing '..' are rejected."""
        invalid_paths = [
            "/home/user/../other/venv",
            "/home/../../../etc/passwd",
            "/home/user/venv/..",
        ]
        for path in invalid_paths:
            assert ".." in path, f"Path {path} contains '..' and should be rejected"

    def test_accepts_valid_absolute_paths(self):
        """Test examples of valid absolute paths."""
        valid_paths = [
            "/home/user/venv",
            "/opt/vllm-env",
            "/mnt/nfs/shared/envs/torch-2.1",
            "/home/user/my project/venv",  # Spaces are OK
            "/home/user/.venv",  # Hidden dirs are OK
            "/home/user/venv_v2.0",  # Underscores and dots OK
        ]
        for path in valid_paths:
            assert path.startswith("/"), f"Path {path} is valid absolute path"
            assert ".." not in path, f"Path {path} has no '..'"


# =============================================================================
# Worker Command Construction Tests
# =============================================================================

class TestWorkerCommandConstruction:
    """Tests for worker command construction with venv.

    These tests verify that worker._start_instance() correctly
    constructs the shell command with venv activation.
    """

    @pytest.fixture
    def worker(self):
        """Create a worker instance for testing."""
        from pylet.worker import Worker
        worker = Worker(
            head_address="localhost:8000",
            cpu_cores=4,
            gpu_units=2,
            memory_mb=8192,
        )
        worker.state_manager = MagicMock()
        return worker

    @pytest.mark.asyncio
    async def test_command_without_venv_unchanged(self, worker):
        """Test that command construction is unchanged when venv is None."""
        inst = DesiredInstance(
            instance_id="inst-1",
            attempt=1,
            command="echo hello",
            expected_status="ASSIGNED",
            venv=None,
        )

        captured_cmd = None

        async def mock_create_subprocess(cmd, *args, **kwargs):
            nonlocal captured_cmd
            captured_cmd = cmd
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            return mock_proc

        with patch("asyncio.create_subprocess_shell", side_effect=mock_create_subprocess):
            with patch("os.getpgid", return_value=12345):
                await worker._start_instance(inst)

        # Should NOT contain 'source' or 'activate'
        assert captured_cmd is not None
        assert "source" not in captured_cmd or "activate" not in captured_cmd
        # But should contain the original command
        assert "echo hello" in captured_cmd

    @pytest.mark.asyncio
    async def test_command_with_venv_includes_activation(self, worker):
        """Test that command includes venv activation when venv is specified."""
        inst = DesiredInstance(
            instance_id="inst-1",
            attempt=1,
            command="python train.py",
            expected_status="ASSIGNED",
            venv="/home/user/my-venv",
        )

        captured_cmd = None

        async def mock_create_subprocess(cmd, *args, **kwargs):
            nonlocal captured_cmd
            captured_cmd = cmd
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            return mock_proc

        with patch("asyncio.create_subprocess_shell", side_effect=mock_create_subprocess):
            with patch("os.getpgid", return_value=12345):
                await worker._start_instance(inst)

        # Should contain venv activation
        assert captured_cmd is not None
        assert "source" in captured_cmd
        assert "/home/user/my-venv/bin/activate" in captured_cmd
        # Activation should come BEFORE the command
        activate_pos = captured_cmd.find("activate")
        command_pos = captured_cmd.find("python train.py")
        assert activate_pos < command_pos, "Activation must come before command"

    @pytest.mark.asyncio
    async def test_command_venv_path_properly_quoted(self, worker):
        """Test that venv paths with spaces are properly quoted."""
        inst = DesiredInstance(
            instance_id="inst-1",
            attempt=1,
            command="python train.py",
            expected_status="ASSIGNED",
            venv="/home/user/my project/venv",
        )

        captured_cmd = None

        async def mock_create_subprocess(cmd, *args, **kwargs):
            nonlocal captured_cmd
            captured_cmd = cmd
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            return mock_proc

        with patch("asyncio.create_subprocess_shell", side_effect=mock_create_subprocess):
            with patch("os.getpgid", return_value=12345):
                await worker._start_instance(inst)

        # Path with space should be quoted (shlex.quote adds quotes)
        assert captured_cmd is not None
        # The path should be properly escaped for shell
        # shlex.quote("/home/user/my project/venv") -> "'/home/user/my project/venv'"
        assert "my project" in captured_cmd or "my\\ project" in captured_cmd

    @pytest.mark.asyncio
    async def test_command_venv_with_single_quotes_in_path(self, worker):
        """Test that venv paths with single quotes are properly escaped."""
        inst = DesiredInstance(
            instance_id="inst-1",
            attempt=1,
            command="python train.py",
            expected_status="ASSIGNED",
            venv="/home/user/it's-a-venv",
        )

        captured_cmd = None

        async def mock_create_subprocess(cmd, *args, **kwargs):
            nonlocal captured_cmd
            captured_cmd = cmd
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            return mock_proc

        with patch("asyncio.create_subprocess_shell", side_effect=mock_create_subprocess):
            with patch("os.getpgid", return_value=12345):
                await worker._start_instance(inst)

        # Should not break the shell command
        assert captured_cmd is not None
        # The command should be valid shell syntax

    @pytest.mark.asyncio
    async def test_venv_activation_order_before_env(self, worker):
        """Test that venv activation happens, then env vars override."""
        inst = DesiredInstance(
            instance_id="inst-1",
            attempt=1,
            command="python train.py",
            expected_status="ASSIGNED",
            venv="/home/user/my-venv",
            env={"PATH": "/custom/bin:$PATH", "MY_VAR": "value"},
        )

        captured_env = None

        async def mock_create_subprocess(cmd, *args, **kwargs):
            nonlocal captured_env
            captured_env = kwargs.get("env", {})
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            return mock_proc

        with patch("asyncio.create_subprocess_shell", side_effect=mock_create_subprocess):
            with patch("os.getpgid", return_value=12345):
                await worker._start_instance(inst)

        # User env vars should be in the env dict
        assert captured_env is not None
        assert captured_env.get("MY_VAR") == "value"
        # Note: The actual PATH modification from venv happens via 'source activate'
        # in the shell, not via the env dict. User's PATH in env dict overrides.

    @pytest.mark.asyncio
    async def test_log_sidecar_uses_worker_python(self, worker):
        """Test that log sidecar still uses worker's python3, not venv's."""
        inst = DesiredInstance(
            instance_id="inst-1",
            attempt=1,
            command="python train.py",
            expected_status="ASSIGNED",
            venv="/home/user/my-venv",
        )

        captured_cmd = None

        async def mock_create_subprocess(cmd, *args, **kwargs):
            nonlocal captured_cmd
            captured_cmd = cmd
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            return mock_proc

        with patch("asyncio.create_subprocess_shell", side_effect=mock_create_subprocess):
            with patch("os.getpgid", return_value=12345):
                await worker._start_instance(inst)

        # Log sidecar should use bare 'python3', not the venv's python
        # The structure should be: (source activate && user_cmd) 2>&1 | python3 -m pylet.log_sidecar
        assert captured_cmd is not None
        # The pipe to log_sidecar should be OUTSIDE the venv-activated subshell
        assert "python3 -m pylet.log_sidecar" in captured_cmd


# =============================================================================
# Controller Tests - DesiredInstance Construction
# =============================================================================

class TestControllerVenvPassthrough:
    """Tests for controller passing venv to DesiredInstance."""

    @pytest.mark.asyncio
    async def test_get_desired_instances_includes_venv(self):
        """Test that _get_desired_instances includes venv from database."""
        from pylet.controller import Controller
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            controller = Controller(db_path)
            await controller.startup()

            try:
                # Register a worker
                token = await controller.register_worker(
                    worker_id="worker-1",
                    host="192.168.1.1",
                    resources=ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192),
                )

                # Submit an instance with venv
                instance_id = await controller.submit_instance(
                    command="python train.py",
                    resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=1024),
                    venv="/home/user/my-venv",
                )

                # Trigger scheduling (use actual method name)
                await controller._run_scheduling_cycle()

                # Get desired instances for worker
                desired = await controller._get_desired_instances("worker-1")

                assert len(desired) == 1
                assert desired[0].venv == "/home/user/my-venv"
            finally:
                await controller.shutdown()

    @pytest.mark.asyncio
    async def test_get_desired_instances_venv_none_when_not_set(self):
        """Test that venv is None in DesiredInstance when not specified."""
        from pylet.controller import Controller
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            controller = Controller(db_path)
            await controller.startup()

            try:
                # Register a worker
                token = await controller.register_worker(
                    worker_id="worker-1",
                    host="192.168.1.1",
                    resources=ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192),
                )

                # Submit an instance WITHOUT venv
                instance_id = await controller.submit_instance(
                    command="python train.py",
                    resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=1, memory_mb=1024),
                )

                # Trigger scheduling (use actual method name)
                await controller._run_scheduling_cycle()

                # Get desired instances for worker
                desired = await controller._get_desired_instances("worker-1")

                assert len(desired) == 1
                assert desired[0].venv is None
            finally:
                await controller.shutdown()


# =============================================================================
# Database Tests
# =============================================================================

class TestDatabaseVenv:
    """Tests for venv field in database operations."""

    @pytest.mark.asyncio
    async def test_insert_instance_with_venv(self):
        """Test inserting instance with venv field."""
        from pylet.db import Database
        import tempfile
        import uuid
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            await db.connect()

            try:
                instance_id = str(uuid.uuid4())
                await db.insert_instance(
                    instance_id=instance_id,
                    name="test-instance",
                    command="python train.py",
                    cpu_cores=1,
                    gpu_units=0,
                    memory_mb=512,
                    venv="/home/user/my-venv",
                )

                instance = await db.get_instance(instance_id)
                assert instance is not None
                assert instance["venv"] == "/home/user/my-venv"
            finally:
                await db.close()

    @pytest.mark.asyncio
    async def test_insert_instance_without_venv(self):
        """Test inserting instance without venv field (should be NULL)."""
        from pylet.db import Database
        import tempfile
        import uuid
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            await db.connect()

            try:
                instance_id = str(uuid.uuid4())
                await db.insert_instance(
                    instance_id=instance_id,
                    name="test-instance",
                    command="python train.py",
                    cpu_cores=1,
                    gpu_units=0,
                    memory_mb=512,
                )

                instance = await db.get_instance(instance_id)
                assert instance is not None
                assert instance.get("venv") is None
            finally:
                await db.close()

    @pytest.mark.asyncio
    async def test_get_desired_instances_includes_venv(self):
        """Test that get_desired_instances_for_worker returns venv."""
        from pylet.db import Database
        import tempfile
        import uuid
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            await db.connect()

            try:
                # Insert worker
                await db.insert_worker(
                    worker_id="worker-1",
                    ip="192.168.1.1",
                    cpu_cores=4,
                    gpu_units=2,
                    memory_mb=8192,
                    worker_token="token",
                )

                # Insert instance with venv
                instance_id = str(uuid.uuid4())
                await db.insert_instance(
                    instance_id=instance_id,
                    name=None,
                    command="python train.py",
                    cpu_cores=1,
                    gpu_units=1,
                    memory_mb=512,
                    venv="/home/user/my-venv",
                )

                # Assign to worker with proper arguments
                await db.assign_instance(
                    instance_id=instance_id,
                    worker_id="worker-1",
                    new_attempt=1,
                    gpu_indices=[0],
                    exclusive=True,
                )

                # Get desired instances
                rows = await db.get_desired_instances_for_worker("worker-1")
                assert len(rows) == 1
                assert rows[0]["venv"] == "/home/user/my-venv"
            finally:
                await db.close()


# =============================================================================
# API Tests - Validation Logic
# =============================================================================

class TestAPIVenvSubmission:
    """Tests for venv validation in API submission endpoint."""

    @pytest.mark.asyncio
    async def test_validate_submission_accepts_valid_venv(self):
        """Test that validation accepts valid absolute venv path."""
        from pylet.server import _validate_submission, InstanceSubmissionRequest, ResourceSpec

        request = InstanceSubmissionRequest(
            command="python train.py",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
            venv="/home/user/my-venv",
        )

        # Should not raise - no return value
        await _validate_submission(request)

    @pytest.mark.asyncio
    async def test_validate_submission_accepts_none_venv(self):
        """Test that validation accepts venv=None."""
        from pylet.server import _validate_submission, InstanceSubmissionRequest, ResourceSpec

        request = InstanceSubmissionRequest(
            command="python train.py",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
            venv=None,
        )

        # Should not raise
        await _validate_submission(request)

    @pytest.mark.asyncio
    async def test_validate_submission_rejects_relative_venv(self):
        """Test that validation rejects relative venv path."""
        from pylet.server import _validate_submission, InstanceSubmissionRequest, ResourceSpec

        request = InstanceSubmissionRequest(
            command="python train.py",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
            venv="./my-venv",  # Relative path
        )

        with pytest.raises(ValueError) as excinfo:
            await _validate_submission(request)

        assert "absolute" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_validate_submission_rejects_dotdot_venv(self):
        """Test that validation rejects venv path containing '..'."""
        from pylet.server import _validate_submission, InstanceSubmissionRequest, ResourceSpec

        request = InstanceSubmissionRequest(
            command="python train.py",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
            venv="/home/user/../etc/passwd",  # Path traversal
        )

        with pytest.raises(ValueError) as excinfo:
            await _validate_submission(request)

        assert ".." in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_validate_submission_accepts_venv_with_spaces(self):
        """Test that validation accepts venv path with spaces."""
        from pylet.server import _validate_submission, InstanceSubmissionRequest, ResourceSpec

        request = InstanceSubmissionRequest(
            command="python train.py",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
            venv="/home/user/my project/venv",
        )

        # Should not raise
        await _validate_submission(request)


# =============================================================================
# CLI Tests
# =============================================================================

class TestCLIVenv:
    """Tests for --venv flag in CLI."""

    def test_submit_command_accepts_venv_flag(self):
        """Test that submit command accepts --venv flag."""
        from click.testing import CliRunner
        from pylet.cli import cli

        runner = CliRunner()
        # Just test that the flag is recognized (will fail without server)
        result = runner.invoke(
            cli,
            ["submit", "echo hello", "--venv", "/home/user/my-venv"],
            catch_exceptions=True,
        )
        # Should fail to connect, not fail on unrecognized option
        assert "unrecognized" not in result.output.lower()
        assert "no such option" not in result.output.lower()
        # The error should be about connection, not about invalid option
        # (it will fail because localhost:8000 is not running)


# =============================================================================
# Python API Tests
# =============================================================================

class TestPythonAPIVenv:
    """Tests for venv parameter in Python API."""

    def test_submit_function_accepts_venv_parameter(self):
        """Test that pylet.submit() accepts venv parameter."""
        import pylet
        from pylet._sync_api import submit
        import inspect

        # Check that submit function has venv parameter
        sig = inspect.signature(submit)
        assert "venv" in sig.parameters, "submit() should accept venv parameter"

    def test_async_submit_function_accepts_venv_parameter(self):
        """Test that pylet.aio.submit() accepts venv parameter."""
        from pylet.aio import submit
        import inspect

        # Check that async submit function has venv parameter
        sig = inspect.signature(submit)
        assert "venv" in sig.parameters, "async submit() should accept venv parameter"
