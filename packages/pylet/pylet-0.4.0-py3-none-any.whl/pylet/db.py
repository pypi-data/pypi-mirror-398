"""
PyLet Database Layer - SQLite persistence with WAL mode.
"""

import asyncio
import contextlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite

DEFAULT_DB_PATH = Path.home() / ".pylet" / "pylet.db"


class Database:
    """Async SQLite database wrapper with WAL mode."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[aiosqlite.Connection] = None
        self._tx_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Open database connection and initialize schema."""
        self._conn = await aiosqlite.connect(str(self.db_path))
        self._conn.row_factory = aiosqlite.Row

        # Enable WAL mode and foreign keys
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._conn.execute("PRAGMA busy_timeout=5000")

        await self._create_tables()
        await self._conn.commit()

    async def close(self) -> None:
        """Close database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        await self._conn.executescript("""
            -- Workers table
            CREATE TABLE IF NOT EXISTS workers (
                id TEXT PRIMARY KEY,
                ip TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ONLINE',
                last_heartbeat_at TEXT,
                worker_token TEXT,
                last_boot_id TEXT,
                cpu_cores INTEGER,
                gpu_units INTEGER,
                memory_mb INTEGER,
                available_cpu REAL,
                available_gpu INTEGER,
                available_memory INTEGER
            );

            -- Worker GPU inventory (populated on registration)
            CREATE TABLE IF NOT EXISTS worker_gpu_inventory (
                worker_id TEXT REFERENCES workers(id) ON DELETE CASCADE,
                gpu_index INTEGER,
                PRIMARY KEY (worker_id, gpu_index)
            );

            -- Instances table (renamed from tasks)
            CREATE TABLE IF NOT EXISTS instances (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE,
                command TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                attempt INTEGER NOT NULL DEFAULT 0,
                assigned_worker TEXT REFERENCES workers(id),
                -- Resources
                cpu_cores REAL,
                gpu_units INTEGER,
                memory_mb INTEGER,
                -- SLLM support fields
                exclusive BOOLEAN DEFAULT TRUE,
                labels TEXT,                  -- JSON object
                env TEXT,                     -- JSON object
                target_worker TEXT,           -- Placement constraint
                requested_gpu_indices TEXT,   -- JSON array
                -- Venv support
                venv TEXT,                    -- Absolute path to virtualenv
                -- Execution
                exit_code INTEGER,
                stdout_log TEXT,
                stderr_log TEXT,
                port INTEGER,
                endpoint TEXT,
                failure_reason TEXT,
                -- Timestamps
                created_at TEXT DEFAULT (datetime('now')),
                assigned_at TEXT,
                started_at TEXT,
                ended_at TEXT,
                last_report_at TEXT,
                cancel_requested_at TEXT
            );

            -- Instance allocations (attempt-scoped GPU tracking)
            CREATE TABLE IF NOT EXISTS instance_allocations (
                instance_id TEXT REFERENCES instances(id) ON DELETE CASCADE,
                attempt INTEGER,
                worker_id TEXT REFERENCES workers(id),
                gpu_index INTEGER,
                exclusive BOOLEAN DEFAULT TRUE,
                PRIMARY KEY (instance_id, attempt, gpu_index)
            );

            -- Indexes for common queries
            CREATE INDEX IF NOT EXISTS idx_instances_status ON instances(status);
            CREATE INDEX IF NOT EXISTS idx_instances_assigned_worker ON instances(assigned_worker);
            CREATE INDEX IF NOT EXISTS idx_allocations_worker ON instance_allocations(worker_id);
            CREATE INDEX IF NOT EXISTS idx_instances_labels ON instances(labels);
        """)

    # Transaction context manager
    class Transaction:
        def __init__(self, db: "Database"):
            self.db = db

        async def __aenter__(self):
            await self.db._tx_lock.acquire()
            try:
                await self.db._conn.execute("BEGIN")
            except Exception:
                self.db._tx_lock.release()
                raise
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            try:
                if exc_type is None:
                    await self.db._conn.commit()
                else:
                    await self.db._conn.rollback()
            except Exception:
                # Best-effort rollback to reset transaction state
                with contextlib.suppress(Exception):
                    await self.db._conn.rollback()
                raise
            finally:
                self.db._tx_lock.release()
            return False

    def transaction(self) -> "Database.Transaction":
        """Start a database transaction."""
        return self.Transaction(self)

    # Read helpers (no commit needed)
    async def fetch_one(self, sql: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch a single row as a dict."""
        cursor = await self._conn.execute(sql, params)
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def fetch_all(self, sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows as a list of dicts."""
        cursor = await self._conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # Worker methods
    async def insert_worker(
        self,
        worker_id: str,
        ip: str,
        cpu_cores: int,
        gpu_units: int,
        memory_mb: int,
        worker_token: str,
    ) -> None:
        """Insert a new worker and populate GPU inventory."""
        async with self.transaction():
            await self._conn.execute(
                """
                INSERT INTO workers (id, ip, status, last_heartbeat_at, worker_token,
                                     cpu_cores, gpu_units, memory_mb,
                                     available_cpu, available_gpu, available_memory)
                VALUES (?, ?, 'ONLINE', datetime('now'), ?, ?, ?, ?, ?, ?, ?)
                """,
                (worker_id, ip, worker_token, cpu_cores, gpu_units, memory_mb,
                 cpu_cores, gpu_units, memory_mb),
            )
            # Populate GPU inventory
            for gpu_idx in range(gpu_units):
                await self._conn.execute(
                    "INSERT INTO worker_gpu_inventory (worker_id, gpu_index) VALUES (?, ?)",
                    (worker_id, gpu_idx),
                )

    async def update_worker_on_reconnect(
        self,
        worker_id: str,
        ip: str,
        cpu_cores: int,
        gpu_units: int,
        memory_mb: int,
        worker_token: str,
    ) -> None:
        """Update worker on reconnect (new token, reset status)."""
        async with self.transaction():
            await self._conn.execute(
                """
                UPDATE workers
                SET ip = ?, status = 'ONLINE', last_heartbeat_at = datetime('now'),
                    worker_token = ?, cpu_cores = ?, gpu_units = ?, memory_mb = ?,
                    available_cpu = ?, available_gpu = ?, available_memory = ?
                WHERE id = ?
                """,
                (ip, worker_token, cpu_cores, gpu_units, memory_mb,
                 cpu_cores, gpu_units, memory_mb, worker_id),
            )
            # Repopulate GPU inventory
            await self._conn.execute(
                "DELETE FROM worker_gpu_inventory WHERE worker_id = ?",
                (worker_id,),
            )
            for gpu_idx in range(gpu_units):
                await self._conn.execute(
                    "INSERT INTO worker_gpu_inventory (worker_id, gpu_index) VALUES (?, ?)",
                    (worker_id, gpu_idx),
                )

    async def get_worker(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Get worker by ID."""
        return await self.fetch_one("SELECT * FROM workers WHERE id = ?", (worker_id,))

    async def get_all_workers(self) -> List[Dict[str, Any]]:
        """Get all workers."""
        return await self.fetch_all("SELECT * FROM workers")

    async def get_online_workers(self) -> List[Dict[str, Any]]:
        """Get all ONLINE workers."""
        return await self.fetch_all("SELECT * FROM workers WHERE status = 'ONLINE'")

    async def update_worker_heartbeat(
        self, worker_id: str, boot_id: Optional[str] = None
    ) -> None:
        """Update worker heartbeat timestamp."""
        async with self.transaction():
            if boot_id:
                await self._conn.execute(
                    """
                    UPDATE workers
                    SET status = 'ONLINE', last_heartbeat_at = datetime('now'), last_boot_id = ?
                    WHERE id = ?
                    """,
                    (boot_id, worker_id),
                )
            else:
                await self._conn.execute(
                    """
                    UPDATE workers
                    SET status = 'ONLINE', last_heartbeat_at = datetime('now')
                    WHERE id = ?
                    """,
                    (worker_id,),
                )

    async def update_worker_status(self, worker_id: str, status: str) -> None:
        """Update worker status."""
        async with self.transaction():
            await self._conn.execute(
                "UPDATE workers SET status = ? WHERE id = ?",
                (status, worker_id),
            )

    async def mark_all_workers_suspect(self) -> None:
        """Mark all workers as SUSPECT (used on controller startup)."""
        async with self.transaction():
            await self._conn.execute("UPDATE workers SET status = 'SUSPECT'")

    async def mark_stale_workers_suspect(self, threshold_seconds: float) -> None:
        """Mark ONLINE workers as SUSPECT if heartbeat exceeds threshold."""
        async with self.transaction():
            await self._conn.execute(
                """
                UPDATE workers
                SET status = 'SUSPECT'
                WHERE status = 'ONLINE'
                AND (julianday('now') - julianday(last_heartbeat_at)) * 86400 > ?
                """,
                (threshold_seconds,),
            )

    async def get_workers_exceeding_threshold(
        self, threshold_seconds: float
    ) -> List[Dict[str, Any]]:
        """Get workers with heartbeat exceeding threshold (for OFFLINE transition)."""
        return await self.fetch_all(
            """
            SELECT id FROM workers
            WHERE status IN ('ONLINE', 'SUSPECT')
            AND (julianday('now') - julianday(last_heartbeat_at)) * 86400 > ?
            """,
            (threshold_seconds,),
        )

    # Instance methods
    async def insert_instance(
        self,
        instance_id: str,
        name: Optional[str],
        command: str,
        cpu_cores: float,
        gpu_units: int,
        memory_mb: int,
        # SLLM support parameters
        exclusive: bool = True,
        labels: Optional[Dict[str, str]] = None,
        env: Optional[Dict[str, str]] = None,
        target_worker: Optional[str] = None,
        gpu_indices: Optional[List[int]] = None,
        # Venv support
        venv: Optional[str] = None,
    ) -> None:
        """Insert a new instance."""
        async with self.transaction():
            await self._conn.execute(
                """
                INSERT INTO instances (
                    id, name, command, status, cpu_cores, gpu_units, memory_mb,
                    exclusive, labels, env, target_worker, requested_gpu_indices, venv
                )
                VALUES (?, ?, ?, 'PENDING', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    instance_id, name, command, cpu_cores, gpu_units, memory_mb,
                    exclusive,
                    json.dumps(labels) if labels else None,
                    json.dumps(env) if env else None,
                    target_worker,
                    json.dumps(gpu_indices) if gpu_indices else None,
                    venv,
                ),
            )

    async def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get instance by ID."""
        return await self.fetch_one("SELECT * FROM instances WHERE id = ?", (instance_id,))

    async def get_instance_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get instance by name."""
        return await self.fetch_one("SELECT * FROM instances WHERE name = ?", (name,))

    async def get_all_instances(
        self,
        status: Optional[str] = None,
        label_filters: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all instances, optionally filtered by status and labels.

        Args:
            status: Optional status filter (e.g., "RUNNING", "PENDING")
            label_filters: Dict of label key:value to filter (AND logic)

        Returns:
            List of instance dicts ordered by creation time (newest first)
        """
        sql = "SELECT * FROM instances WHERE 1=1"
        params: List[Any] = []

        if status:
            sql += " AND status = ?"
            params.append(status)

        if label_filters:
            for key, value in label_filters.items():
                # SQLite JSON extract: json_extract(labels, '$.key') = 'value'
                sql += f" AND json_extract(labels, '$.{key}') = ?"
                params.append(value)

        sql += " ORDER BY created_at DESC"

        return await self.fetch_all(sql, tuple(params))

    async def get_pending_instances(self) -> List[Dict[str, Any]]:
        """Get all pending instances ordered by creation time."""
        return await self.fetch_all(
            "SELECT * FROM instances WHERE status = 'PENDING' ORDER BY created_at ASC"
        )

    async def get_instances_for_worker(self, worker_id: str) -> List[Dict[str, Any]]:
        """Get active instances assigned to a worker."""
        return await self.fetch_all(
            """
            SELECT * FROM instances
            WHERE assigned_worker = ?
            AND status IN ('ASSIGNED', 'RUNNING')
            """,
            (worker_id,),
        )

    # Allowed columns for update_instance_status kwargs
    _INSTANCE_UPDATE_COLUMNS = frozenset({
        "exit_code", "failure_reason", "endpoint", "port",
        "started_at", "ended_at", "last_report_at",
    })

    async def update_instance_status(
        self,
        instance_id: str,
        status: str,
        **kwargs,
    ) -> int:
        """Update instance status and optional fields."""
        set_clauses = ["status = ?"]
        params: List[Any] = [status]

        for key, value in kwargs.items():
            if key not in self._INSTANCE_UPDATE_COLUMNS:
                raise ValueError(f"Invalid column: {key}")
            set_clauses.append(f"{key} = ?")
            params.append(value)

        params.append(instance_id)
        async with self.transaction():
            cursor = await self._conn.execute(
                f"UPDATE instances SET {', '.join(set_clauses)} WHERE id = ?",
                tuple(params),
            )
            return cursor.rowcount

    async def request_cancellation(self, instance_id: str) -> int:
        """
        Mark cancellation requested for an instance.

        Sets cancel_requested_at timestamp if not already set (idempotent).
        Does not change status - status reflects actual process state.
        Returns number of rows affected (0 if already cancelled or terminal).
        """
        async with self.transaction():
            cursor = await self._conn.execute(
                """
                UPDATE instances
                SET cancel_requested_at = COALESCE(cancel_requested_at, datetime('now'))
                WHERE id = ?
                AND status IN ('PENDING', 'ASSIGNED', 'RUNNING', 'UNKNOWN')
                AND cancel_requested_at IS NULL
                """,
                (instance_id,),
            )
            return cursor.rowcount

    async def assign_instance(
        self,
        instance_id: str,
        worker_id: str,
        new_attempt: int,
        gpu_indices: List[int],
        exclusive: bool = True,
    ) -> bool:
        """Assign instance to worker with new attempt. Returns True if successful."""
        async with self.transaction():
            # Clear old allocations
            await self._conn.execute(
                "DELETE FROM instance_allocations WHERE instance_id = ?",
                (instance_id,),
            )

            # Update instance with new attempt (conditional on current status)
            cursor = await self._conn.execute(
                """
                UPDATE instances
                SET status = 'ASSIGNED',
                    attempt = ?,
                    assigned_worker = ?,
                    assigned_at = datetime('now'),
                    port = NULL,
                    endpoint = NULL
                WHERE id = ? AND status = 'PENDING'
                """,
                (new_attempt, worker_id, instance_id),
            )

            if cursor.rowcount == 0:
                return False

            # Create new allocations for this attempt with exclusive flag
            for gpu_idx in gpu_indices:
                await self._conn.execute(
                    """
                    INSERT INTO instance_allocations (instance_id, attempt, worker_id, gpu_index, exclusive)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (instance_id, new_attempt, worker_id, gpu_idx, exclusive),
                )

            return True

    async def transition_to_terminal(
        self,
        instance_id: str,
        attempt: int,
        status: str,
        exit_code: Optional[int] = None,
        failure_reason: Optional[str] = None,
    ) -> bool:
        """Transition instance to terminal state and free allocations."""
        async with self.transaction():
            cursor = await self._conn.execute(
                """
                UPDATE instances
                SET status = ?,
                    exit_code = ?,
                    failure_reason = ?,
                    ended_at = datetime('now'),
                    last_report_at = datetime('now')
                WHERE id = ? AND attempt = ?
                """,
                (status, exit_code, failure_reason, instance_id, attempt),
            )

            if cursor.rowcount > 0:
                # Free allocations
                await self._conn.execute(
                    "DELETE FROM instance_allocations WHERE instance_id = ?",
                    (instance_id,),
                )
                return True
            return False

    async def mark_instances_unknown(self, worker_id: str) -> int:
        """Mark all non-terminal instances for a worker as UNKNOWN."""
        async with self.transaction():
            cursor = await self._conn.execute(
                """
                UPDATE instances
                SET status = 'UNKNOWN'
                WHERE assigned_worker = ?
                AND status IN ('ASSIGNED', 'RUNNING')
                """,
                (worker_id,),
            )
            return cursor.rowcount

    async def get_instance_allocations(
        self, instance_id: str, attempt: int
    ) -> List[Dict[str, Any]]:
        """Get GPU allocations for an instance attempt."""
        return await self.fetch_all(
            """
            SELECT * FROM instance_allocations
            WHERE instance_id = ? AND attempt = ?
            """,
            (instance_id, attempt),
        )

    async def get_used_gpus_for_worker(
        self, worker_id: str, exclusive_only: bool = True
    ) -> List[int]:
        """
        Get list of GPU indices currently in use by a worker.

        Args:
            worker_id: Worker to query
            exclusive_only: If True (default), only count exclusive allocations.
                           This is the key change for GPU sharing support.
        """
        if exclusive_only:
            rows = await self.fetch_all(
                """
                SELECT DISTINCT a.gpu_index
                FROM instance_allocations a
                JOIN instances i ON a.instance_id = i.id AND a.attempt = i.attempt
                WHERE a.worker_id = ?
                AND a.exclusive = TRUE
                AND i.status IN ('ASSIGNED', 'RUNNING', 'UNKNOWN')
                """,
                (worker_id,),
            )
        else:
            rows = await self.fetch_all(
                """
                SELECT DISTINCT a.gpu_index
                FROM instance_allocations a
                JOIN instances i ON a.instance_id = i.id AND a.attempt = i.attempt
                WHERE a.worker_id = ?
                AND i.status IN ('ASSIGNED', 'RUNNING', 'UNKNOWN')
                """,
                (worker_id,),
            )
        return [row["gpu_index"] for row in rows]

    async def get_gpu_allocations_for_worker(
        self, worker_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all active GPU allocations for a worker.

        Returns list of dicts with instance_id, gpu_indices, exclusive.
        """
        rows = await self.fetch_all(
            """
            SELECT
                a.instance_id,
                a.exclusive,
                GROUP_CONCAT(a.gpu_index) as gpu_indices
            FROM instance_allocations a
            JOIN instances i ON a.instance_id = i.id AND a.attempt = i.attempt
            WHERE a.worker_id = ?
            AND i.status IN ('ASSIGNED', 'RUNNING', 'UNKNOWN')
            GROUP BY a.instance_id, a.exclusive
            """,
            (worker_id,),
        )

        result = []
        for row in rows:
            gpu_indices = [int(x) for x in row["gpu_indices"].split(",")]
            result.append({
                "instance_id": row["instance_id"],
                "gpu_indices": gpu_indices,
                "exclusive": bool(row["exclusive"]),
            })

        return result

    async def get_gpu_indices_for_instance(
        self, instance_id: str, attempt: int
    ) -> List[int]:
        """Get GPU indices allocated to a specific instance attempt."""
        rows = await self.fetch_all(
            """
            SELECT gpu_index
            FROM instance_allocations
            WHERE instance_id = ? AND attempt = ?
            ORDER BY gpu_index
            """,
            (instance_id, attempt),
        )
        return [row["gpu_index"] for row in rows]

    async def get_desired_instances_for_worker(
        self, worker_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get instances that should be running on this worker.

        Excludes instances with cancellation requested - worker infers
        "should stop" from absence in desired state.
        """
        return await self.fetch_all(
            """
            SELECT i.*, GROUP_CONCAT(a.gpu_index) as gpu_indices
            FROM instances i
            LEFT JOIN instance_allocations a ON i.id = a.instance_id AND i.attempt = a.attempt
            WHERE i.assigned_worker = ?
            AND i.status IN ('ASSIGNED', 'RUNNING', 'UNKNOWN')
            AND i.cancel_requested_at IS NULL
            GROUP BY i.id
            """,
            (worker_id,),
        )

    async def update_instance_running(
        self,
        instance_id: str,
        attempt: int,
        port: int,
        endpoint: str,
    ) -> bool:
        """Update instance to RUNNING state."""
        async with self.transaction():
            cursor = await self._conn.execute(
                """
                UPDATE instances
                SET status = 'RUNNING',
                    port = ?,
                    endpoint = ?,
                    started_at = COALESCE(started_at, datetime('now')),
                    last_report_at = datetime('now')
                WHERE id = ? AND attempt = ? AND status IN ('ASSIGNED', 'UNKNOWN')
                """,
                (port, endpoint, instance_id, attempt),
            )
            return cursor.rowcount > 0

    # Legacy API methods (no attempt fencing)
    async def set_instance_endpoint(
        self, instance_id: str, endpoint: str, port: int
    ) -> None:
        """Set endpoint for an instance (legacy API, no attempt check)."""
        async with self.transaction():
            await self._conn.execute(
                "UPDATE instances SET endpoint = ?, port = ? WHERE id = ?",
                (endpoint, port, instance_id),
            )

    async def update_instance_running_legacy(
        self, instance_id: str, port: Optional[int], endpoint: Optional[str]
    ) -> None:
        """Update instance to RUNNING state (legacy API, no attempt check)."""
        async with self.transaction():
            await self._conn.execute(
                """
                UPDATE instances
                SET status = 'RUNNING',
                    port = ?,
                    endpoint = ?,
                    started_at = COALESCE(started_at, datetime('now')),
                    last_report_at = datetime('now')
                WHERE id = ?
                """,
                (port, endpoint, instance_id),
            )
