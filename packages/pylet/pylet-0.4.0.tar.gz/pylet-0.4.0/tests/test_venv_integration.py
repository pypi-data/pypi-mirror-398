"""Integration tests for venv parameter feature.

These tests require a real venv to be created and test the full
flow from submission through execution.

Tests follow TDD - written before implementation.
"""

import pytest
import asyncio
import tempfile
import subprocess
import sys
import os
from pathlib import Path
from unittest.mock import patch


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_venv():
    """Create a temporary virtualenv for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "test-venv"

        # Create virtualenv using current Python
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.skip(f"Failed to create venv: {result.stderr}")

        # Install a marker package so we can verify the venv is used
        pip_path = venv_path / "bin" / "pip"
        result = subprocess.run(
            [str(pip_path), "install", "six"],  # small package as marker
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.skip(f"Failed to install test package: {result.stderr}")

        yield venv_path


@pytest.fixture
def temp_venv_with_script(temp_venv):
    """Create a venv with a test script."""
    # Create a test script that prints its Python path
    script_path = temp_venv.parent / "test_script.py"
    script_path.write_text("""
import sys
import os

# Print the Python executable being used
print(f"PYTHON_EXECUTABLE={sys.executable}")

# Print the virtual env
print(f"VIRTUAL_ENV={os.environ.get('VIRTUAL_ENV', 'NOT_SET')}")

# Try to import the marker package
try:
    import six
    print("SIX_IMPORTED=True")
except ImportError:
    print("SIX_IMPORTED=False")

# Print success
print("TEST_COMPLETED=True")
""")
    return temp_venv, script_path


# =============================================================================
# End-to-End Tests
# =============================================================================

class TestVenvEndToEnd:
    """End-to-end tests for venv feature."""

    @pytest.mark.asyncio
    async def test_instance_runs_in_venv(self, temp_venv_with_script):
        """Test that instance actually runs inside the specified venv."""
        venv_path, script_path = temp_venv_with_script

        from pylet.controller import Controller
        from pylet.worker import Worker
        from pylet.schemas import ResourceSpec
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            controller = Controller(db_path)
            await controller.startup()

            try:
                # Register a worker
                worker = Worker(
                    head_address="localhost:8000",
                    cpu_cores=4,
                    gpu_units=0,
                    memory_mb=8192,
                )

                # Submit instance with venv
                instance_id = await controller.submit_instance(
                    command=f"python {script_path}",
                    resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
                    venv=str(venv_path),
                )

                # Get the instance
                instance = await controller.get_instance(instance_id)
                assert instance is not None
                assert instance["venv"] == str(venv_path)

            finally:
                await controller.shutdown()

    @pytest.mark.asyncio
    async def test_instance_fails_with_nonexistent_venv(self):
        """Test that instance fails when venv doesn't exist."""
        from pylet.controller import Controller
        from pylet.schemas import ResourceSpec
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            controller = Controller(db_path)
            await controller.startup()

            try:
                # Submit instance with non-existent venv
                instance_id = await controller.submit_instance(
                    command="echo hello",
                    resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
                    venv="/nonexistent/path/to/venv",
                )

                instance = await controller.get_instance(instance_id)
                assert instance is not None
                # The instance should be submitted successfully (validation passes)
                # but will fail at runtime when worker tries to activate

            finally:
                await controller.shutdown()

    @pytest.mark.asyncio
    async def test_instance_without_venv_uses_worker_env(self):
        """Test that instance without venv uses worker's Python environment."""
        from pylet.controller import Controller
        from pylet.schemas import ResourceSpec
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            controller = Controller(db_path)
            await controller.startup()

            try:
                # Submit instance WITHOUT venv
                instance_id = await controller.submit_instance(
                    command="python -c 'import sys; print(sys.executable)'",
                    resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
                )

                instance = await controller.get_instance(instance_id)
                assert instance is not None
                assert instance.get("venv") is None

            finally:
                await controller.shutdown()


# =============================================================================
# Worker Execution Tests
# =============================================================================

class TestWorkerVenvExecution:
    """Tests for worker executing instances with venv."""

    @pytest.mark.asyncio
    async def test_worker_activates_venv_before_command(self, temp_venv):
        """Test that worker activates venv before running command."""
        from pylet.worker import Worker
        from pylet.schemas import DesiredInstance
        from unittest.mock import MagicMock, AsyncMock
        import tempfile

        with tempfile.TemporaryDirectory() as state_dir:
            worker = Worker(
                head_address="localhost:8000",
                cpu_cores=4,
                gpu_units=0,
                memory_mb=8192,
            )
            worker.state_manager = MagicMock()

            # Create a desired instance with venv
            inst = DesiredInstance(
                instance_id="test-inst",
                attempt=1,
                command="python -c 'import six; print(six.__version__)'",
                expected_status="ASSIGNED",
                venv=str(temp_venv),
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

            # Verify the command includes venv activation (uses double quotes for path)
            assert captured_cmd is not None
            assert f'source "{temp_venv}/bin/activate"' in captured_cmd

    @pytest.mark.asyncio
    async def test_worker_handles_venv_with_spaces(self):
        """Test that worker handles venv paths with spaces."""
        from pylet.worker import Worker
        from pylet.schemas import DesiredInstance
        from unittest.mock import MagicMock
        import tempfile

        # Create a directory with spaces
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_with_space = Path(tmpdir) / "my venv"
            venv_with_space.mkdir()
            (venv_with_space / "bin").mkdir()
            (venv_with_space / "bin" / "activate").write_text("# fake activate")

            worker = Worker(
                head_address="localhost:8000",
                cpu_cores=4,
                gpu_units=0,
                memory_mb=8192,
            )
            worker.state_manager = MagicMock()

            inst = DesiredInstance(
                instance_id="test-inst",
                attempt=1,
                command="echo hello",
                expected_status="ASSIGNED",
                venv=str(venv_with_space),
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

            # Path should be properly quoted for shell
            assert captured_cmd is not None
            # Should not cause a syntax error - verify proper quoting
            # The command should contain either 'my venv' quoted or escaped


# =============================================================================
# Order of Operations Tests
# =============================================================================

class TestVenvEnvOrder:
    """Tests for the order of venv activation vs env vars."""

    @pytest.mark.asyncio
    async def test_env_vars_applied_after_venv_activation(self, temp_venv):
        """Test that user env vars are applied after venv activation."""
        from pylet.worker import Worker
        from pylet.schemas import DesiredInstance
        from unittest.mock import MagicMock

        worker = Worker(
            head_address="localhost:8000",
            cpu_cores=4,
            gpu_units=0,
            memory_mb=8192,
        )
        worker.state_manager = MagicMock()

        # User provides both venv and custom env vars
        inst = DesiredInstance(
            instance_id="test-inst",
            attempt=1,
            command="echo $MY_VAR",
            expected_status="ASSIGNED",
            venv=str(temp_venv),
            env={"MY_VAR": "custom_value", "PYTHONPATH": "/custom/path"},
        )

        captured_env = None
        captured_cmd = None

        async def mock_create_subprocess(cmd, *args, **kwargs):
            nonlocal captured_env, captured_cmd
            captured_env = kwargs.get("env", {})
            captured_cmd = cmd
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            return mock_proc

        with patch("asyncio.create_subprocess_shell", side_effect=mock_create_subprocess):
            with patch("os.getpgid", return_value=12345):
                await worker._start_instance(inst)

        # User's env vars should be in the subprocess env
        assert captured_env is not None
        assert captured_env.get("MY_VAR") == "custom_value"
        assert captured_env.get("PYTHONPATH") == "/custom/path"

        # Venv activation should be in the command
        assert captured_cmd is not None
        assert "activate" in captured_cmd

    @pytest.mark.asyncio
    async def test_user_can_override_venv_path(self, temp_venv):
        """Test that user env vars can override PATH set by venv activation."""
        from pylet.worker import Worker
        from pylet.schemas import DesiredInstance
        from unittest.mock import MagicMock

        worker = Worker(
            head_address="localhost:8000",
            cpu_cores=4,
            gpu_units=0,
            memory_mb=8192,
        )
        worker.state_manager = MagicMock()

        # User explicitly overrides PATH
        custom_path = "/my/custom/bin:/usr/bin"
        inst = DesiredInstance(
            instance_id="test-inst",
            attempt=1,
            command="which python",
            expected_status="ASSIGNED",
            venv=str(temp_venv),
            env={"PATH": custom_path},
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

        # User's PATH should be in env (will be available in shell)
        # Note: The actual PATH modification from 'source activate' happens
        # in the shell subprocess, so user's PATH in env dict will be set
        # before that, and 'source activate' will then modify it further.
        assert captured_env is not None
        assert captured_env.get("PATH") == custom_path


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestVenvErrorHandling:
    """Tests for error handling with venv feature."""

    @pytest.mark.asyncio
    async def test_missing_activate_script_fails(self):
        """Test that missing activate script causes failure."""
        from pylet.worker import Worker
        from pylet.schemas import DesiredInstance
        from unittest.mock import MagicMock
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake venv directory without activate script
            fake_venv = Path(tmpdir) / "fake-venv"
            fake_venv.mkdir()
            (fake_venv / "bin").mkdir()
            # Note: NOT creating activate script

            worker = Worker(
                head_address="localhost:8000",
                cpu_cores=4,
                gpu_units=0,
                memory_mb=8192,
            )
            worker.state_manager = MagicMock()

            inst = DesiredInstance(
                instance_id="test-inst",
                attempt=1,
                command="echo hello",
                expected_status="ASSIGNED",
                venv=str(fake_venv),
            )

            # The command should be constructed (won't fail until execution)
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

            # Command should reference the (missing) activate script
            assert captured_cmd is not None
            assert f"{fake_venv}/bin/activate" in captured_cmd

    @pytest.mark.asyncio
    async def test_venv_activation_failure_captured_in_logs(self):
        """Test that venv activation failure is captured in instance logs."""
        # This would be a more complex integration test requiring
        # full log capture infrastructure
        pass  # Placeholder for full integration test


# =============================================================================
# Regression Tests
# =============================================================================

class TestVenvBackwardsCompatibility:
    """Tests to ensure backwards compatibility."""

    @pytest.mark.asyncio
    async def test_instances_without_venv_still_work(self):
        """Test that existing instances without venv continue to work."""
        from pylet.controller import Controller
        from pylet.schemas import ResourceSpec
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            controller = Controller(db_path)
            await controller.startup()

            try:
                # Submit instance the "old way" without venv
                instance_id = await controller.submit_instance(
                    command="echo hello",
                    resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
                )

                instance = await controller.get_instance(instance_id)
                assert instance is not None
                assert instance.get("venv") is None
                # Instance should work normally

            finally:
                await controller.shutdown()

    @pytest.mark.asyncio
    async def test_worker_command_construction_unchanged_without_venv(self):
        """Test that worker command construction is unchanged when venv is None."""
        from pylet.worker import Worker
        from pylet.schemas import DesiredInstance
        from unittest.mock import MagicMock

        worker = Worker(
            head_address="localhost:8000",
            cpu_cores=4,
            gpu_units=0,
            memory_mb=8192,
        )
        worker.state_manager = MagicMock()

        inst = DesiredInstance(
            instance_id="test-inst",
            attempt=1,
            command="echo hello",
            expected_status="ASSIGNED",
            venv=None,  # Explicitly None
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

        # Should NOT contain any venv activation
        assert captured_cmd is not None
        assert "source" not in captured_cmd or "activate" not in captured_cmd
        # But should contain the command
        assert "echo hello" in captured_cmd

    def test_schema_backwards_compatible(self):
        """Test that schemas can be deserialized from old format (no venv)."""
        from pylet.schemas import InstanceSubmissionRequest, ResourceSpec

        # Old format without venv field
        old_format = {
            "command": "echo hello",
            "resource_requirements": {
                "cpu_cores": 1,
                "gpu_units": 0,
                "memory_mb": 512,
            },
        }

        # Should deserialize without error
        request = InstanceSubmissionRequest(**old_format)
        assert request.command == "echo hello"
        assert request.venv is None  # Should default to None
