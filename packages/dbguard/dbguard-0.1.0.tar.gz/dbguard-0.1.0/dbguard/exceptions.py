"""Custom exceptions for DBGuard"""


class DBGuardError(Exception):
    """Base exception for DBGuard"""

    pass


class MaxRetriesExceeded(DBGuardError):
    """Raised when maximum retry attempts are exceeded"""

    pass


class ConnectionHealthCheckFailed(DBGuardError):
    """Raised when connection health check fails"""

    pass
