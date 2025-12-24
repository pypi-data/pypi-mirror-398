"""Tests for input validation."""

import pytest
from internacia.countries import CountriesClient
from internacia.intblocks import IntblocksClient
from internacia.search import SearchClient
from internacia.exceptions import ValidationError


def test_countries_get_by_code_validation(mock_db_manager):
    """Test country code validation."""
    client = CountriesClient(mock_db_manager)

    # Valid codes
    mock_db_manager.execute_query_dict.return_value = [{"code": "US"}]
    client.get_by_code("US")

    # Invalid codes
    with pytest.raises(ValidationError):
        client.get_by_code("")
    with pytest.raises(ValidationError):
        client.get_by_code("USA")  # Too long
    with pytest.raises(ValidationError):
        client.get_by_code("U")  # Too short
    with pytest.raises(ValidationError):
        client.get_by_code("12")  # Not alphabetic


def test_countries_get_by_iso3_validation(mock_db_manager):
    """Test ISO3 code validation."""
    client = CountriesClient(mock_db_manager)

    # Valid codes
    mock_db_manager.execute_query_dict.return_value = [{"iso3code": "USA"}]
    client.get_by_iso3("USA")

    # Invalid codes
    with pytest.raises(ValidationError):
        client.get_by_iso3("US")  # Too short
    with pytest.raises(ValidationError):
        client.get_by_iso3("USA1")  # Too long
    with pytest.raises(ValidationError):
        client.get_by_iso3("123")  # Not alphabetic


def test_countries_get_by_numeric_code_validation(mock_db_manager):
    """Test numeric code validation."""
    client = CountriesClient(mock_db_manager)

    # Valid codes
    mock_db_manager.execute_query_dict.return_value = [{"numeric_code": "840"}]
    client.get_by_numeric_code("840")

    # Invalid codes
    with pytest.raises(ValidationError):
        client.get_by_numeric_code("84")  # Too short
    with pytest.raises(ValidationError):
        client.get_by_numeric_code("8400")  # Too long
    with pytest.raises(ValidationError):
        client.get_by_numeric_code("ABC")  # Not numeric


def test_countries_get_all_limit_validation(mock_db_manager):
    """Test limit validation in get_all."""
    client = CountriesClient(mock_db_manager)

    # Valid limits
    mock_db_manager.execute_query_dict.return_value = []
    client.get_all(limit=10)
    client.get_all(limit=None)

    # Invalid limits
    with pytest.raises(ValueError):
        client.get_all(limit=0)
    with pytest.raises(ValueError):
        client.get_all(limit=-1)
    with pytest.raises(ValueError):
        client.get_all(limit="10")  # Not an integer


def test_intblocks_get_by_founded_year_validation(mock_db_manager):
    """Test year validation."""
    client = IntblocksClient(mock_db_manager)

    # Valid years
    mock_db_manager.execute_query_dict.return_value = []
    client.get_by_founded_year(1993)
    client.get_by_founded_year(1945)

    # Invalid years
    with pytest.raises(ValidationError):
        client.get_by_founded_year(999)  # Too small
    with pytest.raises(ValidationError):
        client.get_by_founded_year(10000)  # Too large
    with pytest.raises(ValidationError):
        client.get_by_founded_year("1993")  # Not an integer


def test_search_fuzzy_validation(mock_db_manager):
    """Test search query validation."""
    client = SearchClient(mock_db_manager)

    # Valid queries
    mock_db_manager.execute_query_dict.return_value = []
    client.fuzzy("test", limit=10)

    # Invalid queries
    with pytest.raises(ValidationError):
        client.fuzzy("", limit=10)  # Empty query
    with pytest.raises(ValidationError):
        client.fuzzy("   ", limit=10)  # Whitespace only
    with pytest.raises(ValidationError):
        client.fuzzy("test", limit=0)  # Invalid limit
    with pytest.raises(ValidationError):
        client.fuzzy("test", limit=-1)  # Negative limit
    with pytest.raises(ValidationError):
        client.fuzzy("test", limit="10")  # Limit not integer
