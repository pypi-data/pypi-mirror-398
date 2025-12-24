"""Thread-safe DuckDB connection manager for internacia SDK."""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

import duckdb

from internacia.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Thread-safe DuckDB connection manager.

    DuckDB read-only connections are thread-safe for concurrent reads.
    Each query gets its own connection which is closed after use.
    """

    def __init__(self, db_path: Path):
        """
        Initialize the database manager.

        Args:
            db_path: Path to the DuckDB database file

        Raises:
            DatabaseError: If the database file doesn't exist or cannot be accessed
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            logger.error("Database file not found: %s", self.db_path)
            raise DatabaseError(
                f"Database file not found: {self.db_path}. "
                "Please ensure the internacia-db dataset has been built."
            )
        logger.debug("DatabaseManager initialized with path: %s", self.db_path)

    @contextmanager
    def get_connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """
        Get a thread-safe read-only connection to DuckDB.

        Yields:
            DuckDB connection object

        Example:
            >>> with db_manager.get_connection() as conn:
            ...     result = conn.execute("SELECT * FROM countries LIMIT 1").fetchall()
        """
        conn = None
        try:
            # Connect in read-only mode for thread safety
            logger.debug("Opening database connection")
            conn = duckdb.connect(str(self.db_path), read_only=True)
            yield conn
        finally:
            if conn:
                logger.debug("Closing database connection")
                conn.close()

    def execute_query(
        self,
        query: str,
        parameters: Optional[tuple] = None
    ) -> list:
        """
        Execute a query and return results as a list of tuples.

        Args:
            query: SQL query string
            parameters: Query parameters (optional)

        Returns:
            List of result rows (tuples)

        Raises:
            DatabaseError: If the query execution fails
        """
        try:
            query_preview = query[:100] + "..." if len(query) > 100 else query
            logger.debug("Executing query: %s", query_preview)
            with self.get_connection() as conn:
                if parameters:
                    result = conn.execute(query, parameters).fetchall()
                else:
                    result = conn.execute(query).fetchall()
                logger.debug("Query returned %s rows", len(result))
                return result
        except Exception as e:
            logger.error("Query execution failed: %s", str(e))
            raise DatabaseError(f"Query execution failed: {str(e)}") from e

    def execute_query_dict(
        self,
        query: str,
        parameters: Optional[tuple] = None
    ) -> list[dict]:
        """
        Execute a query and return results as a list of dictionaries.

        Args:
            query: SQL query string
            parameters: Query parameters (optional)

        Returns:
            List of result rows (dictionaries with column names as keys)

        Raises:
            DatabaseError: If the query execution fails
        """
        try:
            query_preview = query[:100] + "..." if len(query) > 100 else query
            logger.debug("Executing query: %s", query_preview)
            with self.get_connection() as conn:
                if parameters:
                    result = conn.execute(query, parameters).fetchdf()
                else:
                    result = conn.execute(query).fetchdf()
                records = result.to_dict('records')
                logger.debug("Query returned %s rows", len(records))
                return records
        except Exception as e:
            logger.error("Query execution failed: %s", str(e))
            raise DatabaseError(f"Query execution failed: {str(e)}") from e
