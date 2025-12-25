"""
Base repository class for shared SQLite connection handling.

Design Pattern: Repository Pattern
- Each repository is stateless (just wraps SQL queries)
- All repositories share a single SQLite connection (passed in constructor)
- Transactions are managed by the coordinator (SessionDatabase)
"""

import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base class for all domain repositories"""

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize repository with shared SQLite connection.

        Args:
            conn: SQLite connection (shared across all repositories)
        """
        self.conn = conn
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts

    def _execute(self, query: str, params: Optional[tuple] = None) -> sqlite3.Cursor:
        """
        Execute a SQL query with optional parameters.

        Args:
            query: SQL query string
            params: Optional tuple of query parameters

        Returns:
            Cursor object with results
        """
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def _execute_many(self, query: str, params_list: list) -> sqlite3.Cursor:
        """
        Execute a SQL query multiple times with different parameters.

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Cursor object
        """
        cursor = self.conn.cursor()
        cursor.executemany(query, params_list)
        return cursor

    def commit(self):
        """Commit the current transaction"""
        self.conn.commit()

    def rollback(self):
        """Rollback the current transaction"""
        self.conn.rollback()
