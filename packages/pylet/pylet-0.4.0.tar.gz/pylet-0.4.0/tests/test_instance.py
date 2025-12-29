"""Tests for pylet/_instance.py"""

import pytest
from unittest.mock import MagicMock, patch
import base64

from pylet._instance import Instance, TERMINAL_STATES


class TestInstanceProperties:
    """Test Instance property accessors."""

    def test_id(self):
        """Instance.id returns the instance ID."""
        data = {"instance_id": "abc-123", "status": "PENDING"}
        instance = Instance(data)
        assert instance.id == "abc-123"

    def test_name(self):
        """Instance.name returns the instance name."""
        data = {"instance_id": "abc", "name": "my-instance", "status": "PENDING"}
        instance = Instance(data)
        assert instance.name == "my-instance"

    def test_name_none(self):
        """Instance.name returns None when not set."""
        data = {"instance_id": "abc", "status": "PENDING"}
        instance = Instance(data)
        assert instance.name is None

    def test_status(self):
        """Instance.status returns the current status."""
        data = {"instance_id": "abc", "status": "RUNNING"}
        instance = Instance(data)
        assert instance.status == "RUNNING"

    def test_display_status(self):
        """Instance.display_status returns display_status when available."""
        data = {"instance_id": "abc", "status": "RUNNING", "display_status": "CANCELLING"}
        instance = Instance(data)
        assert instance.display_status == "CANCELLING"

    def test_display_status_fallback(self):
        """Instance.display_status falls back to status."""
        data = {"instance_id": "abc", "status": "RUNNING"}
        instance = Instance(data)
        assert instance.display_status == "RUNNING"

    def test_endpoint(self):
        """Instance.endpoint returns the endpoint."""
        data = {"instance_id": "abc", "status": "RUNNING", "endpoint": "192.168.1.5:8080"}
        instance = Instance(data)
        assert instance.endpoint == "192.168.1.5:8080"

    def test_endpoint_none(self):
        """Instance.endpoint returns None when not available."""
        data = {"instance_id": "abc", "status": "PENDING"}
        instance = Instance(data)
        assert instance.endpoint is None

    def test_exit_code(self):
        """Instance.exit_code returns the exit code."""
        data = {"instance_id": "abc", "status": "COMPLETED", "exit_code": 0}
        instance = Instance(data)
        assert instance.exit_code == 0

    def test_exit_code_none(self):
        """Instance.exit_code returns None when not available."""
        data = {"instance_id": "abc", "status": "RUNNING"}
        instance = Instance(data)
        assert instance.exit_code is None


class TestInstanceRepr:
    """Test Instance string representation."""

    def test_repr_minimal(self):
        """__repr__ shows id and status."""
        data = {"instance_id": "abc-123", "status": "PENDING"}
        instance = Instance(data)
        assert "id='abc-123'" in repr(instance)
        assert "status='PENDING'" in repr(instance)

    def test_repr_with_name(self):
        """__repr__ shows name when available."""
        data = {"instance_id": "abc", "name": "my-instance", "status": "RUNNING"}
        instance = Instance(data)
        assert "name='my-instance'" in repr(instance)

    def test_repr_with_endpoint(self):
        """__repr__ shows endpoint when available."""
        data = {"instance_id": "abc", "status": "RUNNING", "endpoint": "host:8080"}
        instance = Instance(data)
        assert "endpoint='host:8080'" in repr(instance)


class TestTerminalStates:
    """Test terminal state constants."""

    def test_terminal_states(self):
        """TERMINAL_STATES contains expected values."""
        assert "COMPLETED" in TERMINAL_STATES
        assert "FAILED" in TERMINAL_STATES
        assert "CANCELLED" in TERMINAL_STATES
        assert "RUNNING" not in TERMINAL_STATES
        assert "PENDING" not in TERMINAL_STATES


class TestInstanceWaitRunning:
    """Test Instance.wait_running method."""

    def test_wait_running_already_running(self):
        """wait_running returns immediately if already RUNNING."""
        data = {"instance_id": "abc", "status": "RUNNING"}
        instance = Instance(data)

        with patch.object(instance, "refresh"):
            instance.wait_running(timeout=1)
            instance.refresh.assert_called()

    def test_wait_running_raises_on_failed(self):
        """wait_running raises InstanceFailedError if instance fails."""
        from pylet.errors import InstanceFailedError

        data = {"instance_id": "abc", "status": "FAILED"}
        instance = Instance(data)

        with patch.object(instance, "refresh"):
            with pytest.raises(InstanceFailedError) as exc_info:
                instance.wait_running(timeout=1)
            assert exc_info.value.instance is instance

    def test_wait_running_raises_on_cancelled(self):
        """wait_running raises InstanceFailedError if instance is cancelled."""
        from pylet.errors import InstanceFailedError

        data = {"instance_id": "abc", "status": "CANCELLED"}
        instance = Instance(data)

        with patch.object(instance, "refresh"):
            with pytest.raises(InstanceFailedError):
                instance.wait_running(timeout=1)

    def test_wait_running_timeout(self):
        """wait_running raises TimeoutError on timeout."""
        from pylet.errors import TimeoutError

        data = {"instance_id": "abc", "status": "PENDING"}
        instance = Instance(data)

        with patch.object(instance, "refresh"):
            with pytest.raises(TimeoutError):
                instance.wait_running(timeout=0.1)


class TestInstanceWait:
    """Test Instance.wait method."""

    def test_wait_already_terminal(self):
        """wait returns immediately if already terminal."""
        data = {"instance_id": "abc", "status": "COMPLETED"}
        instance = Instance(data)

        with patch.object(instance, "refresh"):
            instance.wait(timeout=1)
            instance.refresh.assert_called()

    def test_wait_timeout(self):
        """wait raises TimeoutError on timeout."""
        from pylet.errors import TimeoutError

        data = {"instance_id": "abc", "status": "RUNNING"}
        instance = Instance(data)

        with patch.object(instance, "refresh"):
            with pytest.raises(TimeoutError):
                instance.wait(timeout=0.1)


class TestInstanceCancel:
    """Test Instance.cancel method."""

    def test_cancel_raises_if_terminal(self):
        """cancel raises InstanceTerminatedError if already terminal."""
        from pylet.errors import InstanceTerminatedError

        data = {"instance_id": "abc", "status": "COMPLETED"}
        instance = Instance(data)

        with pytest.raises(InstanceTerminatedError):
            instance.cancel()

    def test_cancel_makes_request(self):
        """cancel makes POST request to cancel endpoint."""
        from pylet._state import _init_state, _shutdown_state

        data = {"instance_id": "abc-123", "status": "RUNNING"}
        instance = Instance(data)

        _init_state("http://localhost:8000")
        try:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()

            with patch("pylet._state._client") as mock_client:
                mock_client.post.return_value = mock_response
                instance.cancel()
                mock_client.post.assert_called_with(
                    "http://localhost:8000/instances/abc-123/cancel"
                )
        finally:
            _shutdown_state()


class TestInstanceLogs:
    """Test Instance.logs method."""

    def test_logs_decodes_base64(self):
        """logs decodes base64 content."""
        from pylet._state import _init_state, _shutdown_state

        data = {"instance_id": "abc-123", "status": "COMPLETED"}
        instance = Instance(data)

        _init_state("http://localhost:8000")
        try:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {
                "content": base64.b64encode(b"hello world").decode(),
            }

            with patch("pylet._state._client") as mock_client:
                mock_client.get.return_value = mock_response
                logs = instance.logs()
                assert logs == "hello world"
        finally:
            _shutdown_state()

    def test_logs_empty_content(self):
        """logs returns empty string for empty content."""
        from pylet._state import _init_state, _shutdown_state

        data = {"instance_id": "abc-123", "status": "COMPLETED"}
        instance = Instance(data)

        _init_state("http://localhost:8000")
        try:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"content": ""}

            with patch("pylet._state._client") as mock_client:
                mock_client.get.return_value = mock_response
                logs = instance.logs()
                assert logs == ""
        finally:
            _shutdown_state()


class TestInstanceRefresh:
    """Test Instance.refresh method."""

    def test_refresh_updates_data(self):
        """refresh updates instance data from server."""
        from pylet._state import _init_state, _shutdown_state

        data = {"instance_id": "abc-123", "status": "PENDING"}
        instance = Instance(data)

        _init_state("http://localhost:8000")
        try:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {
                "instance_id": "abc-123",
                "status": "RUNNING",
                "endpoint": "host:8080",
            }

            with patch("pylet._state._client") as mock_client:
                mock_client.get.return_value = mock_response
                instance.refresh()

                assert instance.status == "RUNNING"
                assert instance.endpoint == "host:8080"
        finally:
            _shutdown_state()
