"""Unit tests for pylet.schemas module."""

import pytest
from datetime import datetime

from pylet.schemas import (
    ResourceSpec,
    InstanceStatus,
    WorkerStatus,
    VALID_TRANSITIONS,
    validate_transition,
    is_terminal,
    is_active,
    get_display_status,
    Instance,
    Worker,
    InstanceSubmissionRequest,
    WorkerRegistrationRequest,
    WorkerRegistrationResponse,
    InstanceReport,
    HeartbeatRequest,
    HeartbeatResponse,
    DesiredInstance,
)


class TestResourceSpec:
    """Tests for ResourceSpec model."""

    def test_create_resource_spec(self):
        """Test creating a ResourceSpec with valid values."""
        spec = ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192)
        assert spec.cpu_cores == 4
        assert spec.gpu_units == 2
        assert spec.memory_mb == 8192

    def test_resource_spec_zero_values(self):
        """Test ResourceSpec with zero values."""
        spec = ResourceSpec(cpu_cores=0, gpu_units=0, memory_mb=0)
        assert spec.cpu_cores == 0
        assert spec.gpu_units == 0
        assert spec.memory_mb == 0


class TestInstanceStatus:
    """Tests for InstanceStatus enum."""

    def test_all_statuses_defined(self):
        """Test that all expected statuses are defined."""
        expected = {"PENDING", "ASSIGNED", "RUNNING", "UNKNOWN", "COMPLETED", "FAILED", "CANCELLED"}
        actual = {s.value for s in InstanceStatus}
        assert actual == expected

    def test_status_string_values(self):
        """Test that status values match their names."""
        for status in InstanceStatus:
            assert status.value == status.name


class TestWorkerStatus:
    """Tests for WorkerStatus enum."""

    def test_all_statuses_defined(self):
        """Test that all expected worker statuses are defined."""
        expected = {"ONLINE", "SUSPECT", "OFFLINE"}
        actual = {s.value for s in WorkerStatus}
        assert actual == expected


class TestValidTransitions:
    """Tests for VALID_TRANSITIONS constant."""

    def test_pending_transitions(self):
        """Test valid transitions from PENDING."""
        valid = VALID_TRANSITIONS[InstanceStatus.PENDING]
        assert InstanceStatus.ASSIGNED in valid
        assert InstanceStatus.CANCELLED in valid
        assert len(valid) == 2

    def test_assigned_transitions(self):
        """Test valid transitions from ASSIGNED."""
        valid = VALID_TRANSITIONS[InstanceStatus.ASSIGNED]
        assert InstanceStatus.RUNNING in valid
        assert InstanceStatus.UNKNOWN in valid
        assert InstanceStatus.FAILED in valid
        assert InstanceStatus.CANCELLED in valid
        assert len(valid) == 4

    def test_running_transitions(self):
        """Test valid transitions from RUNNING."""
        valid = VALID_TRANSITIONS[InstanceStatus.RUNNING]
        assert InstanceStatus.COMPLETED in valid
        assert InstanceStatus.FAILED in valid
        assert InstanceStatus.UNKNOWN in valid
        assert InstanceStatus.CANCELLED in valid
        assert len(valid) == 4

    def test_unknown_transitions(self):
        """Test valid transitions from UNKNOWN."""
        valid = VALID_TRANSITIONS[InstanceStatus.UNKNOWN]
        assert InstanceStatus.RUNNING in valid
        assert InstanceStatus.COMPLETED in valid
        assert InstanceStatus.FAILED in valid
        assert InstanceStatus.CANCELLED in valid
        assert len(valid) == 4

    def test_terminal_states_have_no_transitions(self):
        """Test that terminal states have no valid transitions."""
        assert VALID_TRANSITIONS[InstanceStatus.COMPLETED] == set()
        assert VALID_TRANSITIONS[InstanceStatus.FAILED] == set()
        assert VALID_TRANSITIONS[InstanceStatus.CANCELLED] == set()

    def test_no_self_transitions(self):
        """Test that no state can transition to itself."""
        for status, valid in VALID_TRANSITIONS.items():
            assert status not in valid, f"{status} should not transition to itself"

    def test_no_direct_pending_to_terminal(self):
        """Test that PENDING cannot directly go to COMPLETED or FAILED."""
        valid = VALID_TRANSITIONS[InstanceStatus.PENDING]
        assert InstanceStatus.COMPLETED not in valid
        assert InstanceStatus.FAILED not in valid


class TestValidateTransition:
    """Tests for validate_transition function."""

    def test_valid_transition(self):
        """Test that valid transitions return True."""
        assert validate_transition(InstanceStatus.PENDING, InstanceStatus.ASSIGNED) is True
        assert validate_transition(InstanceStatus.ASSIGNED, InstanceStatus.RUNNING) is True
        assert validate_transition(InstanceStatus.RUNNING, InstanceStatus.COMPLETED) is True

    def test_invalid_transition(self):
        """Test that invalid transitions return False."""
        assert validate_transition(InstanceStatus.PENDING, InstanceStatus.RUNNING) is False
        assert validate_transition(InstanceStatus.PENDING, InstanceStatus.COMPLETED) is False
        assert validate_transition(InstanceStatus.COMPLETED, InstanceStatus.RUNNING) is False

    def test_terminal_to_any_is_invalid(self):
        """Test that transitions from terminal states are invalid."""
        for target in InstanceStatus:
            assert validate_transition(InstanceStatus.COMPLETED, target) is False
            assert validate_transition(InstanceStatus.FAILED, target) is False
            assert validate_transition(InstanceStatus.CANCELLED, target) is False


class TestIsTerminal:
    """Tests for is_terminal function."""

    def test_terminal_states(self):
        """Test that terminal states return True."""
        assert is_terminal(InstanceStatus.COMPLETED) is True
        assert is_terminal(InstanceStatus.FAILED) is True
        assert is_terminal(InstanceStatus.CANCELLED) is True

    def test_non_terminal_states(self):
        """Test that non-terminal states return False."""
        assert is_terminal(InstanceStatus.PENDING) is False
        assert is_terminal(InstanceStatus.ASSIGNED) is False
        assert is_terminal(InstanceStatus.RUNNING) is False
        assert is_terminal(InstanceStatus.UNKNOWN) is False


class TestIsActive:
    """Tests for is_active function."""

    def test_active_states(self):
        """Test that active states return True."""
        assert is_active(InstanceStatus.ASSIGNED) is True
        assert is_active(InstanceStatus.RUNNING) is True
        assert is_active(InstanceStatus.UNKNOWN) is True

    def test_non_active_states(self):
        """Test that non-active states return False."""
        assert is_active(InstanceStatus.PENDING) is False
        assert is_active(InstanceStatus.COMPLETED) is False
        assert is_active(InstanceStatus.FAILED) is False
        assert is_active(InstanceStatus.CANCELLED) is False


class TestGetDisplayStatus:
    """Tests for get_display_status function."""

    def test_no_cancellation_returns_status_value(self):
        """Test that status value is returned when no cancellation requested."""
        assert get_display_status(InstanceStatus.PENDING, None) == "PENDING"
        assert get_display_status(InstanceStatus.RUNNING, None) == "RUNNING"
        assert get_display_status(InstanceStatus.COMPLETED, None) == "COMPLETED"

    def test_cancellation_non_terminal_returns_cancelling(self):
        """Test that CANCELLING is returned for non-terminal with cancellation."""
        cancel_time = datetime.now()
        assert get_display_status(InstanceStatus.PENDING, cancel_time) == "CANCELLING"
        assert get_display_status(InstanceStatus.ASSIGNED, cancel_time) == "CANCELLING"
        assert get_display_status(InstanceStatus.RUNNING, cancel_time) == "CANCELLING"
        assert get_display_status(InstanceStatus.UNKNOWN, cancel_time) == "CANCELLING"

    def test_cancellation_terminal_returns_status(self):
        """Test that terminal status is returned even with cancellation timestamp."""
        cancel_time = datetime.now()
        assert get_display_status(InstanceStatus.COMPLETED, cancel_time) == "COMPLETED"
        assert get_display_status(InstanceStatus.FAILED, cancel_time) == "FAILED"
        assert get_display_status(InstanceStatus.CANCELLED, cancel_time) == "CANCELLED"


class TestInstance:
    """Tests for Instance model."""

    def test_create_minimal_instance(self):
        """Test creating an instance with minimal required fields."""
        instance = Instance(
            instance_id="test-123",
            command="echo hello",
            resource_requirements=ResourceSpec(cpu_cores=1, gpu_units=0, memory_mb=512),
        )
        assert instance.instance_id == "test-123"
        assert instance.command == "echo hello"
        assert instance.status == InstanceStatus.PENDING
        assert instance.attempt == 0
        assert instance.name is None
        assert instance.assigned_to is None

    def test_create_instance_with_all_fields(self):
        """Test creating an instance with all fields."""
        now = datetime.now()
        instance = Instance(
            instance_id="test-456",
            name="my-instance",
            command="python script.py",
            resource_requirements=ResourceSpec(cpu_cores=4, gpu_units=2, memory_mb=8192),
            status=InstanceStatus.RUNNING,
            attempt=2,
            assigned_to="worker-1",
            port=15600,
            endpoint="192.168.1.1:15600",
            exit_code=None,
            created_at=now,
            cancellation_requested_at=None,
        )
        assert instance.name == "my-instance"
        assert instance.status == InstanceStatus.RUNNING
        assert instance.attempt == 2
        assert instance.assigned_to == "worker-1"


class TestWorker:
    """Tests for Worker model."""

    def test_create_worker(self):
        """Test creating a worker with required fields."""
        worker = Worker(
            worker_id="worker-abc",
            host="192.168.1.100",
            total_resources=ResourceSpec(cpu_cores=8, gpu_units=4, memory_mb=32768),
            available_resources=ResourceSpec(cpu_cores=8, gpu_units=4, memory_mb=32768),
        )
        assert worker.worker_id == "worker-abc"
        assert worker.host == "192.168.1.100"
        assert worker.status == WorkerStatus.ONLINE
        assert worker.total_resources.gpu_units == 4


class TestInstanceReport:
    """Tests for InstanceReport model."""

    def test_create_running_report(self):
        """Test creating a RUNNING instance report."""
        report = InstanceReport(
            instance_id="inst-1",
            attempt=1,
            status="RUNNING",
            port=15600,
        )
        assert report.instance_id == "inst-1"
        assert report.attempt == 1
        assert report.status == "RUNNING"
        assert report.port == 15600
        assert report.exit_code is None

    def test_create_completed_report(self):
        """Test creating a COMPLETED instance report."""
        report = InstanceReport(
            instance_id="inst-2",
            attempt=3,
            status="COMPLETED",
            exit_code=0,
        )
        assert report.status == "COMPLETED"
        assert report.exit_code == 0

    def test_create_failed_report(self):
        """Test creating a FAILED instance report."""
        report = InstanceReport(
            instance_id="inst-3",
            attempt=1,
            status="FAILED",
            exit_code=1,
        )
        assert report.status == "FAILED"
        assert report.exit_code == 1

    def test_create_not_found_report(self):
        """Test creating a NOT_FOUND instance report."""
        report = InstanceReport(
            instance_id="inst-4",
            attempt=2,
            status="NOT_FOUND",
        )
        assert report.status == "NOT_FOUND"


class TestHeartbeatRequest:
    """Tests for HeartbeatRequest model."""

    def test_create_heartbeat_request(self):
        """Test creating a heartbeat request."""
        request = HeartbeatRequest(
            worker_token="token-123",
            boot_id="boot-abc",
            last_seen_gen=5,
            instances=[
                InstanceReport(instance_id="i1", attempt=1, status="RUNNING", port=15600),
            ],
        )
        assert request.worker_token == "token-123"
        assert request.boot_id == "boot-abc"
        assert request.last_seen_gen == 5
        assert len(request.instances) == 1

    def test_heartbeat_request_defaults(self):
        """Test heartbeat request default values."""
        request = HeartbeatRequest(
            worker_token="token",
            boot_id="boot",
        )
        assert request.last_seen_gen == 0
        assert request.instances == []


class TestHeartbeatResponse:
    """Tests for HeartbeatResponse model."""

    def test_create_heartbeat_response(self):
        """Test creating a heartbeat response."""
        response = HeartbeatResponse(
            gen=10,
            desired_instances=[
                DesiredInstance(
                    instance_id="i1",
                    attempt=1,
                    command="echo hello",
                    gpu_indices=[0, 1],
                ),
            ],
        )
        assert response.gen == 10
        assert len(response.desired_instances) == 1
        assert response.desired_instances[0].gpu_indices == [0, 1]


class TestDesiredInstance:
    """Tests for DesiredInstance model."""

    def test_create_desired_instance(self):
        """Test creating a desired instance."""
        desired = DesiredInstance(
            instance_id="inst-1",
            attempt=2,
            command="python train.py",
            gpu_indices=[0, 1, 2, 3],
            env={"MASTER_PORT": "29500"},
            expected_status="ASSIGNED",
        )
        assert desired.instance_id == "inst-1"
        assert desired.attempt == 2
        assert desired.command == "python train.py"
        assert desired.gpu_indices == [0, 1, 2, 3]
        assert desired.env == {"MASTER_PORT": "29500"}
        assert desired.expected_status == "ASSIGNED"

    def test_desired_instance_defaults(self):
        """Test desired instance default values."""
        desired = DesiredInstance(
            instance_id="inst-2",
            attempt=1,
            command="sleep 10",
        )
        assert desired.gpu_indices == []
        assert desired.env == {}
        assert desired.expected_status == "ASSIGNED"
