"""Tests for the NUKAT client module."""

from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from nukat.client import Nukat, NukatError


class TestNukat:
    """Test suite for Nukat."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = Nukat(timeout=60)
        assert client.timeout == 60
        assert client.BASE_URL == "https://katalog.nukat.edu.pl"

    def test_build_search_params_basic(self):
        """Test building basic search parameters."""
        client = Nukat()
        params = client._build_search_params(
            query="Python",
            limit=20,
            offset=0,
            index=None,
            sort_by=None,
            language=None,
            document_type=None,
            year_from=None,
            year_to=None,
        )

        assert params["q"] == "Python"
        assert params["theme"] == "nukat"
        assert params["count"] == 20

    def test_build_search_params_with_filters(self):
        """Test building search parameters with filters."""
        client = Nukat()
        params = client._build_search_params(
            query="Python",
            limit=10,
            offset=20,
            index="ti",
            sort_by="relevance",
            language="pol",
            document_type="BK",
            year_from=2020,
            year_to=2024,
        )

        assert params["q"] == "Python"
        assert params["idx"] == "ti"
        assert params["offset"] == 20
        assert params["sort_by"] == "relevance"
        assert "limit-yr" in params
        assert params["limit-yr"] == "2020-2024"

    def test_search_by_author(self):
        """Test search by author convenience method."""
        client = Nukat()

        with patch.object(client, "search", return_value=[]) as mock_search:
            client.search_by_author("Kowalski Jan", limit=50)
            mock_search.assert_called_once_with(query="Kowalski Jan", index="au", limit=50)

    def test_search_by_title(self):
        """Test search by title convenience method."""
        client = Nukat()

        with patch.object(client, "search", return_value=[]) as mock_search:
            client.search_by_title("Python Programming", year_from=2020)
            mock_search.assert_called_once_with(
                query="Python Programming", index="ti", year_from=2020
            )

    def test_search_by_isbn(self):
        """Test search by ISBN convenience method."""
        client = Nukat()

        with patch.object(client, "search", return_value=[]) as mock_search:
            client.search_by_isbn("978-0-123456-78-9")
            mock_search.assert_called_once_with(query="978-0-123456-78-9", index="nb")

    def test_search_by_subject(self):
        """Test search by subject convenience method."""
        client = Nukat()

        with patch.object(client, "search", return_value=[]) as mock_search:
            client.search_by_subject("Informatyka", language="pol")
            mock_search.assert_called_once_with(query="Informatyka", index="su", language="pol")

    def test_search_network_error(self):
        """Test handling network errors during search."""
        client = Nukat()

        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")

            with pytest.raises(NukatError) as exc_info:
                client.search("Python")

            assert "Error during search" in str(exc_info.value)

    def test_parse_result_item_empty(self):
        """Test parsing empty result item."""
        from bs4 import BeautifulSoup

        client = Nukat()
        soup = BeautifulSoup("<div></div>", "lxml")
        result = client._parse_result_item(soup.div)

        assert result == {} or result is None

    def test_year_range_only_from(self):
        """Test year range with only start year."""
        client = Nukat()
        params = client._build_search_params(
            query="test",
            limit=10,
            offset=0,
            index=None,
            sort_by=None,
            language=None,
            document_type=None,
            year_from=2020,
            year_to=None,
        )

        assert params["limit-yr"] == "2020-"

    def test_year_range_only_to(self):
        """Test year range with only end year."""
        client = Nukat()
        params = client._build_search_params(
            query="test",
            limit=10,
            offset=0,
            index=None,
            sort_by=None,
            language=None,
            document_type=None,
            year_from=None,
            year_to=2020,
        )

        assert params["limit-yr"] == "-2020"

    def test_search_limit_exceeds_max(self):
        """Test that search limits results to max 100 per page."""
        client = Nukat()

        with patch.object(client.session, "get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = "<html></html>"
            mock_response.raise_for_status = lambda: None

            client.search("test", limit=200)

            # Should be capped at 100
            args, kwargs = mock_get.call_args
            assert kwargs["params"]["count"] == 100


class TestNukatError:
    """Test suite for NukatError exception."""

    def test_exception_message(self):
        """Test exception message."""
        error = NukatError("Test error")
        assert str(error) == "Test error"

    def test_exception_inheritance(self):
        """Test exception inheritance."""
        error = NukatError("Test")
        assert isinstance(error, Exception)
