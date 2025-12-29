"""
PyLet Schemas - Pydantic models for instances, workers, and requests.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class ResourceSpec(BaseModel):
    cpu_cores: int
    gpu_units: int
    memory_mb: int


# Instance (formerly Task) Status
class InstanceStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    UNKNOWN = "UNKNOWN"       # Worker OFFLINE; outcome unknown
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# Worker Status
class WorkerStatus(str, Enum):
    ONLINE = "ONLINE"
    SUSPECT = "SUSPECT"
    OFFLINE = "OFFLINE"


# Valid state transitions
# Note: CANCELLING was removed - cancellation is now tracked via
# cancellation_requested_at timestamp, not a separate status
VALID_TRANSITIONS: Dict[InstanceStatus, Set[InstanceStatus]] = {
    InstanceStatus.PENDING: {InstanceStatus.ASSIGNED, InstanceStatus.CANCELLED},
    InstanceStatus.ASSIGNED: {
        InstanceStatus.RUNNING,
        InstanceStatus.UNKNOWN,
        InstanceStatus.FAILED,
        InstanceStatus.CANCELLED,
    },
    InstanceStatus.RUNNING: {
        InstanceStatus.COMPLETED,
        InstanceStatus.FAILED,
        InstanceStatus.UNKNOWN,
        InstanceStatus.CANCELLED,
    },
    InstanceStatus.UNKNOWN: {
        InstanceStatus.RUNNING,
        InstanceStatus.COMPLETED,
        InstanceStatus.FAILED,
        InstanceStatus.CANCELLED,
    },
    InstanceStatus.COMPLETED: set(),  # Terminal
    InstanceStatus.FAILED: set(),     # Terminal
    InstanceStatus.CANCELLED: set(),  # Terminal
}


def validate_transition(current: InstanceStatus, new: InstanceStatus) -> bool:
    """Check if a state transition is valid."""
    return new in VALID_TRANSITIONS.get(current, set())


def is_terminal(status: InstanceStatus) -> bool:
    """Check if a status is terminal (no further transitions)."""
    return status in {InstanceStatus.COMPLETED, InstanceStatus.FAILED, InstanceStatus.CANCELLED}


def is_active(status: InstanceStatus) -> bool:
    """Check if a status represents an active (non-terminal, non-pending) instance."""
    return status in {
        InstanceStatus.ASSIGNED,
        InstanceStatus.RUNNING,
        InstanceStatus.UNKNOWN,
    }


class Instance(BaseModel):
    """An instance (formerly 'task') represents a unit of work to execute."""
    instance_id: str
    name: Optional[str] = None
    command: str  # Renamed from task_data
    resource_requirements: ResourceSpec
    status: InstanceStatus = InstanceStatus.PENDING
    attempt: int = 0
    assigned_to: Optional[str] = None
    port: Optional[int] = None
    endpoint: Optional[str] = None  # "host:port" when instance is running
    exit_code: Optional[int] = None
    stdout_log: Optional[str] = None
    stderr_log: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    # Cancellation intent (like K8s deletionTimestamp)
    cancellation_requested_at: Optional[datetime] = None
    # SLLM support fields
    target_worker: Optional[str] = None
    gpu_indices: Optional[List[int]] = None   # Allocated GPUs (from allocations)
    exclusive: bool = True
    labels: Dict[str, str] = Field(default_factory=dict)
    env: Dict[str, str] = Field(default_factory=dict)
    # Venv support
    venv: Optional[str] = None  # Path to pre-existing virtualenv (must be absolute path)


def get_display_status(status: InstanceStatus, cancellation_requested_at: Optional[datetime]) -> str:
    """
    Derive display status for user visibility.

    Returns "CANCELLING" when cancellation is requested but instance is not yet terminal.
    This mirrors K8s "Terminating" display behavior.
    """
    if cancellation_requested_at and not is_terminal(status):
        return "CANCELLING"
    return status.value


class Worker(BaseModel):
    """A worker node that executes instances."""
    worker_id: str
    host: str  # Worker's IP address
    status: WorkerStatus = WorkerStatus.ONLINE
    worker_token: Optional[str] = None  # Controller-issued secret
    last_boot_id: Optional[str] = None  # Worker-reported UUID
    total_resources: ResourceSpec
    available_resources: ResourceSpec
    last_seen: datetime = Field(default_factory=datetime.now)


# Request/Response schemas for API
class InstanceSubmissionRequest(BaseModel):
    """Request to submit a new instance."""
    command: str  # Renamed from task_data - the command to execute
    resource_requirements: ResourceSpec
    name: Optional[str] = None
    # SLLM support fields
    target_worker: Optional[str] = None       # Place on specific worker
    gpu_indices: Optional[List[int]] = None   # Request specific GPUs
    exclusive: bool = True                    # GPU exclusivity mode
    labels: Dict[str, str] = Field(default_factory=dict)  # Custom metadata
    env: Dict[str, str] = Field(default_factory=dict)     # Environment variables
    # Venv support
    venv: Optional[str] = None  # Path to pre-existing virtualenv (must be absolute path)


class WorkerRegistrationRequest(BaseModel):
    """Request to register a worker."""
    worker_id: str
    host: str
    resources: ResourceSpec
    boot_id: Optional[str] = None


class WorkerRegistrationResponse(BaseModel):
    """Response after worker registration."""
    worker_token: str
    message: str = "Worker registered successfully"


# Heartbeat schemas (Phase 3)
class InstanceReport(BaseModel):
    """Worker report about a local instance."""
    instance_id: str
    attempt: int
    status: str  # "RUNNING", "COMPLETED", "FAILED", "NOT_FOUND", "CANCELLED"
    port: Optional[int] = None
    exit_code: Optional[int] = None


class HeartbeatRequest(BaseModel):
    """Heartbeat request from worker to controller."""
    worker_token: str
    boot_id: str
    last_seen_gen: int = 0
    instances: List[InstanceReport] = []


class DesiredInstance(BaseModel):
    """Instance that should be running on a worker."""
    instance_id: str
    attempt: int
    command: str
    gpu_indices: List[int] = []
    env: Dict[str, str] = {}
    venv: Optional[str] = None  # Path to pre-existing virtualenv
    expected_status: str = "ASSIGNED"  # ASSIGNED means "please start"


class HeartbeatResponse(BaseModel):
    """Heartbeat response from controller to worker."""
    gen: int
    desired_instances: List[DesiredInstance]


