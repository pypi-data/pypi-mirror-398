"""Unit tests for pylet.db module."""

import pytest
import pytest_asyncio
import tempfile
from pathlib import Path
from datetime import datetime

from pylet.db import Database


@pytest_asyncio.fixture
async def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    database = Database(db_path)
    await database.connect()
    yield database
    await database.close()

    # Cleanup
    db_path.unlink(missing_ok=True)
    for ext in ["-wal", "-shm"]:
        Path(str(db_path) + ext).unlink(missing_ok=True)


class TestDatabaseConnection:
    """Tests for database connection and initialization."""

    @pytest.mark.asyncio
    async def test_connect_creates_tables(self, db):
        """Test that connecting creates required tables."""
        # Check workers table exists
        result = await db.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='workers'"
        )
        assert result is not None
        assert result["name"] == "workers"

    @pytest.mark.asyncio
    async def test_connect_creates_instances_table(self, db):
        """Test that instances table is created."""
        result = await db.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='instances'"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_connect_creates_allocations_table(self, db):
        """Test that instance_allocations table is created."""
        result = await db.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='instance_allocations'"
        )
        assert result is not None


class TestWorkerOperations:
    """Tests for worker database operations."""

    @pytest.mark.asyncio
    async def test_insert_worker(self, db):
        """Test inserting a new worker."""
        await db.insert_worker(
            worker_id="worker-1",
            ip="192.168.1.1",
            cpu_cores=8,
            gpu_units=4,
            memory_mb=32768,
            worker_token="token-abc",
        )

        worker = await db.get_worker("worker-1")
        assert worker is not None
        assert worker["id"] == "worker-1"
        assert worker["ip"] == "192.168.1.1"
        assert worker["cpu_cores"] == 8
        assert worker["gpu_units"] == 4
        assert worker["status"] == "ONLINE"
        assert worker["worker_token"] == "token-abc"

    @pytest.mark.asyncio
    async def test_insert_worker_creates_gpu_inventory(self, db):
        """Test that inserting a worker creates GPU inventory."""
        await db.insert_worker(
            worker_id="worker-2",
            ip="192.168.1.2",
            cpu_cores=4,
            gpu_units=2,
            memory_mb=16384,
            worker_token="token-xyz",
        )

        gpus = await db.fetch_all(
            "SELECT gpu_index FROM worker_gpu_inventory WHERE worker_id = ?",
            ("worker-2",)
        )
        assert len(gpus) == 2
        assert {g["gpu_index"] for g in gpus} == {0, 1}

    @pytest.mark.asyncio
    async def test_get_worker_not_found(self, db):
        """Test getting a non-existent worker returns None."""
        worker = await db.get_worker("non-existent")
        assert worker is None

    @pytest.mark.asyncio
    async def test_get_all_workers(self, db):
        """Test getting all workers."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "t1")
        await db.insert_worker("w2", "2.2.2.2", 8, 4, 16384, "t2")

        workers = await db.get_all_workers()
        assert len(workers) == 2
        worker_ids = {w["id"] for w in workers}
        assert worker_ids == {"w1", "w2"}

    @pytest.mark.asyncio
    async def test_get_online_workers(self, db):
        """Test getting only online workers."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "t1")
        await db.insert_worker("w2", "2.2.2.2", 8, 4, 16384, "t2")

        # Mark w2 as OFFLINE
        await db.update_worker_status("w2", "OFFLINE")

        online = await db.get_online_workers()
        assert len(online) == 1
        assert online[0]["id"] == "w1"

    @pytest.mark.asyncio
    async def test_update_worker_heartbeat(self, db):
        """Test updating worker heartbeat."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "t1")

        # Update heartbeat with boot_id
        await db.update_worker_heartbeat("w1", boot_id="boot-123")

        worker = await db.get_worker("w1")
        assert worker["last_boot_id"] == "boot-123"
        assert worker["status"] == "ONLINE"

    @pytest.mark.asyncio
    async def test_update_worker_status(self, db):
        """Test updating worker status."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "t1")

        await db.update_worker_status("w1", "SUSPECT")
        worker = await db.get_worker("w1")
        assert worker["status"] == "SUSPECT"

        await db.update_worker_status("w1", "OFFLINE")
        worker = await db.get_worker("w1")
        assert worker["status"] == "OFFLINE"

    @pytest.mark.asyncio
    async def test_mark_all_workers_suspect(self, db):
        """Test marking all workers as SUSPECT."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "t1")
        await db.insert_worker("w2", "2.2.2.2", 8, 4, 16384, "t2")

        await db.mark_all_workers_suspect()

        workers = await db.get_all_workers()
        for w in workers:
            assert w["status"] == "SUSPECT"

    @pytest.mark.asyncio
    async def test_update_worker_on_reconnect(self, db):
        """Test updating worker on reconnect."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "old-token")

        # Reconnect with new IP and token
        await db.update_worker_on_reconnect(
            worker_id="w1",
            ip="192.168.1.100",
            cpu_cores=8,
            gpu_units=4,
            memory_mb=32768,
            worker_token="new-token",
        )

        worker = await db.get_worker("w1")
        assert worker["ip"] == "192.168.1.100"
        assert worker["worker_token"] == "new-token"
        assert worker["cpu_cores"] == 8
        assert worker["gpu_units"] == 4
        assert worker["status"] == "ONLINE"


class TestInstanceOperations:
    """Tests for instance database operations."""

    @pytest.mark.asyncio
    async def test_insert_instance(self, db):
        """Test inserting a new instance."""
        await db.insert_instance(
            instance_id="inst-1",
            name="my-instance",
            command="echo hello",
            cpu_cores=2,
            gpu_units=1,
            memory_mb=4096,
        )

        instance = await db.get_instance("inst-1")
        assert instance is not None
        assert instance["id"] == "inst-1"
        assert instance["name"] == "my-instance"
        assert instance["command"] == "echo hello"
        assert instance["status"] == "PENDING"
        assert instance["attempt"] == 0

    @pytest.mark.asyncio
    async def test_get_instance_not_found(self, db):
        """Test getting a non-existent instance returns None."""
        instance = await db.get_instance("non-existent")
        assert instance is None

    @pytest.mark.asyncio
    async def test_get_instance_by_name(self, db):
        """Test getting instance by name."""
        await db.insert_instance("inst-1", "my-instance", "cmd", 1, 0, 512)

        instance = await db.get_instance_by_name("my-instance")
        assert instance is not None
        assert instance["id"] == "inst-1"

    @pytest.mark.asyncio
    async def test_get_instance_by_name_not_found(self, db):
        """Test getting non-existent instance by name returns None."""
        instance = await db.get_instance_by_name("no-such-name")
        assert instance is None

    @pytest.mark.asyncio
    async def test_get_pending_instances(self, db):
        """Test getting pending instances."""
        await db.insert_instance("inst-1", "n1", "cmd1", 1, 0, 512)
        await db.insert_instance("inst-2", "n2", "cmd2", 1, 0, 512)

        pending = await db.get_pending_instances()
        assert len(pending) == 2

    @pytest.mark.asyncio
    async def test_update_instance_status(self, db):
        """Test updating instance status."""
        await db.insert_instance("inst-1", "n1", "cmd", 1, 0, 512)

        rows = await db.update_instance_status(
            "inst-1",
            "RUNNING",
            port=15600,
            endpoint="192.168.1.1:15600",
        )
        assert rows == 1

        instance = await db.get_instance("inst-1")
        assert instance["status"] == "RUNNING"
        assert instance["port"] == 15600
        assert instance["endpoint"] == "192.168.1.1:15600"

    @pytest.mark.asyncio
    async def test_update_instance_status_invalid_column(self, db):
        """Test that invalid columns raise ValueError."""
        await db.insert_instance("inst-1", "n1", "cmd", 1, 0, 512)

        with pytest.raises(ValueError, match="Invalid column"):
            await db.update_instance_status("inst-1", "RUNNING", invalid_col="bad")


class TestInstanceAssignment:
    """Tests for instance assignment operations."""

    @pytest.mark.asyncio
    async def test_assign_instance(self, db):
        """Test assigning an instance to a worker."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd", 1, 1, 512)

        success = await db.assign_instance(
            instance_id="inst-1",
            worker_id="w1",
            new_attempt=1,
            gpu_indices=[0],
        )
        assert success is True

        instance = await db.get_instance("inst-1")
        assert instance["status"] == "ASSIGNED"
        assert instance["attempt"] == 1
        assert instance["assigned_worker"] == "w1"

    @pytest.mark.asyncio
    async def test_assign_instance_creates_allocations(self, db):
        """Test that assigning an instance creates GPU allocations."""
        await db.insert_worker("w1", "1.1.1.1", 4, 4, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd", 1, 2, 512)

        await db.assign_instance("inst-1", "w1", 1, [0, 1])

        allocations = await db.get_instance_allocations("inst-1", 1)
        assert len(allocations) == 2
        gpu_indices = {a["gpu_index"] for a in allocations}
        assert gpu_indices == {0, 1}

    @pytest.mark.asyncio
    async def test_assign_instance_fails_if_not_pending(self, db):
        """Test that assigning fails if instance is not PENDING."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd", 1, 1, 512)

        # First assignment succeeds
        success = await db.assign_instance("inst-1", "w1", 1, [0])
        assert success is True

        # Second assignment fails (instance is now ASSIGNED)
        success = await db.assign_instance("inst-1", "w1", 2, [0])
        assert success is False

    @pytest.mark.asyncio
    async def test_get_used_gpus_for_worker(self, db):
        """Test getting used GPUs for a worker."""
        await db.insert_worker("w1", "1.1.1.1", 4, 4, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd", 1, 2, 512)

        # Initially no GPUs used
        used = await db.get_used_gpus_for_worker("w1")
        assert used == []

        # Assign instance with 2 GPUs
        await db.assign_instance("inst-1", "w1", 1, [0, 2])

        used = await db.get_used_gpus_for_worker("w1")
        assert set(used) == {0, 2}


class TestInstanceTermination:
    """Tests for instance termination operations."""

    @pytest.mark.asyncio
    async def test_transition_to_terminal(self, db):
        """Test transitioning instance to terminal state."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd", 1, 1, 512)
        await db.assign_instance("inst-1", "w1", 1, [0])

        success = await db.transition_to_terminal(
            instance_id="inst-1",
            attempt=1,
            status="COMPLETED",
            exit_code=0,
        )
        assert success is True

        instance = await db.get_instance("inst-1")
        assert instance["status"] == "COMPLETED"
        assert instance["exit_code"] == 0
        assert instance["ended_at"] is not None

    @pytest.mark.asyncio
    async def test_transition_to_terminal_frees_allocations(self, db):
        """Test that terminal transition frees GPU allocations."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd", 1, 1, 512)
        await db.assign_instance("inst-1", "w1", 1, [0])

        # Verify allocation exists
        allocations = await db.get_instance_allocations("inst-1", 1)
        assert len(allocations) == 1

        # Transition to terminal
        await db.transition_to_terminal("inst-1", 1, "COMPLETED", 0)

        # Allocations should be freed
        allocations = await db.get_instance_allocations("inst-1", 1)
        assert len(allocations) == 0

    @pytest.mark.asyncio
    async def test_transition_to_terminal_wrong_attempt(self, db):
        """Test that terminal transition fails with wrong attempt."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd", 1, 1, 512)
        await db.assign_instance("inst-1", "w1", 1, [0])

        # Try to terminate with wrong attempt
        success = await db.transition_to_terminal("inst-1", 99, "FAILED", 1)
        assert success is False

        # Instance should still be ASSIGNED
        instance = await db.get_instance("inst-1")
        assert instance["status"] == "ASSIGNED"


class TestCancellation:
    """Tests for cancellation operations."""

    @pytest.mark.asyncio
    async def test_request_cancellation(self, db):
        """Test requesting cancellation."""
        await db.insert_instance("inst-1", "n1", "cmd", 1, 0, 512)

        rows = await db.request_cancellation("inst-1")
        assert rows == 1

        instance = await db.get_instance("inst-1")
        assert instance["cancel_requested_at"] is not None

    @pytest.mark.asyncio
    async def test_request_cancellation_idempotent(self, db):
        """Test that cancellation request is idempotent."""
        await db.insert_instance("inst-1", "n1", "cmd", 1, 0, 512)

        # First request
        rows1 = await db.request_cancellation("inst-1")
        assert rows1 == 1

        instance1 = await db.get_instance("inst-1")
        cancel_time1 = instance1["cancel_requested_at"]

        # Second request should not change timestamp
        rows2 = await db.request_cancellation("inst-1")
        assert rows2 == 0  # No rows affected

        instance2 = await db.get_instance("inst-1")
        assert instance2["cancel_requested_at"] == cancel_time1

    @pytest.mark.asyncio
    async def test_request_cancellation_terminal_instance(self, db):
        """Test that cancellation request fails for terminal instance."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd", 1, 1, 512)
        await db.assign_instance("inst-1", "w1", 1, [0])
        await db.transition_to_terminal("inst-1", 1, "COMPLETED", 0)

        rows = await db.request_cancellation("inst-1")
        assert rows == 0


class TestDesiredInstances:
    """Tests for desired instances query."""

    @pytest.mark.asyncio
    async def test_get_desired_instances_for_worker(self, db):
        """Test getting desired instances for a worker."""
        await db.insert_worker("w1", "1.1.1.1", 4, 4, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd1", 1, 2, 512)
        await db.insert_instance("inst-2", "n2", "cmd2", 1, 1, 512)

        await db.assign_instance("inst-1", "w1", 1, [0, 1])
        await db.assign_instance("inst-2", "w1", 1, [2])

        desired = await db.get_desired_instances_for_worker("w1")
        assert len(desired) == 2

    @pytest.mark.asyncio
    async def test_get_desired_instances_excludes_cancelled(self, db):
        """Test that desired instances excludes cancelled ones."""
        await db.insert_worker("w1", "1.1.1.1", 4, 4, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd1", 1, 1, 512)
        await db.insert_instance("inst-2", "n2", "cmd2", 1, 1, 512)

        await db.assign_instance("inst-1", "w1", 1, [0])
        await db.assign_instance("inst-2", "w1", 1, [1])

        # Request cancellation for inst-1
        await db.request_cancellation("inst-1")

        desired = await db.get_desired_instances_for_worker("w1")
        assert len(desired) == 1
        assert desired[0]["id"] == "inst-2"


class TestMarkInstancesUnknown:
    """Tests for marking instances as UNKNOWN."""

    @pytest.mark.asyncio
    async def test_mark_instances_unknown(self, db):
        """Test marking instances as UNKNOWN when worker goes offline."""
        await db.insert_worker("w1", "1.1.1.1", 4, 4, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd1", 1, 1, 512)
        await db.insert_instance("inst-2", "n2", "cmd2", 1, 1, 512)

        await db.assign_instance("inst-1", "w1", 1, [0])
        await db.assign_instance("inst-2", "w1", 1, [1])

        # Transition inst-1 to RUNNING
        await db.update_instance_status("inst-1", "RUNNING")

        # Mark all instances for worker as UNKNOWN
        affected = await db.mark_instances_unknown("w1")
        assert affected == 2

        inst1 = await db.get_instance("inst-1")
        inst2 = await db.get_instance("inst-2")
        assert inst1["status"] == "UNKNOWN"
        assert inst2["status"] == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_mark_instances_unknown_skips_terminal(self, db):
        """Test that terminal instances are not marked UNKNOWN."""
        await db.insert_worker("w1", "1.1.1.1", 4, 4, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd1", 1, 1, 512)
        await db.insert_instance("inst-2", "n2", "cmd2", 1, 1, 512)

        await db.assign_instance("inst-1", "w1", 1, [0])
        await db.assign_instance("inst-2", "w1", 1, [1])

        # Complete inst-1
        await db.transition_to_terminal("inst-1", 1, "COMPLETED", 0)

        # Mark instances as UNKNOWN
        affected = await db.mark_instances_unknown("w1")
        assert affected == 1  # Only inst-2 affected

        inst1 = await db.get_instance("inst-1")
        inst2 = await db.get_instance("inst-2")
        assert inst1["status"] == "COMPLETED"  # Unchanged
        assert inst2["status"] == "UNKNOWN"


class TestTransaction:
    """Tests for transaction behavior."""

    @pytest.mark.asyncio
    async def test_transaction_commit(self, db):
        """Test that transaction commits on success."""
        async with db.transaction():
            await db._conn.execute(
                "INSERT INTO workers (id, ip, status, cpu_cores, gpu_units, memory_mb, "
                "available_cpu, available_gpu, available_memory) "
                "VALUES (?, ?, 'ONLINE', 4, 2, 8192, 4, 2, 8192)",
                ("w1", "1.1.1.1"),
            )

        worker = await db.get_worker("w1")
        assert worker is not None

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_exception(self, db):
        """Test that transaction rolls back on exception."""
        try:
            async with db.transaction():
                await db._conn.execute(
                    "INSERT INTO workers (id, ip, status, cpu_cores, gpu_units, memory_mb, "
                    "available_cpu, available_gpu, available_memory) "
                    "VALUES (?, ?, 'ONLINE', 4, 2, 8192, 4, 2, 8192)",
                    ("w1", "1.1.1.1"),
                )
                raise ValueError("Simulated error")
        except ValueError:
            pass

        worker = await db.get_worker("w1")
        assert worker is None  # Should have been rolled back


class TestUpdateInstanceRunning:
    """Tests for update_instance_running."""

    @pytest.mark.asyncio
    async def test_update_instance_running(self, db):
        """Test updating instance to RUNNING state."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd", 1, 1, 512)
        await db.assign_instance("inst-1", "w1", 1, [0])

        success = await db.update_instance_running(
            instance_id="inst-1",
            attempt=1,
            port=15600,
            endpoint="1.1.1.1:15600",
        )
        assert success is True

        instance = await db.get_instance("inst-1")
        assert instance["status"] == "RUNNING"
        assert instance["port"] == 15600
        assert instance["endpoint"] == "1.1.1.1:15600"

    @pytest.mark.asyncio
    async def test_update_instance_running_wrong_attempt(self, db):
        """Test that update fails with wrong attempt."""
        await db.insert_worker("w1", "1.1.1.1", 4, 2, 8192, "t1")
        await db.insert_instance("inst-1", "n1", "cmd", 1, 1, 512)
        await db.assign_instance("inst-1", "w1", 1, [0])

        success = await db.update_instance_running("inst-1", 99, 15600, "1.1.1.1:15600")
        assert success is False

    @pytest.mark.asyncio
    async def test_update_instance_running_wrong_status(self, db):
        """Test that update fails if instance not in ASSIGNED or UNKNOWN status."""
        await db.insert_instance("inst-1", "n1", "cmd", 1, 0, 512)

        # Instance is PENDING, should fail
        success = await db.update_instance_running("inst-1", 0, 15600, "1.1.1.1:15600")
        assert success is False
