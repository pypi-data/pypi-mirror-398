"""
PyLet Client - Async HTTP client for the PyLet API.
"""

import base64
from typing import Any, Dict, List, Optional

import httpx

# Default worker HTTP port for direct log access
DEFAULT_WORKER_HTTP_PORT = 15599


class PyletClient:
    """Async client for interacting with the PyLet server."""

    def __init__(self, api_server_url: str = "http://localhost:8000"):
        self.api_server_url = api_server_url
        self.client = httpx.AsyncClient()

    # ========== Instance Methods ==========

    async def submit_instance(
        self,
        command: str,
        resource_requirements: Dict[str, int],
        name: Optional[str] = None,
        # SLLM support parameters
        target_worker: Optional[str] = None,
        gpu_indices: Optional[List[int]] = None,
        exclusive: bool = True,
        labels: Optional[Dict[str, str]] = None,
        env: Optional[Dict[str, str]] = None,
        # Venv support
        venv: Optional[str] = None,
    ) -> str:
        """Submit a new instance for execution."""
        submission_data: Dict[str, Any] = {
            "command": command,
            "resource_requirements": resource_requirements,
            "exclusive": exclusive,
            "labels": labels or {},
            "env": env or {},
        }
        if name:
            submission_data["name"] = name
        if target_worker is not None:
            submission_data["target_worker"] = target_worker
        if gpu_indices is not None:
            submission_data["gpu_indices"] = gpu_indices
        if venv is not None:
            submission_data["venv"] = venv

        response = await self.client.post(
            f"{self.api_server_url}/instances", json=submission_data
        )
        response.raise_for_status()
        return response.json()["instance_id"]

    async def get_instance(self, instance_id: str) -> Dict[str, Any]:
        """Get instance details by ID."""
        response = await self.client.get(
            f"{self.api_server_url}/instances/{instance_id}"
        )
        response.raise_for_status()
        return response.json()

    async def get_instance_by_name(self, name: str) -> Dict[str, Any]:
        """Get instance details by name."""
        response = await self.client.get(
            f"{self.api_server_url}/instances/by-name/{name}"
        )
        response.raise_for_status()
        return response.json()

    async def get_instance_result(self, instance_id: str) -> Dict[str, Any]:
        """Get instance result."""
        response = await self.client.get(
            f"{self.api_server_url}/instances/{instance_id}/result"
        )
        if response.status_code == 202:
            return {"status": "PENDING"}
        response.raise_for_status()
        return response.json()

    async def get_instance_endpoint(self, instance_id: str) -> str:
        """Get the endpoint (host:port) of an instance by ID."""
        response = await self.client.get(
            f"{self.api_server_url}/instances/{instance_id}/endpoint"
        )
        response.raise_for_status()
        return response.json()["endpoint"]

    async def get_instance_endpoint_by_name(self, name: str) -> str:
        """Get the endpoint (host:port) of an instance by name."""
        response = await self.client.get(
            f"{self.api_server_url}/instances/by-name/{name}/endpoint"
        )
        response.raise_for_status()
        return response.json()["endpoint"]

    async def cancel_instance(self, instance_id: str) -> Dict[str, Any]:
        """Request cancellation of an instance."""
        response = await self.client.post(
            f"{self.api_server_url}/instances/{instance_id}/cancel"
        )
        response.raise_for_status()
        return response.json()

    async def get_logs(
        self,
        instance_id: str,
        offset: int = 0,
        limit: int = 1048576,
        use_direct: bool = True,
    ) -> Dict[str, Any]:
        """
        Get instance logs.

        Args:
            instance_id: The instance ID
            offset: Global byte offset to start reading from
            limit: Maximum bytes to return
            use_direct: If True, try direct worker access first

        Returns:
            Dict with keys:
            - available_offset: Oldest byte still available
            - total_size: Current total logical size
            - content: Base64-encoded log bytes
            - size: Number of bytes returned
            - data: Decoded log bytes (added by client)
        """
        if use_direct:
            # Get instance info for worker host
            instance = await self.get_instance(instance_id)
            worker_id = instance.get("assigned_to")

            if worker_id:
                # Get worker info for host
                try:
                    workers = await self.list_workers()
                    worker = next(
                        (w for w in workers if w["worker_id"] == worker_id),
                        None
                    )
                    if worker:
                        worker_host = worker["host"]
                        worker_url = (
                            f"http://{worker_host}:{DEFAULT_WORKER_HTTP_PORT}"
                            f"/logs/{instance_id}?offset={offset}&limit={limit}"
                        )
                        try:
                            response = await self.client.get(
                                worker_url, timeout=10.0
                            )
                            response.raise_for_status()
                            result = response.json()
                            # Decode base64 content
                            if result.get("content"):
                                result["data"] = base64.b64decode(result["content"])
                            else:
                                result["data"] = b""
                            return result
                        except (httpx.ConnectError, httpx.TimeoutException):
                            # Fall through to head proxy
                            pass
                except Exception:
                    # Fall through to head proxy
                    pass

        # Use head proxy as fallback
        response = await self.client.get(
            f"{self.api_server_url}/instances/{instance_id}/logs",
            params={"offset": offset, "limit": limit},
        )
        response.raise_for_status()
        result = response.json()
        # Decode base64 content
        if result.get("content"):
            result["data"] = base64.b64decode(result["content"])
        else:
            result["data"] = b""
        return result

    # ========== Worker Methods ==========

    async def list_workers(self) -> List[Dict[str, Any]]:
        """List all registered workers."""
        response = await self.client.get(f"{self.api_server_url}/workers")
        response.raise_for_status()
        return response.json()

    async def get_worker(self, worker_id: str) -> Dict[str, Any]:
        """Get worker details by ID."""
        response = await self.client.get(
            f"{self.api_server_url}/workers/{worker_id}"
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
