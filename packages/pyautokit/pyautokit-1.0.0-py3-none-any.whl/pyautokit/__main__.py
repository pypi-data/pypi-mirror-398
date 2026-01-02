#!/usr/bin/env python3
"""PyAutokit CLI entry point.

Provides unified command-line interface for all PyAutokit modules.
"""

import sys
import argparse
from pathlib import Path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="pyautokit",
        description="PyAutokit - Python Automation Toolkit",
        epilog="Run 'pyautokit <module> --help' for module-specific help",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="PyAutokit 1.0.0"
    )
    
    subparsers = parser.add_subparsers(
        dest="module",
        title="Available modules",
        description="Choose a module to run",
        help="Module to execute"
    )
    
    # File Organizer
    subparsers.add_parser(
        "file-organizer",
        help="Organize files by extension, date, category, or size",
        add_help=False
    )
    
    # Web Scraper
    subparsers.add_parser(
        "web-scraper",
        help="Scrape websites with rate limiting",
        add_help=False
    )
    
    # Email Automation
    subparsers.add_parser(
        "email",
        help="Send bulk emails with templates",
        add_help=False
    )
    
    # Backup Manager
    subparsers.add_parser(
        "backup",
        help="Create and manage backups",
        add_help=False
    )
    
    # Log Analyzer
    subparsers.add_parser(
        "log-analyzer",
        help="Analyze log files",
        add_help=False
    )
    
    # Blockchain Monitor
    subparsers.add_parser(
        "crypto",
        help="Monitor cryptocurrency prices",
        add_help=False
    )
    
    # API Client
    subparsers.add_parser(
        "api",
        help="Make API requests",
        add_help=False
    )
    
    # Data Processor
    subparsers.add_parser(
        "data",
        help="Process and transform data",
        add_help=False
    )
    
    # Security Utils
    subparsers.add_parser(
        "security",
        help="Encryption and security utilities",
        add_help=False
    )
    
    args, remaining = parser.parse_known_args()
    
    if not args.module:
        parser.print_help()
        return 0
    
    # Map module names to actual module names
    module_map = {
        "file-organizer": "file_organizer",
        "web-scraper": "web_scraper",
        "email": "email_automation",
        "backup": "backup_manager",
        "log-analyzer": "log_analyzer",
        "crypto": "blockchain_monitor",
        "api": "api_client",
        "data": "data_processor",
        "security": "security_utils",
    }
    
    module_name = module_map.get(args.module)
    if not module_name:
        print(f"Unknown module: {args.module}")
        return 1
    
    # Import and run module
    try:
        module = __import__(f"pyautokit.{module_name}", fromlist=["main"])
        sys.argv = [f"pyautokit {args.module}"] + remaining
        return module.main()
    except Exception as e:
        print(f"Error running {args.module}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
