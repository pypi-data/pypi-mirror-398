#!/usr/bin/env python3
"""Example: Backup project directory."""

from pathlib import Path
from pyautokit.backup_manager import BackupManager
from pyautokit.logger import setup_logger

logger = setup_logger("BackupProject")


def main():
    """Backup current project."""
    # Backup the current directory
    project_dir = Path.cwd()
    
    manager = BackupManager(
        compression="tar.gz",
        keep_versions=10
    )
    
    logger.info(f"Creating backup of {project_dir}")
    backup_path = manager.create_backup(
        source=project_dir,
        name="pyautokit_project"
    )
    
    if backup_path:
        logger.info(f"Backup created: {backup_path}")
        
        # List all backups
        backups = manager.list_backups("pyautokit_project")
        logger.info(f"\nAll backups ({len(backups)}):")
        for backup in backups:
            print(f"  - {backup['name']} ({backup['size']}) - {backup['created']}")


if __name__ == "__main__":
    main()
