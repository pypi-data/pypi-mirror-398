"""Configuration management for internacia SDK."""

import os
import logging
from pathlib import Path
from typing import Optional


class Config:
    """Configuration for internacia SDK."""

    # Default database path (relative to internacia-db sibling)
    DEFAULT_DB_RELATIVE_PATH = Path("internacia-db") / "data" / "datasets" / "internacia.duckdb"

    # Environment variable names
    ENV_DB_PATH = "INTERNACIA_DB_PATH"
    ENV_LOG_LEVEL = "INTERNACIA_LOG_LEVEL"
    ENV_CACHE_DIR = "INTERNACIA_CACHE_DIR"

    # Default values
    DEFAULT_LOG_LEVEL = logging.WARNING

    @classmethod
    def get_db_path(cls, explicit_path: Optional[Path] = None) -> Optional[Path]:
        """
        Get database path from various sources.

        Priority:
        1. Explicit path parameter
        2. INTERNACIA_DB_PATH environment variable
        3. Default relative path
        4. Cached database (from downloader)

        Args:
            explicit_path: Explicitly provided database path

        Returns:
            Path to database file, or None if not found
        """
        if explicit_path:
            return Path(explicit_path)

        # Check environment variable
        env_path = os.getenv(cls.ENV_DB_PATH)
        if env_path:
            return Path(env_path)

        # Try default relative path
        current_dir = Path(__file__).parent.parent.parent
        default_path = current_dir.parent / cls.DEFAULT_DB_RELATIVE_PATH
        if default_path.exists():
            return default_path

        # Try cached database (lazy import to avoid circular dependency)
        try:
            from internacia.downloader import get_cached_database_path  # pylint: disable=import-outside-toplevel
            cached_path = get_cached_database_path()
            if cached_path.exists():
                return cached_path
        except Exception:  # pylint: disable=broad-exception-caught
            # If downloader not available or error, continue
            pass

        return None

    @classmethod
    def get_log_level(cls) -> int:
        """
        Get log level from environment variable or default.

        Returns:
            Logging level constant
        """
        env_level = os.getenv(cls.ENV_LOG_LEVEL, "").upper()
        if env_level:
            level_map = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL,
            }
            return level_map.get(env_level, cls.DEFAULT_LOG_LEVEL)
        return cls.DEFAULT_LOG_LEVEL

    @classmethod
    def setup_logging(cls, logger_name: str = "internacia") -> logging.Logger:
        """
        Set up logging for the SDK.

        Args:
            logger_name: Name for the logger

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(logger_name)

        # Only configure if not already configured
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(cls.get_log_level())

        return logger
