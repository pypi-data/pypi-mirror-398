"""Tests for pylet/_sync_api.py"""

import pytest
from unittest.mock import MagicMock, patch

from pylet._state import _shutdown_state
from pylet._sync_api import (
    get,
    init,
    instances,
    is_initialized,
    shutdown,
    submit,
    workers,
)
from pylet.errors import NotFoundError, NotInitializedError


class TestInit:
    """Test pylet.init() function."""

    def setup_method(self):
        """Ensure clean state before each test."""
        _shutdown_state()

    def teardown_method(self):
        """Clean up state after each test."""
        _shutdown_state()

    def test_init_sets_initialized(self):
        """init() sets the module as initialized."""
        with patch("pylet._sync_api._init_state") as mock_init:
            with patch("pylet._sync_api._get_client") as mock_get_client:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_client.get.return_value = mock_response
                mock_get_client.return_value = mock_client

                init("http://localhost:8000")
                mock_init.assert_called_with("http://localhost:8000")

    def test_init_default_address(self):
        """init() uses default address if not specified."""
        with patch("pylet._sync_api._init_state") as mock_init:
            with patch("pylet._sync_api._get_client") as mock_get_client:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_client.get.return_value = mock_response
                mock_get_client.return_value = mock_client

                init()
                mock_init.assert_called_with("http://localhost:8000")

    def test_init_connection_error(self):
        """init() raises ConnectionError if cannot reach head."""
        import httpx

        with patch("pylet._sync_api._init_state"):
            with patch("pylet._sync_api._get_client") as mock_get_client:
                mock_client = MagicMock()
                mock_client.get.side_effect = httpx.ConnectError("Cannot connect")
                mock_get_client.return_value = mock_client

                with pytest.raises(ConnectionError):
                    init("http://localhost:8000")


class TestShutdown:
    """Test pylet.shutdown() function."""

    def test_shutdown_clears_state(self):
        """shutdown() clears module state."""
        with patch("pylet._sync_api._shutdown_state") as mock_shutdown:
            shutdown()
            mock_shutdown.assert_called_once()


class TestIsInitialized:
    """Test pylet.is_initialized() function."""

    def test_is_initialized(self):
        """is_initialized() returns initialization status."""
        with patch("pylet._sync_api._is_initialized", return_value=True):
            assert is_initialized() is True

        with patch("pylet._sync_api._is_initialized", return_value=False):
            assert is_initialized() is False


class TestSubmit:
    """Test pylet.submit() function."""

    def test_submit_string_command(self):
        """submit() accepts string command."""
        with patch("pylet._sync_api._get_client") as mock_get_client:
            with patch("pylet._sync_api._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {"instance_id": "abc-123"}
                mock_client.post.return_value = mock_response
                mock_client.get.return_value = mock_response
                mock_get_client.return_value = mock_client

                # Override the second json call for get
                mock_response.json.side_effect = [
                    {"instance_id": "abc-123"},
                    {"instance_id": "abc-123", "status": "PENDING"},
                ]

                instance = submit("echo hello", cpu=1)
                assert instance.id == "abc-123"

                # Verify POST was called with correct data
                call_args = mock_client.post.call_args
                assert call_args[0][0] == "http://localhost:8000/instances"
                json_data = call_args[1]["json"]
                assert json_data["command"] == "echo hello"
                assert json_data["resource_requirements"]["cpu_cores"] == 1

    def test_submit_list_command(self):
        """submit() accepts list command and shell-escapes it."""
        with patch("pylet._sync_api._get_client") as mock_get_client:
            with patch("pylet._sync_api._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.side_effect = [
                    {"instance_id": "abc-123"},
                    {"instance_id": "abc-123", "status": "PENDING"},
                ]
                mock_client.post.return_value = mock_response
                mock_client.get.return_value = mock_response
                mock_get_client.return_value = mock_client

                submit(["python", "-c", "print('hello world')"], cpu=1)

                call_args = mock_client.post.call_args
                json_data = call_args[1]["json"]
                # shlex.join escapes the command
                assert "python" in json_data["command"]
                assert "-c" in json_data["command"]

    def test_submit_with_resources(self):
        """submit() includes resource requirements."""
        with patch("pylet._sync_api._get_client") as mock_get_client:
            with patch("pylet._sync_api._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.side_effect = [
                    {"instance_id": "abc-123"},
                    {"instance_id": "abc-123", "status": "PENDING"},
                ]
                mock_client.post.return_value = mock_response
                mock_client.get.return_value = mock_response
                mock_get_client.return_value = mock_client

                submit("cmd", gpu=2, cpu=4, memory=8192)

                call_args = mock_client.post.call_args
                json_data = call_args[1]["json"]
                assert json_data["resource_requirements"]["gpu_units"] == 2
                assert json_data["resource_requirements"]["cpu_cores"] == 4
                assert json_data["resource_requirements"]["memory_mb"] == 8192

    def test_submit_with_name(self):
        """submit() includes instance name."""
        with patch("pylet._sync_api._get_client") as mock_get_client:
            with patch("pylet._sync_api._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.side_effect = [
                    {"instance_id": "abc-123"},
                    {"instance_id": "abc-123", "status": "PENDING", "name": "my-instance"},
                ]
                mock_client.post.return_value = mock_response
                mock_client.get.return_value = mock_response
                mock_get_client.return_value = mock_client

                instance = submit("cmd", name="my-instance", cpu=1)

                call_args = mock_client.post.call_args
                json_data = call_args[1]["json"]
                assert json_data["name"] == "my-instance"


class TestGet:
    """Test pylet.get() function."""

    def test_get_by_name(self):
        """get() retrieves instance by name."""
        with patch("pylet._sync_api._get_client") as mock_get_client:
            with patch("pylet._sync_api._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "instance_id": "abc-123",
                    "name": "my-instance",
                    "status": "RUNNING",
                }
                mock_client.get.return_value = mock_response
                mock_get_client.return_value = mock_client

                instance = get("my-instance")
                assert instance.id == "abc-123"
                assert instance.name == "my-instance"

                mock_client.get.assert_called_with(
                    "http://localhost:8000/instances/by-name/my-instance"
                )

    def test_get_by_id(self):
        """get() retrieves instance by ID."""
        with patch("pylet._sync_api._get_client") as mock_get_client:
            with patch("pylet._sync_api._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "instance_id": "abc-123",
                    "status": "RUNNING",
                }
                mock_client.get.return_value = mock_response
                mock_get_client.return_value = mock_client

                instance = get(id="abc-123")
                assert instance.id == "abc-123"

                mock_client.get.assert_called_with(
                    "http://localhost:8000/instances/abc-123"
                )

    def test_get_raises_without_identifier(self):
        """get() raises ValueError without name or id."""
        with pytest.raises(ValueError):
            get()

    def test_get_not_found(self):
        """get() raises NotFoundError for 404."""
        import httpx

        with patch("pylet._sync_api._get_client") as mock_get_client:
            with patch("pylet._sync_api._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.status_code = 404
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=MagicMock(), response=mock_response
                )
                mock_client.get.return_value = mock_response
                mock_get_client.return_value = mock_client

                with pytest.raises(NotFoundError):
                    get(id="nonexistent")


class TestInstances:
    """Test pylet.instances() function."""

    def test_instances_returns_list(self):
        """instances() returns list of Instance objects."""
        with patch("pylet._sync_api._get_client") as mock_get_client:
            with patch("pylet._sync_api._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = [
                    {"instance_id": "abc", "status": "RUNNING"},
                    {"instance_id": "def", "status": "COMPLETED"},
                ]
                mock_client.get.return_value = mock_response
                mock_get_client.return_value = mock_client

                result = instances()
                assert len(result) == 2
                assert result[0].id == "abc"
                assert result[1].id == "def"

    def test_instances_with_status_filter(self):
        """instances() passes status filter."""
        with patch("pylet._sync_api._get_client") as mock_get_client:
            with patch("pylet._sync_api._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = [
                    {"instance_id": "abc", "status": "RUNNING"},
                ]
                mock_client.get.return_value = mock_response
                mock_get_client.return_value = mock_client

                instances(status="RUNNING")

                mock_client.get.assert_called_with(
                    "http://localhost:8000/instances",
                    params={"status": "RUNNING"},
                )


class TestWorkers:
    """Test pylet.workers() function."""

    def test_workers_returns_list(self):
        """workers() returns list of WorkerInfo objects."""
        with patch("pylet._sync_api._get_client") as mock_get_client:
            with patch("pylet._sync_api._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = [
                    {
                        "worker_id": "w-1",
                        "host": "10.0.0.1",
                        "status": "ONLINE",
                        "total_resources": {"gpu_units": 2, "cpu_cores": 8, "memory_mb": 16384},
                        "available_resources": {"gpu_units": 1, "cpu_cores": 4, "memory_mb": 8192},
                    },
                ]
                mock_client.get.return_value = mock_response
                mock_get_client.return_value = mock_client

                result = workers()
                assert len(result) == 1
                assert result[0].id == "w-1"
                assert result[0].host == "10.0.0.1"
