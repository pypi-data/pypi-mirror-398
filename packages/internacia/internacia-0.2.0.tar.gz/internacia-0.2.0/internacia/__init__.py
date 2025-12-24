"""
Internacia Python SDK

A Python SDK for accessing internacia-db data with support for countries,
international blocks, and fuzzy search across multiple languages.
"""

from internacia.client import InternaciaClient
from internacia.version import __version__
from internacia.exceptions import (
    InternaciaError,
    DatabaseError,
    NotFoundError,
    ValidationError,
    DownloadError,
    VersionError,
)
from internacia.models import (
    Country,
    Intblock,
    SearchResult,
    CapitalCity,
    Region,
    IncomeLevel,
    Language,
    Currency,
    NativeName,
    Translation,
    Acronym,
    Topic,
    Member,
)
from internacia.downloader import (
    download_database,
    get_latest_version,
    check_for_updates,
    get_cache_dir,
    get_cached_database_path,
)

__all__ = [
    "InternaciaClient",
    "__version__",
    "InternaciaError",
    "DatabaseError",
    "NotFoundError",
    "ValidationError",
    "DownloadError",
    "VersionError",
    "Country",
    "Intblock",
    "SearchResult",
    "CapitalCity",
    "Region",
    "IncomeLevel",
    "Language",
    "Currency",
    "NativeName",
    "Translation",
    "Acronym",
    "Topic",
    "Member",
    "download_database",
    "get_latest_version",
    "check_for_updates",
    "get_cache_dir",
    "get_cached_database_path",
]
