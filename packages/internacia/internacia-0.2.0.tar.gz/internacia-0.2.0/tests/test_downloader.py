"""Tests for downloader module."""

from unittest.mock import Mock, patch

import pytest
import requests

from internacia.downloader import (
    get_cache_dir,
    get_cached_database_path,
    get_latest_version,
    get_database_info,
    download_database,
    check_for_updates,
)
from internacia.exceptions import DownloadError, VersionError


class TestGetCacheDir:
    """Test get_cache_dir function."""

    def test_get_cache_dir_env_var(self, tmp_path, monkeypatch):
        """Test cache dir from environment variable."""
        cache_path = tmp_path / "custom_cache"
        monkeypatch.setenv("INTERNACIA_CACHE_DIR", str(cache_path))

        result = get_cache_dir()
        assert result == cache_path
        assert result.exists()

    def test_get_cache_dir_default(self, tmp_path, monkeypatch):
        """Test default cache directory."""
        monkeypatch.delenv("INTERNACIA_CACHE_DIR", raising=False)

        # Use tmp_path as home directory
        fake_home = tmp_path / "home" / "test"
        fake_home.mkdir(parents=True)

        with patch("internacia.downloader.Path.home") as mock_home:
            mock_home.return_value = fake_home
            result = get_cache_dir()
            assert result == fake_home / ".internacia"
            assert result.exists()

    def test_get_cache_dir_creates_directory(self, tmp_path, monkeypatch):
        """Test that cache directory is created if it doesn't exist."""
        cache_path = tmp_path / "new_cache"
        monkeypatch.setenv("INTERNACIA_CACHE_DIR", str(cache_path))

        assert not cache_path.exists()
        result = get_cache_dir()
        assert result.exists()


class TestGetCachedDatabasePath:
    """Test get_cached_database_path function."""

    def test_get_cached_database_path_no_version(self, tmp_path, monkeypatch):
        """Test cached path without version."""
        monkeypatch.delenv("INTERNACIA_CACHE_DIR", raising=False)

        # Use tmp_path as home directory
        fake_home = tmp_path / "home" / "test"
        fake_home.mkdir(parents=True)

        with patch("internacia.downloader.Path.home") as mock_home:
            mock_home.return_value = fake_home
            result = get_cached_database_path()
            assert result == fake_home / ".internacia" / "internacia.duckdb"
            assert result.parent.exists()

    def test_get_cached_database_path_with_version(self, tmp_path, monkeypatch):
        """Test cached path with version."""
        monkeypatch.delenv("INTERNACIA_CACHE_DIR", raising=False)

        # Use tmp_path as home directory
        fake_home = tmp_path / "home" / "test"
        fake_home.mkdir(parents=True)

        with patch("internacia.downloader.Path.home") as mock_home:
            mock_home.return_value = fake_home
            result = get_cached_database_path(version="v1.0.0")
            assert result == fake_home / ".internacia" / "v1.0.0" / "internacia.duckdb"
            assert result.parent.exists()

    def test_get_cached_database_path_creates_version_dir(self, tmp_path, monkeypatch):
        """Test that version directory is created."""
        cache_path = tmp_path / "cache"
        monkeypatch.setenv("INTERNACIA_CACHE_DIR", str(cache_path))

        result = get_cached_database_path(version="v1.0.0")
        assert result.parent.exists()
        assert result.parent.name == "v1.0.0"


class TestGetLatestVersion:
    """Test get_latest_version function."""

    def test_get_latest_version_success(self):
        """Test successful version fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {"tag_name": "v1.0.0"}
        mock_response.raise_for_status = Mock()

        with patch("internacia.downloader.requests.get", return_value=mock_response):
            result = get_latest_version()
            assert result == "v1.0.0"

    def test_get_latest_version_no_tag(self):
        """Test version fetch with no tag_name."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()

        with patch("internacia.downloader.requests.get", return_value=mock_response):
            with pytest.raises(VersionError, match="No version tag"):
                get_latest_version()

    def test_get_latest_version_network_error(self):
        """Test network error handling."""
        with patch("internacia.downloader.requests.get", side_effect=requests.exceptions.RequestException("Network error")):
            with pytest.raises(DownloadError, match="Failed to fetch latest version"):
                get_latest_version()

    def test_get_latest_version_http_error(self):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")

        with patch("internacia.downloader.requests.get", return_value=mock_response):
            with pytest.raises(DownloadError):
                get_latest_version()


class TestGetDatabaseInfo:
    """Test get_database_info function."""

    def test_get_database_info_latest(self):
        """Test getting latest database info."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "tag_name": "v1.0.0",
            "assets": [
                {
                    "name": "internacia.duckdb",
                    "size": 1024000,
                    "browser_download_url": "https://github.com/releases/download/v1.0.0/internacia.duckdb",
                    "content_type": "application/octet-stream",
                }
            ],
            "published_at": "2024-01-01T00:00:00Z",
        }
        mock_response.raise_for_status = Mock()

        with patch("internacia.downloader.requests.get", return_value=mock_response):
            result = get_database_info()
            assert result["version"] == "v1.0.0"
            assert result["name"] == "internacia.duckdb"
            assert result["size"] == 1024000
            assert "download_url" in result

    def test_get_database_info_specific_version(self):
        """Test getting specific version info."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "tag_name": "v1.0.0",
            "assets": [
                {
                    "name": "internacia.duckdb",
                    "size": 1024000,
                    "browser_download_url": "https://github.com/releases/download/v1.0.0/internacia.duckdb",
                    "content_type": "application/octet-stream",
                }
            ],
            "published_at": "2024-01-01T00:00:00Z",
        }
        mock_response.raise_for_status = Mock()

        with patch("internacia.downloader.requests.get", return_value=mock_response):
            result = get_database_info(version="v1.0.0")
            assert result["version"] == "v1.0.0"

    def test_get_database_info_no_asset(self):
        """Test when no database asset is found."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "tag_name": "v1.0.0",
            "assets": [],
        }
        mock_response.raise_for_status = Mock()

        with patch("internacia.downloader.requests.get", return_value=mock_response):
            with pytest.raises(VersionError, match="No database file found"):
                get_database_info()

    def test_get_database_info_network_error(self):
        """Test network error handling."""
        with patch("internacia.downloader.requests.get", side_effect=requests.exceptions.RequestException("Network error")):
            with pytest.raises(DownloadError):
                get_database_info()


class TestDownloadDatabase:
    """Test download_database function."""

    def test_download_database_success(self, tmp_path, monkeypatch):
        """Test successful database download."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        monkeypatch.setenv("INTERNACIA_CACHE_DIR", str(cache_dir))

        # Mock GitHub API responses
        latest_response = Mock()
        latest_response.json.return_value = {"tag_name": "v1.0.0"}
        latest_response.raise_for_status = Mock()

        release_response = Mock()
        release_response.json.return_value = {
            "tag_name": "v1.0.0",
            "assets": [
                {
                    "name": "internacia.duckdb",
                    "size": 1024,
                    "browser_download_url": "https://example.com/db.duckdb",
                }
            ],
        }
        release_response.raise_for_status = Mock()

        # Mock download response
        download_response = Mock()
        download_response.iter_content.return_value = [b"fake database content"]
        download_response.headers = {"content-length": "1024"}
        download_response.raise_for_status = Mock()

        # Create a temporary file to simulate the download
        temp_file = tmp_path / "temp.duckdb.tmp"
        temp_file.write_bytes(b"fake database content")

        with patch("internacia.downloader.requests.get") as mock_get:
            mock_get.side_effect = [latest_response, release_response, download_response]
            with patch("internacia.downloader._download_file") as mock_download:
                # Make _download_file write to the temp file
                def write_temp_file(url, dest, **kwargs):
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(b"fake database content")
                mock_download.side_effect = write_temp_file
                result = download_database()
                assert result.exists()
                assert result.stat().st_size > 0

    def test_download_database_already_cached(self, tmp_path, monkeypatch):
        """Test download when database already cached."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        # When version is None, the function gets latest version and uses it for cache path
        # So we need to create the file at the versioned path
        version_dir = cache_dir / "v1.0.0"
        version_dir.mkdir()
        cached_file = version_dir / "internacia.duckdb"
        cached_file.write_bytes(b"existing database")
        monkeypatch.setenv("INTERNACIA_CACHE_DIR", str(cache_dir))

        # Mock GitHub API - need to mock both get_latest_version and get_database_info
        latest_response = Mock()
        latest_response.json.return_value = {"tag_name": "v1.0.0"}
        latest_response.raise_for_status = Mock()

        release_response = Mock()
        release_response.json.return_value = {
            "tag_name": "v1.0.0",
            "assets": [
                {
                    "name": "internacia.duckdb",
                    "size": 1024,
                    "browser_download_url": "https://example.com/db.duckdb",
                }
            ],
        }
        release_response.raise_for_status = Mock()

        with patch("internacia.downloader.requests.get") as mock_get:
            mock_get.side_effect = [latest_response, release_response]
            result = download_database()
            assert result == cached_file

    def test_download_database_force_redownload(self, tmp_path, monkeypatch):
        """Test force re-download."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cached_file = cache_dir / "internacia.duckdb"
        cached_file.write_bytes(b"old database")
        monkeypatch.setenv("INTERNACIA_CACHE_DIR", str(cache_dir))

        # Mock responses
        latest_response = Mock()
        latest_response.json.return_value = {"tag_name": "v1.0.0"}
        latest_response.raise_for_status = Mock()

        release_response = Mock()
        release_response.json.return_value = {
            "tag_name": "v1.0.0",
            "assets": [
                {
                    "name": "internacia.duckdb",
                    "size": 1024,
                    "browser_download_url": "https://example.com/db.duckdb",
                }
            ],
        }
        release_response.raise_for_status = Mock()

        download_response = Mock()
        download_response.iter_content.return_value = [b"new database content"]
        download_response.headers = {"content-length": "1024"}
        download_response.raise_for_status = Mock()

        with patch("internacia.downloader.requests.get") as mock_get:
            mock_get.side_effect = [latest_response, release_response, download_response]
            with patch("internacia.downloader._download_file") as mock_download:
                # Make _download_file write to the temp file
                def write_temp_file(url, dest, **kwargs):
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(b"new database content")
                mock_download.side_effect = write_temp_file
                result = download_database(force=True)
                # Should have attempted download
                assert mock_get.call_count >= 2
                assert result.exists()
                assert result.stat().st_size > 0

    def test_download_database_specific_version(self, tmp_path, monkeypatch):
        """Test downloading specific version."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        monkeypatch.setenv("INTERNACIA_CACHE_DIR", str(cache_dir))

        release_response = Mock()
        release_response.json.return_value = {
            "tag_name": "v1.0.0",
            "assets": [
                {
                    "name": "internacia.duckdb",
                    "size": 1024,
                    "browser_download_url": "https://example.com/db.duckdb",
                }
            ],
        }
        release_response.raise_for_status = Mock()

        download_response = Mock()
        download_response.iter_content.return_value = [b"database content"]
        download_response.headers = {"content-length": "1024"}
        download_response.raise_for_status = Mock()

        with patch("internacia.downloader.requests.get") as mock_get:
            mock_get.side_effect = [release_response, download_response]
            with patch("internacia.downloader._download_file") as mock_download:
                # Make _download_file write to the temp file
                def write_temp_file(url, dest, **kwargs):
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(b"database content")
                mock_download.side_effect = write_temp_file
                result = download_database(version="v1.0.0")
                # Should use version-specific URL
                assert any("tags/v1.0.0" in str(call) for call in mock_get.call_args_list)
                assert result.exists()
                assert result.stat().st_size > 0

    def test_download_database_no_download_url(self, tmp_path, monkeypatch):
        """Test error when no download URL."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        monkeypatch.setenv("INTERNACIA_CACHE_DIR", str(cache_dir))

        latest_response = Mock()
        latest_response.json.return_value = {"tag_name": "v1.0.0"}
        latest_response.raise_for_status = Mock()

        release_response = Mock()
        release_response.json.return_value = {
            "tag_name": "v1.0.0",
            "assets": [
                {
                    "name": "internacia.duckdb",
                    "size": 1024,
                    # Missing browser_download_url
                }
            ],
        }
        release_response.raise_for_status = Mock()

        with patch("internacia.downloader.requests.get") as mock_get:
            mock_get.side_effect = [latest_response, release_response]
            with pytest.raises(DownloadError, match="No download URL"):
                download_database()

    def test_download_database_network_error(self, tmp_path, monkeypatch):
        """Test network error during download."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        monkeypatch.setenv("INTERNACIA_CACHE_DIR", str(cache_dir))

        latest_response = Mock()
        latest_response.json.return_value = {"tag_name": "v1.0.0"}
        latest_response.raise_for_status = Mock()

        release_response = Mock()
        release_response.json.return_value = {
            "tag_name": "v1.0.0",
            "assets": [
                {
                    "name": "internacia.duckdb",
                    "size": 1024,
                    "browser_download_url": "https://example.com/db.duckdb",
                }
            ],
        }
        release_response.raise_for_status = Mock()

        with patch("internacia.downloader.requests.get") as mock_get:
            mock_get.side_effect = [
                latest_response,
                release_response,
                requests.exceptions.RequestException("Network error"),
            ]
            with pytest.raises(DownloadError):
                download_database()


class TestCheckForUpdates:
    """Test check_for_updates function."""

    def test_check_for_updates_success(self, tmp_path, monkeypatch):
        """Test successful update check."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        monkeypatch.setenv("INTERNACIA_CACHE_DIR", str(cache_dir))

        latest_response = Mock()
        latest_response.json.return_value = {"tag_name": "v1.0.0"}
        latest_response.raise_for_status = Mock()

        release_response = Mock()
        release_response.json.return_value = {
            "tag_name": "v1.0.0",
            "assets": [
                {
                    "name": "internacia.duckdb",
                    "size": 1024,
                    "browser_download_url": "https://example.com/db.duckdb",
                }
            ],
            "published_at": "2024-01-01T00:00:00Z",
        }
        release_response.raise_for_status = Mock()

        with patch("internacia.downloader.requests.get") as mock_get:
            mock_get.side_effect = [latest_response, release_response]
            result = check_for_updates()
            assert "has_update" in result
            assert "latest_version" in result
            assert result["latest_version"] == "v1.0.0"

    def test_check_for_updates_with_cached_db(self, tmp_path, monkeypatch):
        """Test update check when database is cached."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cached_file = cache_dir / "internacia.duckdb"
        cached_file.write_bytes(b"database content")
        monkeypatch.setenv("INTERNACIA_CACHE_DIR", str(cache_dir))

        latest_response = Mock()
        latest_response.json.return_value = {"tag_name": "v1.0.0"}
        latest_response.raise_for_status = Mock()

        release_response = Mock()
        release_response.json.return_value = {
            "tag_name": "v1.0.0",
            "assets": [
                {
                    "name": "internacia.duckdb",
                    "size": 1024,
                    "browser_download_url": "https://example.com/db.duckdb",
                }
            ],
            "published_at": "2024-01-01T00:00:00Z",
        }
        release_response.raise_for_status = Mock()

        with patch("internacia.downloader.requests.get") as mock_get:
            mock_get.side_effect = [latest_response, release_response]
            result = check_for_updates()
            assert result["current_path"] == cached_file

    def test_check_for_updates_network_error(self):
        """Test network error during update check."""
        with patch("internacia.downloader.requests.get", side_effect=requests.exceptions.RequestException("Network error")):
            with pytest.raises(DownloadError):
                check_for_updates()
