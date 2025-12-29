"""
PyLet Sync API - Synchronous API functions.

These are the main entry points for the sync-first PyLet API.
"""

import shlex
from typing import Dict, List, Optional, Union

import httpx

from pylet._instance import Instance
from pylet._state import (
    _get_client,
    _get_head_address,
    _init_state,
    _is_initialized,
    _shutdown_state,
)
from pylet._worker_info import WorkerInfo
from pylet.errors import NotFoundError, NotInitializedError


def init(address: str = "http://localhost:8000") -> None:
    """
    Initialize connection to PyLet head node.

    Must be called before any other client API.

    Args:
        address: Head node URL. Default "http://localhost:8000"

    Raises:
        ConnectionError: Cannot reach head node

    Example:
        pylet.init()
        pylet.init("http://192.168.1.10:8000")
    """
    _init_state(address)

    # Verify connection by hitting a simple endpoint
    try:
        client = _get_client()
        response = client.get(f"{address}/workers")
        response.raise_for_status()
    except httpx.ConnectError as e:
        _shutdown_state()
        raise ConnectionError(f"Cannot reach head node at {address}") from e
    except Exception as e:
        _shutdown_state()
        raise ConnectionError(f"Failed to connect to head node: {e}") from e


def shutdown() -> None:
    """
    Close connection to head node.

    Optional - called automatically via atexit.
    """
    _shutdown_state()


def is_initialized() -> bool:
    """
    Check if init() has been called.

    Returns:
        True if pylet is initialized, False otherwise.
    """
    return _is_initialized()


def submit(
    command: Union[str, List[str]],
    *,
    name: Optional[str] = None,
    gpu: int = 0,
    cpu: int = 1,
    memory: int = 512,
    # SLLM support parameters
    target_worker: Optional[str] = None,
    gpu_indices: Optional[List[int]] = None,
    exclusive: bool = True,
    labels: Optional[Dict[str, str]] = None,
    env: Optional[Dict[str, str]] = None,
    # Venv support
    venv: Optional[str] = None,
) -> Instance:
    """
    Submit a new instance.

    Args:
        command: Shell command string, or list of args (auto shell-escaped)
        name: Optional instance name for service discovery
        gpu: GPU units required (default 0, ignored if gpu_indices specified)
        cpu: CPU cores required (default 1)
        memory: Memory in MB required (default 512)
        target_worker: Place on specific worker node
        gpu_indices: Request specific physical GPU indices
        exclusive: If False, GPUs don't block allocation pool (default True)
        labels: Custom metadata dict
        env: Environment variables to set
        venv: Path to pre-existing virtualenv (must be absolute path)

    Returns:
        Instance handle

    Raises:
        NotInitializedError: init() not called
        ValueError: Invalid command or resources

    Example:
        instance = pylet.submit("echo hello", cpu=1)
        instance = pylet.submit("vllm serve model --port $PORT", name="vllm", gpu=1, memory=4096)
        instance = pylet.submit(["python", "-c", "print('hello')"], cpu=1)

        # SLLM examples
        instance = pylet.submit(
            "sllm-store start",
            target_worker="gpu-0",
            gpu_indices=[0,1,2,3],
            exclusive=False,
            labels={"type": "sllm-store"},
        )

        # Venv example
        instance = pylet.submit(
            "python train.py",
            venv="/home/user/my-venv",
            gpu=1,
        )
    """
    client = _get_client()
    address = _get_head_address()

    # Normalize command
    if isinstance(command, list):
        command = shlex.join(command)

    # Build submission request
    submission = {
        "command": command,
        "resource_requirements": {
            "cpu_cores": cpu,
            "gpu_units": gpu,
            "memory_mb": memory,
        },
        "name": name,
        "exclusive": exclusive,
        "labels": labels or {},
        "env": env or {},
    }
    if target_worker is not None:
        submission["target_worker"] = target_worker
    if gpu_indices is not None:
        submission["gpu_indices"] = gpu_indices
    if venv is not None:
        submission["venv"] = venv

    # Submit instance
    response = client.post(f"{address}/instances", json=submission)
    response.raise_for_status()

    instance_id = response.json()["instance_id"]

    # Fetch full instance data
    response = client.get(f"{address}/instances/{instance_id}")
    response.raise_for_status()

    return Instance(response.json())


def get(
    name: Optional[str] = None,
    *,
    id: Optional[str] = None,
) -> Instance:
    """
    Get an existing instance by name or ID.

    Args:
        name: Instance name (positional or keyword)
        id: Instance ID (keyword only)

    Returns:
        Instance handle

    Raises:
        NotInitializedError: init() not called
        NotFoundError: Instance not found
        ValueError: Neither name nor id provided

    Example:
        instance = pylet.get("my-vllm")
        instance = pylet.get(id="abc-123-def")
    """
    if name is None and id is None:
        raise ValueError("Either 'name' or 'id' must be provided")

    client = _get_client()
    address = _get_head_address()

    try:
        if id is not None:
            response = client.get(f"{address}/instances/{id}")
        else:
            response = client.get(f"{address}/instances/by-name/{name}")

        response.raise_for_status()
        return Instance(response.json())
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            identifier = id if id else f"name='{name}'"
            raise NotFoundError(f"Instance not found: {identifier}") from e
        raise


def instances(
    *,
    status: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None,
) -> List[Instance]:
    """
    List all instances.

    Args:
        status: Filter by status (e.g., "RUNNING", "PENDING")
        labels: Filter by labels (key=value pairs, AND logic)

    Returns:
        List of Instance handles

    Raises:
        NotInitializedError: init() not called

    Example:
        all_instances = pylet.instances()
        running = pylet.instances(status="RUNNING")
        sllm_stores = pylet.instances(labels={"type": "sllm-store"})
    """
    client = _get_client()
    address = _get_head_address()

    params = {}
    if status:
        params["status"] = status
    if labels:
        # Pass first label (API supports one at a time currently)
        for key, value in labels.items():
            params["label"] = f"{key}={value}"
            break  # Currently API supports single label filter

    response = client.get(f"{address}/instances", params=params)
    response.raise_for_status()

    # Post-filter for additional labels if multiple provided
    result = [Instance(data) for data in response.json()]
    if labels and len(labels) > 1:
        result = [
            inst for inst in result
            if all(inst.labels.get(k) == v for k, v in labels.items())
        ]

    return result


def workers() -> List[WorkerInfo]:
    """
    List all registered workers.

    Returns:
        List of WorkerInfo objects

    Raises:
        NotInitializedError: init() not called
    """
    client = _get_client()
    address = _get_head_address()

    response = client.get(f"{address}/workers")
    response.raise_for_status()

    return [WorkerInfo(data) for data in response.json()]
