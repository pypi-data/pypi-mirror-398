"""VectorVein API Exception Definitions"""


class VectorVeinAPIError(Exception):
    """Base exception class for VectorVein API"""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class APIKeyError(VectorVeinAPIError):
    """API key related errors"""

    pass


class WorkflowError(VectorVeinAPIError):
    """Workflow related errors"""

    pass


class AccessKeyError(VectorVeinAPIError):
    """Access key related errors"""

    pass


class RequestError(VectorVeinAPIError):
    """Request related errors"""

    pass


class TimeoutError(VectorVeinAPIError):
    """Timeout errors"""

    pass
