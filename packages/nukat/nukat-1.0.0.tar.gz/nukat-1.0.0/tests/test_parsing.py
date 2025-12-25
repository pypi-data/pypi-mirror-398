"""Tests for HTML parsing functionality."""

from bs4 import BeautifulSoup

from nukat.client import Nukat


class TestParseResultItem:
    """Test suite for _parse_result_item method."""

    def test_parse_complete_result(self):
        """Test parsing a complete result with all fields."""
        html = """
        <div class="title_summary">
            <a class="title" href="/cgi-bin/koha/opac-detail.pl?biblionumber=12345">
                Test Book Title / Author Name
            </a>
            <ul class="author resource_list">
                <li>
                    <a href="#">Kowalski, Jan</a>
                    <span class="relatorcode">[Author]</span>
                </li>
            </ul>
            <span class="publisher_date">2023.</span>
            <span class="publisher_name">Test Publisher,</span>
            <span class="publisher_place">Warsaw:</span>
            <span class="results_material_type">
                <span class="label">Material type:</span>
                Book
            </span>
            <span class="language">
                <span class="lang_code-eng">English</span>
            </span>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        item = soup.find("div", class_="title_summary")

        client = Nukat()
        result = client._parse_result_item(item)

        assert result is not None
        assert result["title"] == "Test Book Title"
        assert result["id"] == "12345"
        assert "Kowalski, Jan" in result["author"]
        assert result["year"] == "2023"
        assert result["publisher"] == "Test Publisher"
        assert result["place"] == "Warsaw"
        assert result["document_type"] == "Book"
        assert result["language"] == "English"

    def test_parse_title_without_slash(self):
        """Test parsing title without author part."""
        html = """
        <div class="title_summary">
            <a class="title" href="/cgi-bin/koha/opac-detail.pl?biblionumber=123">
                Simple Title
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        item = soup.find("div", class_="title_summary")

        client = Nukat()
        result = client._parse_result_item(item)

        assert result is not None
        assert result["title"] == "Simple Title"
        assert result["id"] == "123"

    def test_parse_multiple_authors(self):
        """Test parsing multiple authors."""
        html = """
        <div class="title_summary">
            <a class="title" href="/cgi-bin/koha/opac-detail.pl?biblionumber=999">Title</a>
            <ul class="author resource_list">
                <li><a href="#">Smith, John (1950-2020)</a></li>
                <li>
                    <a href="#">Doe, Jane</a>
                    <span class="relatorcode">[Translator]</span>
                </li>
            </ul>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        item = soup.find("div", class_="title_summary")

        client = Nukat()
        result = client._parse_result_item(item)

        assert result is not None
        assert "author" in result
        # Check that dates were removed
        assert "1950-2020" not in result["author"]
        assert "Smith, John" in result["author"]
        assert "Doe, Jane" in result["author"]
        assert "[Translator]" in result["author"]

    def test_parse_minimal_result(self):
        """Test parsing result with only title."""
        html = """
        <div class="title_summary">
            <a class="title" href="/cgi-bin/koha/opac-detail.pl?biblionumber=456">
                Minimal Title
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        item = soup.find("div", class_="title_summary")

        client = Nukat()
        result = client._parse_result_item(item)

        assert result is not None
        assert "title" in result
        assert "author" not in result
        assert "year" not in result

    def test_parse_without_url(self):
        """Test parsing result without biblionumber in URL."""
        html = """
        <div class="title_summary">
            <a class="title" href="/some/other/path">Title</a>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        item = soup.find("div", class_="title_summary")

        client = Nukat()
        result = client._parse_result_item(item)

        assert result is not None
        assert "title" in result
        assert "id" not in result


class TestParseRecordDetails:
    """Test suite for _parse_record_details method."""

    def test_parse_record_details_complete(self):
        """Test parsing complete record details."""
        html = """
        <html>
            <body>
                <h1 class="title">Complete Book Title</h1>
                <span class="author">Author, Test</span>
                <div id="catalogue_detail_biblio">
                    <span class="label">ISBN:</span>
                    <span>978-0-123456-78-9</span>
                    <span class="label">Publisher:</span>
                    <span>Test Publisher</span>
                </div>
            </body>
        </html>
        """
        client = Nukat()
        details = client._parse_record_details(html)

        assert details is not None
        assert details["title"] == "Complete Book Title"
        assert details["author"] == "Author, Test"
        assert "isbn" in details
        assert "publisher" in details

    def test_parse_record_details_minimal(self):
        """Test parsing minimal record details."""
        html = """
        <html>
            <body>
                <h1 class="title">Minimal Title</h1>
            </body>
        </html>
        """
        client = Nukat()
        details = client._parse_record_details(html)

        assert details is not None
        assert details["title"] == "Minimal Title"
        assert "author" not in details

    def test_parse_record_details_empty(self):
        """Test parsing empty HTML."""
        html = "<html><body></body></html>"
        client = Nukat()
        details = client._parse_record_details(html)

        assert details == {}


class TestParseSearchResults:
    """Test suite for _parse_search_results method."""

    def test_parse_multiple_results(self):
        """Test parsing multiple search results."""
        html = """
        <html>
            <body>
                <div class="title_summary">
                    <a class="title" href="/cgi-bin/koha/opac-detail.pl?biblionumber=1">Book 1</a>
                </div>
                <div class="title_summary">
                    <a class="title" href="/cgi-bin/koha/opac-detail.pl?biblionumber=2">Book 2</a>
                </div>
                <div class="title_summary">
                    <a class="title" href="/cgi-bin/koha/opac-detail.pl?biblionumber=3">Book 3</a>
                </div>
            </body>
        </html>
        """
        client = Nukat()
        results = client._parse_search_results(html)

        assert len(results) == 3
        assert results[0]["title"] == "Book 1"
        assert results[1]["title"] == "Book 2"
        assert results[2]["title"] == "Book 3"

    def test_parse_no_results(self):
        """Test parsing page with no results."""
        html = "<html><body></body></html>"
        client = Nukat()
        results = client._parse_search_results(html)

        assert results == []
