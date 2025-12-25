"""Tests for search_all and pagination functionality."""

from unittest.mock import patch

from nukat.client import Nukat


class TestSearchAll:
    """Test suite for search_all method."""

    def test_search_all_single_page(self):
        """Test search_all when all results fit in one page."""
        client = Nukat()

        test_results = [{"title": f"Book {i}", "id": str(i)} for i in range(10)]

        with patch.object(client, "search", return_value=test_results) as mock_search:
            results = client.search_all("test query", page_size=100)

            assert len(results) == 10
            mock_search.assert_called_once()

    def test_search_all_multiple_pages(self):
        """Test search_all with pagination across multiple pages."""
        client = Nukat()

        # Simulate 3 pages of results
        page1 = [{"title": f"Book {i}", "id": str(i)} for i in range(100)]
        page2 = [{"title": f"Book {i}", "id": str(i + 100)} for i in range(100)]
        page3 = [{"title": f"Book {i}", "id": str(i + 200)} for i in range(50)]

        with patch.object(client, "search", side_effect=[page1, page2, page3]) as mock_search:
            results = client.search_all("test query", page_size=100)

            assert len(results) == 250
            assert mock_search.call_count == 3
            # Check that offset was properly incremented
            assert mock_search.call_args_list[0][1]["offset"] == 0
            assert mock_search.call_args_list[1][1]["offset"] == 100
            assert mock_search.call_args_list[2][1]["offset"] == 200

    def test_search_all_with_max_results(self):
        """Test search_all with max_results limit."""
        client = Nukat()

        page1 = [{"title": f"Book {i}", "id": str(i)} for i in range(100)]
        page2 = [{"title": f"Book {i}", "id": str(i + 100)} for i in range(100)]

        with patch.object(client, "search", side_effect=[page1, page2]) as mock_search:
            results = client.search_all("test query", max_results=150, page_size=100)

            # Should stop after getting 150 results
            assert len(results) == 150
            assert mock_search.call_count == 2

    def test_search_all_empty_results(self):
        """Test search_all when no results are found."""
        client = Nukat()

        with patch.object(client, "search", return_value=[]) as mock_search:
            results = client.search_all("nonexistent query")

            assert len(results) == 0
            mock_search.assert_called_once()

    def test_search_all_stops_on_partial_page(self):
        """Test that search_all stops when getting less than page_size results."""
        client = Nukat()

        page1 = [{"title": f"Book {i}", "id": str(i)} for i in range(100)]
        page2 = [{"title": f"Book {i}", "id": str(i + 100)} for i in range(30)]

        with patch.object(client, "search", side_effect=[page1, page2]) as mock_search:
            results = client.search_all("test query", page_size=100)

            # Should stop after page2 since it has less than page_size results
            assert len(results) == 130
            assert mock_search.call_count == 2

    def test_search_all_with_kwargs(self):
        """Test that search_all passes through additional kwargs."""
        client = Nukat()

        test_results = [{"title": "Book 1"}]

        with patch.object(client, "search", return_value=test_results) as mock_search:
            results = client.search_all(
                "test query", page_size=50, language="eng", year_from=2020, year_to=2023
            )

            assert len(results) == 1
            # Check that kwargs were passed through
            call_kwargs = mock_search.call_args[1]
            assert call_kwargs["language"] == "eng"
            assert call_kwargs["year_from"] == 2020
            assert call_kwargs["year_to"] == 2023

    def test_search_all_max_results_less_than_page(self):
        """Test search_all when max_results is less than page_size."""
        client = Nukat()

        page1 = [{"title": f"Book {i}", "id": str(i)} for i in range(100)]

        with patch.object(client, "search", return_value=page1) as mock_search:
            results = client.search_all("test query", max_results=50, page_size=100)

            assert len(results) == 50
            mock_search.assert_called_once()
