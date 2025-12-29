# sqlean-stubs

Type hints for [sqlean.py](https://github.com/nalgeon/sqlean.py) - Python's sqlite3 + extensions.

## Installation

```bash
pip install sqlean-stubs
```

or with uv:

```bash
uv add sqlean-stubs
```

## Usage

Type hints enable IDE autocomplete and type checking for sqlean code:

```python
import sqlean

conn: sqlean.Connection = sqlean.connect(":memory:")
cursor = conn.cursor()

# Type hints work with parameters
cursor.execute("SELECT * FROM users WHERE id = ?", (1,))

# fetchone() returns Optional[Any]
row = cursor.fetchone()
if row is not None:
    print(row[0])  # Type-safe indexing

# User-defined functions
def double(x: int) -> int:
    return x * 2

conn.create_function("double", 1, double)
conn.close()
```

**Benefits:**
- IDE autocomplete and navigation
- Catch type errors before runtime with mypy or ty
- Better code documentation and refactoring safety

## Features

- Complete type hints for Connection, Cursor, and Row objects
- Support for custom factories and row factories
- Type hints for user-defined functions and aggregates
- Callbacks support (authorizer, progress handler, trace callback, busy handler)
- Window function support
- Extensions management API
- Compatible with mypy, ty, pyright, and other type checkers

## Requirements

- Python 3.9 or later
- pip, uv, or pipx for installation

---

## Contributing

### Development Setup

```bash
git clone https://github.com/nalgeon/sqlean-stubs.git
cd sqlean-stubs
uv sync
```

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Linting
uv run ruff check .

# Type checking
uv run mypy tests/test_mypy.py
uv run ty check

# Test multiple Python versions (3.9-3.14)
uv run tox
```

### Project Structure

- `sqlean/dbapi2.pyi` - Main DB-API 2.0 interface
- `sqlean/extensions.pyi` - Extension management API
- `sqlean/py.typed` - PEP 561 marker file
- `tests/test_types.py` - Runtime tests
- `tests/test_mypy.py` - Type checking tests

### Adding Type Hints

1. Update the `.pyi` stub file
2. Add runtime test in `tests/test_types.py`
3. Add type checking test in `tests/test_mypy.py`
4. Run `pytest tests/`, `mypy tests/test_mypy.py`, and `ty check`

### Code Style

- Follow PEP 484 for type hints
- Use `Optional[X]` instead of `X | None` (Python 3.9 compatibility)
- Use `Literal` types for constrained values
- Include docstrings for complex types

### Before Submitting

```bash
uv run ruff check .
uv run pytest tests/ -v
uv run mypy tests/test_mypy.py
uv run ty check
```

## License

Zlib (same as sqlean.py)
