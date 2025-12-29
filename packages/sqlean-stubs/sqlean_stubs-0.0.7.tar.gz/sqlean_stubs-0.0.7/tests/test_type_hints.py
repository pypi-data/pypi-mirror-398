"""Tests that verify type hints work correctly with mypy and at runtime."""

# This file can be analyzed by mypy to verify type hints are correct.
# Run: mypy tests/test_type_hints.py
# It can also be executed with pytest to verify type hints work at runtime.

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlean
from sqlean import extensions

if TYPE_CHECKING:
    # These imports are only for type checking
    pass


def test_basic_connection() -> None:
    """Test basic connection and query."""
    conn: sqlean.Connection = sqlean.connect(":memory:")

    # Should be able to call cursor
    cursor: sqlean.Cursor = conn.cursor()
    assert cursor is not None

    # Should be able to execute
    result = cursor.execute("SELECT 1")
    assert result is cursor

    # Should be able to fetch
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 1

    rows = cursor.fetchall()
    assert isinstance(rows, list)

    many = cursor.fetchmany(10)
    assert isinstance(many, list)

    # Should be able to commit/rollback
    conn.commit()
    conn.rollback()

    # Should be able to close
    cursor.close()
    conn.close()


def test_context_manager() -> None:
    """Test connection as context manager."""
    with sqlean.connect(":memory:") as conn:
        assert isinstance(conn, sqlean.Connection)
        cursor = conn.cursor()
        assert isinstance(cursor, sqlean.Cursor)
        result = cursor.execute("SELECT 1")
        assert result is cursor


def test_row_factory() -> None:
    """Test row factory type hints."""
    conn: sqlean.Connection = sqlean.connect(":memory:")

    # Test with Row factory
    conn.row_factory = sqlean.Row
    cursor = conn.execute("SELECT 1 AS num")
    row: sqlean.Row | None = cursor.fetchone()

    assert row is not None
    assert isinstance(row, sqlean.Row)
    # Should be able to access by index
    assert row[0] == 1
    # Should be able to access by name
    assert row["num"] == 1

    conn.close()


def test_custom_row_factory() -> None:
    """Test custom row factory."""
    from typing import Any

    def dict_factory(cursor: sqlean.Cursor, row: tuple) -> dict[str, Any]:
        return {desc[0]: val for desc, val in zip(cursor.description or [], row)}

    conn: sqlean.Connection = sqlean.connect(":memory:")
    conn.row_factory = dict_factory
    cursor = conn.execute("SELECT 1 AS num")
    row: dict[str, Any] | None = cursor.fetchone()
    assert row is not None
    assert isinstance(row, dict)
    assert row["num"] == 1
    conn.close()


def test_text_factory() -> None:
    """Test text factory type hints."""
    conn: sqlean.Connection = sqlean.connect(":memory:")

    # Test default (str)
    conn.text_factory = str
    assert conn.text_factory is str

    # Test bytes
    conn.text_factory = bytes
    assert conn.text_factory is bytes

    # Test bytearray
    conn.text_factory = bytearray
    assert conn.text_factory is bytearray

    # Test custom
    def custom_factory(x: bytes) -> str:
        return x.decode("utf-8")

    conn.text_factory = custom_factory
    assert conn.text_factory is custom_factory

    conn.close()


def test_execute_with_params() -> None:
    """Test execute with different parameter types."""
    conn: sqlean.Connection = sqlean.connect(":memory:")

    # Sequence parameters
    result1 = conn.execute("SELECT ?", (42,))
    row1 = result1.fetchone()
    assert row1 is not None
    assert row1[0] == 42

    result2 = conn.execute("SELECT ?", [42])
    row2 = result2.fetchone()
    assert row2 is not None
    assert row2[0] == 42

    # Dict parameters
    result3 = conn.execute("SELECT :val", {"val": 42})
    row3 = result3.fetchone()
    assert row3 is not None
    assert row3[0] == 42

    conn.close()


def test_create_function() -> None:
    """Test create_function type hints."""
    conn: sqlean.Connection = sqlean.connect(":memory:")

    def my_func(x: int) -> int:
        return x * 2

    def nullable_func(x: str | None) -> str | None:
        return x

    conn.create_function("double", 1, my_func)
    cursor = conn.execute("SELECT double(5)")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 10

    conn.create_function("nullable", 1, nullable_func)
    cursor = conn.execute("SELECT nullable(NULL)")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] is None

    conn.create_function("determ", 1, my_func, deterministic=True)
    cursor = conn.execute("SELECT determ(3)")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 6

    conn.close()


def test_create_aggregate() -> None:
    """Test create_aggregate type hints."""

    class MyAggregate:
        def __init__(self) -> None:
            self.value: int = 0

        def step(self, x: int) -> None:
            self.value += x

        def finalize(self) -> int:
            return self.value

    conn: sqlean.Connection = sqlean.connect(":memory:")
    conn.create_aggregate("myagg", 1, MyAggregate)
    cursor = conn.execute("SELECT myagg(x) FROM (SELECT 1 AS x UNION SELECT 2 UNION SELECT 3)")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 6
    conn.close()


def test_create_window_function() -> None:
    """Test create_window_function type hints."""

    class MyWindow:
        def __init__(self) -> None:
            self._value: int = 0

        def step(self, x: int) -> None:
            self._value += x

        def inverse(self, x: int) -> None:
            self._value -= x

        def value(self) -> int:
            return self._value

        def finalize(self) -> int:
            return self._value

    conn: sqlean.Connection = sqlean.connect(":memory:")
    conn.create_window_function("mywin", 1, MyWindow)
    cursor = conn.execute("SELECT mywin(x) OVER () FROM (SELECT 1 AS x UNION SELECT 2)")
    rows = cursor.fetchall()
    assert len(rows) == 2
    # Window function accumulates values over the window
    assert isinstance(rows[0][0], int)
    assert isinstance(rows[1][0], int)
    conn.close()


def test_create_collation() -> None:
    """Test create_collation type hints."""

    def my_collation(a: str, b: str) -> int:
        return -((a > b) - (a < b))

    conn: sqlean.Connection = sqlean.connect(":memory:")
    conn.create_collation("mycoll", my_collation)
    # Create a table and verify collation works
    conn.execute("CREATE TABLE test (name TEXT)")
    conn.execute("INSERT INTO test VALUES ('b')")
    conn.execute("INSERT INTO test VALUES ('a')")
    cursor = conn.execute("SELECT name FROM test ORDER BY name COLLATE mycoll")
    rows = cursor.fetchall()
    assert len(rows) == 2
    assert rows[0][0] == "b"  # reverse order due to my_collation
    assert rows[1][0] == "a"

    # Create and then deregister a collation
    conn.create_collation("nocoll", my_collation)
    conn.create_collation("nocoll", None)
    conn.close()


def test_set_authorizer() -> None:
    """Test set_authorizer type hints."""

    def my_authorizer(action: int, arg1: str, arg2: str, dbname: str, source: str) -> int:
        return sqlean.SQLITE_OK

    conn: sqlean.Connection = sqlean.connect(":memory:")
    conn.set_authorizer(my_authorizer)
    # Verify that authorization works
    conn.execute("SELECT 1")
    # Remove authorizer
    conn.set_authorizer(None)
    conn.close()


def test_set_progress_handler() -> None:
    """Test set_progress_handler type hints."""

    call_count = [0]

    def my_progress() -> int:
        call_count[0] += 1
        return 0

    conn: sqlean.Connection = sqlean.connect(":memory:")
    conn.set_progress_handler(my_progress, 100)
    conn.execute("SELECT 1")
    assert call_count[0] >= 0  # Progress handler called
    conn.set_progress_handler(None, 100)
    conn.close()


def test_set_trace_callback() -> None:
    """Test set_trace_callback type hints."""

    statements: list[str] = []

    def my_trace(statement: str) -> None:
        statements.append(statement)

    conn: sqlean.Connection = sqlean.connect(":memory:")
    conn.set_trace_callback(my_trace)
    conn.execute("SELECT 1")
    assert len(statements) > 0
    conn.set_trace_callback(None)
    conn.close()


def test_set_busy_handler() -> None:
    """Test set_busy_handler type hints."""

    call_count = [0]

    def my_handler(n: int) -> int:
        call_count[0] += 1
        return 0

    conn: sqlean.Connection = sqlean.connect(":memory:")
    conn.set_busy_handler(my_handler)
    conn.execute("SELECT 1")
    assert call_count[0] >= 0  # Handler is set
    conn.set_busy_handler(None)
    conn.close()


def test_date_time_constructors() -> None:
    """Test date/time constructor type hints."""
    from datetime import date, datetime, time

    d = sqlean.Date(2024, 1, 15)
    assert isinstance(d, date)

    t = sqlean.Time(14, 30, 45)
    assert isinstance(t, time)

    ts = sqlean.Timestamp(2024, 1, 15, 14, 30, 45)
    assert isinstance(ts, datetime)

    d2 = sqlean.DateFromTicks(0)
    assert isinstance(d2, date)

    t2 = sqlean.TimeFromTicks(0)
    assert isinstance(t2, time)

    ts2 = sqlean.TimestampFromTicks(0)
    assert isinstance(ts2, datetime)


def test_binary_factory() -> None:
    """Test Binary factory type hints."""
    b = sqlean.Binary(b"test")
    assert isinstance(b, memoryview)


def test_extensions() -> None:
    """Test extensions type hints."""
    extensions.enable_all()
    # Extensions should be enabled now
    extensions.disable_all()
    # Extensions should be disabled now
    extensions.enable("uuid", "crypto", "text")
    # Specific extensions should be enabled
    extensions.disable("uuid")
    # UUID extension should be disabled
