"""PyAutokit - Python Automation Toolkit.

A comprehensive collection of automation utilities for everyday tasks.
Each module provides both CLI and programmatic interfaces.

Modules:
    - file_organizer: Organize files by extension, date, category, or size
    - web_scraper: Ethical web scraping with rate limiting
    - email_automation: SMTP email automation with templates
    - backup_manager: Backup management with compression and versioning
    - log_analyzer: Parse and analyze log files
    - api_client: Generic REST API client with retry logic
    - data_processor: CSV/JSON conversion and data transformation
    - task_scheduler: Cron-like task scheduling
    - security_utils: Encryption, hashing, and password generation
    - blockchain_monitor: Cryptocurrency price monitoring
    - github_utils: GitHub repository and issue management
    - playwright_utils: Browser automation with Playwright

Examples:
    >>> from pyautokit import FileOrganizer
    >>> organizer = FileOrganizer()
    >>> results = organizer.organize_by_category("/path/to/folder")
    
    >>> from pyautokit import BlockchainMonitor
    >>> monitor = BlockchainMonitor()
    >>> price = monitor.get_price("EGLD")
    
    >>> from pyautokit import GitHubUtils
    >>> gh = GitHubUtils(token="ghp_...")
    >>> repos = gh.list_repositories()
    
    >>> import asyncio
    >>> from pyautokit import PlaywrightUtils
    >>> async def capture():
    ...     async with PlaywrightUtils() as pw:
    ...         await pw.screenshot("https://example.com", "page.png")
    >>> asyncio.run(capture())

CLI Usage:
    $ pyautokit-organizer ~/Downloads --method category
    $ pyautokit-crypto --coin EGLD
    $ pyautokit-github list-repos --user Gzeu
    $ pyautokit-browser screenshot https://example.com -o page.png
    $ pyautokit-security genpass --length 20
    $ pyautokit-backup create ./project --compression tar.gz
"""

__version__ = "1.0.0"
__author__ = "George Pricop"
__email__ = "contact@georgepricop.com"
__license__ = "MIT"

# Import main classes for easy access
from .file_organizer import FileOrganizer, SortMethod
from .web_scraper import WebScraper
from .email_automation import EmailClient
from .backup_manager import BackupManager
from .log_analyzer import LogAnalyzer
from .api_client import APIClient
from .data_processor import DataProcessor
from .task_scheduler import TaskScheduler
from .security_utils import SecurityUtils
from .blockchain_monitor import BlockchainMonitor
from .github_utils import GitHubUtils
from .playwright_utils import PlaywrightUtils

__all__ = [
    "FileOrganizer",
    "SortMethod",
    "WebScraper",
    "EmailClient",
    "BackupManager",
    "LogAnalyzer",
    "APIClient",
    "DataProcessor",
    "TaskScheduler",
    "SecurityUtils",
    "BlockchainMonitor",
    "GitHubUtils",
    "PlaywrightUtils",
]
