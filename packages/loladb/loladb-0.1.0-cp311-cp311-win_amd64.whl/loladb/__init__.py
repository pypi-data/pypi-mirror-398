"""
LolaDB Python Client

A fast embedded database written in Rust with Python bindings and Arrow Flight support.
"""

__version__ = "0.1.0"

from .loladb import start, from_parquet_files, PyTable
from .client import LolaDbClient

__all__ = ["start", "from_parquet_files", "PyTable", "LolaDbClient"]

