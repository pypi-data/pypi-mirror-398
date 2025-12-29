"""Type hints for sqlean.dbapi2 - DB-API 2.0 interface for SQLite."""

from collections.abc import Iterator, Sequence
from datetime import date, datetime, time
from typing import (
    Any,
    Callable,
    Literal,
    TypeVar,
    overload,
)

# DB-API module constants
paramstyle: Literal["qmark"]
threadsafety: Literal[1]
apilevel: Literal["2.0"]

# Version information
version: str
sqlite_version: str
version_info: tuple[int, int, int]
sqlite_version_info: tuple[int, int, int]

# Type aliases
_SQLiteValue = str | int | float | bytes | None
_SQLiteParam = str | int | float | bytes | None | memoryview
_Parameters = Sequence[_SQLiteParam] | dict[str, _SQLiteParam]
_RowFactory = Callable[["Cursor", tuple[_SQLiteValue, ...]], Any]

T = TypeVar("T")

# Date/time constructors
def Date(year: int, month: int, day: int) -> date: ...
def Time(hour: int, minute: int, second: int) -> time: ...
def Timestamp(year: int, month: int, day: int, hour: int, minute: int, second: int) -> datetime: ...
def DateFromTicks(ticks: float) -> date: ...
def TimeFromTicks(ticks: float) -> time: ...
def TimestampFromTicks(ticks: float) -> datetime: ...

# Type converters
Binary = memoryview

class OptimizedUnicode:
    """Text factory that optimizes between str and bytes."""
    def __call__(self, data: bytes) -> str | bytes: ...

# Exception hierarchy
class Warning(Exception):
    """Base class for warnings."""

    pass

class Error(Exception):
    """Base class for all exceptions."""

    pass

class InterfaceError(Error):
    """Interface error."""

    pass

class DatabaseError(Error):
    """Database error."""

    pass

class DataError(DatabaseError):
    """Data error."""

    pass

class OperationalError(DatabaseError):
    """Operational error."""

    pass

class IntegrityError(DatabaseError):
    """Integrity error."""

    pass

class InternalError(DatabaseError):
    """Internal error."""

    pass

class ProgrammingError(DatabaseError):
    """Programming error."""

    pass

class NotSupportedError(DatabaseError):
    """Not supported error."""

    pass

# Authorization and progress callback constants
SQLITE_OK: int
SQLITE_DENY: int
SQLITE_IGNORE: int
SQLITE_CREATE_INDEX: int
SQLITE_CREATE_TABLE: int
SQLITE_CREATE_TEMP_INDEX: int
SQLITE_CREATE_TEMP_TABLE: int
SQLITE_CREATE_TEMP_TRIGGER: int
SQLITE_CREATE_TEMP_VIEW: int
SQLITE_CREATE_TRIGGER: int
SQLITE_CREATE_VIEW: int
SQLITE_DELETE: int
SQLITE_DROP_INDEX: int
SQLITE_DROP_TABLE: int
SQLITE_DROP_TEMP_INDEX: int
SQLITE_DROP_TEMP_TABLE: int
SQLITE_DROP_TEMP_TRIGGER: int
SQLITE_DROP_TEMP_VIEW: int
SQLITE_DROP_TRIGGER: int
SQLITE_DROP_VIEW: int
SQLITE_INSERT: int
SQLITE_PRAGMA: int
SQLITE_READ: int
SQLITE_SELECT: int
SQLITE_TRANSACTION: int
SQLITE_UPDATE: int
SQLITE_ATTACH: int
SQLITE_DETACH: int
SQLITE_REINDEX: int
SQLITE_ANALYZE: int
SQLITE_CREATE_VTABLE: int
SQLITE_DROP_VTABLE: int
SQLITE_FUNCTION: int
SQLITE_SAVEPOINT: int
SQLITE_RECURSIVE: int

# Adapter/converter registration
def register_adapter(type_: type[Any], adapter: Callable[[Any], _SQLiteValue]) -> None:
    """Register an adapter for a custom type."""
    ...

def register_converter(typename: str, converter: Callable[[bytes], Any]) -> None:
    """Register a converter for a custom type."""
    ...

class Row:
    """Represents a row from a database query result."""

    def __init__(self, cursor: Cursor, data: tuple[_SQLiteValue, ...]) -> None: ...
    @overload
    def __getitem__(self, key: int) -> _SQLiteValue: ...
    @overload
    def __getitem__(self, key: str) -> _SQLiteValue: ...
    @overload
    def __getitem__(self, key: slice) -> tuple[_SQLiteValue, ...]: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[_SQLiteValue]: ...
    def __contains__(self, item: Any) -> bool: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...
    def __hash__(self) -> int: ...
    def __reversed__(self) -> Iterator[_SQLiteValue]: ...
    def keys(self) -> list[str]: ...

class Cursor:
    """Database cursor for executing SQL queries."""

    connection: Connection
    description: list[tuple[str, str | None, None, None, None, None, int | None]] | None
    rowcount: int
    lastrowid: int
    arraysize: int

    def __init__(self, connection: Connection) -> None: ...
    def __iter__(self) -> Iterator[Any]: ...
    def __next__(self) -> Any: ...
    @overload
    def execute(self, sql: str) -> Cursor: ...
    @overload
    def execute(self, sql: str, parameters: Sequence[_SQLiteParam]) -> Cursor: ...
    @overload
    def execute(self, sql: str, parameters: dict[str, _SQLiteParam]) -> Cursor: ...
    def executemany(self, sql: str, parameters: Sequence[Sequence[_SQLiteParam]]) -> Cursor: ...
    def executescript(self, sql_script: str) -> Cursor: ...
    def fetchone(self) -> Any | None: ...
    def fetchall(self) -> list[Any]: ...
    def fetchmany(self, size: int = 2) -> list[Any]: ...
    def close(self) -> None: ...
    def setinputsizes(self, sizes: Sequence[int | None]) -> None: ...
    def setoutputsize(self, size: int, column: int | None = None) -> None: ...

class Connection:
    """Database connection."""

    isolation_level: str | None
    in_transaction: bool
    row_factory: _RowFactory | None
    text_factory: type[str] | type[bytes] | type[bytearray] | Callable[[bytes], Any]
    total_changes: int

    def __init__(
        self,
        database: str | bytes,
        timeout: float = 5.0,
        isolation_level: str | None = "DEFERRED",
        check_same_thread: bool = True,
        factory: type[Connection] = ...,
        cached_statements: int = 100,
        uri: bool = False,
    ) -> None: ...
    def __enter__(self) -> Connection: ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...
    def __iter__(self) -> Iterator[Any]: ...
    def __next__(self) -> Any: ...
    def __call__(self) -> Cursor: ...
    def cursor(
        self,
        factory: type[Cursor] | Callable[[Connection], Cursor] | None = None,
    ) -> Cursor: ...
    @overload
    def execute(self, sql: str) -> Cursor: ...
    @overload
    def execute(self, sql: str, parameters: Sequence[_SQLiteParam]) -> Cursor: ...
    @overload
    def execute(self, sql: str, parameters: dict[str, _SQLiteParam]) -> Cursor: ...
    def executemany(self, sql: str, parameters: Sequence[Sequence[_SQLiteParam]]) -> Cursor: ...
    def executescript(self, sql_script: str) -> Cursor: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...
    def create_function(
        self,
        name: str,
        num_params: int,
        func: Callable[..., _SQLiteValue | None],
        *,
        deterministic: bool = False,
    ) -> None: ...
    def create_aggregate(
        self,
        name: str,
        num_params: int,
        aggregate_class: type[Any],
    ) -> None: ...
    def create_window_function(
        self,
        name: str,
        num_params: int,
        aggregate_class: type[Any],
    ) -> None: ...
    def create_collation(
        self,
        name: str,
        callable: Callable[[str, str], int] | None,
    ) -> None: ...
    def set_authorizer(
        self,
        authorizer: Callable[[int, str, str, str, str], int] | None,
    ) -> None: ...
    def set_progress_handler(
        self,
        progress_handler: Callable[[], int] | None,
        n: int,
    ) -> None: ...
    def set_trace_callback(
        self,
        trace_callback: Callable[[str], None] | None,
    ) -> None: ...
    def set_busy_handler(
        self,
        handler: Callable[[int], int] | None,
    ) -> None: ...
    def set_busy_timeout(self, timeout: float) -> None: ...
    def interrupt(self) -> None: ...
    def open_blob(
        self,
        table: str,
        column: str,
        row: int,
        readonly: bool = False,
    ) -> Blob: ...
    def backup(
        self,
        target: Connection,
        *,
        pages: int = -1,
        progress: Callable[[int, int, int], None] | None = None,
        name: str = "main",
        sleep: float = 0.25,
    ) -> None: ...
    def enable_load_extension(self, enabled: bool) -> None: ...
    def load_extension(self, path: str, entry_point: str | None = None) -> None: ...
    @property
    def schema(self) -> str | None: ...

class Blob:
    """BLOB object for reading and writing."""

    def read(self, n: int = -1) -> bytes: ...
    def write(self, data: bytes) -> None: ...
    def close(self) -> None: ...
    def seek(self, offset: int, origin: int = 0) -> int: ...
    def tell(self) -> int: ...
    def __enter__(self) -> Blob: ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...

def connect(
    database: str | bytes,
    timeout: float = 5.0,
    isolation_level: str | None = "DEFERRED",
    check_same_thread: bool = True,
    factory: type[Connection] = Connection,
    cached_statements: int = 100,
    uri: bool = False,
) -> Connection:
    """Create a connection to a SQLite database."""
    ...
