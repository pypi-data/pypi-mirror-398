"""Tests for pylet/_worker_info.py"""

import pytest

from pylet._worker_info import WorkerInfo


class TestWorkerInfoProperties:
    """Test WorkerInfo property accessors."""

    @pytest.fixture
    def sample_data(self):
        """Sample worker data from API."""
        return {
            "worker_id": "worker-123",
            "host": "192.168.1.10",
            "status": "ONLINE",
            "total_resources": {
                "gpu_units": 4,
                "cpu_cores": 16,
                "memory_mb": 32768,
            },
            "available_resources": {
                "gpu_units": 2,
                "cpu_cores": 8,
                "memory_mb": 16384,
            },
        }

    def test_id(self, sample_data):
        """WorkerInfo.id returns the worker ID."""
        worker = WorkerInfo(sample_data)
        assert worker.id == "worker-123"

    def test_host(self, sample_data):
        """WorkerInfo.host returns the host address."""
        worker = WorkerInfo(sample_data)
        assert worker.host == "192.168.1.10"

    def test_status(self, sample_data):
        """WorkerInfo.status returns the worker status."""
        worker = WorkerInfo(sample_data)
        assert worker.status == "ONLINE"

    def test_gpu(self, sample_data):
        """WorkerInfo.gpu returns total GPU units."""
        worker = WorkerInfo(sample_data)
        assert worker.gpu == 4

    def test_gpu_available(self, sample_data):
        """WorkerInfo.gpu_available returns available GPU units."""
        worker = WorkerInfo(sample_data)
        assert worker.gpu_available == 2

    def test_cpu(self, sample_data):
        """WorkerInfo.cpu returns total CPU cores."""
        worker = WorkerInfo(sample_data)
        assert worker.cpu == 16

    def test_cpu_available(self, sample_data):
        """WorkerInfo.cpu_available returns available CPU cores."""
        worker = WorkerInfo(sample_data)
        assert worker.cpu_available == 8

    def test_memory(self, sample_data):
        """WorkerInfo.memory returns total memory in MB."""
        worker = WorkerInfo(sample_data)
        assert worker.memory == 32768

    def test_memory_available(self, sample_data):
        """WorkerInfo.memory_available returns available memory in MB."""
        worker = WorkerInfo(sample_data)
        assert worker.memory_available == 16384


class TestWorkerInfoRepr:
    """Test WorkerInfo string representation."""

    def test_repr(self):
        """__repr__ shows worker info."""
        data = {
            "worker_id": "w-123",
            "host": "10.0.0.1",
            "status": "ONLINE",
            "total_resources": {
                "gpu_units": 2,
                "cpu_cores": 8,
                "memory_mb": 16384,
            },
            "available_resources": {
                "gpu_units": 1,
                "cpu_cores": 4,
                "memory_mb": 8192,
            },
        }
        worker = WorkerInfo(data)
        repr_str = repr(worker)

        assert "WorkerInfo" in repr_str
        assert "w-123" in repr_str
        assert "10.0.0.1" in repr_str
        assert "ONLINE" in repr_str
        assert "gpu=1/2" in repr_str
        assert "cpu=4/8" in repr_str
        assert "memory=8192/16384" in repr_str
