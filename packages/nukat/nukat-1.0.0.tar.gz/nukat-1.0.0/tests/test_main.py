"""Tests for the main module."""

from unittest.mock import MagicMock, patch

import pytest

from nukat.client import NukatError
from nukat.main import main


def test_main_no_arguments(capsys):
    """Test main function without arguments."""
    with patch("sys.argv", ["nukat"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2


def test_main_with_query(capsys):
    """Test main function with search query."""
    test_results = [
        {
            "title": "Test Book",
            "author": "Test Author",
            "year": "2023",
            "url": "https://katalog.nukat.edu.pl/test",
            "id": "12345",
        }
    ]

    with patch("sys.argv", ["nukat", "test", "query"]):
        with patch("nukat.main.Nukat") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = test_results
            mock_client_class.return_value = mock_client

            main()
            captured = capsys.readouterr()

            assert "Test Book" in captured.out
            assert "Test Author" in captured.out
            assert "2023" in captured.out


def test_main_no_results(capsys):
    """Test main function when no results found."""
    with patch("sys.argv", ["nukat", "nonexistent"]):
        with patch("nukat.main.Nukat") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = []
            mock_client_class.return_value = mock_client

            main()
            captured = capsys.readouterr()

            assert "No results found" in captured.out


def test_main_client_error(capsys):
    """Test main function handling client errors."""
    with patch("sys.argv", ["nukat", "test"]):
        with patch("nukat.main.Nukat") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.side_effect = NukatError("Test error")
            mock_client_class.return_value = mock_client

            with pytest.raises(SystemExit):
                main()

            captured = capsys.readouterr()
            assert "Error:" in captured.err


def test_main_with_limit(capsys):
    """Test main function with custom limit."""
    test_results = [{"title": f"Book {i}", "year": "2023", "id": str(i)} for i in range(5)]

    with patch("sys.argv", ["nukat", "test", "--limit", "5"]):
        with patch("nukat.main.Nukat") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = test_results
            mock_client_class.return_value = mock_client

            main()
            captured = capsys.readouterr()

            assert "first 5 results" in captured.out
            assert "Book 0" in captured.out or "Book 4" in captured.out


def test_main_with_all_flag(capsys):
    """Test main function with --all flag."""
    test_results = [{"title": "Book 1", "year": "2023"}, {"title": "Book 2", "year": "2024"}]

    with patch("sys.argv", ["nukat", "test", "--all"]):
        with patch("nukat.main.Nukat") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search_all.return_value = test_results
            mock_client_class.return_value = mock_client

            main()
            captured = capsys.readouterr()

            assert "all results" in captured.out
            assert "Book 1" in captured.out
            assert "Book 2" in captured.out


def test_main_with_id_flag(capsys):
    """Test main function with --id flag to get record details."""
    test_details = {
        "title": "Test Book Details",
        "author": "Test Author",
        "year": "2023",
        "isbn": "978-0-123456-78-9",
    }

    with patch("sys.argv", ["nukat", "12345", "--id"]):
        with patch("nukat.main.Nukat") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_record_details.return_value = test_details
            mock_client_class.return_value = mock_client

            main()
            captured = capsys.readouterr()

            assert "Record details" in captured.out
            assert "Test Book Details" in captured.out
            assert "Test Author" in captured.out
            mock_client.get_record_details.assert_called_once_with("12345")


def test_main_with_id_flag_not_found(capsys):
    """Test main function with --id flag when record is not found."""
    with patch("sys.argv", ["nukat", "99999", "--id"]):
        with patch("nukat.main.Nukat") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_record_details.return_value = {}
            mock_client_class.return_value = mock_client

            main()
            captured = capsys.readouterr()

            assert "Record not found" in captured.out
            mock_client.get_record_details.assert_called_once_with("99999")
