"""Tests for pylet/errors.py"""

import pytest

from pylet.errors import (
    InstanceFailedError,
    InstanceTerminatedError,
    NotFoundError,
    NotInitializedError,
    PyletError,
    TimeoutError,
)


class TestPyletError:
    def test_base_exception(self):
        """PyletError is the base for all pylet exceptions."""
        err = PyletError("test error")
        assert str(err) == "test error"
        assert isinstance(err, Exception)

    def test_all_errors_inherit_from_pylet_error(self):
        """All custom exceptions inherit from PyletError."""
        assert issubclass(NotInitializedError, PyletError)
        assert issubclass(NotFoundError, PyletError)
        assert issubclass(TimeoutError, PyletError)
        assert issubclass(InstanceFailedError, PyletError)
        assert issubclass(InstanceTerminatedError, PyletError)


class TestNotInitializedError:
    def test_default_message(self):
        """NotInitializedError has a default message."""
        err = NotInitializedError()
        assert "init()" in str(err)

    def test_custom_message(self):
        """NotInitializedError accepts custom message."""
        err = NotInitializedError("custom message")
        assert str(err) == "custom message"


class TestNotFoundError:
    def test_message(self):
        """NotFoundError stores message."""
        err = NotFoundError("Instance not found: abc")
        assert str(err) == "Instance not found: abc"


class TestTimeoutError:
    def test_message(self):
        """TimeoutError stores message."""
        err = TimeoutError("Operation timed out after 30s")
        assert str(err) == "Operation timed out after 30s"


class TestInstanceFailedError:
    def test_stores_instance(self):
        """InstanceFailedError stores the failed instance."""
        # Create a mock instance
        class MockInstance:
            status = "FAILED"

        instance = MockInstance()
        err = InstanceFailedError("Instance failed", instance=instance)
        assert err.instance is instance
        assert str(err) == "Instance failed"


class TestInstanceTerminatedError:
    def test_message(self):
        """InstanceTerminatedError stores message."""
        err = InstanceTerminatedError("Cannot cancel terminated instance")
        assert str(err) == "Cannot cancel terminated instance"
