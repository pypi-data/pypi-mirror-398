"""NUKAT Catalog Client - module for searching NUKAT catalog."""

from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class Nukat:
    """Client for searching the NUKAT library catalog.

    Example usage:
        client = Nukat()
        results = client.search("Python programming")
        for result in results:
            print(result['title'])
    """

    BASE_URL = "https://katalog.nukat.edu.pl"
    SEARCH_PATH = "/cgi-bin/koha/opac-search.pl"

    def __init__(self, timeout: int = 30):
        """Initialize the NUKAT client.

        Args:
            timeout: Timeout for HTTP requests in seconds (default 30)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "NukatClient/0.1.0 (Python)"})

    def search(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        index: Optional[str] = None,
        sort_by: Optional[str] = None,
        language: Optional[str] = None,
        document_type: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search the NUKAT catalog.

        Args:
            query: Search query
            limit: Maximum number of results per page (default 20, max 100)
            offset: Result offset (default 0)
            index: Search type (e.g. 'ti' for title, 'au' for author)
            sort_by: Result sorting method
            language: Language filter
            document_type: Document type filter
            year_from: Start year of date range
            year_to: End year of date range

        Returns:
            List of dictionaries with search results
        """
        # Maximum 100 results per page
        if limit > 100:
            limit = 100

        params = self._build_search_params(
            query=query,
            limit=limit,
            offset=offset,
            index=index,
            sort_by=sort_by,
            language=language,
            document_type=document_type,
            year_from=year_from,
            year_to=year_to,
        )

        url = urljoin(self.BASE_URL, self.SEARCH_PATH)

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return self._parse_search_results(response.text)
        except requests.RequestException as e:
            raise NukatError(f"Error during search: {e}") from e

    def _build_search_params(
        self,
        query: str,
        limit: int,
        offset: int,
        index: Optional[str],
        sort_by: Optional[str],
        language: Optional[str],
        document_type: Optional[str],
        year_from: Optional[int],
        year_to: Optional[int],
    ) -> Dict[str, Any]:
        """Build search query parameters."""
        params = {
            "q": query,
            "theme": "nukat",
            "count": limit,
        }

        if offset > 0:
            params["offset"] = offset
        if index:
            params["idx"] = index
        if sort_by:
            params["sort_by"] = sort_by
        if language:
            params["limit"] = f"ln:{language}"
        if document_type:
            params["limit"] = f"mc-itype:{document_type}"
        if year_from is not None and year_to is not None:
            params["limit-yr"] = f"{year_from}-{year_to}"
        elif year_from is not None:
            params["limit-yr"] = f"{year_from}-"
        elif year_to is not None:
            params["limit-yr"] = f"-{year_to}"

        return params

    def _parse_search_results(self, html: str) -> List[Dict[str, Any]]:
        """Parse HTML with search results.

        Args:
            html: HTML page with results

        Returns:
            List of dictionaries with results
        """
        soup = BeautifulSoup(html, "lxml")
        results = []

        # Results are in divs with class title_summary
        result_items = soup.find_all("div", class_="title_summary")

        for item in result_items:
            result = self._parse_result_item(item)
            if result:
                results.append(result)

        return results

    def _parse_result_item(self, item) -> Optional[Dict[str, Any]]:
        """Parse a single result item.

        Args:
            item: BeautifulSoup element representing a result

        Returns:
            Dictionary with result data or None if parsing failed
        """
        result = {}

        # Title - link with class "title"
        title_elem = item.find("a", class_="title")
        if title_elem:
            # Remove title_resp_stmt part to get clean title
            title_text = title_elem.get_text(strip=True)
            # Sometimes author is in title, so we cut off the part after /
            if " / " in title_text:
                title_text = title_text.split(" / ")[0].strip()
            result["title"] = title_text
            result["url"] = urljoin(self.BASE_URL, title_elem.get("href", ""))

            # Record ID from URL
            import re

            match = re.search(r"biblionumber=(\d+)", result["url"])
            if match:
                result["id"] = match.group(1)

        # Author - in ul.author.resource_list
        author_list = item.find("ul", class_="author")
        if author_list:
            authors = []
            for li in author_list.find_all("li"):
                author_link = li.find("a")
                if author_link:
                    author_text = author_link.get_text(strip=True)
                    # Remove dates in parentheses
                    author_text = re.sub(r"\s*\([^)]*\)\s*", "", author_text)
                    # Remove relatorcode like [Transl.]
                    relator = li.find("span", class_="relatorcode")
                    if relator:
                        relator_text = relator.get_text(strip=True)
                        if relator_text:
                            author_text += " " + relator_text
                    authors.append(author_text)
            if authors:
                result["author"] = "; ".join(authors)

        # Publication year - in span with class publisher_date
        year_elem = item.find("span", class_="publisher_date")
        if year_elem:
            year_text = year_elem.get_text(strip=True).rstrip(".")
            result["year"] = year_text

        # Publisher - in span with class publisher_name
        publisher_elem = item.find("span", class_="publisher_name")
        if publisher_elem:
            result["publisher"] = publisher_elem.get_text(strip=True).rstrip(",")

        # Publication place
        place_elem = item.find("span", class_="publisher_place")
        if place_elem:
            result["place"] = place_elem.get_text(strip=True).rstrip(":")

        # Document type
        doc_type_elem = item.find("span", class_="results_material_type")
        if doc_type_elem:
            # Extract just the text, without "Material type:" label
            label = doc_type_elem.find("span", class_="label")
            if label:
                label.extract()
            result["document_type"] = doc_type_elem.get_text(strip=True)

        # Language
        lang_elem = item.find("span", class_="language")
        if lang_elem:
            lang_code = lang_elem.find("span", class_=lambda x: x and "lang_code-" in str(x))
            if lang_code:
                result["language"] = lang_code.get_text(strip=True)

        return result if result else None

    def get_record_details(self, record_id: str) -> Dict[str, Any]:
        """Fetch detailed information about a record.

        Args:
            record_id: Record ID (biblionumber)

        Returns:
            Dictionary with detailed record information
        """
        url = urljoin(self.BASE_URL, f"/cgi-bin/koha/opac-detail.pl?biblionumber={record_id}")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return self._parse_record_details(response.text)
        except requests.RequestException as e:
            raise NukatError(f"Error fetching record details: {e}") from e

    def _parse_record_details(self, html: str) -> Dict[str, Any]:
        """Parse record details.

        Args:
            html: HTML page with details

        Returns:
            Dictionary with detailed data
        """
        soup = BeautifulSoup(html, "lxml")
        details = {}

        # Title
        title_elem = soup.find("h1", class_="title")
        if title_elem:
            details["title"] = title_elem.get_text(strip=True)

        # Author
        author_elem = soup.find("span", class_="author")
        if author_elem:
            details["author"] = author_elem.get_text(strip=True)

        # Metadata in div #catalogue_detail_biblio
        detail_div = soup.find("div", id="catalogue_detail_biblio")
        if detail_div:
            # Find all lists with metadata
            for span in detail_div.find_all("span", class_="label"):
                label = span.get_text(strip=True).rstrip(":")
                value_elem = span.find_next_sibling()
                if value_elem:
                    value = value_elem.get_text(strip=True)
                    details[label.lower().replace(" ", "_")] = value

        return details

    def search_all(
        self, query: str, max_results: Optional[int] = None, page_size: int = 100, **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Fetch all search results using pagination.

        Args:
            query: Search query
            max_results: Maximum number of results to fetch (None = all)
            page_size: Number of results per page (max 100)
            **kwargs: Additional parameters passed to search()

        Returns:
            List of all search results
        """
        all_results = []
        offset = 0

        while True:
            # Fetch page of results
            results = self.search(query=query, limit=page_size, offset=offset, **kwargs)

            if not results:
                # End of results
                break

            all_results.extend(results)

            # Check if we reached the limit
            if max_results and len(all_results) >= max_results:
                all_results = all_results[:max_results]
                break

            # Move to next page
            offset += page_size

            # If we got fewer results than page size, we're done
            if len(results) < page_size:
                break

        return all_results

    def search_by_author(self, author: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Search by author.

        Args:
            author: Author name
            **kwargs: Additional parameters passed to search()

        Returns:
            List of search results
        """
        return self.search(query=author, index="au", **kwargs)

    def search_by_title(self, title: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Search by title.

        Args:
            title: Publication title
            **kwargs: Additional parameters passed to search()

        Returns:
            List of search results
        """
        return self.search(query=title, index="ti", **kwargs)

    def search_by_subject(self, subject: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Search by subject.

        Args:
            subject: Subject/topic heading
            **kwargs: Additional parameters passed to search()

        Returns:
            List of search results
        """
        return self.search(query=subject, index="su", **kwargs)

    def search_by_isbn(self, isbn: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Search by ISBN number.

        Args:
            isbn: ISBN number
            **kwargs: Additional parameters passed to search()

        Returns:
            List of search results
        """
        return self.search(query=isbn, index="nb", **kwargs)


class NukatError(Exception):
    """Exception for NUKAT client errors."""

    pass
