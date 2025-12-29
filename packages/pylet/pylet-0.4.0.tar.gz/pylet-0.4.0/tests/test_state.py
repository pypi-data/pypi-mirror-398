"""Tests for pylet/_state.py"""

import pytest

from pylet._state import (
    _get_async_client,
    _get_client,
    _get_head_address,
    _init_state,
    _is_initialized,
    _shutdown_state,
)
from pylet.errors import NotInitializedError


class TestStateManagement:
    """Test module state management."""

    def setup_method(self):
        """Ensure clean state before each test."""
        _shutdown_state()

    def teardown_method(self):
        """Clean up state after each test."""
        _shutdown_state()

    def test_not_initialized_by_default(self):
        """State is not initialized by default."""
        assert _is_initialized() is False

    def test_get_client_raises_when_not_initialized(self):
        """_get_client raises NotInitializedError when not initialized."""
        with pytest.raises(NotInitializedError):
            _get_client()

    def test_get_async_client_raises_when_not_initialized(self):
        """_get_async_client raises NotInitializedError when not initialized."""
        with pytest.raises(NotInitializedError):
            _get_async_client()

    def test_get_head_address_raises_when_not_initialized(self):
        """_get_head_address raises NotInitializedError when not initialized."""
        with pytest.raises(NotInitializedError):
            _get_head_address()

    def test_init_state_sets_initialized(self):
        """_init_state sets the module as initialized."""
        _init_state("http://localhost:8000")
        assert _is_initialized() is True

    def test_init_state_creates_clients(self):
        """_init_state creates HTTP clients."""
        _init_state("http://localhost:8000")
        client = _get_client()
        assert client is not None

        async_client = _get_async_client()
        assert async_client is not None

    def test_init_state_stores_address(self):
        """_init_state stores the head address."""
        _init_state("http://test:9000")
        assert _get_head_address() == "http://test:9000"

    def test_shutdown_state_clears_initialized(self):
        """_shutdown_state clears the initialized state."""
        _init_state("http://localhost:8000")
        assert _is_initialized() is True

        _shutdown_state()
        assert _is_initialized() is False

    def test_shutdown_state_clears_clients(self):
        """_shutdown_state clears the HTTP clients."""
        _init_state("http://localhost:8000")
        _shutdown_state()

        with pytest.raises(NotInitializedError):
            _get_client()

    def test_reinit_state(self):
        """Can reinitialize state with different address."""
        _init_state("http://localhost:8000")
        assert _get_head_address() == "http://localhost:8000"

        _init_state("http://newhost:9000")
        assert _get_head_address() == "http://newhost:9000"

    def test_shutdown_is_idempotent(self):
        """_shutdown_state can be called multiple times."""
        _shutdown_state()
        _shutdown_state()  # Should not raise
        assert _is_initialized() is False


class TestAsyncStateManagement:
    """Test async state management functions."""

    def setup_method(self):
        """Ensure clean state before each test."""
        _shutdown_state()

    def teardown_method(self):
        """Clean up state after each test."""
        _shutdown_state()

    @pytest.mark.asyncio
    async def test_init_state_async(self):
        """_init_state_async initializes the module."""
        from pylet._state import _init_state_async

        await _init_state_async("http://localhost:8000")
        assert _is_initialized() is True
        assert _get_head_address() == "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_shutdown_state_async(self):
        """_shutdown_state_async clears the state."""
        from pylet._state import _init_state_async, _shutdown_state_async

        await _init_state_async("http://localhost:8000")
        await _shutdown_state_async()
        assert _is_initialized() is False
