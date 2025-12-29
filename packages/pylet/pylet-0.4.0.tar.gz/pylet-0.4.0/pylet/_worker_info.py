"""
PyLet WorkerInfo - Read-only data object for worker information.

Returned by pylet.workers().
"""

from typing import Any, Dict, List


class WorkerInfo:
    """
    Read-only data object representing a worker.

    Returned by pylet.workers().
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize from server data.

        Args:
            data: Worker data dict from server API
        """
        self._data = data

    @property
    def id(self) -> str:
        """Worker UUID."""
        return self._data["worker_id"]

    @property
    def host(self) -> str:
        """Worker IP address."""
        return self._data["host"]

    @property
    def status(self) -> str:
        """Worker status: ONLINE, SUSPECT, or OFFLINE."""
        return self._data["status"]

    @property
    def gpu(self) -> int:
        """Total GPU units."""
        return self._data["total_resources"]["gpu_units"]

    @property
    def gpu_available(self) -> int:
        """Available GPU units."""
        return self._data["available_resources"]["gpu_units"]

    @property
    def cpu(self) -> int:
        """Total CPU cores."""
        return self._data["total_resources"]["cpu_cores"]

    @property
    def cpu_available(self) -> int:
        """Available CPU cores."""
        return self._data["available_resources"]["cpu_cores"]

    @property
    def memory(self) -> int:
        """Total memory in MB."""
        return self._data["total_resources"]["memory_mb"]

    @property
    def memory_available(self) -> int:
        """Available memory in MB."""
        return self._data["available_resources"]["memory_mb"]

    @property
    def gpu_indices_available(self) -> List[int]:
        """List of available GPU indices."""
        return self._data.get("available_gpu_indices", [])

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"WorkerInfo(id='{self.id}', host='{self.host}', status='{self.status}', "
            f"gpu={self.gpu_available}/{self.gpu}, "
            f"cpu={self.cpu_available}/{self.cpu}, "
            f"memory={self.memory_available}/{self.memory})"
        )
