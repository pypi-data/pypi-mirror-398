"""Tests for CountriesClient functionality."""

from internacia.countries import CountriesClient


class TestCountriesClientGetByCode:
    """Test get_by_code method."""

    def test_get_by_code_success(self, mock_db_manager, sample_country_data):
        """Test successful retrieval by code."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        result = client.get_by_code("US")

        assert result == sample_country_data
        mock_db_manager.execute_query_dict.assert_called_once()
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "code = ?" in call_args[0][0]
        assert call_args[0][1] == ("US",)

    def test_get_by_code_not_found(self, mock_db_manager):
        """Test when country not found."""
        mock_db_manager.execute_query_dict.return_value = []
        client = CountriesClient(mock_db_manager)

        result = client.get_by_code("XX")

        assert result is None

    def test_get_by_code_case_insensitive(self, mock_db_manager, sample_country_data):
        """Test that code is converted to uppercase."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        client.get_by_code("us")

        call_args = mock_db_manager.execute_query_dict.call_args
        assert call_args[0][1] == ("US",)


class TestCountriesClientGetByIso3:
    """Test get_by_iso3 method."""

    def test_get_by_iso3_success(self, mock_db_manager, sample_country_data):
        """Test successful retrieval by ISO3 code."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        result = client.get_by_iso3("USA")

        assert result == sample_country_data
        mock_db_manager.execute_query_dict.assert_called_once()
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "iso3code = ?" in call_args[0][0]
        assert call_args[0][1] == ("USA",)

    def test_get_by_iso3_not_found(self, mock_db_manager):
        """Test when country not found."""
        mock_db_manager.execute_query_dict.return_value = []
        client = CountriesClient(mock_db_manager)

        result = client.get_by_iso3("XXX")

        assert result is None

    def test_get_by_iso3_case_insensitive(self, mock_db_manager, sample_country_data):
        """Test that ISO3 code is converted to uppercase."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        client.get_by_iso3("usa")

        call_args = mock_db_manager.execute_query_dict.call_args
        assert call_args[0][1] == ("USA",)


class TestCountriesClientGetByNumericCode:
    """Test get_by_numeric_code method."""

    def test_get_by_numeric_code_success(self, mock_db_manager, sample_country_data):
        """Test successful retrieval by numeric code."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        result = client.get_by_numeric_code("840")

        assert result == sample_country_data
        mock_db_manager.execute_query_dict.assert_called_once()
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "numeric_code = ?" in call_args[0][0]
        assert call_args[0][1] == ("840",)

    def test_get_by_numeric_code_not_found(self, mock_db_manager):
        """Test when country not found."""
        mock_db_manager.execute_query_dict.return_value = []
        client = CountriesClient(mock_db_manager)

        result = client.get_by_numeric_code("999")

        assert result is None


class TestCountriesClientGetAll:
    """Test get_all method."""

    def test_get_all_without_limit(self, mock_db_manager, sample_country_data):
        """Test get_all without limit."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        result = client.get_all()

        assert result == [sample_country_data]
        mock_db_manager.execute_query_dict.assert_called_once()
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "LIMIT" not in call_args[0][0]
        # When no limit, only query is passed (no parameters tuple)
        assert len(call_args[0]) == 1

    def test_get_all_with_limit(self, mock_db_manager, sample_country_data):
        """Test get_all with limit."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        result = client.get_all(limit=10)

        assert result == [sample_country_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "LIMIT ?" in call_args[0][0]
        assert call_args[0][1] == (10,)


class TestCountriesClientGetByRegion:
    """Test get_by_region method."""

    def test_get_by_region(self, mock_db_manager, sample_country_data):
        """Test get_by_region."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        result = client.get_by_region("NAC")

        assert result == [sample_country_data]
        mock_db_manager.execute_query_dict.assert_called_once()
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "region.id = ?" in call_args[0][0]
        assert call_args[0][1] == ("NAC",)


class TestCountriesClientGetByIncomeLevel:
    """Test get_by_income_level method."""

    def test_get_by_income_level(self, mock_db_manager, sample_country_data):
        """Test get_by_income_level."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        result = client.get_by_income_level("HIC")

        assert result == [sample_country_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "incomeLevel.id = ?" in call_args[0][0]
        assert call_args[0][1] == ("HIC",)


class TestCountriesClientGetUnMembers:
    """Test get_un_members method."""

    def test_get_un_members(self, mock_db_manager, sample_country_data):
        """Test get_un_members."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        result = client.get_un_members()

        assert result == [sample_country_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "un_member = true" in call_args[0][0]


class TestCountriesClientGetIndependent:
    """Test get_independent method."""

    def test_get_independent(self, mock_db_manager, sample_country_data):
        """Test get_independent."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        result = client.get_independent()

        assert result == [sample_country_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "independent = true" in call_args[0][0]


class TestCountriesClientGetByContinent:
    """Test get_by_continent method."""

    def test_get_by_continent(self, mock_db_manager, sample_country_data):
        """Test get_by_continent."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        result = client.get_by_continent("North America")

        assert result == [sample_country_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "LIST_CONTAINS(continents, ?)" in call_args[0][0]
        assert call_args[0][1] == ("North America",)


class TestCountriesClientGetByCurrency:
    """Test get_by_currency method."""

    def test_get_by_currency(self, mock_db_manager, sample_country_data):
        """Test get_by_currency."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        result = client.get_by_currency("USD")

        assert result == [sample_country_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "curr.code = ?" in call_args[0][0]
        assert call_args[0][1] == ("USD",)

    def test_get_by_currency_case_insensitive(self, mock_db_manager, sample_country_data):
        """Test that currency code is converted to uppercase."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        client.get_by_currency("usd")

        call_args = mock_db_manager.execute_query_dict.call_args
        assert call_args[0][1] == ("USD",)


class TestCountriesClientGetByLanguage:
    """Test get_by_language method."""

    def test_get_by_language(self, mock_db_manager, sample_country_data):
        """Test get_by_language."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        result = client.get_by_language("eng")

        assert result == [sample_country_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "lang.code = ?" in call_args[0][0]
        assert call_args[0][1] == ("eng",)

    def test_get_by_language_case_insensitive(self, mock_db_manager, sample_country_data):
        """Test that language code is converted to lowercase."""
        mock_db_manager.execute_query_dict.return_value = [sample_country_data]
        client = CountriesClient(mock_db_manager)

        client.get_by_language("ENG")

        call_args = mock_db_manager.execute_query_dict.call_args
        assert call_args[0][1] == ("eng",)


class TestCountriesClientCount:
    """Test count method."""

    def test_count(self, mock_db_manager):
        """Test count."""
        mock_db_manager.execute_query_dict.return_value = [{"count": 195}]
        client = CountriesClient(mock_db_manager)

        result = client.count()

        assert result == 195
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "COUNT(*)" in call_args[0][0]

    def test_count_empty(self, mock_db_manager):
        """Test count when no results."""
        mock_db_manager.execute_query_dict.return_value = []
        client = CountriesClient(mock_db_manager)

        result = client.count()

        assert result == 0
