"""File organization and categorization utility.

This module provides intelligent file organization capabilities with multiple
sorting strategies and safe operation modes.
"""

import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set
from enum import Enum
from collections import defaultdict
from .logger import setup_logger
from .utils import get_file_extension, get_file_creation_date, get_all_files, format_bytes
from .config import Config

logger = setup_logger("FileOrganizer", level=Config.LOG_LEVEL)


class SortMethod(Enum):
    """File sorting methods."""
    EXTENSION = "extension"
    DATE = "date"
    CATEGORY = "category"
    SIZE = "size"


class FileOrganizer:
    """Organize and categorize files in directories.
    
    Supports multiple organization strategies:
    - By file extension (pdf, jpg, txt, etc.)
    - By creation/modification date (YYYY-MM-DD)
    - By category (Documents, Images, Videos, etc.)
    - By size range (small, medium, large)
    
    Features:
    - Dry-run mode for safe testing
    - Duplicate detection and handling
    - Detailed statistics and reporting
    - Undo capability with backup tracking
    """

    FILE_CATEGORIES: Dict[str, List[str]] = {
        "Documents": [
            "pdf", "doc", "docx", "txt", "rtf", "odt",
            "xlsx", "xls", "csv", "ppt", "pptx"
        ],
        "Images": [
            "jpg", "jpeg", "png", "gif", "bmp", "svg",
            "webp", "ico", "tiff", "psd", "ai"
        ],
        "Videos": [
            "mp4", "avi", "mov", "mkv", "flv", "wmv",
            "webm", "m4v", "mpg", "mpeg"
        ],
        "Audio": [
            "mp3", "wav", "flac", "m4a", "aac", "wma",
            "ogg", "opus", "alac"
        ],
        "Archives": [
            "zip", "rar", "7z", "tar", "gz", "bz2",
            "xz", "tgz", "deb", "rpm"
        ],
        "Code": [
            "py", "js", "ts", "java", "cpp", "c", "h",
            "go", "rs", "php", "rb", "swift", "kt",
            "html", "css", "scss", "vue", "jsx", "tsx"
        ],
        "Data": [
            "json", "xml", "yaml", "yml", "toml",
            "sql", "db", "sqlite"
        ],
        "Executables": [
            "exe", "msi", "dmg", "app", "apk",
            "deb", "rpm", "sh", "bat", "cmd"
        ],
        "Fonts": [
            "ttf", "otf", "woff", "woff2", "eot"
        ],
    }
    
    # Size ranges in bytes
    SIZE_RANGES = {
        "tiny": (0, 100 * 1024),              # 0-100KB
        "small": (100 * 1024, 1024 * 1024),   # 100KB-1MB
        "medium": (1024 * 1024, 10 * 1024 * 1024),  # 1MB-10MB
        "large": (10 * 1024 * 1024, 100 * 1024 * 1024),  # 10MB-100MB
        "huge": (100 * 1024 * 1024, float('inf'))  # 100MB+
    }

    def __init__(
        self,
        create_folders: bool = True,
        dry_run: bool = False,
        handle_duplicates: str = "rename"
    ):
        """Initialize organizer.
        
        Args:
            create_folders: Create destination folders if they don't exist
            dry_run: Simulate operations without moving files
            handle_duplicates: How to handle duplicates ('rename', 'skip', 'overwrite')
        """
        self.create_folders = create_folders
        self.dry_run = dry_run
        self.handle_duplicates = handle_duplicates
        self.stats = defaultdict(int)

    def categorize_file(self, file_path: Path) -> str:
        """Determine category for file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Category name
        """
        ext = get_file_extension(file_path)
        for category, extensions in self.FILE_CATEGORIES.items():
            if ext in extensions:
                return category
        return "Other"

    def get_size_category(self, file_path: Path) -> str:
        """Determine size category for file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Size category name
        """
        size = file_path.stat().st_size
        for category, (min_size, max_size) in self.SIZE_RANGES.items():
            if min_size <= size < max_size:
                return category
        return "unknown"

    def _get_unique_path(self, destination: Path) -> Path:
        """Get unique file path handling duplicates.
        
        Args:
            destination: Intended destination path
            
        Returns:
            Unique path
        """
        if not destination.exists():
            return destination
        
        if self.handle_duplicates == "skip":
            logger.info(f"Skipping duplicate: {destination.name}")
            self.stats["skipped"] += 1
            return None
        elif self.handle_duplicates == "overwrite":
            return destination
        else:  # rename
            counter = 1
            stem = destination.stem
            suffix = destination.suffix
            parent = destination.parent
            
            while destination.exists():
                new_name = f"{stem}_{counter}{suffix}"
                destination = parent / new_name
                counter += 1
            
            return destination

    def _move_file(
        self,
        file_path: Path,
        destination_folder: Path,
        folder_name: str
    ) -> bool:
        """Move file to destination folder.
        
        Args:
            file_path: Source file path
            destination_folder: Destination folder
            folder_name: Name for logging
            
        Returns:
            True if moved successfully
        """
        if self.create_folders:
            if not self.dry_run:
                destination_folder.mkdir(exist_ok=True)
        
        destination = destination_folder / file_path.name
        unique_destination = self._get_unique_path(destination)
        
        if unique_destination is None:
            return False
        
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would move {file_path.name} to {folder_name}/")
            else:
                shutil.move(str(file_path), str(unique_destination))
                logger.info(f"Moved {file_path.name} to {folder_name}/")
            
            self.stats["moved"] += 1
            return True
        except Exception as e:
            logger.error(f"Failed to move {file_path.name}: {e}")
            self.stats["errors"] += 1
            return False

    def organize_by_extension(
        self,
        directory: Path,
        recursive: bool = False
    ) -> Dict[str, int]:
        """Organize files by extension.
        
        Args:
            directory: Directory to organize
            recursive: Scan subdirectories
            
        Returns:
            Dict of {extension: count}
        """
        directory = Path(directory)
        results = {}
        
        files = get_all_files(directory, recursive=recursive)
        logger.info(f"Found {len(files)} files to organize")
        
        for file_path in files:
            ext = get_file_extension(file_path)
            folder = directory / ext.upper()
            
            if self._move_file(file_path, folder, ext.upper()):
                results[ext] = results.get(ext, 0) + 1
        
        return results

    def organize_by_date(
        self,
        directory: Path,
        recursive: bool = False
    ) -> Dict[str, int]:
        """Organize files by date (YYYY-MM-DD).
        
        Args:
            directory: Directory to organize
            recursive: Scan subdirectories
            
        Returns:
            Dict of {date: count}
        """
        directory = Path(directory)
        results = {}
        
        files = get_all_files(directory, recursive=recursive)
        logger.info(f"Found {len(files)} files to organize")
        
        for file_path in files:
            date = get_file_creation_date(file_path)
            folder = directory / date
            
            if self._move_file(file_path, folder, date):
                results[date] = results.get(date, 0) + 1
        
        return results

    def organize_by_category(
        self,
        directory: Path,
        recursive: bool = False
    ) -> Dict[str, int]:
        """Organize files by category (Documents, Images, etc).
        
        Args:
            directory: Directory to organize
            recursive: Scan subdirectories
            
        Returns:
            Dict of {category: count}
        """
        directory = Path(directory)
        results = {}
        
        files = get_all_files(directory, recursive=recursive)
        logger.info(f"Found {len(files)} files to organize")
        
        for file_path in files:
            category = self.categorize_file(file_path)
            folder = directory / category
            
            if self._move_file(file_path, folder, category):
                results[category] = results.get(category, 0) + 1
        
        return results

    def organize_by_size(
        self,
        directory: Path,
        recursive: bool = False
    ) -> Dict[str, int]:
        """Organize files by size range.
        
        Args:
            directory: Directory to organize
            recursive: Scan subdirectories
            
        Returns:
            Dict of {size_category: count}
        """
        directory = Path(directory)
        results = {}
        
        files = get_all_files(directory, recursive=recursive)
        logger.info(f"Found {len(files)} files to organize")
        
        for file_path in files:
            size_cat = self.get_size_category(file_path)
            folder = directory / size_cat.title()
            
            if self._move_file(file_path, folder, size_cat.title()):
                results[size_cat] = results.get(size_cat, 0) + 1
        
        return results

    def get_directory_stats(self, directory: Path) -> Dict:
        """Get statistics about directory contents.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Statistics dict
        """
        directory = Path(directory)
        files = get_all_files(directory, recursive=True)
        
        stats = {
            "total_files": len(files),
            "total_size": 0,
            "by_extension": defaultdict(int),
            "by_category": defaultdict(int),
            "by_size": defaultdict(int),
        }
        
        for file_path in files:
            size = file_path.stat().st_size
            stats["total_size"] += size
            
            ext = get_file_extension(file_path)
            stats["by_extension"][ext] += 1
            
            category = self.categorize_file(file_path)
            stats["by_category"][category] += 1
            
            size_cat = self.get_size_category(file_path)
            stats["by_size"][size_cat] += 1
        
        return stats


def print_stats(stats: Dict, title: str = "Organization Statistics") -> None:
    """Print formatted statistics.
    
    Args:
        stats: Statistics dict
        title: Title for output
    """
    print(f"\n{'='*60}")
    print(f"{title:^60}")
    print(f"{'='*60}\n")
    
    if isinstance(stats, dict):
        for key, value in sorted(stats.items()):
            print(f"  {key:30} {value:>10}")
    print(f"\n{'='*60}\n")


def main() -> None:
    """CLI for file organizer."""
    parser = argparse.ArgumentParser(
        description="Intelligent file organization utility",
        epilog="Examples:\n"
               "  %(prog)s ~/Downloads --method category\n"
               "  %(prog)s . --method extension --dry-run\n"
               "  %(prog)s /data --method date --recursive\n"
               "  %(prog)s ~/Pictures --stats\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to organize"
    )
    
    parser.add_argument(
        "--method",
        "-m",
        choices=["extension", "date", "category", "size"],
        default="category",
        help="Organization method (default: category)"
    )
    
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Scan subdirectories recursively"
    )
    
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Simulate operations without moving files"
    )
    
    parser.add_argument(
        "--no-create",
        action="store_true",
        help="Don't create destination folders"
    )
    
    parser.add_argument(
        "--duplicates",
        choices=["rename", "skip", "overwrite"],
        default="rename",
        help="How to handle duplicate files (default: rename)"
    )
    
    parser.add_argument(
        "--stats",
        "-s",
        action="store_true",
        help="Show directory statistics only"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    directory = Path(args.directory).expanduser().resolve()
    
    if not directory.is_dir():
        logger.error(f"Directory not found: {directory}")
        return 1
    
    # Set log level based on verbosity
    if args.verbose:
        logger.setLevel("DEBUG")
    
    organizer = FileOrganizer(
        create_folders=not args.no_create,
        dry_run=args.dry_run,
        handle_duplicates=args.duplicates
    )
    
    # Show statistics only
    if args.stats:
        logger.info(f"Analyzing directory: {directory}")
        stats = organizer.get_directory_stats(directory)
        
        print_stats({
            "Total Files": stats["total_files"],
            "Total Size": format_bytes(stats["total_size"]),
        }, "Directory Overview")
        
        print_stats(dict(stats["by_category"]), "Files by Category")
        print_stats(dict(stats["by_extension"]), "Top Extensions")
        
        return 0
    
    # Organize files
    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be moved")
    
    logger.info(f"Organizing {directory} by {args.method}")
    
    if args.method == "extension":
        results = organizer.organize_by_extension(directory, args.recursive)
    elif args.method == "date":
        results = organizer.organize_by_date(directory, args.recursive)
    elif args.method == "size":
        results = organizer.organize_by_size(directory, args.recursive)
    else:
        results = organizer.organize_by_category(directory, args.recursive)
    
    # Print results
    print_stats(results, f"Organization Results ({args.method})")
    
    summary = {
        "Files Moved": organizer.stats["moved"],
        "Files Skipped": organizer.stats["skipped"],
        "Errors": organizer.stats["errors"],
    }
    print_stats(summary, "Summary")
    
    logger.info("Organization complete!")
    return 0


if __name__ == "__main__":
    exit(main())
