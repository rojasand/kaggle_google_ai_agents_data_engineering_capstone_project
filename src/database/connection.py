"""DuckDB connection manager."""

from collections.abc import Generator
from contextlib import contextmanager

import duckdb

from src.config import settings


@contextmanager
def get_db_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    Create a context-managed DuckDB connection.

    Yields:
        DuckDB connection object

    Example:
        >>> with get_db_connection() as conn:
        ...     result = conn.execute("SELECT * FROM customers").fetchall()
    """
    # Ensure the database directory exists
    settings.ensure_directories()

    # Connect to the database
    conn = duckdb.connect(str(settings.database_file))

    try:
        yield conn
    finally:
        conn.close()


def execute_query(query: str, params: tuple = ()) -> list:
    """
    Execute a SQL query and return results.

    Args:
        query: SQL query string
        params: Query parameters (optional)

    Returns:
        List of result rows

    Example:
        >>> results = execute_query("SELECT * FROM customers WHERE customer_id = ?", (1,))
    """
    with get_db_connection() as conn:
        return conn.execute(query, params).fetchall()


def execute_script(script: str) -> None:
    """
    Execute a SQL script (multiple statements).

    Args:
        script: SQL script with multiple statements

    Example:
        >>> execute_script('''
        ...     CREATE TABLE test (id INTEGER);
        ...     INSERT INTO test VALUES (1);
        ... ''')
    """
    with get_db_connection() as conn:
        conn.executemany(script)
