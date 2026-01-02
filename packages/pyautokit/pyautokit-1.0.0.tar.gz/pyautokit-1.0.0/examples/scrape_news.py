#!/usr/bin/env python3
"""Example: Scrape news headlines from a website."""

from pyautokit.web_scraper import WebScraper
from pyautokit.logger import setup_logger
from pyautokit.utils import save_json
from pyautokit.config import Config

logger = setup_logger("ScrapeNews")


def main():
    """Scrape news headlines."""
    # Example: Scrape Hacker News
    url = "https://news.ycombinator.com/"
    
    scraper = WebScraper(rate_limit=1.0)
    
    # Define selectors for headlines and links
    selectors = {
        "headlines": ".titleline > a",
        "scores": ".score",
    }
    
    logger.info(f"Scraping {url}")
    data = scraper.scrape_page(url, selectors)
    
    if data:
        logger.info(f"Found {len(data.get('headlines', []))} headlines")
        
        # Save to JSON
        output_file = Config.DATA_DIR / "news_headlines.json"
        save_json(data, output_file)
        logger.info(f"Saved to {output_file}")
        
        # Print first 5 headlines
        for i, headline in enumerate(data.get("headlines", [])[:5], 1):
            print(f"{i}. {headline}")


if __name__ == "__main__":
    main()
