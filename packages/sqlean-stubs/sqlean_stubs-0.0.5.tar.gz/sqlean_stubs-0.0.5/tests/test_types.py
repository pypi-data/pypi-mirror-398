"""Type checking tests for sqlean stubs."""

from typing import TYPE_CHECKING

import sqlean
from sqlean import extensions

# Only run actual type checks if mypy is available
if TYPE_CHECKING:
    import sqlean


def test_connect_returns_connection() -> None:
    """Test that connect returns a Connection object."""
    conn = sqlean.connect(":memory:")
    assert isinstance(conn, sqlean.Connection)
    conn.close()


def test_connection_cursor() -> None:
    """Test cursor creation from connection."""
    conn = sqlean.connect(":memory:")
    cursor = conn.cursor()
    assert isinstance(cursor, sqlean.Cursor)
    cursor.close()
    conn.close()


def test_execute_returns_cursor() -> None:
    """Test that execute returns a Cursor."""
    conn = sqlean.connect(":memory:")
    cursor = conn.execute("SELECT 1 AS num")
    assert isinstance(cursor, sqlean.Cursor)
    conn.close()


def test_fetchone_returns_optional() -> None:
    """Test fetchone returns optional value."""
    conn = sqlean.connect(":memory:")
    cursor = conn.execute("SELECT 1 AS num")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 1

    # Fetch again should return None
    row = cursor.fetchone()
    assert row is None
    conn.close()


def test_fetchall_returns_list() -> None:
    """Test fetchall returns a list."""
    conn = sqlean.connect(":memory:")
    cursor = conn.execute("SELECT 1 AS num UNION SELECT 2")
    rows = cursor.fetchall()
    assert isinstance(rows, list)
    assert len(rows) == 2
    conn.close()


def test_fetchmany_returns_list() -> None:
    """Test fetchmany returns a list."""
    conn = sqlean.connect(":memory:")
    cursor = conn.execute("SELECT 1 AS num UNION SELECT 2 UNION SELECT 3")
    rows = cursor.fetchmany(2)
    assert isinstance(rows, list)
    assert len(rows) <= 2
    conn.close()


def test_cursor_iteration() -> None:
    """Test cursor is iterable."""
    conn = sqlean.connect(":memory:")
    cursor = conn.execute("SELECT 1 AS num UNION SELECT 2")
    rows = list(cursor)
    assert len(rows) == 2
    conn.close()


def test_cursor_description() -> None:
    """Test cursor.description."""
    conn = sqlean.connect(":memory:")
    cursor = conn.execute("SELECT 1 AS num, 'text' AS text")
    assert cursor.description is not None
    assert len(cursor.description) == 2
    assert cursor.description[0][0] == "num"
    assert cursor.description[1][0] == "text"
    conn.close()


def test_cursor_rowcount() -> None:
    """Test cursor.rowcount."""
    conn = sqlean.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    cursor.execute("INSERT INTO test VALUES (1, 'Alice')")
    cursor.execute("INSERT INTO test VALUES (2, 'Bob')")
    assert cursor.rowcount == 1
    conn.close()


def test_cursor_lastrowid() -> None:
    """Test cursor.lastrowid."""
    conn = sqlean.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
    cursor.execute("INSERT INTO test (name) VALUES ('Alice')")
    assert cursor.lastrowid == 1
    conn.close()


def test_parameters_with_sequence() -> None:
    """Test execute with sequence parameters."""
    conn = sqlean.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("SELECT ?", (42,))
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 42
    conn.close()


def test_parameters_with_dict() -> None:
    """Test execute with dict parameters."""
    conn = sqlean.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("SELECT :value", {"value": 42})
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 42
    conn.close()


def test_executemany() -> None:
    """Test executemany."""
    conn = sqlean.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test (id INTEGER, value TEXT)")
    cursor.executemany("INSERT INTO test VALUES (?, ?)", [(1, "a"), (2, "b")])
    rows = cursor.execute("SELECT * FROM test").fetchall()
    assert len(rows) == 2
    conn.close()


def test_executescript() -> None:
    """Test executescript."""
    conn = sqlean.connect(":memory:")
    cursor = conn.executescript("""
        CREATE TABLE test (id INTEGER);
        INSERT INTO test VALUES (1);
        INSERT INTO test VALUES (2);
    """)
    rows = cursor.execute("SELECT * FROM test").fetchall()
    assert len(rows) == 2
    conn.close()


def test_row_factory_tuple() -> None:
    """Test default row factory (tuple)."""
    conn = sqlean.connect(":memory:")
    cursor = conn.execute("SELECT 1 AS num")
    row = cursor.fetchone()
    assert isinstance(row, tuple)
    assert row[0] == 1
    conn.close()


def test_row_factory_custom() -> None:
    """Test custom row factory."""

    def dict_factory(cursor: sqlean.Cursor, row: tuple) -> dict:
        return {desc[0]: val for desc, val in zip(cursor.description or [], row)}

    conn = sqlean.connect(":memory:")
    conn.row_factory = dict_factory
    cursor = conn.execute("SELECT 1 AS num, 'text' AS txt")
    row = cursor.fetchone()
    assert isinstance(row, dict)
    assert row["num"] == 1
    assert row["txt"] == "text"
    conn.close()


def test_row_sqlite_row() -> None:
    """Test Row factory."""
    conn = sqlean.connect(":memory:")
    conn.row_factory = sqlean.Row
    cursor = conn.execute("SELECT 1 AS num, 'text' AS txt")
    row = cursor.fetchone()
    assert isinstance(row, sqlean.Row)
    assert row["num"] == 1
    assert row["txt"] == "text"
    assert row[0] == 1
    assert row[1] == "text"
    conn.close()


def test_text_factory_str() -> None:
    """Test text factory with str (default)."""
    conn = sqlean.connect(":memory:")
    cursor = conn.execute("SELECT 'text'")
    row = cursor.fetchone()
    assert row is not None
    assert isinstance(row[0], str)
    assert row[0] == "text"
    conn.close()


def test_text_factory_bytes() -> None:
    """Test text factory with bytes."""
    conn = sqlean.connect(":memory:")
    conn.text_factory = bytes
    cursor = conn.execute("SELECT 'text'")
    row = cursor.fetchone()
    assert row is not None
    assert isinstance(row[0], bytes)
    assert row[0] == b"text"
    conn.close()


def test_connection_commit() -> None:
    """Test connection commit."""
    conn = sqlean.connect(":memory:")
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.execute("INSERT INTO test VALUES (1)")
    conn.commit()
    row = conn.execute("SELECT * FROM test").fetchone()
    assert row is not None
    assert row[0] == 1
    conn.close()


def test_connection_rollback() -> None:
    """Test connection rollback."""
    conn = sqlean.connect(":memory:")
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.execute("INSERT INTO test VALUES (1)")
    conn.rollback()
    rows = conn.execute("SELECT * FROM test").fetchall()
    assert len(rows) == 0
    conn.close()


def test_connection_context_manager() -> None:
    """Test connection as context manager."""
    with sqlean.connect(":memory:") as conn:
        cursor = conn.execute("SELECT 1")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == 1


def test_create_function() -> None:
    """Test create_function."""
    conn = sqlean.connect(":memory:")

    def double(x: int) -> int:
        return x * 2

    conn.create_function("double", 1, double)
    cursor = conn.execute("SELECT double(21)")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 42
    conn.close()


def test_create_function_deterministic() -> None:
    """Test create_function with deterministic flag."""
    conn = sqlean.connect(":memory:")

    def add_one(x: int) -> int:
        return x + 1

    conn.create_function("add_one", 1, add_one, deterministic=True)
    cursor = conn.execute("SELECT add_one(41)")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 42
    conn.close()


def test_create_aggregate() -> None:
    """Test create_aggregate."""

    class Sum:
        def __init__(self) -> None:
            self.value = 0

        def step(self, x: int) -> None:
            self.value += x

        def finalize(self) -> int:
            return self.value

    conn = sqlean.connect(":memory:")
    conn.execute("CREATE TABLE test (val INTEGER)")
    conn.execute("INSERT INTO test VALUES (10)")
    conn.execute("INSERT INTO test VALUES (20)")
    conn.execute("INSERT INTO test VALUES (30)")

    conn.create_aggregate("mysum", 1, Sum)
    cursor = conn.execute("SELECT mysum(val) FROM test")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 60
    conn.close()


def test_create_collation() -> None:
    """Test create_collation."""

    def reverse_collation(a: str, b: str) -> int:
        return -((a > b) - (a < b))

    conn = sqlean.connect(":memory:")
    conn.create_collation("reverse", reverse_collation)
    conn.execute("CREATE TABLE test (val TEXT)")
    conn.execute("INSERT INTO test VALUES ('a')")
    conn.execute("INSERT INTO test VALUES ('b')")
    conn.execute("INSERT INTO test VALUES ('c')")

    rows = conn.execute("SELECT val FROM test ORDER BY val COLLATE reverse").fetchall()
    assert rows[0][0] == "c"
    assert rows[1][0] == "b"
    assert rows[2][0] == "a"
    conn.close()


def test_set_authorizer() -> None:
    """Test set_authorizer."""

    def authorizer(action: int, arg1: str, arg2: str, dbname: str, source: str) -> int:
        return sqlean.SQLITE_OK

    conn = sqlean.connect(":memory:")
    conn.set_authorizer(authorizer)
    cursor = conn.execute("SELECT 1")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 1
    conn.close()


def test_set_progress_handler() -> None:
    """Test set_progress_handler."""
    calls = []

    def progress() -> int:
        calls.append(True)
        return 0

    conn = sqlean.connect(":memory:")
    conn.set_progress_handler(progress, 1)
    conn.execute("SELECT 1")
    # Progress handler should have been called
    assert len(calls) > 0
    conn.close()


def test_set_trace_callback() -> None:
    """Test set_trace_callback."""
    statements = []

    def trace(statement: str) -> None:
        statements.append(statement)

    conn = sqlean.connect(":memory:")
    conn.set_trace_callback(trace)
    conn.execute("SELECT 1")
    # Trace callback should have been called
    assert len(statements) > 0
    assert any("SELECT 1" in stmt for stmt in statements)
    conn.close()


def test_set_busy_timeout() -> None:
    """Test set_busy_timeout."""
    conn = sqlean.connect(":memory:")
    conn.set_busy_timeout(1.0)
    conn.close()


def test_total_changes() -> None:
    """Test total_changes property."""
    conn = sqlean.connect(":memory:")
    initial = conn.total_changes
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.execute("INSERT INTO test VALUES (1)")
    assert conn.total_changes > initial
    conn.close()


def test_isolation_level() -> None:
    """Test isolation_level property."""
    conn = sqlean.connect(":memory:")
    # isolation_level may be "DEFERRED" or "" depending on version
    assert conn.isolation_level in ("DEFERRED", "")
    conn.isolation_level = None
    assert conn.isolation_level is None
    conn.close()


def test_in_transaction() -> None:
    """Test in_transaction property."""
    conn = sqlean.connect(":memory:")
    assert not conn.in_transaction
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.execute("INSERT INTO test VALUES (1)")
    assert conn.in_transaction
    conn.commit()
    assert not conn.in_transaction
    conn.close()


def test_date_constructor() -> None:
    """Test Date constructor."""
    d = sqlean.Date(2024, 1, 15)
    assert d.year == 2024
    assert d.month == 1
    assert d.day == 15


def test_time_constructor() -> None:
    """Test Time constructor."""
    t = sqlean.Time(14, 30, 45)
    assert t.hour == 14
    assert t.minute == 30
    assert t.second == 45


def test_timestamp_constructor() -> None:
    """Test Timestamp constructor."""
    ts = sqlean.Timestamp(2024, 1, 15, 14, 30, 45)
    assert ts.year == 2024
    assert ts.month == 1
    assert ts.day == 15
    assert ts.hour == 14
    assert ts.minute == 30
    assert ts.second == 45


def test_date_from_ticks() -> None:
    """Test DateFromTicks."""
    d = sqlean.DateFromTicks(0)
    assert d.year == 1970


def test_time_from_ticks() -> None:
    """Test TimeFromTicks."""
    from datetime import time

    t = sqlean.TimeFromTicks(0)
    # TimeFromTicks(0) gives time at UTC epoch (which is 1:00 for UTC+1 offset on some systems)
    assert isinstance(t, time)


def test_timestamp_from_ticks() -> None:
    """Test TimestampFromTicks."""
    ts = sqlean.TimestampFromTicks(0)
    assert ts.year == 1970


def test_binary() -> None:
    """Test Binary factory."""
    b = sqlean.Binary(b"test")
    assert isinstance(b, memoryview)


def test_extensions_enable_all() -> None:
    """Test extensions.enable_all."""
    extensions.enable_all()
    # Should not raise


def test_extensions_disable_all() -> None:
    """Test extensions.disable_all."""
    extensions.disable_all()
    # Should not raise


def test_extensions_enable() -> None:
    """Test extensions.enable."""
    extensions.enable("uuid", "crypto")
    # Should not raise


def test_extensions_disable() -> None:
    """Test extensions.disable."""
    extensions.disable("uuid", "crypto")
    # Should not raise


def test_api_level_constant() -> None:
    """Test apilevel constant."""
    assert sqlean.apilevel == "2.0"


def test_param_style_constant() -> None:
    """Test paramstyle constant."""
    assert sqlean.paramstyle == "qmark"


def test_thread_safety_constant() -> None:
    """Test threadsafety constant."""
    assert sqlean.threadsafety == 1


def test_version_info() -> None:
    """Test version_info constant."""
    assert isinstance(sqlean.version_info, tuple)
    assert len(sqlean.version_info) == 3


def test_sqlite_version_info() -> None:
    """Test sqlite_version_info constant."""
    assert isinstance(sqlean.sqlite_version_info, tuple)
    assert len(sqlean.sqlite_version_info) == 3


def test_exceptions_hierarchy() -> None:
    """Test exception hierarchy."""
    assert issubclass(sqlean.OperationalError, sqlean.DatabaseError)
    assert issubclass(sqlean.DatabaseError, sqlean.Error)
    assert issubclass(sqlean.Error, Exception)
