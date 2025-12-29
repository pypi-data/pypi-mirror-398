"""
PyLet Server - FastAPI REST API for the controller.

Provides /instances endpoints for instance management and /workers for worker management.
Implements unified heartbeat protocol with long-poll.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from pylet import config
from pylet.controller import Controller
from pylet.logger import logger
from pylet.schemas import (
    HeartbeatRequest,
    InstanceStatus,
    ResourceSpec,
    WorkerRegistrationResponse,
    get_display_status,
)


# Request/Response models for API
class EndpointReport(BaseModel):
    host: str
    port: int


class InstanceSubmissionRequest(BaseModel):
    """Request to submit a new instance."""
    command: str
    resource_requirements: ResourceSpec
    name: Optional[str] = None
    # SLLM support fields
    target_worker: Optional[str] = None
    gpu_indices: Optional[List[int]] = None
    exclusive: bool = True
    labels: Dict[str, str] = Field(default_factory=dict)
    env: Dict[str, str] = Field(default_factory=dict)
    # Venv support
    venv: Optional[str] = None  # Path to pre-existing virtualenv (must be absolute path)


class WorkerRegistrationRequest(BaseModel):
    worker_id: str
    host: str
    resources: ResourceSpec
    boot_id: Optional[str] = None


controller = Controller()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting pylet server.")
    await controller.startup()

    # Start background tasks
    liveness_task = asyncio.create_task(controller.liveness_loop())
    scheduler_task = asyncio.create_task(controller.scheduler_loop())

    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down pylet server.")
        liveness_task.cancel()
        scheduler_task.cancel()
        try:
            await liveness_task
            await scheduler_task
        except asyncio.CancelledError:
            pass
        await controller.shutdown()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    logger.error(f"Validation error for request {request.url}: {exc}")
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


# ========== Instance Endpoints ==========


import json


def _parse_json_field(value: Optional[str], default=None):
    """Parse JSON field from database."""
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


async def _get_gpu_indices_for_instance(instance: Dict) -> Optional[List[int]]:
    """Get allocated GPU indices for an instance."""
    if not instance.get("assigned_worker"):
        return None

    allocations = await controller.db.get_gpu_indices_for_instance(
        instance["id"], instance.get("attempt", 0)
    )
    return allocations if allocations else None


async def _build_instance_response(inst: Dict) -> Dict:
    """Build a full instance response with all fields."""
    display_status = get_display_status(
        InstanceStatus(inst["status"]),
        inst.get("cancel_requested_at")
    )

    # Get allocated GPU indices from allocations table
    gpu_indices = await _get_gpu_indices_for_instance(inst)

    return {
        "instance_id": inst["id"],
        "name": inst["name"],
        "command": inst["command"],
        "status": inst["status"],
        "display_status": display_status,
        "attempt": inst["attempt"],
        "assigned_to": inst["assigned_worker"],
        "endpoint": inst["endpoint"],
        "port": inst["port"],
        "exit_code": inst["exit_code"],
        "failure_reason": inst["failure_reason"],
        "created_at": inst["created_at"],
        "assigned_at": inst["assigned_at"],
        "started_at": inst["started_at"],
        "ended_at": inst["ended_at"],
        "cancellation_requested_at": inst.get("cancel_requested_at"),
        # SLLM fields
        "gpu_indices": gpu_indices,
        "exclusive": bool(inst.get("exclusive", True)),
        "labels": _parse_json_field(inst.get("labels"), {}),
        "env": _parse_json_field(inst.get("env"), {}),
        "target_worker": inst.get("target_worker"),
        # Venv support
        "venv": inst.get("venv"),
    }


@app.get("/instances")
async def list_instances(
    status: Optional[str] = None,
    label: Optional[str] = None,
):
    """
    List all instances, optionally filtered by status and labels.

    Query params:
    - status: Filter by status (e.g., "RUNNING", "PENDING")
    - label: Filter by label (key=value format, can specify multiple)
    """
    # Parse label filters from query param
    label_filters = None
    if label:
        label_filters = {}
        for lbl in [label]:  # Future: support multiple
            if "=" in lbl:
                key, value = lbl.split("=", 1)
                label_filters[key] = value

    instances = await controller.get_all_instances(status, label_filters)
    return [await _build_instance_response(inst) for inst in instances]


async def _validate_submission(request: InstanceSubmissionRequest) -> None:
    """Validate submission request."""
    # 1. Validate target_worker if specified
    if request.target_worker:
        worker = await controller.get_worker(request.target_worker)
        if not worker:
            raise ValueError(f"Worker '{request.target_worker}' not found")
        if worker["status"] != "ONLINE":
            raise ValueError(f"Worker '{request.target_worker}' is not ONLINE")

    # 2. Validate gpu_indices if specified
    if request.gpu_indices is not None:
        if not request.target_worker:
            raise ValueError("target_worker is required when specifying gpu_indices")

        if len(request.gpu_indices) != len(set(request.gpu_indices)):
            raise ValueError("gpu_indices must be unique")

        if any(idx < 0 for idx in request.gpu_indices):
            raise ValueError("gpu_indices must be non-negative")

        worker = await controller.get_worker(request.target_worker)
        worker_gpu_count = worker["gpu_units"] or 0
        if any(idx >= worker_gpu_count for idx in request.gpu_indices):
            raise ValueError(
                f"gpu_indices must be < {worker_gpu_count} for worker {request.target_worker}"
            )

    # 3. Validate labels
    for key, value in request.labels.items():
        if len(key) > 63:
            raise ValueError(f"Label key '{key}' exceeds 63 characters")
        if len(value) > 255:
            raise ValueError(f"Label value for '{key}' exceeds 255 characters")

    # 4. Warn about Pylet-managed env vars
    PYLET_MANAGED_VARS = {"PORT", "CUDA_VISIBLE_DEVICES"}
    conflicts = set(request.env.keys()) & PYLET_MANAGED_VARS
    if conflicts:
        logger.warning(f"User env vars {conflicts} will be overridden by Pylet")

    # 5. Validate venv path if specified
    if request.venv is not None:
        if not request.venv.startswith("/"):
            raise ValueError("venv must be an absolute path")
        if ".." in request.venv:
            raise ValueError("venv path cannot contain '..'")
        # Note: We don't check if the path exists - that happens at runtime on the worker


@app.post("/instances")
async def submit_instance(request: InstanceSubmissionRequest):
    """Submit a new instance for execution."""
    try:
        # Validate the submission
        await _validate_submission(request)

        instance_id = await controller.submit_instance(
            command=request.command,
            resource_requirements=request.resource_requirements,
            name=request.name,
            target_worker=request.target_worker,
            gpu_indices=request.gpu_indices,
            exclusive=request.exclusive,
            labels=request.labels,
            env=request.env,
            venv=request.venv,
        )
        logger.info(
            f"Client submitted instance {instance_id} ('{request.name}') "
            f"target_worker={request.target_worker}, "
            f"gpu_indices={request.gpu_indices}, "
            f"exclusive={request.exclusive}"
        )
        return {"instance_id": instance_id}
    except ValueError as e:
        logger.error(f"Error submitting instance: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/instances/{instance_id}")
async def get_instance_details(instance_id: str):
    """Get instance details by ID."""
    instance = await controller.get_instance(instance_id)
    if not instance:
        logger.warning(f"Client requested non-existent instance {instance_id}.")
        raise HTTPException(status_code=404, detail="Instance not found")

    return await _build_instance_response(instance)


@app.get("/instances/by-name/{instance_name}")
async def get_instance_by_name(instance_name: str):
    """Get instance details by name."""
    instance = await controller.get_instance_by_name(instance_name)
    if not instance:
        logger.warning(
            f"Client requested non-existent instance with name '{instance_name}'."
        )
        raise HTTPException(status_code=404, detail="Instance not found")

    return await _build_instance_response(instance)


@app.get("/instances/by-name/{instance_name}/endpoint")
async def get_instance_endpoint_by_name(instance_name: str):
    """Get the endpoint (host:port) of an instance by name."""
    instance = await controller.get_instance_by_name(instance_name)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    if not instance["endpoint"]:
        raise HTTPException(status_code=404, detail="Instance endpoint not available yet")
    return {"endpoint": instance["endpoint"]}


@app.get("/instances/{instance_id}/endpoint")
async def get_instance_endpoint(instance_id: str):
    """Get the endpoint (host:port) of an instance."""
    instance = await controller.get_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    if not instance["endpoint"]:
        raise HTTPException(status_code=404, detail="Instance endpoint not available yet")
    return {"endpoint": instance["endpoint"]}


@app.get("/instances/{instance_id}/result")
async def get_instance_result(instance_id: str):
    """Get the result of an instance."""
    instance = await controller.get_instance(instance_id)
    if not instance:
        logger.warning(f"Client requested non-existent instance {instance_id}.")
        raise HTTPException(status_code=404, detail="Instance not found")

    if instance["status"] == "COMPLETED":
        logger.info(f"Client retrieved result for instance {instance_id}.")
        return {"result": {"exit_code": instance["exit_code"]}}
    elif instance["status"] == "FAILED":
        logger.info(f"Client retrieved failure for instance {instance_id}.")
        return {
            "error": {
                "exit_code": instance["exit_code"],
                "failure_reason": instance["failure_reason"],
            }
        }
    elif instance["status"] == "CANCELLED":
        return {"cancelled": True}
    else:
        logger.debug(f"Client requested incomplete instance {instance_id}.")
        raise HTTPException(status_code=202, detail="Instance not yet completed")


@app.post("/instances/{instance_id}/cancel")
async def cancel_instance(instance_id: str):
    """
    Request cancellation of an instance.

    Idempotent - multiple requests return success without error.
    Sets cancellation_requested_at timestamp if not already set.
    """
    instance = await controller.get_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    if instance["status"] in ("COMPLETED", "FAILED", "CANCELLED"):
        raise HTTPException(
            status_code=400,
            detail=f"Instance already in terminal state: {instance['status']}",
        )

    # Check if already requested (idempotent)
    if instance.get("cancel_requested_at") is not None:
        return {"status": "already_cancelling", "instance_id": instance_id}

    success = await controller.request_cancellation(instance_id)
    if success:
        return {"status": "cancelling", "instance_id": instance_id}
    else:
        raise HTTPException(status_code=400, detail="Failed to cancel instance")


@app.get("/instances/{instance_id}/logs")
async def get_instance_logs(
    instance_id: str,
    offset: int = 0,
    limit: int = 1048576,  # 1MB default
):
    """
    Get instance logs via head proxy.

    Proxies the request to the worker's HTTP server.
    Use this when direct worker access is not available.

    Query params:
    - offset: Global byte offset to start reading from
    - limit: Maximum bytes to return
    """
    instance = await controller.get_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    # Get worker info
    worker_id = instance.get("assigned_worker")
    if not worker_id:
        raise HTTPException(
            status_code=404,
            detail="Instance not assigned to any worker"
        )

    worker = await controller.get_worker(worker_id)
    if not worker:
        raise HTTPException(status_code=503, detail="Worker not found")

    if worker["status"] == "OFFLINE":
        raise HTTPException(status_code=503, detail="Worker is offline")

    # Proxy to worker HTTP server
    worker_host = worker["ip"]
    worker_port = config.WORKER_HTTP_PORT

    worker_url = (
        f"http://{worker_host}:{worker_port}"
        f"/logs/{instance_id}?offset={offset}&limit={limit}"
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(worker_url)
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Cannot connect to worker")
    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="Worker request timeout")
    except Exception as e:
        logger.error(f"Error proxying log request: {e}")
        raise HTTPException(status_code=503, detail="Worker request failed")


# ========== Worker Endpoints ==========


@app.post("/workers")
async def register_worker(request: WorkerRegistrationRequest):
    """Register a worker node."""
    try:
        token = await controller.register_worker(
            worker_id=request.worker_id,
            host=request.host,
            resources=request.resources,
            boot_id=request.boot_id,
        )
        logger.info(
            f"Worker {request.worker_id} ({request.host}) registered via API."
        )
        return WorkerRegistrationResponse(worker_token=token)
    except ValueError as e:
        logger.warning(f"Worker registration failed for {request.worker_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


async def _build_worker_response(w: Dict) -> Dict:
    """Build worker response with available_gpu_indices."""
    total_gpus = w["gpu_units"] or 0
    used_gpus = await controller.db.get_used_gpus_for_worker(
        w["id"], exclusive_only=True
    )
    all_gpus = set(range(total_gpus))
    available_gpu_indices = sorted(all_gpus - set(used_gpus))

    return {
        "worker_id": w["id"],
        "host": w["ip"],
        "status": w["status"],
        "total_resources": {
            "cpu_cores": w["cpu_cores"],
            "gpu_units": w["gpu_units"],
            "memory_mb": w["memory_mb"],
        },
        "available_resources": {
            "cpu_cores": w["available_cpu"],
            "gpu_units": w["available_gpu"],
            "memory_mb": w["available_memory"],
        },
        "available_gpu_indices": available_gpu_indices,
        "last_seen": w["last_heartbeat_at"],
    }


@app.get("/workers")
async def get_workers():
    """List all registered workers."""
    workers = await controller.get_all_workers()
    return [await _build_worker_response(w) for w in workers]


@app.get("/workers/{worker_id}")
async def get_worker(worker_id: str):
    """Get worker details."""
    worker = await controller.get_worker(worker_id)
    if not worker:
        logger.warning(f"Requested non-existent worker {worker_id}.")
        raise HTTPException(status_code=404, detail="Worker not found")
    return await _build_worker_response(worker)


@app.post("/workers/{worker_id}/heartbeat")
async def worker_heartbeat(worker_id: str, request: Optional[HeartbeatRequest] = None):
    """
    Worker heartbeat endpoint.

    Accepts HeartbeatRequest with token, boot_id, instance reports.
    Returns HeartbeatResponse with generation and desired state.
    """
    try:
        if request and request.worker_token:
            response = await controller.process_heartbeat(worker_id, request)
            return response
        else:
            raise HTTPException(
                status_code=400, detail="HeartbeatRequest with worker_token is required"
            )
    except ValueError as e:
        logger.warning(f"Heartbeat error for worker {worker_id}: {e}")
        raise HTTPException(
            status_code=401 if "token" in str(e).lower() else 404, detail=str(e)
        )
