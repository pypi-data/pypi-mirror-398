"""
PyLet - Distributed instance execution system.

PyLet orchestrates distributed GPU servers, enabling you to submit commands
that run across a cluster of worker nodes. Instances expose IP:port for
communication via HTTP.

Basic Usage:
    import pylet

    pylet.init()  # Connect to head at localhost:8000

    instance = pylet.submit("echo hello", cpu=1)
    instance.wait()

    print(f"Exit code: {instance.exit_code}")

For async usage, import pylet.aio:
    import pylet.aio as pylet

    async def main():
        await pylet.init()
        instance = await pylet.submit("echo hello", cpu=1)
        await instance.wait()
"""

# Core API functions
from pylet._sync_api import (
    get,
    init,
    instances,
    is_initialized,
    shutdown,
    submit,
    workers,
)

# Cluster management
from pylet._cluster import (
    Cluster,
    Head,
    Worker,
    local_cluster,
    start,
)

# Data classes
from pylet._instance import Instance
from pylet._worker_info import WorkerInfo

# Exceptions
from pylet.errors import (
    InstanceFailedError,
    InstanceTerminatedError,
    NotFoundError,
    NotInitializedError,
    PyletError,
    TimeoutError,
)

__all__ = [
    # API functions
    "init",
    "shutdown",
    "is_initialized",
    "submit",
    "get",
    "instances",
    "workers",
    # Cluster management
    "start",
    "local_cluster",
    # Classes
    "Instance",
    "WorkerInfo",
    "Head",
    "Worker",
    "Cluster",
    # Exceptions
    "PyletError",
    "NotInitializedError",
    "NotFoundError",
    "TimeoutError",
    "InstanceFailedError",
    "InstanceTerminatedError",
]

__version__ = "0.3.0"
