"""
Database Interface for Clinical Trials Information.

This module provides a database interface for querying clinical trials data
from the SQLite database.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pandas as pd

from aixtools.logging.logging_config import get_logger

logger = get_logger(__name__)


class DatabaseError(Exception):
    """Exception raised for database-related errors."""


class SqliteDb:
    """
    Database interface.
    """

    def __init__(self, db_path: str | Path):
        """Initialize the database interface"""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        # Test connection
        with self.connection() as conn:
            logger.info("Connected to database: %s, connection: %s", self.db_path, conn)

    @contextmanager
    def connection(self):
        """
        Context manager for database connections.

        Yields:
            sqlite3.Connection: An active database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            # Enable dictionary row factory
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            raise DatabaseError(f"Database error: {e}") from e
        finally:
            if conn:
                conn.close()

    def query(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        Execute a SQL query and return the results as a list of dictionaries.

        Args:
            query: SQL query to execute
            params: Parameters for the query

        Returns:
            List of dictionaries representing the query results
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            results = cursor.fetchall()
            # Convert sqlite3.Row objects to dictionaries
            return [dict(row) for row in results]

    def query_df(self, query: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
        """
        Execute a SQL query and return the results as a pandas DataFrame.

        Args:
            query: SQL query to execute.
            params: Parameters to substitute in the query.

        Returns:
            A pandas DataFrame containing the query results.
        """
        with self.connection() as conn:
            if params:
                df = pd.read_sql_query(query, conn, params=params)
            else:
                df = pd.read_sql_query(query, conn)
            return df

    def validate(self, query) -> str | None:
        """
        Validate the SQL query by executing an EXPLAIN QUERY PLAN statement.
        Returns the error string if there is an issue, otherwise returns None
        """
        with self.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(f"EXPLAIN QUERY PLAN\n{query}")
                cursor.fetchall()
                return None
            except Exception as e:  # pylint: disable=broad-exception-caught
                return str(e)
