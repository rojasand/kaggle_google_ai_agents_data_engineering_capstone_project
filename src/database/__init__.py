"""Database module for DuckDB connection and data management."""

from src.database.connection import get_db_connection

__all__ = ["get_db_connection"]
