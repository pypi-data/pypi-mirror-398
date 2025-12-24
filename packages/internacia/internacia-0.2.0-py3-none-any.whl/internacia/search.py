"""Search functionality with fuzzy matching support."""

import logging
from typing import List
from internacia.database import DatabaseManager
from internacia.exceptions import ValidationError
from internacia.models import SearchResult

logger = logging.getLogger(__name__)


class SearchClient:
    """Client for searching countries and international blocks."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the search client.

        Args:
            db_manager: Database manager instance
        """
        self._db = db_manager

    def fuzzy(
        self,
        query: str,
        limit: int = 10,
        search_countries: bool = True,
        search_intblocks: bool = True
    ) -> List[SearchResult]:
        """
        Perform fuzzy search across countries and international blocks.

        This function searches across:
        - Country names (in any language via native_names)
        - Country codes (ISO 3166-1 alpha-2, alpha-3, numeric)
        - International block names
        - Block translations (in any language)
        - Block acronyms (in any language)
        - Block IDs

        Args:
            query: Search query string
            limit: Maximum number of results to return
            search_countries: Whether to search countries (default: True)
            search_intblocks: Whether to search international blocks (default: True)

        Returns:
            List of matching records with a 'type' field indicating 'country' or 'intblock'

        Raises:
            ValidationError: If query is empty or limit is invalid

        Example:
            >>> results = client.search.fuzzy("United States")
            >>> results = client.search.fuzzy("EU", search_countries=False)
            >>> results = client.search.fuzzy("Европа", limit=5)
        """
        if not isinstance(query, str) or not query.strip():
            raise ValidationError("query must be a non-empty string")
        if not isinstance(limit, int) or limit <= 0:
            raise ValidationError("limit must be a positive integer")
        if not isinstance(search_countries, bool) or not isinstance(search_intblocks, bool):
            raise ValidationError("search_countries and search_intblocks must be boolean")

        logger.debug("Fuzzy search: query='%s', limit=%s, countries=%s, blocks=%s",
                     query, limit, search_countries, search_intblocks)
        query_upper = query.upper()
        query_lower = query.lower()
        results = []

        if search_countries:
            # Search countries by code (exact match)
            country_by_code = self._db.execute_query_dict(
                "SELECT *, 'country' as type FROM countries WHERE code = ? LIMIT ?",
                (query_upper, limit)
            )
            results.extend(country_by_code)

            # Search countries by ISO3 code
            country_by_iso3 = self._db.execute_query_dict(
                "SELECT *, 'country' as type FROM countries WHERE iso3code = ? LIMIT ?",
                (query_upper, limit)
            )
            results.extend([c for c in country_by_iso3 if c not in results])

            # Search countries by numeric code
            if query.isdigit():
                country_by_numeric = self._db.execute_query_dict(
                    "SELECT *, 'country' as type FROM countries WHERE numeric_code = ? LIMIT ?",
                    (query, limit)
                )
                results.extend([c for c in country_by_numeric if c not in results])

            # Search countries by name (case-insensitive partial match)
            country_by_name = self._db.execute_query_dict(
                "SELECT *, 'country' as type FROM countries WHERE UPPER(name) LIKE ? LIMIT ?",
                (f"%{query_upper}%", limit)
            )
            results.extend([c for c in country_by_name if c not in results])

            # Search countries by official name
            country_by_official = self._db.execute_query_dict(
                ("SELECT *, 'country' as type FROM countries "
                 "WHERE UPPER(official_name) LIKE ? LIMIT ?"),
                (f"%{query_upper}%", limit)
            )
            results.extend([c for c in country_by_official if c not in results])

            # Search countries by native names (any language)
            # Note: This is a simplified approach. For better performance with large datasets,
            # you might want to create a full-text search index
            country_by_native = self._db.execute_query_dict(
                """
                SELECT DISTINCT c.*, 'country' as type
                FROM countries c, UNNEST(map_keys(c.native_names)) AS lang_key
                WHERE UPPER(c.native_names[lang_key].common) LIKE ?
                   OR UPPER(c.native_names[lang_key].official) LIKE ?
                LIMIT ?
                """,
                (f"%{query_upper}%", f"%{query_upper}%", limit)
            )
            results.extend([c for c in country_by_native if c not in results])

        if search_intblocks:
            # Search intblocks by ID (exact match)
            block_by_id = self._db.execute_query_dict(
                "SELECT *, 'intblock' as type FROM intblocks WHERE id = ? LIMIT ?",
                (query_upper, limit)
            )
            results.extend(block_by_id)

            # Search intblocks by name (case-insensitive partial match)
            block_by_name = self._db.execute_query_dict(
                "SELECT *, 'intblock' as type FROM intblocks WHERE UPPER(name) LIKE ? LIMIT ?",
                (f"%{query_upper}%", limit)
            )
            results.extend([b for b in block_by_name if b not in results])

            # Search intblocks by translations (any language)
            block_by_translation = self._db.execute_query_dict(
                """
                SELECT DISTINCT i.*, 'intblock' as type
                FROM intblocks i, UNNEST(i.translations) AS trans
                WHERE UPPER(trans.name) LIKE ?
                LIMIT ?
                """,
                (f"%{query_upper}%", limit)
            )
            results.extend([b for b in block_by_translation if b not in results])

            # Search intblocks by acronyms (any language)
            block_by_acronym = self._db.execute_query_dict(
                """
                SELECT DISTINCT i.*, 'intblock' as type
                FROM intblocks i, UNNEST(i.acronyms) AS acr
                WHERE UPPER(acr.value) LIKE ?
                LIMIT ?
                """,
                (f"%{query_upper}%", limit)
            )
            results.extend([b for b in block_by_acronym if b not in results])

            # Search intblocks by tags
            block_by_tag = self._db.execute_query_dict(
                """
                SELECT *, 'intblock' as type
                FROM intblocks
                WHERE LIST_CONTAINS(tags, ?)
                LIMIT ?
                """,
                (query_lower, limit)
            )
            results.extend([b for b in block_by_tag if b not in results])

        # Remove duplicates based on type and id/code
        seen = set()
        unique_results = []
        for item in results:
            if item.get('type') == 'country':
                key = ('country', item.get('code'))
            else:
                key = ('intblock', item.get('id'))

            if key not in seen:
                seen.add(key)
                unique_results.append(item)

        # Sort results: exact matches first, then by relevance
        def sort_key(item):
            query_lower_item = query.lower()
            name = item.get('name', '').lower()
            code_or_id = (item.get('code') or item.get('id') or '').lower()

            # Exact match gets highest priority
            if code_or_id == query_lower_item:
                return (0, 0)
            # Starts with query
            if name.startswith(query_lower_item) or code_or_id.startswith(query_lower_item):
                return (1, len(name))
            # Contains query
            return (2, len(name))

        unique_results.sort(key=sort_key)

        final_results = unique_results[:limit]
        logger.debug("Fuzzy search returned %s results", len(final_results))
        return final_results

    def search_countries(
        self,
        query: str,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Search only countries.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching country dictionaries
        """
        results = self.fuzzy(query, limit=limit, search_countries=True, search_intblocks=False)
        return [r for r in results if r.get('type') == 'country']

    def search_intblocks(
        self,
        query: str,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Search only international blocks.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching block dictionaries
        """
        results = self.fuzzy(query, limit=limit, search_countries=False, search_intblocks=True)
        return [r for r in results if r.get('type') == 'intblock']
