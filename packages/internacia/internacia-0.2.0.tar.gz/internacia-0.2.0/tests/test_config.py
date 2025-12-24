"""Tests for Config class."""

import logging
from pathlib import Path
from unittest.mock import patch
from internacia.config import Config


class TestConfigGetDbPath:
    """Test get_db_path method."""

    def test_get_db_path_explicit(self):
        """Test with explicit path."""
        explicit_path = Path("/explicit/path/db.duckdb")
        result = Config.get_db_path(explicit_path=explicit_path)
        assert result == explicit_path

    def test_get_db_path_env_var(self, monkeypatch):
        """Test with environment variable."""
        env_path = "/env/path/db.duckdb"
        monkeypatch.setenv("INTERNACIA_DB_PATH", env_path)
        result = Config.get_db_path()
        assert result == Path(env_path)

    def test_get_db_path_default_exists(self, monkeypatch):
        """Test with default path when it exists."""
        monkeypatch.delenv("INTERNACIA_DB_PATH", raising=False)

        with patch('internacia.config.Path.exists', return_value=True):
            with patch('internacia.config.Path.__init__', return_value=None):
                with patch('internacia.config.Path.parent') as mock_parent:
                    mock_parent.__truediv__ = lambda self, other: Path(f"/default/path/{other}")
                    result = Config.get_db_path()
                    # The exact path depends on the file location, but should not be None
                    assert result is not None

    def test_get_db_path_not_found(self, monkeypatch):
        """Test when no path is found."""
        monkeypatch.delenv("INTERNACIA_DB_PATH", raising=False)

        with patch('internacia.config.Path.exists', return_value=False):
            result = Config.get_db_path()
            assert result is None


class TestConfigGetLogLevel:
    """Test get_log_level method."""

    def test_get_log_level_default(self, monkeypatch):
        """Test default log level."""
        monkeypatch.delenv("INTERNACIA_LOG_LEVEL", raising=False)
        result = Config.get_log_level()
        assert result == logging.WARNING

    def test_get_log_level_debug(self, monkeypatch):
        """Test DEBUG log level."""
        monkeypatch.setenv("INTERNACIA_LOG_LEVEL", "DEBUG")
        result = Config.get_log_level()
        assert result == logging.DEBUG

    def test_get_log_level_info(self, monkeypatch):
        """Test INFO log level."""
        monkeypatch.setenv("INTERNACIA_LOG_LEVEL", "INFO")
        result = Config.get_log_level()
        assert result == logging.INFO

    def test_get_log_level_warning(self, monkeypatch):
        """Test WARNING log level."""
        monkeypatch.setenv("INTERNACIA_LOG_LEVEL", "WARNING")
        result = Config.get_log_level()
        assert result == logging.WARNING

    def test_get_log_level_error(self, monkeypatch):
        """Test ERROR log level."""
        monkeypatch.setenv("INTERNACIA_LOG_LEVEL", "ERROR")
        result = Config.get_log_level()
        assert result == logging.ERROR

    def test_get_log_level_critical(self, monkeypatch):
        """Test CRITICAL log level."""
        monkeypatch.setenv("INTERNACIA_LOG_LEVEL", "CRITICAL")
        result = Config.get_log_level()
        assert result == logging.CRITICAL

    def test_get_log_level_invalid(self, monkeypatch):
        """Test invalid log level falls back to default."""
        monkeypatch.setenv("INTERNACIA_LOG_LEVEL", "INVALID")
        result = Config.get_log_level()
        assert result == logging.WARNING

    def test_get_log_level_case_insensitive(self, monkeypatch):
        """Test that log level is case insensitive."""
        monkeypatch.setenv("INTERNACIA_LOG_LEVEL", "debug")
        result = Config.get_log_level()
        assert result == logging.DEBUG


class TestConfigSetupLogging:
    """Test setup_logging method."""

    def test_setup_logging_creates_handler(self):
        """Test that setup_logging creates a handler."""
        logger = Config.setup_logging("test_logger")
        assert logger is not None
        assert len(logger.handlers) > 0

    def test_setup_logging_does_not_duplicate_handlers(self):
        """Test that setup_logging doesn't duplicate handlers."""
        logger1 = Config.setup_logging("test_logger_2")
        handler_count_1 = len(logger1.handlers)

        logger2 = Config.setup_logging("test_logger_2")
        handler_count_2 = len(logger2.handlers)

        # Should not add duplicate handlers
        assert handler_count_1 == handler_count_2

    def test_setup_logging_sets_level(self, monkeypatch):
        """Test that setup_logging sets the log level."""
        monkeypatch.setenv("INTERNACIA_LOG_LEVEL", "DEBUG")
        logger = Config.setup_logging("test_logger_3")
        assert logger.level == logging.DEBUG

    def test_setup_logging_formatter(self):
        """Test that setup_logging sets a formatter."""
        logger = Config.setup_logging("test_logger_4")
        handler = logger.handlers[0]
        assert handler.formatter is not None
