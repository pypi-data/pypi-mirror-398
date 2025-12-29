"""
PyLet Exception Classes.

All PyLet-specific exceptions inherit from PyletError.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pylet._instance import Instance


class PyletError(Exception):
    """Base exception for all PyLet errors."""

    pass


class NotInitializedError(PyletError):
    """pylet.init() not called."""

    def __init__(self, message: str = "Call pylet.init() first"):
        super().__init__(message)


class NotFoundError(PyletError):
    """Instance or worker not found."""

    pass


class TimeoutError(PyletError):
    """Operation timed out."""

    pass


class InstanceFailedError(PyletError):
    """Instance entered FAILED/CANCELLED state unexpectedly."""

    def __init__(self, message: str, instance: "Instance"):
        super().__init__(message)
        self.instance = instance


class InstanceTerminatedError(PyletError):
    """Operation invalid on terminated instance."""

    pass
