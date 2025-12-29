"""Comprehensive tests for DBGuard"""

import pytest
import sqlite3
import time
from dbguard import (
    DBGuard,
    retry_query,
    MaxRetriesExceeded,
    ConnectionHealthCheckFailed,
)


class TestDBGuard:
    """Test cases for DBGuard class"""

    def setup_method(self):
        """Set up test database before each test"""
        self.conn = sqlite3.connect(":memory:")
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            )
        """
        )
        cursor.execute("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')")
        cursor.execute("INSERT INTO users VALUES (2, 'Bob', 'bob@example.com')")
        self.conn.commit()

    def teardown_method(self):
        """Clean up after each test"""
        self.conn.close()

    def test_successful_query(self):
        """Test that a successful query works without retries"""
        guard = DBGuard(self.conn)

        @guard.protect
        def get_users():
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users")
            return cursor.fetchall()

        users = get_users()
        assert len(users) == 2
        assert users[0][1] == "Alice"

    def test_health_check_success(self):
        """Test that health check passes on healthy connection"""
        guard = DBGuard(self.conn)
        assert guard.check_health() is True

    def test_health_check_custom_query(self):
        """Test health check with custom query"""
        guard = DBGuard(self.conn, health_check_query="SELECT COUNT(*) FROM users")
        assert guard.check_health() is True

    def test_retry_on_transient_failure(self):
        """Test that operations retry on transient failures"""
        guard = DBGuard(self.conn, max_retries=3, initial_delay=0.01)
        call_count = 0

        @guard.protect
        def flaky_query():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise sqlite3.OperationalError("Database is locked")
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users")
            return cursor.fetchall()

        result = flaky_query()
        assert len(result) == 2
        assert call_count == 3

    def test_max_retries_exceeded(self):
        """Test that MaxRetriesExceeded is raised after exhausting retries"""
        guard = DBGuard(self.conn, max_retries=2, initial_delay=0.01)

        @guard.protect
        def always_fails():
            raise sqlite3.OperationalError("Persistent error")

        with pytest.raises(MaxRetriesExceeded) as exc_info:
            always_fails()

        assert "failed after 3 attempts" in str(exc_info.value)

    def test_exponential_backoff(self):
        """Test that exponential backoff increases delay"""
        guard = DBGuard(self.conn, max_retries=3, initial_delay=0.1, backoff_factor=2.0)
        call_times = []

        @guard.protect
        def record_timing():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise sqlite3.OperationalError("Retry me")
            return "success"

        result = record_timing()
        assert result == "success"

        # Check that delays increase (approximately)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        assert delay2 > delay1


class TestRetryQueryDecorator:
    """Test cases for retry_query decorator"""

    def test_successful_execution(self):
        """Test that successful execution doesn't retry"""
        call_count = 0

        @retry_query(max_retries=3)
        def simple_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = simple_function()
        assert result == "success"
        assert call_count == 1

    def test_retry_and_succeed(self):
        """Test that function retries and eventually succeeds"""
        call_count = 0

        @retry_query(max_retries=5, initial_delay=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise Exception("Transient error")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 4

    def test_max_retries_exceeded(self):
        """Test that decorator raises MaxRetriesExceeded"""

        @retry_query(max_retries=2, initial_delay=0.01)
        def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(MaxRetriesExceeded) as exc_info:
            always_fails()

        assert "failed after 3 attempts" in str(exc_info.value)
        assert "Always fails" in str(exc_info.value)

    def test_with_arguments(self):
        """Test that decorator works with function arguments"""

        @retry_query(max_retries=2, initial_delay=0.01)
        def add_numbers(a, b):
            return a + b

        result = add_numbers(5, 3)
        assert result == 8

    def test_max_delay_cap(self):
        """Test that delay doesn't exceed max_delay"""
        call_times = []

        @retry_query(
            max_retries=5, initial_delay=1.0, backoff_factor=10.0, max_delay=2.0
        )
        def record_timing():
            call_times.append(time.time())
            if len(call_times) < 4:
                raise Exception("Keep retrying")
            return "done"

        result = record_timing()
        assert result == "done"

        # Later delays should be capped at max_delay
        last_delay = call_times[-1] - call_times[-2]
        assert last_delay < 2.5  # Give some tolerance for execution time


class TestEdgeCases:
    """Test edge cases and error scenarios"""

    def test_zero_retries(self):
        """Test with zero retries (fail immediately)"""
        call_count = 0

        @retry_query(max_retries=0, initial_delay=0.01)
        def fails_once():
            nonlocal call_count
            call_count += 1
            raise Exception("Error")

        with pytest.raises(MaxRetriesExceeded):
            fails_once()

        assert call_count == 1

    def test_none_return_value(self):
        """Test that None can be returned successfully"""

        @retry_query(max_retries=2)
        def returns_none():
            return None

        result = returns_none()
        assert result is None

    def test_with_closed_connection(self):
        """Test behavior with closed database connection"""
        conn = sqlite3.connect(":memory:")
        guard = DBGuard(conn, max_retries=1, initial_delay=0.01)
        conn.close()

        with pytest.raises(ConnectionHealthCheckFailed):
            guard.check_health()


class TestIntegration:
    """Integration tests with real database operations"""

    def test_transaction_with_retry(self):
        """Test that transactions work with retry logic"""
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE counter (value INTEGER)")
        cursor.execute("INSERT INTO counter VALUES (0)")
        conn.commit()

        guard = DBGuard(conn, max_retries=3, initial_delay=0.01)

        @guard.protect
        def increment_counter():
            cursor = conn.cursor()
            cursor.execute("UPDATE counter SET value = value + 1")
            conn.commit()
            cursor.execute("SELECT value FROM counter")
            return cursor.fetchone()[0]

        result = increment_counter()
        assert result == 1

        conn.close()

    def test_multiple_operations(self):
        """Test multiple operations in sequence"""
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE logs (message TEXT)")
        conn.commit()

        guard = DBGuard(conn)

        @guard.protect
        def insert_log(message):
            cursor = conn.cursor()
            cursor.execute("INSERT INTO logs VALUES (?)", (message,))
            conn.commit()

        @guard.protect
        def count_logs():
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM logs")
            return cursor.fetchone()[0]

        insert_log("First log")
        insert_log("Second log")
        insert_log("Third log")

        count = count_logs()
        assert count == 3

        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
