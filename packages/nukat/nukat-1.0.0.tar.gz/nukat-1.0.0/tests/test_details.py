"""Tests for get_record_details functionality."""

from unittest.mock import patch

import pytest
import requests

from nukat.client import Nukat, NukatError


class TestGetRecordDetails:
    """Test suite for get_record_details method."""

    def test_get_record_details_success(self):
        """Test successful retrieval of record details."""
        client = Nukat()

        html_response = """
        <html>
            <body>
                <h1 class="title">Test Book Title</h1>
                <span class="author">Test Author</span>
                <div id="catalogue_detail_biblio">
                    <span class="label">ISBN:</span>
                    <span>978-0-123456-78-9</span>
                </div>
            </body>
        </html>
        """

        with patch.object(client.session, "get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = html_response
            mock_response.raise_for_status = lambda: None

            details = client.get_record_details("12345")

            assert details is not None
            assert details["title"] == "Test Book Title"
            assert details["author"] == "Test Author"
            mock_get.assert_called_once()
            # Check that correct URL was called
            args, kwargs = mock_get.call_args
            assert "biblionumber=12345" in args[0]

    def test_get_record_details_network_error(self):
        """Test handling network error in get_record_details."""
        client = Nukat()

        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")

            with pytest.raises(NukatError) as exc_info:
                client.get_record_details("12345")

            assert "Error fetching record details" in str(exc_info.value)

    def test_get_record_details_http_error(self):
        """Test handling HTTP error in get_record_details."""
        client = Nukat()

        with patch.object(client.session, "get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

            with pytest.raises(NukatError):
                client.get_record_details("99999")
