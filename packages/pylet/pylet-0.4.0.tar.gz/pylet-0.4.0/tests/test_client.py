"""Unit tests for pylet.client module."""

import pytest
import pytest_asyncio
import base64
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from pylet.client import PyletClient, DEFAULT_WORKER_HTTP_PORT


class MockResponse:
    """Mock HTTP response."""

    def __init__(self, json_data=None, status_code=200, text=""):
        self._json_data = json_data
        self.status_code = status_code
        self._text = text

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "Error",
                request=MagicMock(),
                response=self,
            )


@pytest_asyncio.fixture
async def client():
    """Create a PyletClient instance."""
    client = PyletClient("http://localhost:8000")
    yield client
    await client.close()


class TestClientInit:
    """Tests for client initialization."""

    def test_default_url(self):
        """Test default API server URL."""
        client = PyletClient()
        assert client.api_server_url == "http://localhost:8000"

    def test_custom_url(self):
        """Test custom API server URL."""
        client = PyletClient("http://192.168.1.1:9000")
        assert client.api_server_url == "http://192.168.1.1:9000"


class TestSubmitInstance:
    """Tests for submit_instance method."""

    @pytest.mark.asyncio
    async def test_submit_instance(self, client):
        """Test submitting an instance."""
        mock_response = MockResponse({"instance_id": "inst-123"})

        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            instance_id = await client.submit_instance(
                command="echo hello",
                resource_requirements={"cpu_cores": 2, "gpu_units": 1, "memory_mb": 4096},
                name="my-instance",
            )

            assert instance_id == "inst-123"
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "http://localhost:8000/instances"
            assert call_args[1]["json"]["command"] == "echo hello"
            assert call_args[1]["json"]["name"] == "my-instance"

    @pytest.mark.asyncio
    async def test_submit_instance_without_name(self, client):
        """Test submitting instance without name."""
        mock_response = MockResponse({"instance_id": "inst-456"})

        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await client.submit_instance(
                command="cmd",
                resource_requirements={"cpu_cores": 1, "gpu_units": 0, "memory_mb": 512},
            )

            call_args = mock_post.call_args
            assert "name" not in call_args[1]["json"]


class TestGetInstance:
    """Tests for get_instance method."""

    @pytest.mark.asyncio
    async def test_get_instance(self, client):
        """Test getting instance by ID."""
        instance_data = {
            "id": "inst-123",
            "name": "my-instance",
            "status": "RUNNING",
            "command": "echo hello",
        }
        mock_response = MockResponse(instance_data)

        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client.get_instance("inst-123")

            assert result == instance_data
            mock_get.assert_called_once_with(
                "http://localhost:8000/instances/inst-123"
            )

    @pytest.mark.asyncio
    async def test_get_instance_by_name(self, client):
        """Test getting instance by name."""
        instance_data = {"id": "inst-789", "name": "named-instance"}
        mock_response = MockResponse(instance_data)

        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client.get_instance_by_name("named-instance")

            assert result == instance_data
            mock_get.assert_called_once_with(
                "http://localhost:8000/instances/by-name/named-instance"
            )


class TestGetInstanceResult:
    """Tests for get_instance_result method."""

    @pytest.mark.asyncio
    async def test_get_instance_result_completed(self, client):
        """Test getting result of completed instance."""
        result_data = {"status": "COMPLETED", "exit_code": 0}
        mock_response = MockResponse(result_data, status_code=200)

        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client.get_instance_result("inst-123")

            assert result == result_data

    @pytest.mark.asyncio
    async def test_get_instance_result_pending(self, client):
        """Test getting result of pending instance."""
        mock_response = MockResponse(status_code=202)

        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client.get_instance_result("inst-123")

            assert result == {"status": "PENDING"}


class TestGetInstanceEndpoint:
    """Tests for get_instance_endpoint methods."""

    @pytest.mark.asyncio
    async def test_get_instance_endpoint(self, client):
        """Test getting instance endpoint by ID."""
        mock_response = MockResponse({"endpoint": "192.168.1.1:15600"})

        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            endpoint = await client.get_instance_endpoint("inst-123")

            assert endpoint == "192.168.1.1:15600"

    @pytest.mark.asyncio
    async def test_get_instance_endpoint_by_name(self, client):
        """Test getting instance endpoint by name."""
        mock_response = MockResponse({"endpoint": "192.168.1.2:15601"})

        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            endpoint = await client.get_instance_endpoint_by_name("my-instance")

            assert endpoint == "192.168.1.2:15601"
            mock_get.assert_called_once_with(
                "http://localhost:8000/instances/by-name/my-instance/endpoint"
            )


class TestCancelInstance:
    """Tests for cancel_instance method."""

    @pytest.mark.asyncio
    async def test_cancel_instance(self, client):
        """Test cancelling an instance."""
        mock_response = MockResponse({"message": "Cancellation requested"})

        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await client.cancel_instance("inst-123")

            assert result == {"message": "Cancellation requested"}
            mock_post.assert_called_once_with(
                "http://localhost:8000/instances/inst-123/cancel"
            )


class TestGetLogs:
    """Tests for get_logs method."""

    @pytest.mark.asyncio
    async def test_get_logs_direct_worker(self, client):
        """Test getting logs directly from worker."""
        log_content = base64.b64encode(b"Log line 1\nLog line 2\n").decode()
        instance_data = {"assigned_to": "worker-1"}
        workers_data = [{"worker_id": "worker-1", "host": "192.168.1.100"}]
        log_response = {
            "available_offset": 0,
            "total_size": 26,
            "content": log_content,
            "size": 26,
        }

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if "instances/inst-123" in url and "logs" not in url:
                return MockResponse(instance_data)
            elif "/workers" in url:
                return MockResponse(workers_data)
            elif "192.168.1.100" in url:
                return MockResponse(log_response)
            raise ValueError(f"Unexpected URL: {url}")

        with patch.object(client.client, "get", side_effect=mock_get):
            result = await client.get_logs("inst-123")

            assert result["content"] == log_content
            assert result["data"] == b"Log line 1\nLog line 2\n"

    @pytest.mark.asyncio
    async def test_get_logs_fallback_to_head(self, client):
        """Test getting logs falls back to head when direct fails."""
        log_content = base64.b64encode(b"Fallback logs\n").decode()
        instance_data = {"assigned_to": "worker-1"}
        workers_data = [{"worker_id": "worker-1", "host": "192.168.1.100"}]
        log_response = {
            "available_offset": 0,
            "total_size": 15,
            "content": log_content,
            "size": 15,
        }

        async def mock_get(url, **kwargs):
            if "instances/inst-123" in url and "logs" not in url:
                return MockResponse(instance_data)
            elif "/workers" in url:
                return MockResponse(workers_data)
            elif "192.168.1.100" in url:
                raise httpx.ConnectError("Connection refused")
            elif "logs" in url:
                return MockResponse(log_response)
            raise ValueError(f"Unexpected URL: {url}")

        with patch.object(client.client, "get", side_effect=mock_get):
            result = await client.get_logs("inst-123")

            assert result["data"] == b"Fallback logs\n"

    @pytest.mark.asyncio
    async def test_get_logs_no_direct(self, client):
        """Test getting logs with use_direct=False."""
        log_content = base64.b64encode(b"Head logs\n").decode()
        log_response = {
            "available_offset": 0,
            "total_size": 11,
            "content": log_content,
            "size": 11,
        }

        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MockResponse(log_response)

            result = await client.get_logs("inst-123", use_direct=False)

            assert result["data"] == b"Head logs\n"
            # Should only call head endpoint
            mock_get.assert_called_once()
            assert "localhost:8000" in mock_get.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_logs_empty_content(self, client):
        """Test getting logs with empty content."""
        log_response = {
            "available_offset": 0,
            "total_size": 0,
            "content": "",
            "size": 0,
        }

        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MockResponse(log_response)

            result = await client.get_logs("inst-123", use_direct=False)

            assert result["data"] == b""


class TestListWorkers:
    """Tests for list_workers method."""

    @pytest.mark.asyncio
    async def test_list_workers(self, client):
        """Test listing workers."""
        workers_data = [
            {"worker_id": "w1", "host": "1.1.1.1", "status": "ONLINE"},
            {"worker_id": "w2", "host": "2.2.2.2", "status": "OFFLINE"},
        ]
        mock_response = MockResponse(workers_data)

        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client.list_workers()

            assert result == workers_data
            mock_get.assert_called_once_with("http://localhost:8000/workers")


class TestGetWorker:
    """Tests for get_worker method."""

    @pytest.mark.asyncio
    async def test_get_worker(self, client):
        """Test getting worker by ID."""
        worker_data = {"worker_id": "w1", "host": "1.1.1.1", "status": "ONLINE"}
        mock_response = MockResponse(worker_data)

        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client.get_worker("w1")

            assert result == worker_data
            mock_get.assert_called_once_with("http://localhost:8000/workers/w1")


class TestClientClose:
    """Tests for client close method."""

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the client."""
        client = PyletClient()

        with patch.object(client.client, "aclose", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()


class TestDefaultWorkerHTTPPort:
    """Tests for DEFAULT_WORKER_HTTP_PORT constant."""

    def test_default_port(self):
        """Test default worker HTTP port value."""
        assert DEFAULT_WORKER_HTTP_PORT == 15599
