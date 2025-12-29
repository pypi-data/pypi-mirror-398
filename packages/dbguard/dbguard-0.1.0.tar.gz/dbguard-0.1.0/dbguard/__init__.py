"""
DBGuard - Database resilience and retry logic made simple
"""

__version__ = "0.1.0"

from .core import DBGuard, retry_query
from .exceptions import DBGuardError, MaxRetriesExceeded, ConnectionHealthCheckFailed

__all__ = [
    "DBGuard",
    "retry_query",
    "DBGuardError",
    "MaxRetriesExceeded",
    "ConnectionHealthCheckFailed",
]
