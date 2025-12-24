"""Extended tests for database manager."""

from unittest.mock import MagicMock, patch

import pytest

from internacia.database import DatabaseManager
from internacia.exceptions import DatabaseError


class TestDatabaseManagerExecuteQuery:
    """Test execute_query method."""

    def test_execute_query_without_parameters(self, mock_db_path):
        """Test execute_query without parameters."""
        # Create a real DuckDB connection for this test
        with patch('internacia.database.duckdb') as mock_duckdb:
            mock_conn = MagicMock()
            mock_conn.execute.return_value.fetchall.return_value = [("US", "United States")]
            mock_duckdb.connect.return_value = mock_conn

            manager = DatabaseManager(mock_db_path)
            result = manager.execute_query("SELECT code, name FROM countries LIMIT 1")

            assert result == [("US", "United States")]
            mock_conn.execute.assert_called_once_with("SELECT code, name FROM countries LIMIT 1")
            mock_conn.close.assert_called_once()

    def test_execute_query_with_parameters(self, mock_db_path):
        """Test execute_query with parameters."""
        with patch('internacia.database.duckdb') as mock_duckdb:
            mock_conn = MagicMock()
            mock_conn.execute.return_value.fetchall.return_value = [("US",)]
            mock_duckdb.connect.return_value = mock_conn

            manager = DatabaseManager(mock_db_path)
            result = manager.execute_query("SELECT code FROM countries WHERE code = ?", ("US",))

            assert result == [("US",)]
            mock_conn.execute.assert_called_once_with("SELECT code FROM countries WHERE code = ?", ("US",))

    def test_execute_query_error_handling(self, mock_db_path):
        """Test execute_query error handling."""
        with patch('internacia.database.duckdb') as mock_duckdb:
            mock_conn = MagicMock()
            mock_conn.execute.side_effect = Exception("SQL syntax error")
            mock_duckdb.connect.return_value = mock_conn

            manager = DatabaseManager(mock_db_path)

            with pytest.raises(DatabaseError) as exc_info:
                manager.execute_query("INVALID SQL")

            assert "Query execution failed" in str(exc_info.value)
            mock_conn.close.assert_called_once()


class TestDatabaseManagerExecuteQueryDict:
    """Test execute_query_dict method."""

    def test_execute_query_dict_without_parameters(self, mock_db_path):
        """Test execute_query_dict without parameters."""
        with patch('internacia.database.duckdb') as mock_duckdb:
            import pandas as pd
            mock_conn = MagicMock()
            mock_df = pd.DataFrame({"code": ["US"], "name": ["United States"]})
            mock_conn.execute.return_value.fetchdf.return_value = mock_df
            mock_duckdb.connect.return_value = mock_conn

            manager = DatabaseManager(mock_db_path)
            result = manager.execute_query_dict("SELECT code, name FROM countries LIMIT 1")

            assert len(result) == 1
            assert result[0]["code"] == "US"
            assert result[0]["name"] == "United States"
            mock_conn.execute.assert_called_once()
            mock_conn.close.assert_called_once()

    def test_execute_query_dict_with_parameters(self, mock_db_path):
        """Test execute_query_dict with parameters."""
        with patch('internacia.database.duckdb') as mock_duckdb:
            import pandas as pd
            mock_conn = MagicMock()
            mock_df = pd.DataFrame({"code": ["US"]})
            mock_conn.execute.return_value.fetchdf.return_value = mock_df
            mock_duckdb.connect.return_value = mock_conn

            manager = DatabaseManager(mock_db_path)
            result = manager.execute_query_dict("SELECT code FROM countries WHERE code = ?", ("US",))

            assert len(result) == 1
            assert result[0]["code"] == "US"
            mock_conn.execute.assert_called_once_with("SELECT code FROM countries WHERE code = ?", ("US",))

    def test_execute_query_dict_error_handling(self, mock_db_path):
        """Test execute_query_dict error handling."""
        with patch('internacia.database.duckdb') as mock_duckdb:
            mock_conn = MagicMock()
            mock_conn.execute.side_effect = Exception("SQL syntax error")
            mock_duckdb.connect.return_value = mock_conn

            manager = DatabaseManager(mock_db_path)

            with pytest.raises(DatabaseError) as exc_info:
                manager.execute_query_dict("INVALID SQL")

            assert "Query execution failed" in str(exc_info.value)
            mock_conn.close.assert_called_once()

    def test_execute_query_dict_empty_result(self, mock_db_path):
        """Test execute_query_dict with empty result."""
        with patch('internacia.database.duckdb') as mock_duckdb:
            import pandas as pd
            mock_conn = MagicMock()
            mock_df = pd.DataFrame()
            mock_conn.execute.return_value.fetchdf.return_value = mock_df
            mock_duckdb.connect.return_value = mock_conn

            manager = DatabaseManager(mock_db_path)
            result = manager.execute_query_dict("SELECT * FROM countries WHERE code = 'XX'")

            assert not result


class TestDatabaseManagerConnection:
    """Test connection management."""

    def test_get_connection_read_only(self, mock_db_path):
        """Test that connections are opened in read-only mode."""
        with patch('internacia.database.duckdb') as mock_duckdb:
            mock_conn = MagicMock()
            mock_duckdb.connect.return_value = mock_conn

            manager = DatabaseManager(mock_db_path)
            with manager.get_connection() as conn:
                assert conn == mock_conn

            mock_duckdb.connect.assert_called_once_with(str(mock_db_path), read_only=True)
            mock_conn.close.assert_called_once()

    def test_get_connection_closes_on_exception(self, mock_db_path):
        """Test that connection is closed even if exception occurs."""
        with patch('internacia.database.duckdb') as mock_duckdb:
            mock_conn = MagicMock()
            mock_conn.execute.side_effect = Exception("Test error")
            mock_duckdb.connect.return_value = mock_conn

            manager = DatabaseManager(mock_db_path)

            try:
                with manager.get_connection() as conn:
                    conn.execute("SELECT * FROM test")
            except Exception:
                pass

            mock_conn.close.assert_called_once()

    def test_get_connection_handles_connection_failure(self, mock_db_path):
        """Test handling of connection failure."""
        with patch('internacia.database.duckdb') as mock_duckdb:
            mock_duckdb.connect.side_effect = Exception("Connection failed")

            manager = DatabaseManager(mock_db_path)

            with pytest.raises(Exception):
                with manager.get_connection():
                    pass
