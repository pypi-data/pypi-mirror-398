"""Backup management with compression and versioning.

Features:
- Multiple compression formats (ZIP, TAR, TAR.GZ)
- Version management
- Incremental backups
- Easy restore functionality
"""

import argparse
import sys
import shutil
import tarfile
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from .logger import setup_logger
from .config import Config

logger = setup_logger("BackupManager", level=Config.LOG_LEVEL)


class BackupManager:
    """Backup management with versioning."""

    def __init__(
        self,
        BACKUPS_DIR: Path = Config.BACKUPS_DIR,
        compression: str = Config.BACKUP_COMPRESSION,
        keep_versions: int = Config.BACKUP_KEEP_VERSIONS
    ):
        """Initialize backup manager.
        
        Args:
            BACKUPS_DIR: Directory to store backups
            compression: Compression format (zip, tar, tar.gz)
            keep_versions: Number of versions to keep (0 = unlimited)
        """
        self.BACKUPS_DIR = Path(BACKUPS_DIR)
        self.BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        self.compression = compression.lower()
        self.keep_versions = keep_versions

    def _get_backup_name(
        self,
        source: Path,
        timestamp: Optional[str] = None
    ) -> str:
        """Generate backup filename.
        
        Args:
            source: Source path being backed up
            timestamp: Optional timestamp (auto-generated if not provided)
            
        Returns:
            Backup filename
        """
        if not timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        name = source.name
        if self.compression == "zip":
            return f"{name}_{timestamp}.zip"
        elif self.compression == "tar":
            return f"{name}_{timestamp}.tar"
        elif self.compression == "tar.gz":
            return f"{name}_{timestamp}.tar.gz"
        else:
            return f"{name}_{timestamp}.backup"

    def create_backup(
        self,
        source: Path,
        name: Optional[str] = None
    ) -> Optional[Path]:
        """Create backup of source.
        
        Args:
            source: Path to backup
            name: Optional custom backup name
            
        Returns:
            Path to created backup or None on failure
        """
        source = Path(source).resolve()
        
        if not source.exists():
            logger.error(f"Source not found: {source}")
            return None
        
        backup_name = name or self._get_backup_name(source)
        backup_path = self.BACKUPS_DIR / backup_name
        
        try:
            logger.info(f"Creating backup: {source} -> {backup_path}")
            
            if self.compression == "zip":
                self._create_zip(source, backup_path)
            elif self.compression == "tar":
                self._create_tar(source, backup_path, compressed=False)
            elif self.compression == "tar.gz":
                self._create_tar(source, backup_path, compressed=True)
            else:
                logger.error(f"Unknown compression: {self.compression}")
                return None
            
            logger.info(f"Backup created: {backup_path}")
            self._cleanup_old_versions(source.name)
            
            return backup_path
        
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

    def _create_zip(self, source: Path, output: Path) -> None:
        """Create ZIP backup."""
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if source.is_file():
                zipf.write(source, source.name)
            else:
                for file in source.rglob('*'):
                    if file.is_file():
                        zipf.write(file, file.relative_to(source.parent))

    def _create_tar(self, source: Path, output: Path, compressed: bool) -> None:
        """Create TAR backup."""
        mode = 'w:gz' if compressed else 'w'
        with tarfile.open(output, mode) as tar:
            tar.add(source, arcname=source.name)

    def _cleanup_old_versions(self, base_name: str) -> None:
        """Remove old backup versions."""
        if self.keep_versions <= 0:
            return
        
        pattern = f"{base_name}_*"
        backups = sorted(
            self.BACKUPS_DIR.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for old_backup in backups[self.keep_versions:]:
            logger.info(f"Removing old backup: {old_backup}")
            old_backup.unlink()

    def list_backups(self, filter_name: Optional[str] = None) -> List[Path]:
        """List available backups.
        
        Args:
            filter_name: Optional name filter
            
        Returns:
            List of backup paths
        """
        pattern = f"{filter_name}_*" if filter_name else "*"
        backups = sorted(
            self.BACKUPS_DIR.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        return backups

    def restore_backup(
        self,
        backup_path: Path,
        destination: Path,
        overwrite: bool = False
    ) -> bool:
        """Restore backup to destination.
        
        Args:
            backup_path: Path to backup file
            destination: Restore destination
            overwrite: Overwrite existing files
            
        Returns:
            True if successful
        """
        backup_path = Path(backup_path)
        destination = Path(destination)
        
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_path}")
            return False
        
        if destination.exists() and not overwrite:
            logger.error(f"Destination exists: {destination}")
            return False
        
        try:
            logger.info(f"Restoring: {backup_path} -> {destination}")
            
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(destination)
            elif backup_path.suffix in ['.tar', '.gz']:
                with tarfile.open(backup_path, 'r:*') as tar:
                    tar.extractall(destination)
            else:
                logger.error(f"Unknown backup format: {backup_path.suffix}")
                return False
            
            logger.info("Restore complete")
            return True
        
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False


def main() -> int:
    """CLI for backup manager."""
    parser = argparse.ArgumentParser(
        description="Backup management with compression and versioning",
        epilog="Examples:\n"
               "  %(prog)s create ./myproject\n"
               "  %(prog)s create ./myproject --compression tar.gz\n"
               "  %(prog)s list\n"
               "  %(prog)s restore backups/myproject_20250101_120000.zip ./restored\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create backup
    create_parser = subparsers.add_parser("create", help="Create new backup")
    create_parser.add_argument(
        "source",
        help="Source file or directory to backup"
    )
    create_parser.add_argument(
        "--compression",
        "-c",
        choices=["zip", "tar", "tar.gz"],
        default=Config.BACKUP_COMPRESSION,
        help="Compression format (default: zip)"
    )
    create_parser.add_argument(
        "--name",
        "-n",
        help="Custom backup name"
    )
    create_parser.add_argument(
        "--keep",
        "-k",
        type=int,
        default=Config.BACKUP_KEEP_VERSIONS,
        help="Number of versions to keep (default: 5)"
    )
    
    # List backups
    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.add_argument(
        "--filter",
        "-f",
        help="Filter by name"
    )
    
    # Restore backup
    restore_parser = subparsers.add_parser("restore", help="Restore backup")
    restore_parser.add_argument(
        "backup",
        help="Backup file path"
    )
    restore_parser.add_argument(
        "destination",
        help="Restore destination"
    )
    restore_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files"
    )
    
    # Delete backup
    delete_parser = subparsers.add_parser("delete", help="Delete backup")
    delete_parser.add_argument(
        "backup",
        help="Backup file path to delete"
    )
    
    # Global options
    parser.add_argument(
        "--backup-dir",
        default=Config.BACKUPS_DIR,
        help=f"Backup directory (default: {Config.BACKUPS_DIR})"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.verbose:
        logger.setLevel("DEBUG")
    
    manager = BackupManager(
        BACKUPS_DIR=Path(args.BACKUPS_DIR),
        compression=getattr(args, 'compression', Config.BACKUP_COMPRESSION),
        keep_versions=getattr(args, 'keep', Config.BACKUP_KEEP_VERSIONS)
    )
    
    # Execute command
    if args.command == "create":
        result = manager.create_backup(
            Path(args.source),
            name=args.name
        )
        if result:
            print(f"✅ Backup created: {result}")
            return 0
        else:
            print("❌ Backup failed")
            return 1
    
    elif args.command == "list":
        backups = manager.list_backups(args.filter)
        if backups:
            print(f"\n💾 Found {len(backups)} backup(s):\n")
            for backup in backups:
                size = backup.stat().st_size / (1024 * 1024)  # MB
                mtime = datetime.fromtimestamp(backup.stat().st_mtime)
                print(f"  • {backup.name}")
                print(f"    Size: {size:.2f} MB")
                print(f"    Date: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                print()
        else:
            print("⚠️  No backups found")
        return 0
    
    elif args.command == "restore":
        success = manager.restore_backup(
            Path(args.backup),
            Path(args.destination),
            overwrite=args.overwrite
        )
        if success:
            print(f"✅ Restored to: {args.destination}")
            return 0
        else:
            print("❌ Restore failed")
            return 1
    
    elif args.command == "delete":
        backup_path = Path(args.backup)
        if backup_path.exists():
            backup_path.unlink()
            print(f"✅ Deleted: {backup_path}")
            return 0
        else:
            print(f"❌ Backup not found: {backup_path}")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
