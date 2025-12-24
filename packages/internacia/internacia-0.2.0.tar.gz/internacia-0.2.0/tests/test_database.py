"""Tests for database manager."""

from unittest.mock import MagicMock, patch

import pytest

from internacia.database import DatabaseManager
from internacia.exceptions import DatabaseError


def test_database_manager_init_file_not_found(tmp_path):
    """Test database manager raises error when file doesn't exist."""
    non_existent = tmp_path / "nonexistent.duckdb"
    with pytest.raises(DatabaseError) as exc_info:
        DatabaseManager(non_existent)
    assert "not found" in str(exc_info.value).lower()


def test_database_manager_init_success(mock_db_path):
    """Test database manager initialization with valid path."""
    manager = DatabaseManager(mock_db_path)
    assert manager.db_path == mock_db_path


def test_database_manager_get_connection(mock_db_path):
    """Test database connection context manager."""
    with patch('internacia.database.duckdb') as mock_duckdb:
        mock_conn = MagicMock()
        mock_duckdb.connect.return_value = mock_conn

        manager = DatabaseManager(mock_db_path)
        with manager.get_connection() as conn:
            assert conn == mock_conn
            # Connection should be closed after context exits
        # Connection should be closed now
        mock_conn.close.assert_called_once()
        mock_duckdb.connect.assert_called_once_with(str(mock_db_path), read_only=True)
