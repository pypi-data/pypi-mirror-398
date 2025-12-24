"""Tests for IntblocksClient functionality."""

from internacia.intblocks import IntblocksClient


class TestIntblocksClientGetById:
    """Test get_by_id method."""

    def test_get_by_id_success(self, mock_db_manager, sample_block_data):
        """Test successful retrieval by ID."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        result = client.get_by_id("EU")

        assert result == sample_block_data
        mock_db_manager.execute_query_dict.assert_called_once()
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "id = ?" in call_args[0][0]
        assert call_args[0][1] == ("EU",)

    def test_get_by_id_not_found(self, mock_db_manager):
        """Test when block not found."""
        mock_db_manager.execute_query_dict.return_value = []
        client = IntblocksClient(mock_db_manager)

        result = client.get_by_id("XXX")

        assert result is None

    def test_get_by_id_case_insensitive(self, mock_db_manager, sample_block_data):
        """Test that ID is converted to uppercase."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        client.get_by_id("eu")

        call_args = mock_db_manager.execute_query_dict.call_args
        assert call_args[0][1] == ("EU",)


class TestIntblocksClientGetAll:
    """Test get_all method."""

    def test_get_all_without_limit(self, mock_db_manager, sample_block_data):
        """Test get_all without limit."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        result = client.get_all()

        assert result == [sample_block_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "LIMIT" not in call_args[0][0]
        # When no limit, only query is passed (no parameters tuple)
        assert len(call_args[0]) == 1

    def test_get_all_with_limit(self, mock_db_manager, sample_block_data):
        """Test get_all with limit."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        result = client.get_all(limit=10)

        assert result == [sample_block_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "LIMIT ?" in call_args[0][0]
        assert call_args[0][1] == (10,)


class TestIntblocksClientGetByBlocktype:
    """Test get_by_blocktype method."""

    def test_get_by_blocktype(self, mock_db_manager, sample_block_data):
        """Test get_by_blocktype."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        result = client.get_by_blocktype("economic")

        assert result == [sample_block_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "LIST_CONTAINS(blocktype, ?)" in call_args[0][0]
        assert call_args[0][1] == ("economic",)

    def test_get_by_blocktype_case_insensitive(self, mock_db_manager, sample_block_data):
        """Test that blocktype is converted to lowercase."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        client.get_by_blocktype("ECONOMIC")

        call_args = mock_db_manager.execute_query_dict.call_args
        assert call_args[0][1] == ("economic",)


class TestIntblocksClientGetByStatus:
    """Test get_by_status method."""

    def test_get_by_status(self, mock_db_manager, sample_block_data):
        """Test get_by_status."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        result = client.get_by_status("formal")

        assert result == [sample_block_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "status = ?" in call_args[0][0]
        assert call_args[0][1] == ("formal",)

    def test_get_by_status_case_insensitive(self, mock_db_manager, sample_block_data):
        """Test that status is converted to lowercase."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        client.get_by_status("FORMAL")

        call_args = mock_db_manager.execute_query_dict.call_args
        assert call_args[0][1] == ("formal",)


class TestIntblocksClientGetByGeographicScope:
    """Test get_by_geographic_scope method."""

    def test_get_by_geographic_scope(self, mock_db_manager, sample_block_data):
        """Test get_by_geographic_scope."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        result = client.get_by_geographic_scope("regional")

        assert result == [sample_block_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "geographic_scope = ?" in call_args[0][0]
        assert call_args[0][1] == ("regional",)

    def test_get_by_geographic_scope_case_insensitive(self, mock_db_manager, sample_block_data):
        """Test that scope is converted to lowercase."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        client.get_by_geographic_scope("REGIONAL")

        call_args = mock_db_manager.execute_query_dict.call_args
        assert call_args[0][1] == ("regional",)


class TestIntblocksClientGetByMember:
    """Test get_by_member method."""

    def test_get_by_member(self, mock_db_manager, sample_block_data):
        """Test get_by_member."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        result = client.get_by_member("US")

        assert result == [sample_block_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "member.id = ?" in call_args[0][0]
        assert call_args[0][1] == ("US",)

    def test_get_by_member_case_insensitive(self, mock_db_manager, sample_block_data):
        """Test that country code is converted to uppercase."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        client.get_by_member("us")

        call_args = mock_db_manager.execute_query_dict.call_args
        assert call_args[0][1] == ("US",)


class TestIntblocksClientGetByAcronym:
    """Test get_by_acronym method."""

    def test_get_by_acronym(self, mock_db_manager, sample_block_data):
        """Test get_by_acronym."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        result = client.get_by_acronym("EU")

        assert result == [sample_block_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "acronyms" in call_args[0][0]
        assert call_args[0][1] == ("EU",)

    def test_get_by_acronym_case_insensitive(self, mock_db_manager, sample_block_data):
        """Test that acronym is converted to uppercase."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        client.get_by_acronym("eu")

        call_args = mock_db_manager.execute_query_dict.call_args
        assert call_args[0][1] == ("EU",)


class TestIntblocksClientGetByTag:
    """Test get_by_tag method."""

    def test_get_by_tag(self, mock_db_manager, sample_block_data):
        """Test get_by_tag."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        result = client.get_by_tag("trade")

        assert result == [sample_block_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "LIST_CONTAINS(tags, ?)" in call_args[0][0]
        assert call_args[0][1] == ("trade",)

    def test_get_by_tag_case_insensitive(self, mock_db_manager, sample_block_data):
        """Test that tag is converted to lowercase."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        client.get_by_tag("TRADE")

        call_args = mock_db_manager.execute_query_dict.call_args
        assert call_args[0][1] == ("trade",)


class TestIntblocksClientGetByTopic:
    """Test get_by_topic method."""

    def test_get_by_topic(self, mock_db_manager, sample_block_data):
        """Test get_by_topic."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        result = client.get_by_topic("economy")

        assert result == [sample_block_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "topic.key = ?" in call_args[0][0]
        assert call_args[0][1] == ("economy",)

    def test_get_by_topic_case_insensitive(self, mock_db_manager, sample_block_data):
        """Test that topic key is converted to lowercase."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        client.get_by_topic("ECONOMY")

        call_args = mock_db_manager.execute_query_dict.call_args
        assert call_args[0][1] == ("economy",)


class TestIntblocksClientGetByFoundedYear:
    """Test get_by_founded_year method."""

    def test_get_by_founded_year_success(self, mock_db_manager, sample_block_data):
        """Test successful retrieval by founded year."""
        mock_db_manager.execute_query_dict.return_value = [sample_block_data]
        client = IntblocksClient(mock_db_manager)

        result = client.get_by_founded_year(1993)

        assert result == [sample_block_data]
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "founded LIKE ?" in call_args[0][0]
        assert call_args[0][1] == ("1993%",)

    def test_get_by_founded_year_not_found(self, mock_db_manager):
        """Test when no blocks found."""
        mock_db_manager.execute_query_dict.return_value = []
        client = IntblocksClient(mock_db_manager)

        result = client.get_by_founded_year(1993)

        assert not result


class TestIntblocksClientCount:
    """Test count method."""

    def test_count(self, mock_db_manager):
        """Test count."""
        mock_db_manager.execute_query_dict.return_value = [{"count": 50}]
        client = IntblocksClient(mock_db_manager)

        result = client.count()

        assert result == 50
        call_args = mock_db_manager.execute_query_dict.call_args
        assert "COUNT(*)" in call_args[0][0]

    def test_count_empty(self, mock_db_manager):
        """Test count when no results."""
        mock_db_manager.execute_query_dict.return_value = []
        client = IntblocksClient(mock_db_manager)

        result = client.count()

        assert result == 0
