"""
PyLet Configuration - Configurable constants with environment variable overrides.

All values can be overridden via environment variables with PYLET_ prefix.
"""

import os
from pathlib import Path


def _get_int(key: str, default: int) -> int:
    """Get integer from environment variable."""
    val = os.environ.get(f"PYLET_{key}")
    if val is not None:
        try:
            return int(val)
        except ValueError:
            pass
    return default


def _get_float(key: str, default: float) -> float:
    """Get float from environment variable."""
    val = os.environ.get(f"PYLET_{key}")
    if val is not None:
        try:
            return float(val)
        except ValueError:
            pass
    return default


def _get_path(key: str, default: Path) -> Path:
    """Get path from environment variable."""
    val = os.environ.get(f"PYLET_{key}")
    if val is not None:
        return Path(val)
    return default


# ========== Worker Configuration ==========

# Port range for instance processes (exposed via PORT env var)
WORKER_PORT_MIN = _get_int("WORKER_PORT_MIN", 15600)
WORKER_PORT_MAX = _get_int("WORKER_PORT_MAX", 15700)


# ========== Controller Configuration ==========

# Worker liveness thresholds (seconds)
SUSPECT_THRESHOLD_SECONDS = _get_int("SUSPECT_THRESHOLD_SECONDS", 30)
OFFLINE_THRESHOLD_SECONDS = _get_int("OFFLINE_THRESHOLD_SECONDS", 90)

# Background loop intervals (seconds)
LIVENESS_CHECK_INTERVAL = _get_int("LIVENESS_CHECK_INTERVAL", 5)
SCHEDULER_INTERVAL = _get_int("SCHEDULER_INTERVAL", 2)

# Heartbeat long-poll timeout (seconds)
HEARTBEAT_POLL_TIMEOUT = _get_float("HEARTBEAT_POLL_TIMEOUT", 30.0)


# ========== Instance Graceful Shutdown ==========

# Default grace period for instance cancellation (seconds)
# Time between SIGTERM and SIGKILL
DEFAULT_GRACE_PERIOD_SECONDS = _get_int("DEFAULT_GRACE_PERIOD_SECONDS", 30)

# Maximum allowed grace period (seconds)
MAX_GRACE_PERIOD_SECONDS = _get_int("MAX_GRACE_PERIOD_SECONDS", 300)


# ========== Log Capture ==========

# Directory for instance logs (relative to DATA_DIR)
# Logs stored as {instance_id}.{index}
LOG_CHUNK_SIZE = _get_int("LOG_CHUNK_SIZE", 10 * 1024 * 1024)  # 10MB per file
LOG_MAX_FILES = _get_int("LOG_MAX_FILES", 5)  # Keep 5 files max

# Worker HTTP server for log retrieval
WORKER_HTTP_PORT = _get_int("WORKER_HTTP_PORT", 15599)

# Max bytes to return per log request
LOG_MAX_RESPONSE_SIZE = _get_int("LOG_MAX_RESPONSE_SIZE", 10 * 1024 * 1024)  # 10MB


# ========== Paths ==========

DATA_DIR = _get_path("DATA_DIR", Path.home() / ".pylet")
DB_PATH = DATA_DIR / "pylet.db"
RUN_DIR = DATA_DIR / "run"
LOG_DIR = DATA_DIR / "logs"
