"""
PyLet Module State - Global state for the pylet module.

Uses module-level state with atexit cleanup, similar to Ray's pattern.
"""

import atexit
from typing import Optional

import httpx

from pylet.errors import NotInitializedError

# Module-level state
_client: Optional[httpx.Client] = None
_async_client: Optional[httpx.AsyncClient] = None
_head_address: Optional[str] = None


def _get_client() -> httpx.Client:
    """Get the sync HTTP client, raising if not initialized."""
    global _client
    if _client is None:
        raise NotInitializedError()
    return _client


def _get_async_client() -> httpx.AsyncClient:
    """Get the async HTTP client, raising if not initialized."""
    global _async_client
    if _async_client is None:
        raise NotInitializedError()
    return _async_client


def _get_head_address() -> str:
    """Get the head node address, raising if not initialized."""
    global _head_address
    if _head_address is None:
        raise NotInitializedError()
    return _head_address


def _init_state(address: str) -> None:
    """Initialize the module state."""
    global _client, _async_client, _head_address

    # Close existing clients if reinitializing
    if _client is not None:
        _client.close()
    if _async_client is not None:
        # We can't close async client synchronously here
        # It will be closed on next async operation or atexit
        pass

    _head_address = address
    _client = httpx.Client(timeout=30.0)
    _async_client = httpx.AsyncClient(timeout=30.0)


async def _init_state_async(address: str) -> None:
    """Initialize the module state (async version)."""
    global _client, _async_client, _head_address

    # Close existing clients
    if _client is not None:
        _client.close()
    if _async_client is not None:
        await _async_client.aclose()

    _head_address = address
    _client = httpx.Client(timeout=30.0)
    _async_client = httpx.AsyncClient(timeout=30.0)


def _shutdown_state() -> None:
    """Shutdown the module state."""
    global _client, _async_client, _head_address

    if _client is not None:
        _client.close()
        _client = None
    # Note: async client may not be properly closed in sync shutdown
    # This is acceptable as it will be GC'd
    _async_client = None
    _head_address = None


async def _shutdown_state_async() -> None:
    """Shutdown the module state (async version)."""
    global _client, _async_client, _head_address

    if _client is not None:
        _client.close()
        _client = None
    if _async_client is not None:
        await _async_client.aclose()
        _async_client = None
    _head_address = None


def _is_initialized() -> bool:
    """Check if the module is initialized."""
    return _head_address is not None


# Register atexit handler for cleanup
def _atexit_cleanup() -> None:
    """Clean up on process exit."""
    global _client, _async_client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
    # Note: can't properly close async client at exit
    # but httpx handles this gracefully


atexit.register(_atexit_cleanup)
