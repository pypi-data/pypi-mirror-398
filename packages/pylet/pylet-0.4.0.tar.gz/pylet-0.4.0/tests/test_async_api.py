"""Tests for pylet/aio module"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pylet._state import _shutdown_state
import pylet.aio as aio
from pylet.errors import NotFoundError


class TestAsyncInit:
    """Test pylet.aio.init() function."""

    def setup_method(self):
        """Ensure clean state before each test."""
        _shutdown_state()

    def teardown_method(self):
        """Clean up state after each test."""
        _shutdown_state()

    @pytest.mark.asyncio
    async def test_init_sets_initialized(self):
        """init() sets the module as initialized."""
        with patch("pylet.aio._init_state_async", new_callable=AsyncMock) as mock_init:
            with patch("pylet.aio._get_async_client") as mock_get_client:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_get_client.return_value = mock_client

                await aio.init("http://localhost:8000")
                mock_init.assert_called_with("http://localhost:8000")

    @pytest.mark.asyncio
    async def test_init_connection_error(self):
        """init() raises ConnectionError if cannot reach head."""
        import httpx

        with patch("pylet.aio._init_state_async", new_callable=AsyncMock):
            with patch("pylet.aio._get_async_client") as mock_get_client:
                mock_client = MagicMock()
                mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Cannot connect"))
                mock_get_client.return_value = mock_client

                with pytest.raises(ConnectionError):
                    await aio.init("http://localhost:8000")


class TestAsyncShutdown:
    """Test pylet.aio.shutdown() function."""

    @pytest.mark.asyncio
    async def test_shutdown_clears_state(self):
        """shutdown() clears module state."""
        with patch("pylet.aio._shutdown_state_async", new_callable=AsyncMock) as mock_shutdown:
            await aio.shutdown()
            mock_shutdown.assert_called_once()


class TestAsyncIsInitialized:
    """Test pylet.aio.is_initialized() function."""

    def test_is_initialized(self):
        """is_initialized() returns initialization status (sync)."""
        with patch("pylet.aio._is_initialized", return_value=True):
            assert aio.is_initialized() is True


class TestAsyncSubmit:
    """Test pylet.aio.submit() function."""

    @pytest.mark.asyncio
    async def test_submit_string_command(self):
        """submit() accepts string command."""
        with patch("pylet.aio._get_async_client") as mock_get_client:
            with patch("pylet.aio._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.side_effect = [
                    {"instance_id": "abc-123"},
                    {"instance_id": "abc-123", "status": "PENDING"},
                ]
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_get_client.return_value = mock_client

                instance = await aio.submit("echo hello", cpu=1)
                assert instance.id == "abc-123"

    @pytest.mark.asyncio
    async def test_submit_with_resources(self):
        """submit() includes resource requirements."""
        with patch("pylet.aio._get_async_client") as mock_get_client:
            with patch("pylet.aio._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.side_effect = [
                    {"instance_id": "abc-123"},
                    {"instance_id": "abc-123", "status": "PENDING"},
                ]
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_get_client.return_value = mock_client

                await aio.submit("cmd", gpu=2, cpu=4, memory=8192)

                call_args = mock_client.post.call_args
                json_data = call_args[1]["json"]
                assert json_data["resource_requirements"]["gpu_units"] == 2
                assert json_data["resource_requirements"]["cpu_cores"] == 4
                assert json_data["resource_requirements"]["memory_mb"] == 8192


class TestAsyncGet:
    """Test pylet.aio.get() function."""

    @pytest.mark.asyncio
    async def test_get_by_name(self):
        """get() retrieves instance by name."""
        with patch("pylet.aio._get_async_client") as mock_get_client:
            with patch("pylet.aio._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "instance_id": "abc-123",
                    "name": "my-instance",
                    "status": "RUNNING",
                }
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_get_client.return_value = mock_client

                instance = await aio.get("my-instance")
                assert instance.id == "abc-123"

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """get() retrieves instance by ID."""
        with patch("pylet.aio._get_async_client") as mock_get_client:
            with patch("pylet.aio._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "instance_id": "abc-123",
                    "status": "RUNNING",
                }
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_get_client.return_value = mock_client

                instance = await aio.get(id="abc-123")
                assert instance.id == "abc-123"

    @pytest.mark.asyncio
    async def test_get_raises_without_identifier(self):
        """get() raises ValueError without name or id."""
        with pytest.raises(ValueError):
            await aio.get()

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """get() raises NotFoundError for 404."""
        import httpx

        with patch("pylet.aio._get_async_client") as mock_get_client:
            with patch("pylet.aio._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.status_code = 404
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=MagicMock(), response=mock_response
                )
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_get_client.return_value = mock_client

                with pytest.raises(NotFoundError):
                    await aio.get(id="nonexistent")


class TestAsyncInstances:
    """Test pylet.aio.instances() function."""

    @pytest.mark.asyncio
    async def test_instances_returns_list(self):
        """instances() returns list of Instance objects."""
        with patch("pylet.aio._get_async_client") as mock_get_client:
            with patch("pylet.aio._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = [
                    {"instance_id": "abc", "status": "RUNNING"},
                    {"instance_id": "def", "status": "COMPLETED"},
                ]
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_get_client.return_value = mock_client

                result = await aio.instances()
                assert len(result) == 2
                assert result[0].id == "abc"
                assert result[1].id == "def"

    @pytest.mark.asyncio
    async def test_instances_with_status_filter(self):
        """instances() passes status filter."""
        with patch("pylet.aio._get_async_client") as mock_get_client:
            with patch("pylet.aio._get_head_address", return_value="http://localhost:8000"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = []
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_get_client.return_value = mock_client

                await aio.instances(status="RUNNING")

                mock_client.get.assert_called_with(
                    "http://localhost:8000/instances",
                    params={"status": "RUNNING"},
                )


class TestAsyncWorkers:
    """Test pylet.aio.workers() function."""

    @pytest.mark.asyncio
    async def test_workers_returns_list(self):
        """workers() returns list of WorkerInfo objects."""
        with patch("pylet.aio._get_async_client") as mock_get_client:
            with patch("pylet.aio._get_head_address", return_value="http://localhost:8000"):
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
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_get_client.return_value = mock_client

                result = await aio.workers()
                assert len(result) == 1
                assert result[0].id == "w-1"


class TestAsyncInstance:
    """Test pylet.aio.Instance methods."""

    @pytest.mark.asyncio
    async def test_instance_wait_running(self):
        """Instance.wait_running works asynchronously."""
        from pylet.aio._instance import Instance

        data = {"instance_id": "abc", "status": "RUNNING"}
        instance = Instance(data)

        with patch.object(instance, "refresh", new_callable=AsyncMock):
            await instance.wait_running(timeout=1)
            instance.refresh.assert_called()

    @pytest.mark.asyncio
    async def test_instance_wait(self):
        """Instance.wait works asynchronously."""
        from pylet.aio._instance import Instance

        data = {"instance_id": "abc", "status": "COMPLETED"}
        instance = Instance(data)

        with patch.object(instance, "refresh", new_callable=AsyncMock):
            await instance.wait(timeout=1)
            instance.refresh.assert_called()

    @pytest.mark.asyncio
    async def test_instance_cancel(self):
        """Instance.cancel works asynchronously."""
        from pylet.aio._instance import Instance
        from pylet._state import _init_state, _shutdown_state

        data = {"instance_id": "abc-123", "status": "RUNNING"}
        instance = Instance(data)

        _init_state("http://localhost:8000")
        try:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()

            with patch("pylet._state._async_client") as mock_client:
                mock_client.post = AsyncMock(return_value=mock_response)
                await instance.cancel()
                mock_client.post.assert_called()
        finally:
            _shutdown_state()
