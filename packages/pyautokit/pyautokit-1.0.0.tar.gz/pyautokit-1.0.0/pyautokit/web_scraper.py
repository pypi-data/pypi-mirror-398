"""Ethical web scraping utility with rate limiting.

Features:
- Rate limiting to be respectful
- CSS selector support
- Session management
- Link extraction
- Multiple page scraping
"""

import argparse
import time
import sys
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from .logger import setup_logger
from .config import Config
from .utils import save_json

logger = setup_logger("WebScraper", level=Config.LOG_LEVEL)


class WebScraper:
    """Ethical web scraper with rate limiting."""

    def __init__(
        self,
        user_agent: str = Config.SCRAPER_USER_AGENT,
        timeout: int = Config.SCRAPER_TIMEOUT,
        rate_limit: float = Config.SCRAPER_RATE_LIMIT
    ):
        """Initialize scraper.
        
        Args:
            user_agent: User agent string for requests
            timeout: Request timeout in seconds
            rate_limit: Minimum seconds between requests
        """
        self.user_agent = user_agent
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.last_request_time = 0.0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def _wait_for_rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()

    def fetch_url(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> Optional[requests.Response]:
        """Fetch URL with rate limiting.
        
        Args:
            url: URL to fetch
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional requests parameters
            
        Returns:
            Response object or None on failure
        """
        self._wait_for_rate_limit()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            logger.info(f"Fetched {url} - Status: {response.status_code}")
            return response
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content.
        
        Args:
            html: HTML string to parse
            
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, "html.parser")

    def extract_links(
        self,
        soup: BeautifulSoup,
        base_url: str,
        external: bool = False
    ) -> List[str]:
        """Extract links from parsed HTML.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            external: Include external links
            
        Returns:
            List of URLs
        """
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all("a", href=True):
            url = urljoin(base_url, link["href"])
            url_domain = urlparse(url).netloc
            
            if external or url_domain == base_domain:
                links.append(url)
        
        return list(set(links))

    def extract_text(
        self,
        soup: BeautifulSoup,
        selector: Optional[str] = None
    ) -> str:
        """Extract text from HTML.
        
        Args:
            soup: BeautifulSoup object
            selector: CSS selector to target specific elements
            
        Returns:
            Extracted text
        """
        if selector:
            elements = soup.select(selector)
            return " ".join(el.get_text(strip=True) for el in elements)
        return soup.get_text(strip=True)

    def scrape_page(
        self,
        url: str,
        selectors: Optional[Dict[str, str]] = None
    ) -> Dict[str, any]:
        """Scrape page and extract data.
        
        Args:
            url: URL to scrape
            selectors: Dict of {field: css_selector} for extraction
            
        Returns:
            Dict of extracted data
        """
        response = self.fetch_url(url)
        if not response:
            return {}
        
        soup = self.parse_html(response.text)
        data = {"url": url, "status": response.status_code}
        
        if selectors:
            for field, selector in selectors.items():
                elements = soup.select(selector)
                if elements:
                    data[field] = [el.get_text(strip=True) for el in elements]
        else:
            data["text"] = self.extract_text(soup)
            data["links"] = self.extract_links(soup, url)
        
        return data

    def scrape_multiple(
        self,
        urls: List[str],
        selectors: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, any]]:
        """Scrape multiple URLs.
        
        Args:
            urls: List of URLs to scrape
            selectors: CSS selectors for data extraction
            
        Returns:
            List of extracted data dicts
        """
        results = []
        for url in urls:
            logger.info(f"Scraping {url}")
            data = self.scrape_page(url, selectors)
            if data:
                results.append(data)
        return results


def main() -> int:
    """CLI for web scraper."""
    parser = argparse.ArgumentParser(
        description="Web scraping utility with rate limiting",
        epilog="Examples:\n"
               "  %(prog)s https://example.com\n"
               "  %(prog)s https://news.ycombinator.com -s 'title:a.storylink'\n"
               "  %(prog)s https://example.com --links --output links.json\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "url",
        help="URL to scrape"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON file path"
    )
    
    parser.add_argument(
        "--selector",
        "-s",
        action="append",
        help="CSS selector (format: field:selector)"
    )
    
    parser.add_argument(
        "--links",
        action="store_true",
        help="Extract all links from page"
    )
    
    parser.add_argument(
        "--external",
        action="store_true",
        help="Include external links"
    )
    
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=Config.SCRAPER_RATE_LIMIT,
        help="Rate limit in seconds (default: 1.0)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=Config.SCRAPER_TIMEOUT,
        help="Request timeout in seconds (default: 10)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel("DEBUG")
    
    selectors = None
    if args.selector:
        selectors = {}
        for s in args.selector:
            if ":" in s:
                field, selector = s.split(":", 1)
                selectors[field] = selector
            else:
                logger.warning(f"Invalid selector format: {s} (use field:selector)")
    
    scraper = WebScraper(
        rate_limit=args.rate_limit,
        timeout=args.timeout
    )
    
    logger.info(f"Scraping {args.url}")
    data = scraper.scrape_page(args.url, selectors)
    
    if not data:
        logger.error("Failed to scrape page")
        return 1
    
    # Extract links if requested
    if args.links:
        soup = scraper.parse_html(requests.get(args.url).text)
        data["all_links"] = scraper.extract_links(soup, args.url, args.external)
        logger.info(f"Extracted {len(data['all_links'])} links")
    
    if args.output:
        output_path = Config.DATA_DIR / args.output
        save_json(data, output_path)
        logger.info(f"Saved to {output_path}")
    else:
        import json
        print(json.dumps(data, indent=2))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
