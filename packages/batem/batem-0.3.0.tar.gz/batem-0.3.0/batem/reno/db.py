"""
Database operations for the reno package.

This module provides functions for interacting with the IRISE database,
including connection management, query execution, and schema inspection.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import List, Optional, Tuple, Any
from batem.reno.utils import FilePathBuilder

from batem.core import dataloader


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.

    This function provides a context manager for SQLite database connections,
    ensuring proper connection handling and cleanup.

    Yields:
        sqlite3.Connection: A connection to the IRISE database

    Example:
        >>> with get_db_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM some_table")
    """
    if not os.path.exists(FilePathBuilder().get_irise_db_path()):
        print("IRISE database not found, loading data...")
        dataloader.load_data("15499551")

    conn = sqlite3.connect(FilePathBuilder().get_irise_db_path())
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query: str, params: Optional[tuple] = None
                  ) -> List[Tuple[Any, ...]]:
    """
    Execute a query and return results.

    Args:
        query: SQL query string to execute
        params: Optional tuple of parameters for the query

    Returns:
        List[Tuple[Any, ...]]: Query results as a list of tuples

    Example:
        >>> results = execute_query("SELECT * FROM houses WHERE id = ?", (1,))
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        return cursor.fetchall()


def get_table_schema(table_name: str) -> List[Tuple[Any, ...]]:
    """
    Get the schema of a table.

    Args:
        table_name: Name of the table to inspect

    Returns:
        List[Tuple[Any, ...]]: List of tuples containing column information
            (cid, name, type, notnull, dflt_value, pk)

    Example:
        >>> schema = get_table_schema("houses")
        >>> for col_info in schema:
        ...     print(f"Column: {col_info[1]}, Type: {col_info[2]}")
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return cursor.fetchall()


def print_table_schema(table_name: str):
    """
    Print the schema of a table in a human-readable format.

    Args:
        table_name: Name of the table to inspect

    Example:
        >>> print_table_schema("houses")
        houses table schema:
        Column: id, Type: INTEGER
        Column: name, Type: TEXT
        ...
    """
    schema = get_table_schema(table_name)
    print(f"{table_name} table schema:")
    for column in schema:
        print(f"Column: {column[1]}, Type: {column[2]}")
