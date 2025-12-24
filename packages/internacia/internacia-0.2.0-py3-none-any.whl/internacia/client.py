"""Main client class for Internacia SDK."""

import logging
from pathlib import Path
from typing import Optional
from internacia.database import DatabaseManager
from internacia.countries import CountriesClient
from internacia.intblocks import IntblocksClient
from internacia.search import SearchClient
from internacia.config import Config

logger = logging.getLogger(__name__)


class InternaciaClient:
    """
    Main client for accessing internacia-db data.

    This client provides access to countries, international blocks, and search
    functionality through a unified interface.

    Example:
        >>> from internacia import InternaciaClient
        >>> client = InternaciaClient()
        >>> country = client.countries.get_by_code("US")
        >>> results = client.search.fuzzy("United States")
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        data_dir: Optional[Path] = None  # pylint: disable=unused-argument
    ):
        """
        Initialize the Internacia client.

        Args:
            db_path: Path to the DuckDB database file. If None, will try to
                     find it in the default location relative to internacia-db.
            data_dir: Path to the internacia-db data directory. If None, will
                      try to find it in the default location.

        Raises:
            FileNotFoundError: If the database file cannot be found
        """
        # Set up logging
        Config.setup_logging()

        if db_path is None:
            # Use config to find database path
            db_path = Config.get_db_path()
            if db_path is None:
                raise FileNotFoundError(
                    "Could not find internacia.duckdb database. "
                    "Please specify db_path, set INTERNACIA_DB_PATH environment variable, "
                    "ensure the database is built in the default location, or download it using:\n"
                    "  from internacia import download_database\n"
                    "  download_database()"
                )
            if not db_path.exists():
                raise FileNotFoundError(
                    f"Database file not found at: {db_path}. "
                    "You can download it using:\n"
                    "  from internacia import download_database\n"
                    "  download_database()"
                )
        else:
            db_path = Path(db_path)
            if not db_path.exists():
                raise FileNotFoundError(
                    f"Database file not found at specified path: {db_path}"
                )

        logger.info("Initializing InternaciaClient with database: %s", db_path)
        self._db_manager = DatabaseManager(db_path)
        self.countries = CountriesClient(self._db_manager)
        self.intblocks = IntblocksClient(self._db_manager)
        self.search = SearchClient(self._db_manager)
