"""
PyLet Instance - Handle to a submitted instance.

Instance objects are returned by pylet.submit() and pylet.get().
They provide properties and methods to interact with the instance.
"""

import time
from typing import Any, Dict, List, Optional

from pylet._state import _get_client, _get_head_address
from pylet.errors import (
    InstanceFailedError,
    InstanceTerminatedError,
    TimeoutError,
)


# Terminal states
TERMINAL_STATES = frozenset({"COMPLETED", "FAILED", "CANCELLED"})


class Instance:
    """
    Handle to a submitted instance.

    Properties are cached; call refresh() to update from server.
    Wait methods automatically refresh.
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize instance from server data.

        Args:
            data: Instance data dict from server API
        """
        self._data = data

    @property
    def id(self) -> str:
        """Instance UUID."""
        return self._data["instance_id"]

    @property
    def name(self) -> Optional[str]:
        """User-provided name, or None."""
        return self._data.get("name")

    @property
    def status(self) -> str:
        """
        Current status.

        One of: PENDING, ASSIGNED, RUNNING, COMPLETED, FAILED, CANCELLED, UNKNOWN.
        Note: Use display_status for user-facing status (shows CANCELLING).
        """
        return self._data["status"]

    @property
    def display_status(self) -> str:
        """
        Display status for user-facing output.

        Shows CANCELLING when cancellation is requested but not yet terminal.
        """
        return self._data.get("display_status", self._data["status"])

    @property
    def endpoint(self) -> Optional[str]:
        """host:port when running, None otherwise."""
        return self._data.get("endpoint")

    @property
    def exit_code(self) -> Optional[int]:
        """Process exit code when terminal, None otherwise."""
        return self._data.get("exit_code")

    # SLLM support properties
    @property
    def gpu_indices(self) -> Optional[List[int]]:
        """Allocated GPU indices when assigned/running, None otherwise."""
        return self._data.get("gpu_indices")

    @property
    def exclusive(self) -> bool:
        """Whether this instance has exclusive GPU access."""
        return self._data.get("exclusive", True)

    @property
    def labels(self) -> Dict[str, str]:
        """User-defined labels."""
        return self._data.get("labels", {})

    @property
    def env(self) -> Dict[str, str]:
        """User-defined environment variables."""
        return self._data.get("env", {})

    @property
    def target_worker(self) -> Optional[str]:
        """Target worker constraint, if set."""
        return self._data.get("target_worker")

    def wait_running(self, timeout: float = 300) -> None:
        """
        Block until instance reaches RUNNING status.

        Args:
            timeout: Maximum seconds to wait (default 300)

        Raises:
            TimeoutError: Instance not running within timeout
            InstanceFailedError: Instance entered FAILED or CANCELLED state
        """
        deadline = time.time() + timeout
        poll_interval = 2.0

        while time.time() < deadline:
            self.refresh()

            if self.status == "RUNNING":
                return
            if self.status in TERMINAL_STATES:
                raise InstanceFailedError(
                    f"Instance entered {self.status} state while waiting for RUNNING",
                    instance=self,
                )

            remaining = deadline - time.time()
            if remaining <= 0:
                break
            time.sleep(min(poll_interval, remaining))

        raise TimeoutError(f"Instance not running after {timeout}s (status: {self.status})")

    def wait(self, timeout: Optional[float] = None) -> None:
        """
        Block until instance reaches terminal state (COMPLETED, FAILED, CANCELLED).

        Args:
            timeout: Maximum seconds to wait, or None for no limit

        Raises:
            TimeoutError: Instance not terminal within timeout
        """
        deadline = time.time() + timeout if timeout else None
        poll_interval = 2.0

        while True:
            self.refresh()

            if self.status in TERMINAL_STATES:
                return

            if deadline:
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise TimeoutError(
                        f"Instance not terminal after {timeout}s (status: {self.status})"
                    )
                time.sleep(min(poll_interval, remaining))
            else:
                time.sleep(poll_interval)

    def cancel(self) -> None:
        """
        Request instance cancellation.

        Returns immediately (cancellation is async).

        Raises:
            InstanceTerminatedError: Instance already in terminal state
        """
        if self.status in TERMINAL_STATES:
            raise InstanceTerminatedError(
                f"Cannot cancel instance in terminal state: {self.status}"
            )

        client = _get_client()
        address = _get_head_address()

        response = client.post(f"{address}/instances/{self.id}/cancel")
        response.raise_for_status()

    def logs(self, tail: Optional[int] = None) -> str:
        """
        Get instance logs.

        Args:
            tail: If provided, return only last N bytes

        Returns:
            Log content as string
        """
        client = _get_client()
        address = _get_head_address()

        params = {}
        if tail is not None:
            # Get total size first to calculate offset
            response = client.get(
                f"{address}/instances/{self.id}/logs",
                params={"limit": 0},
            )
            response.raise_for_status()
            data = response.json()
            total_size = data.get("total_size", 0)
            if total_size > tail:
                params["offset"] = total_size - tail
            params["limit"] = tail

        response = client.get(
            f"{address}/instances/{self.id}/logs",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        # Decode base64 content
        import base64

        content = data.get("content", "")
        if content:
            return base64.b64decode(content).decode("utf-8", errors="replace")
        return ""

    def refresh(self) -> None:
        """Fetch latest state from server. Updates all properties."""
        client = _get_client()
        address = _get_head_address()

        response = client.get(f"{address}/instances/{self.id}")
        response.raise_for_status()
        self._data = response.json()

    def __repr__(self) -> str:
        """Return string representation."""
        parts = [f"id='{self.id}'"]
        if self.name:
            parts.append(f"name='{self.name}'")
        parts.append(f"status='{self.display_status}'")
        if self.endpoint:
            parts.append(f"endpoint='{self.endpoint}'")
        return f"Instance({', '.join(parts)})"
