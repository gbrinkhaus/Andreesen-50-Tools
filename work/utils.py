#!/usr/bin/env python3
"""
Utils - Shared utility functions for URL validation and content fetching
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Tuple, List, Optional


class URLValidator:
    """Validates URLs by making HTTP requests"""

    def __init__(self, timeout=10):
        """
        Initialize URL validator

        Args:
            timeout: Seconds to wait for response
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Validate if a URL is accessible

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, status_message)
        """
        if not url or url.strip() == "":
            return False, "Empty URL"

        try:
            response = self.session.head(
                url, timeout=self.timeout, allow_redirects=True
            )

            # If HEAD request doesn't work, try GET
            if response.status_code >= 400:
                response = self.session.get(
                    url, timeout=self.timeout, allow_redirects=True
                )

            if response.status_code == 200:
                return True, f"HTTP {response.status_code}"
            elif 200 <= response.status_code < 300:
                return True, f"HTTP {response.status_code}"
            elif response.status_code == 403:
                # Some sites block HEAD requests but work with GET
                try:
                    response = self.session.get(
                        url, timeout=self.timeout, allow_redirects=True
                    )
                    if response.status_code == 200:
                        return True, f"HTTP {response.status_code} (via GET)"
                except:
                    pass
                return False, f"HTTP {response.status_code} Forbidden"
            else:
                return False, f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "Timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection Error"
        except requests.exceptions.TooManyRedirects:
            return False, "Too Many Redirects"
        except requests.exceptions.RequestException as e:
            return False, f"Request Error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"


class ContentFetcher:
    """Fetches and parses web page content"""

    def __init__(self, timeout=10):
        """
        Initialize content fetcher

        Args:
            timeout: Seconds to wait for response
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def fetch_content(self, url: str) -> Optional[str]:
        """
        Fetch the HTML content of a URL

        Args:
            url: URL to fetch

        Returns:
            HTML content as string or None if failed
        """
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)

            if response.status_code == 200:
                return response.text
            else:
                return None

        except Exception as e:
            print(f"      ⚠️  Error fetching content: {str(e)}")
            return None

    def fetch_and_parse(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse HTML content

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if failed
        """
        content = self.fetch_content(url)
        if content:
            return BeautifulSoup(content, "html.parser")
        return None


class LinkFinder:
    """Extracts and analyzes links from web pages"""

    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """
        Extract all links from HTML content

        Args:
            html_content: HTML content as string
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute URLs
        """
        soup = BeautifulSoup(html_content, "html.parser")
        links = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]

            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)

            # Only include http/https links
            if absolute_url.startswith(("http://", "https://")):
                links.append(absolute_url)

        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)

        return unique_links

    def filter_links_by_keywords(
        self, links: List[str], keywords: List[str]
    ) -> List[str]:
        """
        Filter links that contain any of the keywords

        Args:
            links: List of URLs
            keywords: List of keywords to search for

        Returns:
            Filtered list of URLs
        """
        filtered = []
        for link in links:
            link_lower = link.lower()
            if any(keyword.lower() in link_lower for keyword in keywords):
                filtered.append(link)
        return filtered

    def find_best_match(
        self, links: List[str], keywords: List[str], prefer_domain: Optional[str] = None
    ) -> Optional[str]:
        """
        Find the best matching link based on keywords

        Args:
            links: List of URLs to search
            keywords: List of keywords (in priority order)
            prefer_domain: Preferred domain to prioritize

        Returns:
            Best matching URL or None
        """
        best_match = None
        best_score = 0

        for link in links:
            score = 0
            link_lower = link.lower()

            # Score based on keywords (earlier keywords = higher score)
            for i, keyword in enumerate(keywords):
                if keyword.lower() in link_lower:
                    score += (len(keywords) - i) * 10

            # Bonus for preferred domain
            if prefer_domain and prefer_domain in link:
                score += 50

            # Prefer shorter URLs (usually more direct)
            score -= len(link) / 100

            if score > best_score:
                best_score = score
                best_match = link

        return best_match if best_score > 0 else None


def get_domain(url: str) -> str:
    """
    Extract domain from URL

    Args:
        url: Full URL

    Returns:
        Domain name
    """
    parsed = urlparse(url)
    return parsed.netloc
