"""
PyLet Cluster Management - Start head/worker nodes programmatically.

Provides Head, Worker, and Cluster classes for managing PyLet nodes.
"""

import asyncio
import socket
import threading
import time
from typing import List, NoReturn, Optional, Union

import uvicorn


class Head:
    """
    Handle to a running head node.

    Returned by pylet.start() when starting head with block=False.
    """

    def __init__(self, port: int, server: uvicorn.Server, thread: threading.Thread):
        self._port = port
        self._server = server
        self._thread = thread

    def stop(self) -> None:
        """Stop the head node."""
        self._server.should_exit = True
        self._thread.join(timeout=10)

    @property
    def address(self) -> str:
        """Head node URL."""
        return f"http://localhost:{self._port}"


class Worker:
    """
    Handle to a running worker node.

    Returned by pylet.start() when starting worker with block=False.
    """

    def __init__(self, thread: threading.Thread, stop_event: asyncio.Event):
        self._thread = thread
        self._stop_event = stop_event

    def stop(self) -> None:
        """Stop the worker."""
        # Signal the worker to stop
        self._stop_event.set()
        self._thread.join(timeout=10)


class Cluster:
    """
    Handle to a local cluster (head + workers).

    Returned by pylet.local_cluster(). Context manager.
    """

    def __init__(
        self,
        head: Head,
        workers: List[Worker],
    ):
        self._head = head
        self._workers = workers

    @property
    def address(self) -> str:
        """Head node URL."""
        return self._head.address

    def shutdown(self) -> None:
        """Stop all workers and head."""
        # Stop workers first
        for worker in self._workers:
            worker.stop()
        # Then stop head
        self._head.stop()

    def __enter__(self) -> "Cluster":
        """Enter context - cluster already started."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context - shutdown cluster."""
        self.shutdown()
        # Shutdown pylet connection
        from pylet._state import _shutdown_state

        _shutdown_state()


def _start_head_server(port: int) -> tuple:
    """Start head server in background thread."""
    from pylet.server import app

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    def run_server():
        # Run in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(server.serve())

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    # Wait for server to be ready
    _wait_for_port(port, timeout=30)

    return server, thread


def _start_worker_process(
    head_address: str,
    gpu: int,
    cpu: int,
    memory: int,
) -> tuple:
    """Start worker in background thread."""
    from pylet.worker import Worker as WorkerProcess

    stop_event = None
    loop = None

    def run_worker():
        nonlocal stop_event, loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stop_event = asyncio.Event()

        worker = WorkerProcess(
            head_address=head_address,
            cpu_cores=cpu,
            gpu_units=gpu,
            memory_mb=memory,
        )

        async def run_with_stop():
            worker_task = asyncio.create_task(worker.run())
            stop_task = asyncio.create_task(stop_event.wait())

            done, pending = await asyncio.wait(
                [worker_task, stop_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        loop.run_until_complete(run_with_stop())

    thread = threading.Thread(target=run_worker, daemon=True)
    thread.start()

    # Wait for thread to initialize stop_event
    while stop_event is None:
        time.sleep(0.01)

    return thread, stop_event


def _wait_for_port(port: int, timeout: float = 30, host: str = "localhost") -> None:
    """Wait for a port to become available."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                sock.connect((host, port))
                return
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.1)
    raise TimeoutError(f"Port {port} not available after {timeout}s")


def start(
    *,
    address: Optional[str] = None,
    port: int = 8000,
    gpu: int = 0,
    cpu: int = 4,
    memory: int = 4096,
    block: bool = False,
) -> Union[Head, Worker, NoReturn]:
    """
    Start head node or worker.

    - If address is None: start head node
    - If address is provided: start worker and join cluster

    Args:
        address: Head node URL. If None, start as head. If provided, start as worker.
        port: Port for head node (only used when starting head, default 8000)
        gpu: GPU units to offer (only used when starting worker, default 0)
        cpu: CPU cores to offer (only used when starting worker, default 4)
        memory: Memory in MB to offer (only used when starting worker, default 4096)
        block: If True, run in foreground and block forever. If False, run in background.

    Returns:
        Head if starting head with block=False
        Worker if starting worker with block=False
        Does not return if block=True

    Example:
        # Start head in background
        head = pylet.start(port=8000)
        head.stop()

        # Start head in foreground (blocks forever)
        pylet.start(port=8000, block=True)

        # Start worker in background
        worker = pylet.start(address="http://head:8000", gpu=1, cpu=4)
        worker.stop()

        # Start worker in foreground (blocks forever)
        pylet.start(address="http://head:8000", gpu=1, block=True)
    """
    from pylet.logger import configure_file_logging

    configure_file_logging()

    if address is None:
        # Start head node
        if block:
            # Blocking mode - run in foreground
            from pylet.server import app

            uvicorn.run(app, host="0.0.0.0", port=port)
            # Never returns
            raise RuntimeError("Unreachable")
        else:
            # Background mode
            server, thread = _start_head_server(port)
            return Head(port, server, thread)
    else:
        # Start worker
        if block:
            # Blocking mode - run in foreground
            from pylet.worker import Worker as WorkerProcess

            worker = WorkerProcess(
                head_address=address,
                cpu_cores=cpu,
                gpu_units=gpu,
                memory_mb=memory,
            )
            asyncio.run(worker.run())
            # Never returns (worker runs forever until killed)
            raise RuntimeError("Unreachable")
        else:
            # Background mode
            thread, stop_event = _start_worker_process(address, gpu, cpu, memory)
            return Worker(thread, stop_event)


def local_cluster(
    workers: int = 1,
    *,
    gpu_per_worker: int = 0,
    cpu_per_worker: int = 4,
    memory_per_worker: int = 4096,
    port: int = 8000,
) -> Cluster:
    """
    Start a local cluster (head + workers) for testing.

    Args:
        workers: Number of workers to start (default 1)
        gpu_per_worker: GPU units per worker (default 0)
        cpu_per_worker: CPU cores per worker (default 4)
        memory_per_worker: Memory in MB per worker (default 4096)
        port: Head node port (default 8000)

    Returns:
        Cluster context manager

    Example:
        with pylet.local_cluster(workers=2, gpu_per_worker=1) as cluster:
            # pylet is auto-initialized to this cluster
            instance = pylet.submit("nvidia-smi", gpu=1)
            instance.wait()
    """
    # Start head
    head = start(port=port)

    # Wait a bit for head to be fully ready
    time.sleep(0.5)

    # Start workers
    worker_handles = []
    head_address = head.address
    for _ in range(workers):
        worker = start(
            address=head_address,
            gpu=gpu_per_worker,
            cpu=cpu_per_worker,
            memory=memory_per_worker,
        )
        worker_handles.append(worker)
        # Small delay between worker starts
        time.sleep(0.2)

    # Wait for workers to register
    time.sleep(1.0)

    # Auto-initialize pylet to this cluster
    from pylet._state import _init_state

    _init_state(head_address)

    return Cluster(head, worker_handles)
