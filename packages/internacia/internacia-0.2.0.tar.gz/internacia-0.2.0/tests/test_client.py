"""Tests for main client."""

from unittest.mock import patch

import pytest

from internacia.client import InternaciaClient
from internacia.countries import CountriesClient
from internacia.intblocks import IntblocksClient
from internacia.search import SearchClient


def test_client_init_with_db_path(mock_db_path):
    """Test client initialization with explicit db_path."""
    client = InternaciaClient(db_path=mock_db_path)
    assert client._db_manager.db_path == mock_db_path
    assert client.countries is not None
    assert client.intblocks is not None
    assert client.search is not None


def test_client_init_with_env_var(mock_db_path, monkeypatch):
    """Test client initialization with environment variable."""
    monkeypatch.setenv("INTERNACIA_DB_PATH", str(mock_db_path))
    client = InternaciaClient()
    assert client._db_manager.db_path == mock_db_path


def test_client_init_env_var_not_found(monkeypatch):
    """Test client raises error when env var points to non-existent file."""
    monkeypatch.setenv("INTERNACIA_DB_PATH", "/nonexistent/path.duckdb")
    with pytest.raises(FileNotFoundError):
        InternaciaClient()


def test_client_init_no_db_found(tmp_path, monkeypatch):
    """Test client raises error when no database found."""
    # Remove env var if set
    monkeypatch.delenv("INTERNACIA_DB_PATH", raising=False)

    # Mock parent directory to not contain internacia-db
    with patch("internacia.client.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError) as exc_info:
            InternaciaClient()
        assert "Could not find" in str(exc_info.value)


def test_client_init_db_path_not_exists(mock_db_path):
    """Test client raises error when explicit db_path doesn't exist."""
    non_existent = mock_db_path.parent / "nonexistent.duckdb"
    with pytest.raises(FileNotFoundError) as exc_info:
        InternaciaClient(db_path=non_existent)
    assert "not found at specified path" in str(exc_info.value)


def test_client_init_with_data_dir(mock_db_path, tmp_path):
    """Test client initialization with data_dir parameter."""
    # data_dir is currently not used in the implementation, but we test it doesn't break
    client = InternaciaClient(db_path=mock_db_path, data_dir=tmp_path)
    assert client._db_manager.db_path == mock_db_path  # pylint: disable=protected-access
    assert client.countries is not None
    assert client.intblocks is not None
    assert client.search is not None


def test_client_attributes(mock_db_path):
    """Test that client has all expected attributes."""
    client = InternaciaClient(db_path=mock_db_path)

    assert hasattr(client, '_db_manager')
    assert hasattr(client, 'countries')
    assert hasattr(client, 'intblocks')
    assert hasattr(client, 'search')

    # Test that attributes are the correct types
    assert isinstance(client.countries, CountriesClient)
    assert isinstance(client.intblocks, IntblocksClient)
    assert isinstance(client.search, SearchClient)
