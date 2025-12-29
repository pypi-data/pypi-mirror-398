"""Type hints for sqlean.extensions - Extension management."""

from typing import Literal

# Available extensions
_ExtensionName = Literal[
    "crypto",
    "define",
    "fileio",
    "fuzzy",
    "ipaddr",
    "regexp",
    "stats",
    "text",
    "time",
    "unicode",
    "uuid",
    "vsv",
]

def enable_all() -> None:
    """Enable all available extensions."""
    ...

def disable_all() -> None:
    """Disable all extensions."""
    ...

def enable(*names: _ExtensionName) -> None:
    """Enable specific extensions.

    Args:
        *names: Extension names to enable
            - 'crypto': Hashing, encoding and decoding data
            - 'define': User-defined functions and dynamic SQL
            - 'fileio': Reading and writing files
            - 'fuzzy': Fuzzy string matching and phonetics
            - 'ipaddr': IP address manipulation
            - 'regexp': Regular expressions
            - 'stats': Math statistics
            - 'text': String functions
            - 'time': High-precision date/time
            - 'unicode': Unicode utilities
            - 'uuid': Universally Unique IDentifiers
            - 'vsv': CSV files as virtual tables
    """
    ...

def disable(*names: _ExtensionName) -> None:
    """Disable specific extensions.

    Args:
        *names: Extension names to disable
    """
    ...
