#!/usr/bin/env python3
"""Example: Organize Downloads folder with advanced features.

This example demonstrates:
- Basic file organization by category
- Dry-run mode for safe testing
- Directory statistics
- Optional auto-watch mode for continuous organization
"""

import argparse
import time
from pathlib import Path
from pyautokit.file_organizer import FileOrganizer, print_stats
from pyautokit.logger import setup_logger

logger = setup_logger("OrganizeDownloads")


def organize_once(
    directory: Path,
    method: str = "category",
    dry_run: bool = False
) -> None:
    """Organize directory once.
    
    Args:
        directory: Directory to organize
        method: Organization method
        dry_run: Dry run mode
    """
    logger.info(f"Organizing {directory} by {method}")
    
    organizer = FileOrganizer(
        create_folders=True,
        dry_run=dry_run,
        handle_duplicates="rename"
    )
    
    # Get initial stats
    if not dry_run:
        print("\n📊 Before Organization:")
        stats = organizer.get_directory_stats(directory)
        print_stats({
            "Total Files": stats["total_files"],
            "Documents": stats["by_category"].get("Documents", 0),
            "Images": stats["by_category"].get("Images", 0),
            "Videos": stats["by_category"].get("Videos", 0),
            "Archives": stats["by_category"].get("Archives", 0),
            "Other": stats["by_category"].get("Other", 0),
        }, "Current Status")
    
    # Organize
    if method == "category":
        results = organizer.organize_by_category(directory)
    elif method == "extension":
        results = organizer.organize_by_extension(directory)
    elif method == "date":
        results = organizer.organize_by_date(directory)
    else:
        results = organizer.organize_by_size(directory)
    
    # Print results
    print("\n✅ Organization Complete!")
    print_stats(results, f"Results ({method})")
    
    summary = {
        "Files Moved": organizer.stats["moved"],
        "Files Skipped": organizer.stats["skipped"],
        "Errors": organizer.stats["errors"],
    }
    print_stats(summary, "Summary")


def watch_and_organize(
    directory: Path,
    method: str = "category",
    interval: int = 30
) -> None:
    """Continuously watch and organize directory.
    
    Args:
        directory: Directory to watch
        method: Organization method
        interval: Check interval in seconds
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class OrganizeHandler(FileSystemEventHandler):
            def __init__(self, organizer_method):
                self.method = organizer_method
                self.organizer = FileOrganizer()
            
            def on_created(self, event):
                if not event.is_directory:
                    logger.info(f"New file detected: {event.src_path}")
                    time.sleep(1)  # Wait for file to be fully written
                    self.organize()
            
            def organize(self):
                try:
                    if self.method == "category":
                        self.organizer.organize_by_category(directory)
                    elif self.method == "extension":
                        self.organizer.organize_by_extension(directory)
                    elif self.method == "date":
                        self.organizer.organize_by_date(directory)
                except Exception as e:
                    logger.error(f"Organization failed: {e}")
        
        logger.info(f"👀 Watching {directory} for new files...")
        logger.info(f"Files will be organized by {method}")
        logger.info("Press Ctrl+C to stop\n")
        
        event_handler = OrganizeHandler(method)
        observer = Observer()
        observer.schedule(event_handler, str(directory), recursive=False)
        observer.start()
        
        try:
            while True:
                time.sleep(interval)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("\n👋 Stopped watching")
        
        observer.join()
        
    except ImportError:
        logger.error("watchdog package not installed!")
        logger.info("Install with: pip install watchdog")
        logger.info("Falling back to periodic checking...\n")
        
        # Fallback to simple periodic checking
        organizer = FileOrganizer()
        
        try:
            while True:
                logger.info("Checking for new files...")
                if method == "category":
                    results = organizer.organize_by_category(directory)
                elif method == "extension":
                    results = organizer.organize_by_extension(directory)
                elif method == "date":
                    results = organizer.organize_by_date(directory)
                
                if results:
                    logger.info(f"Organized {sum(results.values())} files")
                
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("\n👋 Stopped organizing")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Organize Downloads folder intelligently",
        epilog="Examples:\n"
               "  %(prog)s                          # Organize ~/Downloads by category\n"
               "  %(prog)s --dry-run                # Test without moving files\n"
               "  %(prog)s --method extension       # Organize by file extension\n"
               "  %(prog)s --watch                  # Continuously watch and organize\n"
               "  %(prog)s --stats                  # Show statistics only\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--directory",
        "-d",
        type=str,
        default="~/Downloads",
        help="Directory to organize (default: ~/Downloads)"
    )
    
    parser.add_argument(
        "--method",
        "-m",
        choices=["category", "extension", "date", "size"],
        default="category",
        help="Organization method (default: category)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without moving files"
    )
    
    parser.add_argument(
        "--watch",
        "-w",
        action="store_true",
        help="Continuously watch for new files (requires watchdog)"
    )
    
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=30,
        help="Watch interval in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--stats",
        "-s",
        action="store_true",
        help="Show directory statistics only"
    )
    
    args = parser.parse_args()
    
    directory = Path(args.directory).expanduser().resolve()
    
    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        logger.info("Creating directory...")
        directory.mkdir(parents=True, exist_ok=True)
    
    if not directory.is_dir():
        logger.error(f"Not a directory: {directory}")
        return 1
    
    logger.info(f"📁 Target directory: {directory}\n")
    
    # Show stats only
    if args.stats:
        organizer = FileOrganizer()
        stats = organizer.get_directory_stats(directory)
        
        from pyautokit.utils import format_bytes
        print_stats({
            "Total Files": stats["total_files"],
            "Total Size": format_bytes(stats["total_size"]),
        }, "Directory Overview")
        
        print_stats(dict(stats["by_category"]), "Files by Category")
        
        # Show top extensions
        top_ext = dict(sorted(
            stats["by_extension"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])
        print_stats(top_ext, "Top 10 Extensions")
        
        return 0
    
    # Watch mode
    if args.watch:
        if args.dry_run:
            logger.warning("Dry-run mode not supported in watch mode")
            return 1
        
        watch_and_organize(directory, args.method, args.interval)
        return 0
    
    # One-time organization
    organize_once(directory, args.method, args.dry_run)
    
    if args.dry_run:
        print("\n💡 This was a dry run. Run without --dry-run to actually organize files.")
    else:
        print(f"\n✨ Your {directory.name} folder is now organized!")
    
    return 0


if __name__ == "__main__":
    exit(main())
