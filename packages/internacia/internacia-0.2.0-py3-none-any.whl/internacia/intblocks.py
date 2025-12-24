"""International blocks data access module."""

import logging
from typing import Optional, List
from internacia.database import DatabaseManager
from internacia.exceptions import ValidationError
from internacia.models import Intblock

logger = logging.getLogger(__name__)


class IntblocksClient:
    """Client for querying international blocks data."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the intblocks client.

        Args:
            db_manager: Database manager instance
        """
        self._db = db_manager

    def get_by_id(self, block_id: str) -> Optional[Intblock]:
        """
        Get an international block by its ID.

        Args:
            block_id: Block identifier (e.g., "EU", "UN", "NATO")

        Returns:
            Block data as a dictionary, or None if not found

        Example:
            >>> block = client.intblocks.get_by_id("EU")
            >>> print(block["name"])  # "European Union"
        """
        logger.debug("Querying block by ID: %s", block_id)
        query = "SELECT * FROM intblocks WHERE id = ?"
        results = self._db.execute_query_dict(query, (block_id.upper(),))

        if results:
            logger.debug("Found block: %s", results[0].get('name'))
            return results[0]
        logger.debug("Block not found for ID: %s", block_id)
        return None

    def get_all(self, limit: Optional[int] = None) -> List[Intblock]:
        """
        Get all international blocks.

        Args:
            limit: Maximum number of results to return (optional)

        Returns:
            List of block dictionaries

        Raises:
            ValueError: If limit is not a positive integer
        """
        if limit is not None:
            if not isinstance(limit, int) or limit <= 0:
                raise ValueError("limit must be a positive integer")
            query = "SELECT * FROM intblocks LIMIT ?"
            return self._db.execute_query_dict(query, (limit,))
        query = "SELECT * FROM intblocks"
        return self._db.execute_query_dict(query)

    def get_by_blocktype(self, blocktype: str) -> List[Intblock]:
        """
        Get blocks by type.

        Args:
            blocktype: Block type (e.g., "economic", "political", "military")

        Returns:
            List of block dictionaries
        """
        query = """
            SELECT * FROM intblocks
            WHERE LIST_CONTAINS(blocktype, ?)
        """
        results = self._db.execute_query_dict(query, (blocktype.lower(),))
        return results

    def get_by_status(self, status: str) -> List[Intblock]:
        """
        Get blocks by status.

        Args:
            status: Status (e.g., "formal", "informal", "de-facto")

        Returns:
            List of block dictionaries
        """
        query = "SELECT * FROM intblocks WHERE status = ?"
        results = self._db.execute_query_dict(query, (status.lower(),))
        return results

    def get_by_geographic_scope(self, scope: str) -> List[Intblock]:
        """
        Get blocks by geographic scope.

        Args:
            scope: Geographic scope (e.g., "global", "regional", "sub-regional")

        Returns:
            List of block dictionaries
        """
        query = "SELECT * FROM intblocks WHERE geographic_scope = ?"
        results = self._db.execute_query_dict(query, (scope.lower(),))
        return results

    def get_by_member(self, country_code: str) -> List[Intblock]:
        """
        Get blocks that include a specific country as a member.

        Args:
            country_code: Two-letter country code (e.g., "US", "FR", "DE")

        Returns:
            List of block dictionaries
        """
        query = """
            SELECT DISTINCT i.*
            FROM intblocks i, UNNEST(i.includes) AS member
            WHERE member.id = ?
        """
        results = self._db.execute_query_dict(query, (country_code.upper(),))
        return results

    def get_by_acronym(self, acronym: str) -> List[Intblock]:
        """
        Get blocks by acronym.

        Args:
            acronym: Acronym (e.g., "EU", "UN", "NATO")

        Returns:
            List of block dictionaries
        """
        query = """
            SELECT DISTINCT i.*
            FROM intblocks i, UNNEST(i.acronyms) AS acr
            WHERE UPPER(acr.value) = ?
        """
        results = self._db.execute_query_dict(query, (acronym.upper(),))
        return results

    def get_by_tag(self, tag: str) -> List[Intblock]:
        """
        Get blocks by tag.

        Args:
            tag: Tag keyword

        Returns:
            List of block dictionaries
        """
        query = """
            SELECT * FROM intblocks
            WHERE LIST_CONTAINS(tags, ?)
        """
        results = self._db.execute_query_dict(query, (tag.lower(),))
        return results

    def get_by_topic(self, topic_key: str) -> List[Intblock]:
        """
        Get blocks by topic key.

        Args:
            topic_key: Topic key (e.g., "economy", "political", "trade")

        Returns:
            List of block dictionaries
        """
        query = """
            SELECT DISTINCT i.*
            FROM intblocks i, UNNEST(i.topics) AS topic
            WHERE topic.key = ?
        """
        results = self._db.execute_query_dict(query, (topic_key.lower(),))
        return results

    def get_by_founded_year(self, year: int) -> List[Intblock]:
        """
        Get blocks founded in a specific year.

        Args:
            year: Foundation year (e.g., 1993, 1945)

        Returns:
            List of block dictionaries

        Raises:
            ValidationError: If year is not a valid integer in reasonable range
        """
        if not isinstance(year, int):
            raise ValidationError("year must be an integer")
        if year < 1000 or year > 9999:
            raise ValidationError("year must be between 1000 and 9999")
        query = """
            SELECT * FROM intblocks
            WHERE founded LIKE ?
        """
        results = self._db.execute_query_dict(query, (f"{year}%",))
        return results

    def count(self) -> int:
        """
        Get the total number of international blocks.

        Returns:
            Total count of blocks
        """
        query = "SELECT COUNT(*) as count FROM intblocks"
        result = self._db.execute_query_dict(query)
        return result[0]["count"] if result else 0
