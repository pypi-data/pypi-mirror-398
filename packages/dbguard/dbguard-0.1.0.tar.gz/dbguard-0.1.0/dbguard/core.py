"""Core functionality for DBGuard"""

import time
import logging
from typing import Callable, Any, Optional
from functools import wraps

from .exceptions import MaxRetriesExceeded, ConnectionHealthCheckFailed

logger = logging.getLogger(__name__)


class DBGuard:
    """
    Database connection wrapper with automatic retry logic and health checking.

    Example:
        >>> import sqlite3
        >>> from dbguard import DBGuard
        >>>
        >>> conn = sqlite3.connect(':memory:')
        >>> guard = DBGuard(conn, max_retries=3)
        >>>
        >>> @guard.protect
        >>> def get_users():
        >>>     cursor = conn.cursor()
        >>>     cursor.execute("SELECT * FROM users")
        >>>     return cursor.fetchall()
    """

    def __init__(
        self,
        connection: Any,
        max_retries: int = 3,
        initial_delay: float = 0.1,
        backoff_factor: float = 2.0,
        max_delay: float = 10.0,
        health_check_query: Optional[str] = None,
    ):
        """
        Initialize DBGuard with a database connection.

        Args:
            connection: Database connection object
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries (seconds)
            backoff_factor: Multiplier for exponential backoff
            max_delay: Maximum delay between retries (seconds)
            health_check_query: Custom query for health checks (e.g., "SELECT 1")
        """
        self.connection = connection
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.health_check_query = health_check_query or "SELECT 1"

    def check_health(self) -> bool:
        """
        Check if the database connection is healthy.

        Returns:
            bool: True if connection is healthy

        Raises:
            ConnectionHealthCheckFailed: If health check fails
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(self.health_check_query)
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise ConnectionHealthCheckFailed(f"Database health check failed: {e}")

    def protect(self, func: Callable) -> Callable:
        """
        Decorator to add retry logic to database operations.

        Args:
            func: Function to protect with retry logic

        Returns:
            Wrapped function with retry logic
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = self.initial_delay

            for attempt in range(self.max_retries + 1):
                try:
                    # Check connection health before attempting
                    if attempt > 0:
                        logger.info(
                            f"Checking connection health before retry {attempt}"
                        )
                        self.check_health()

                    result = func(*args, **kwargs)

                    if attempt > 0:
                        logger.info(f"Operation succeeded on attempt {attempt + 1}")

                    return result

                except Exception as e:
                    last_exception = e

                    if attempt < self.max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * self.backoff_factor, self.max_delay)
                    else:
                        logger.error(
                            f"All {self.max_retries + 1} attempts failed. "
                            f"Last error: {e}"
                        )

            raise MaxRetriesExceeded(
                f"Operation failed after {self.max_retries + 1} attempts. "
                f"Last error: {last_exception}"
            )

        return wrapper


def retry_query(
    max_retries: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    max_delay: float = 10.0,
):
    """
    Standalone decorator for adding retry logic to functions.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        backoff_factor: Multiplier for exponential backoff
        max_delay: Maximum delay between retries (seconds)

    Example:
        >>> @retry_query(max_retries=5)
        >>> def fetch_data(conn):
        >>>     cursor = conn.cursor()
        >>>     cursor.execute("SELECT * FROM data")
        >>>     return cursor.fetchall()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"Operation succeeded on attempt {attempt + 1}")
                    return result

                except Exception as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)

            raise MaxRetriesExceeded(
                f"Operation failed after {max_retries + 1} attempts. "
                f"Last error: {last_exception}"
            )

        return wrapper

    return decorator


# Example usage and tests
if __name__ == "__main__":
    import sqlite3

    # Create a test database
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """
    )
    cursor.execute(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        ("Mohamed", "mohamed@example.com"),
    )
    cursor.execute(
        "INSERT INTO users (name, email) VALUES (?, ?)", ("Shady", "shady@example.com")
    )
    conn.commit()

    # Example 1: Using DBGuard class
    print("Example 1: Using DBGuard class")
    guard = DBGuard(conn, max_retries=3)

    @guard.protect
    def get_all_users():
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()

    users = get_all_users()
    print(f"Users: {users}")

    # Check health
    print(f"Connection healthy: {guard.check_health()}")

    # Example 2: Using standalone decorator
    print("\nExample 2: Using standalone decorator")

    @retry_query(max_retries=3, initial_delay=0.1)
    def get_user_by_id(user_id):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

    user = get_user_by_id(1)
    print(f"User 1: {user}")

    conn.close()
    print("\nAll examples completed successfully!")
