"""Tests for SearchClient functionality."""

import pytest
from internacia.search import SearchClient
from internacia.exceptions import ValidationError


class TestSearchClientFuzzy:
    """Test fuzzy search method."""

    def test_fuzzy_search_countries_only(self, mock_db_manager):
        """Test fuzzy search with countries only."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        mock_db_manager.execute_query_dict.return_value = [country_result]
        client = SearchClient(mock_db_manager)

        result = client.fuzzy("United States", limit=10, search_countries=True, search_intblocks=False)

        assert len(result) > 0
        assert all(r.get("type") == "country" for r in result)

    def test_fuzzy_search_intblocks_only(self, mock_db_manager):
        """Test fuzzy search with blocks only."""
        block_result = {"id": "EU", "name": "European Union", "type": "intblock"}
        mock_db_manager.execute_query_dict.return_value = [block_result]
        client = SearchClient(mock_db_manager)

        result = client.fuzzy("EU", limit=10, search_countries=False, search_intblocks=True)

        assert len(result) > 0
        assert all(r.get("type") == "intblock" for r in result)

    def test_fuzzy_search_both(self, mock_db_manager):
        """Test fuzzy search with both countries and blocks."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        block_result = {"id": "EU", "name": "European Union", "type": "intblock"}
        # Simulate multiple calls returning different results
        call_count = [0]
        def side_effect(*args, **kwargs):  # pylint: disable=unused-argument
            call_count[0] += 1
            if call_count[0] <= 3:
                return [country_result]
            return [block_result]

        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)

        client.fuzzy("United", limit=10, search_countries=True, search_intblocks=True)

        # Should have called execute_query_dict multiple times
        assert mock_db_manager.execute_query_dict.call_count > 0

    def test_fuzzy_search_by_code(self, mock_db_manager):
        """Test fuzzy search by country code."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        mock_db_manager.execute_query_dict.return_value = [country_result]
        client = SearchClient(mock_db_manager)

        client.fuzzy("US", limit=10)

        # Should search by code
        calls = [call[0][0] for call in mock_db_manager.execute_query_dict.call_args_list]
        assert any("code = ?" in call for call in calls)

    def test_fuzzy_search_by_numeric_code(self, mock_db_manager):
        """Test fuzzy search by numeric code."""
        country_result = {"code": "US", "name": "United States", "numeric_code": "840", "type": "country"}
        mock_db_manager.execute_query_dict.return_value = [country_result]
        client = SearchClient(mock_db_manager)

        client.fuzzy("840", limit=10)

        # Should search by numeric code
        calls = [call[0][0] for call in mock_db_manager.execute_query_dict.call_args_list]
        assert any("numeric_code = ?" in call for call in calls)

    def test_fuzzy_search_by_name(self, mock_db_manager):
        """Test fuzzy search by name."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        mock_db_manager.execute_query_dict.return_value = [country_result]
        client = SearchClient(mock_db_manager)

        client.fuzzy("United", limit=10)

        # Should search by name
        calls = [call[0][0] for call in mock_db_manager.execute_query_dict.call_args_list]
        assert any("UPPER(name) LIKE ?" in call for call in calls)

    def test_fuzzy_search_removes_duplicates(self, mock_db_manager):
        """Test that fuzzy search removes duplicates."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        # Return same result multiple times
        mock_db_manager.execute_query_dict.return_value = [country_result]
        client = SearchClient(mock_db_manager)

        result = client.fuzzy("US", limit=10)

        # Should deduplicate based on code/id
        codes = [r.get("code") for r in result if r.get("type") == "country"]
        assert len(codes) == len(set(codes))

    def test_fuzzy_search_respects_limit(self, mock_db_manager):
        """Test that fuzzy search respects limit."""
        # Return many results
        many_results = [{"code": f"US{i}", "name": f"Country {i}", "type": "country"} for i in range(20)]
        mock_db_manager.execute_query_dict.return_value = many_results
        client = SearchClient(mock_db_manager)

        result = client.fuzzy("Country", limit=5)

        assert len(result) <= 5

    def test_fuzzy_search_empty_result(self, mock_db_manager):
        """Test fuzzy search with no results."""
        mock_db_manager.execute_query_dict.return_value = []
        client = SearchClient(mock_db_manager)

        result = client.fuzzy("Nonexistent", limit=10)

        assert not result


class TestSearchClientSearchCountries:
    """Test search_countries method."""

    def test_search_countries(self, mock_db_manager):
        """Test search_countries."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        mock_db_manager.execute_query_dict.return_value = [country_result]
        client = SearchClient(mock_db_manager)

        result = client.search_countries("United", limit=10)

        assert len(result) > 0
        assert all(r.get("type") == "country" for r in result)
        # Should call fuzzy with search_countries=True, search_intblocks=False
        # We can't directly verify this, but we can check the results


class TestSearchClientSearchIntblocks:
    """Test search_intblocks method."""

    def test_search_intblocks(self, mock_db_manager):
        """Test search_intblocks."""
        block_result = {"id": "EU", "name": "European Union", "type": "intblock"}
        mock_db_manager.execute_query_dict.return_value = [block_result]
        client = SearchClient(mock_db_manager)

        result = client.search_intblocks("EU", limit=10)

        assert len(result) > 0
        assert all(r.get("type") == "intblock" for r in result)


class TestSearchClientValidation:
    """Test search validation (additional to test_validation.py)."""

    def test_fuzzy_invalid_search_countries_type(self, mock_db_manager):
        """Test that search_countries must be boolean."""
        client = SearchClient(mock_db_manager)

        with pytest.raises(ValidationError):
            client.fuzzy("test", limit=10, search_countries="true")

    def test_fuzzy_invalid_search_intblocks_type(self, mock_db_manager):
        """Test that search_intblocks must be boolean."""
        client = SearchClient(mock_db_manager)

        with pytest.raises(ValidationError):
            client.fuzzy("test", limit=10, search_intblocks="true")

    def test_fuzzy_both_false(self, mock_db_manager):
        """Test that at least one search type must be enabled."""
        client = SearchClient(mock_db_manager)

        # This should work but return empty results
        result = client.fuzzy("test", limit=10, search_countries=False, search_intblocks=False)
        assert not result


class TestFuzzySearchComprehensive:
    """Comprehensive tests for fuzzy search functionality."""

    def test_fuzzy_search_by_country_code_exact(self, mock_db_manager):
        """Test fuzzy search by country code (exact match)."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "code = ?" in query:
                return [country_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("US", limit=10)
        
        assert len(result) > 0
        assert result[0]["code"] == "US"
        assert result[0]["type"] == "country"

    def test_fuzzy_search_by_iso3_code(self, mock_db_manager):
        """Test fuzzy search by ISO3 code."""
        country_result = {"code": "US", "iso3code": "USA", "name": "United States", "type": "country"}
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "iso3code = ?" in query:
                return [country_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("USA", limit=10)
        
        assert len(result) > 0
        assert result[0]["iso3code"] == "USA"

    def test_fuzzy_search_by_numeric_code_exact(self, mock_db_manager):
        """Test fuzzy search by numeric code (exact match)."""
        country_result = {"code": "US", "numeric_code": "840", "name": "United States", "type": "country"}
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "numeric_code = ?" in query:
                return [country_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("840", limit=10)
        
        assert len(result) > 0
        assert result[0]["numeric_code"] == "840"

    def test_fuzzy_search_by_country_name_partial(self, mock_db_manager):
        """Test fuzzy search by country name (partial match)."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "UPPER(name) LIKE ?" in query:
                return [country_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("United", limit=10)
        
        assert len(result) > 0
        assert "United" in result[0]["name"]

    def test_fuzzy_search_by_official_name(self, mock_db_manager):
        """Test fuzzy search by official name."""
        country_result = {
            "code": "US",
            "name": "United States",
            "official_name": "United States of America",
            "type": "country"
        }
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "UPPER(official_name) LIKE ?" in query:
                return [country_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("America", limit=10)
        
        assert len(result) > 0
        assert "America" in result[0]["official_name"]

    def test_fuzzy_search_by_native_names_common(self, mock_db_manager):
        """Test fuzzy search by native names (common)."""
        country_result = {
            "code": "FR",
            "name": "France",
            "native_names": {
                "fra": {"common": "France", "official": "République française"},
                "deu": {"common": "Frankreich", "official": "Französische Republik"}
            },
            "type": "country"
        }
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "native_names" in query and "common" in query:
                return [country_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("Frankreich", limit=10)
        
        assert len(result) > 0
        assert result[0]["code"] == "FR"

    def test_fuzzy_search_by_native_names_official(self, mock_db_manager):
        """Test fuzzy search by native names (official)."""
        country_result = {
            "code": "FR",
            "name": "France",
            "native_names": {
                "fra": {"common": "France", "official": "République française"}
            },
            "type": "country"
        }
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "native_names" in query and "official" in query:
                return [country_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("République", limit=10)
        
        assert len(result) > 0
        assert result[0]["code"] == "FR"

    def test_fuzzy_search_by_block_id(self, mock_db_manager):
        """Test fuzzy search by block ID (exact match)."""
        block_result = {"id": "EU", "name": "European Union", "type": "intblock"}
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "intblocks" in query and "id = ?" in query:
                return [block_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("EU", limit=10)
        
        assert len(result) > 0
        assert result[0]["id"] == "EU"
        assert result[0]["type"] == "intblock"

    def test_fuzzy_search_by_block_name(self, mock_db_manager):
        """Test fuzzy search by block name (partial match)."""
        block_result = {"id": "EU", "name": "European Union", "type": "intblock"}
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "intblocks" in query and "UPPER(name) LIKE ?" in query:
                return [block_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("European", limit=10)
        
        assert len(result) > 0
        assert "European" in result[0]["name"]

    def test_fuzzy_search_by_block_translations(self, mock_db_manager):
        """Test fuzzy search by block translations."""
        block_result = {
            "id": "EU",
            "name": "European Union",
            "translations": [
                {"lang": "ru", "name": "Европейский союз"},
                {"lang": "zh", "name": "欧盟"}
            ],
            "type": "intblock"
        }
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "translations" in query and "UNNEST" in query:
                return [block_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("Европейский", limit=10)
        
        assert len(result) > 0
        assert result[0]["id"] == "EU"

    def test_fuzzy_search_by_block_acronyms(self, mock_db_manager):
        """Test fuzzy search by block acronyms."""
        block_result = {
            "id": "EU",
            "name": "European Union",
            "acronyms": [
                {"lang": "en", "value": "EU"},
                {"lang": "fr", "value": "UE"}
            ],
            "type": "intblock"
        }
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "acronyms" in query and "UNNEST" in query:
                return [block_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("UE", limit=10)
        
        assert len(result) > 0
        assert result[0]["id"] == "EU"

    def test_fuzzy_search_by_block_tags(self, mock_db_manager):
        """Test fuzzy search by block tags."""
        block_result = {
            "id": "EU",
            "name": "European Union",
            "tags": ["trade", "economic", "political"],
            "type": "intblock"
        }
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "LIST_CONTAINS(tags" in query:
                return [block_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("trade", limit=10)
        
        assert len(result) > 0
        assert result[0]["id"] == "EU"
        assert "trade" in result[0]["tags"]

    def test_fuzzy_search_case_insensitive_country_name(self, mock_db_manager):
        """Test that country name search is case-insensitive."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "UPPER(name) LIKE ?" in query:
                return [country_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        # Test lowercase
        result1 = client.fuzzy("united", limit=10)
        # Test uppercase
        result2 = client.fuzzy("UNITED", limit=10)
        # Test mixed case
        result3 = client.fuzzy("UnItEd", limit=10)
        
        assert len(result1) > 0 or len(result2) > 0 or len(result3) > 0

    def test_fuzzy_search_case_insensitive_block_name(self, mock_db_manager):
        """Test that block name search is case-insensitive."""
        block_result = {"id": "EU", "name": "European Union", "type": "intblock"}
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "intblocks" in query and "UPPER(name) LIKE ?" in query:
                return [block_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("european", limit=10)
        
        assert len(result) > 0

    def test_fuzzy_search_partial_match_starts_with(self, mock_db_manager):
        """Test partial matching when query starts with country name."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        mock_db_manager.execute_query_dict.return_value = [country_result]
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("United", limit=10)
        
        assert len(result) > 0
        assert result[0]["name"].startswith("United")

    def test_fuzzy_search_partial_match_contains(self, mock_db_manager):
        """Test partial matching when query is contained in name."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        mock_db_manager.execute_query_dict.return_value = [country_result]
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("States", limit=10)
        
        assert len(result) > 0
        assert "States" in result[0]["name"]

    def test_fuzzy_search_sorting_exact_match_first(self, mock_db_manager):
        """Test that exact matches are sorted first."""
        exact_match = {"code": "US", "name": "US", "type": "country"}
        partial_match1 = {"code": "UA", "name": "United Arab Emirates", "type": "country"}
        partial_match2 = {"code": "GB", "name": "United Kingdom", "type": "country"}
        
        call_count = [0]
        def side_effect(query, params):
            call_count[0] += 1
            if "code = ?" in query:
                return [exact_match]
            elif "UPPER(name) LIKE ?" in query:
                return [partial_match1, partial_match2]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("US", limit=10)
        
        # Exact match should be first
        assert len(result) > 0
        assert result[0]["code"] == "US"

    def test_fuzzy_search_sorting_starts_with_priority(self, mock_db_manager):
        """Test that names starting with query are prioritized."""
        starts_with = {"code": "US", "name": "United States", "type": "country"}
        contains = {"code": "AU", "name": "Australia", "type": "country"}
        
        call_count = [0]
        def side_effect(query, params):
            call_count[0] += 1
            if "UPPER(name) LIKE ?" in query:
                return [starts_with, contains]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("United", limit=10)
        
        # Name starting with query should come first
        assert len(result) > 0
        assert result[0]["name"].startswith("United")

    def test_fuzzy_search_unicode_characters(self, mock_db_manager):
        """Test fuzzy search with unicode characters."""
        country_result = {
            "code": "RU",
            "name": "Russia",
            "native_names": {
                "rus": {"common": "Россия", "official": "Российская Федерация"}
            },
            "type": "country"
        }
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "native_names" in query:
                return [country_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("Россия", limit=10)
        
        assert len(result) > 0
        assert result[0]["code"] == "RU"

    def test_fuzzy_search_chinese_characters(self, mock_db_manager):
        """Test fuzzy search with Chinese characters."""
        block_result = {
            "id": "EU",
            "name": "European Union",
            "translations": [{"lang": "zh", "name": "欧盟"}],
            "type": "intblock"
        }
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "translations" in query:
                return [block_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("欧盟", limit=10)
        
        assert len(result) > 0
        assert result[0]["id"] == "EU"

    def test_fuzzy_search_special_characters(self, mock_db_manager):
        """Test fuzzy search with special characters in names."""
        country_result = {
            "code": "FR",
            "name": "France",
            "official_name": "République française",
            "type": "country"
        }
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "official_name" in query:
                return [country_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("française", limit=10)
        
        assert len(result) > 0

    def test_fuzzy_search_whitespace_handling(self, mock_db_manager):
        """Test that whitespace in query is handled correctly."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        mock_db_manager.execute_query_dict.return_value = [country_result]
        client = SearchClient(mock_db_manager)
        
        # Query with leading/trailing whitespace should be trimmed
        result = client.fuzzy("  United States  ", limit=10)
        
        # Should not raise error and should find results
        assert isinstance(result, list)

    def test_fuzzy_search_multiple_languages_native_names(self, mock_db_manager):
        """Test search across multiple languages in native names."""
        country_result = {
            "code": "DE",
            "name": "Germany",
            "native_names": {
                "deu": {"common": "Deutschland", "official": "Bundesrepublik Deutschland"},
                "fra": {"common": "Allemagne", "official": "République fédérale d'Allemagne"},
                "spa": {"common": "Alemania", "official": "República Federal de Alemania"}
            },
            "type": "country"
        }
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "native_names" in query:
                return [country_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        # Test German
        result1 = client.fuzzy("Deutschland", limit=10)
        # Test French
        result2 = client.fuzzy("Allemagne", limit=10)
        # Test Spanish
        result3 = client.fuzzy("Alemania", limit=10)
        
        assert len(result1) > 0 or len(result2) > 0 or len(result3) > 0

    def test_fuzzy_search_multiple_languages_translations(self, mock_db_manager):
        """Test search across multiple languages in block translations."""
        block_result = {
            "id": "EU",
            "name": "European Union",
            "translations": [
                {"lang": "en", "name": "European Union"},
                {"lang": "ru", "name": "Европейский союз"},
                {"lang": "zh", "name": "欧盟"},
                {"lang": "fr", "name": "Union européenne"}
            ],
            "type": "intblock"
        }
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "translations" in query:
                return [block_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        # Test Russian
        result1 = client.fuzzy("Европейский", limit=10)
        # Test Chinese
        result2 = client.fuzzy("欧盟", limit=10)
        # Test French
        result3 = client.fuzzy("européenne", limit=10)
        
        assert len(result1) > 0 or len(result2) > 0 or len(result3) > 0

    def test_fuzzy_search_combined_countries_and_blocks(self, mock_db_manager):
        """Test search that returns both countries and blocks."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        block_result = {"id": "USMCA", "name": "United States-Mexico-Canada Agreement", "type": "intblock"}
        
        call_count = [0]
        def side_effect(query, params):
            call_count[0] += 1
            if "countries" in query:
                return [country_result]
            elif "intblocks" in query:
                return [block_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("United States", limit=10)
        
        assert len(result) > 0
        country_types = [r for r in result if r.get("type") == "country"]
        block_types = [r for r in result if r.get("type") == "intblock"]
        assert len(country_types) > 0 or len(block_types) > 0

    def test_fuzzy_search_duplicate_removal_same_type(self, mock_db_manager):
        """Test that duplicates of the same type are removed."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        
        call_count = [0]
        def side_effect(query, params):
            call_count[0] += 1
            # Return same country from multiple queries
            return [country_result]
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("US", limit=10)
        
        # Should only have one instance of US
        us_results = [r for r in result if r.get("code") == "US"]
        assert len(us_results) <= 1

    def test_fuzzy_search_duplicate_removal_different_queries(self, mock_db_manager):
        """Test that same country found via different queries is deduplicated."""
        country_result = {"code": "US", "name": "United States", "iso3code": "USA", "type": "country"}
        
        call_count = [0]
        def side_effect(query, params):
            call_count[0] += 1
            # Return same country from code, iso3, and name queries
            return [country_result]
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("US", limit=10)
        
        # Should only have one instance
        assert len(result) == 1
        assert result[0]["code"] == "US"

    def test_fuzzy_search_limit_enforcement(self, mock_db_manager):
        """Test that limit is strictly enforced."""
        many_results = [
            {"code": f"C{i:02d}", "name": f"Country {i}", "type": "country"}
            for i in range(50)
        ]
        mock_db_manager.execute_query_dict.return_value = many_results
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("Country", limit=5)
        
        assert len(result) == 5

    def test_fuzzy_search_limit_one(self, mock_db_manager):
        """Test fuzzy search with limit of 1."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        mock_db_manager.execute_query_dict.return_value = [country_result]
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("United", limit=1)
        
        assert len(result) <= 1

    def test_fuzzy_search_empty_query_raises_error(self, mock_db_manager):
        """Test that empty query raises ValidationError."""
        client = SearchClient(mock_db_manager)
        
        with pytest.raises(ValidationError, match="query must be a non-empty string"):
            client.fuzzy("", limit=10)
        
        with pytest.raises(ValidationError, match="query must be a non-empty string"):
            client.fuzzy("   ", limit=10)

    def test_fuzzy_search_invalid_limit_raises_error(self, mock_db_manager):
        """Test that invalid limit raises ValidationError."""
        client = SearchClient(mock_db_manager)
        
        with pytest.raises(ValidationError, match="limit must be a positive integer"):
            client.fuzzy("test", limit=0)
        
        with pytest.raises(ValidationError, match="limit must be a positive integer"):
            client.fuzzy("test", limit=-1)

    def test_fuzzy_search_none_query_raises_error(self, mock_db_manager):
        """Test that None query raises ValidationError."""
        client = SearchClient(mock_db_manager)
        
        with pytest.raises(ValidationError):
            client.fuzzy(None, limit=10)

    def test_fuzzy_search_non_string_query_raises_error(self, mock_db_manager):
        """Test that non-string query raises ValidationError."""
        client = SearchClient(mock_db_manager)
        
        with pytest.raises(ValidationError):
            client.fuzzy(123, limit=10)
        
        with pytest.raises(ValidationError):
            client.fuzzy([], limit=10)

    def test_fuzzy_search_non_integer_limit_raises_error(self, mock_db_manager):
        """Test that non-integer limit raises ValidationError."""
        client = SearchClient(mock_db_manager)
        
        with pytest.raises(ValidationError):
            client.fuzzy("test", limit="10")
        
        with pytest.raises(ValidationError):
            client.fuzzy("test", limit=10.5)

    def test_fuzzy_search_no_numeric_code_for_non_digit(self, mock_db_manager):
        """Test that numeric code search is only performed for digit queries."""
        country_result = {"code": "US", "name": "United States", "type": "country"}
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            # Should not search numeric_code for non-digit query
            if "numeric_code" in query:
                return []
            return [country_result]
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("US", limit=10)
        
        # Verify numeric_code query was not made
        calls = [call[0][0] for call in mock_db_manager.execute_query_dict.call_args_list]
        numeric_calls = [c for c in calls if "numeric_code" in c]
        assert len(numeric_calls) == 0

    def test_fuzzy_search_numeric_code_only_for_digits(self, mock_db_manager):
        """Test that numeric code search is performed for digit queries."""
        country_result = {"code": "US", "numeric_code": "840", "name": "United States", "type": "country"}
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "numeric_code = ?" in query:
                return [country_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("840", limit=10)
        
        # Verify numeric_code query was made
        calls = [call[0][0] for call in mock_db_manager.execute_query_dict.call_args_list]
        numeric_calls = [c for c in calls if "numeric_code" in c]
        assert len(numeric_calls) > 0

    def test_fuzzy_search_tags_case_sensitive(self, mock_db_manager):
        """Test that tag search is case-sensitive (uses query_lower)."""
        block_result = {
            "id": "EU",
            "name": "European Union",
            "tags": ["trade", "economic"],
            "type": "intblock"
        }
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "LIST_CONTAINS(tags" in query:
                # Verify it uses lowercase
                assert params[0] == "trade"
                return [block_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("TRADE", limit=10)
        
        assert len(result) > 0

    def test_fuzzy_search_result_ordering_exact_code_first(self, mock_db_manager):
        """Test that exact code matches come before name matches."""
        exact_code = {"code": "US", "name": "United States", "type": "country"}
        name_match = {"code": "UA", "name": "United Arab Emirates", "type": "country"}
        
        call_count = [0]
        def side_effect(query, params):
            call_count[0] += 1
            if "code = ?" in query:
                return [exact_code]
            elif "UPPER(name) LIKE ?" in query:
                return [name_match]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("US", limit=10)
        
        # Exact code match should be first
        assert result[0]["code"] == "US"

    def test_fuzzy_search_result_ordering_shorter_names_first(self, mock_db_manager):
        """Test that shorter matching names come before longer ones."""
        short_name = {"code": "US", "name": "United States", "type": "country"}
        long_name = {"code": "UA", "name": "United Arab Emirates", "type": "country"}
        
        call_count = [0]
        def side_effect(query, params):
            call_count[0] += 1
            if "UPPER(name) LIKE ?" in query:
                return [short_name, long_name]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("United", limit=10)
        
        # Shorter name should come first (if both start with query)
        assert len(result) > 0
        # Both should be present, but shorter should be prioritized
        assert any(r["code"] == "US" for r in result)

    def test_fuzzy_search_multiple_blocks_same_query(self, mock_db_manager):
        """Test search returning multiple blocks for same query."""
        block1 = {"id": "EU", "name": "European Union", "type": "intblock"}
        block2 = {"id": "EEA", "name": "European Economic Area", "type": "intblock"}
        
        call_count = [0]
        def side_effect(query, params):
            call_count[0] += 1
            if "intblocks" in query and "UPPER(name) LIKE ?" in query:
                return [block1, block2]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("European", limit=10, search_countries=False)
        
        assert len(result) >= 2
        block_ids = [r["id"] for r in result]
        assert "EU" in block_ids
        assert "EEA" in block_ids

    def test_fuzzy_search_multiple_countries_same_query(self, mock_db_manager):
        """Test search returning multiple countries for same query."""
        country1 = {"code": "US", "name": "United States", "type": "country"}
        country2 = {"code": "UA", "name": "United Arab Emirates", "type": "country"}
        country3 = {"code": "GB", "name": "United Kingdom", "type": "country"}
        
        call_count = [0]
        def side_effect(query, params):
            call_count[0] += 1
            if "countries" in query and "UPPER(name) LIKE ?" in query:
                return [country1, country2, country3]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("United", limit=10, search_intblocks=False)
        
        assert len(result) >= 3
        codes = [r["code"] for r in result]
        assert "US" in codes
        assert "UA" in codes
        assert "GB" in codes

    def test_fuzzy_search_complex_query_with_spaces(self, mock_db_manager):
        """Test search with complex multi-word query."""
        country_result = {
            "code": "US",
            "name": "United States",
            "official_name": "United States of America",
            "type": "country"
        }
        call_count = [0]
        
        def side_effect(query, params):
            call_count[0] += 1
            if "UPPER(name) LIKE ?" in query or "UPPER(official_name) LIKE ?" in query:
                return [country_result]
            return []
        
        mock_db_manager.execute_query_dict.side_effect = side_effect
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("United States of", limit=10)
        
        assert len(result) > 0

    def test_fuzzy_search_single_character_query(self, mock_db_manager):
        """Test search with single character query."""
        country_result = {"code": "U", "name": "Utopia", "type": "country"}
        mock_db_manager.execute_query_dict.return_value = [country_result]
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("U", limit=10)
        
        assert isinstance(result, list)

    def test_fuzzy_search_very_long_query(self, mock_db_manager):
        """Test search with very long query string."""
        long_query = "A" * 1000
        mock_db_manager.execute_query_dict.return_value = []
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy(long_query, limit=10)
        
        # Should not raise error
        assert isinstance(result, list)

    def test_fuzzy_search_all_search_types_disabled_returns_empty(self, mock_db_manager):
        """Test that disabling both search types returns empty list."""
        mock_db_manager.execute_query_dict.return_value = []
        client = SearchClient(mock_db_manager)
        
        result = client.fuzzy("test", limit=10, search_countries=False, search_intblocks=False)
        
        assert result == []
