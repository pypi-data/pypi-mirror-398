#!/usr/bin/env python3
"""Example: Analyze log files for errors and patterns."""

from pathlib import Path
from pyautokit.log_analyzer import LogAnalyzer
from pyautokit.logger import setup_logger
from pyautokit.config import Config

logger = setup_logger("AnalyzeLogs")


def main():
    """Analyze log files."""
    # Analyze a log file (create a sample if needed)
    log_file = Config.LOGS_DIR / "FileOrganizer.log"
    
    if not log_file.exists():
        logger.warning(f"Log file not found: {log_file}")
        logger.info("Run some pyautokit scripts first to generate logs")
        return
    
    analyzer = LogAnalyzer()
    
    logger.info(f"Analyzing {log_file}")
    report = analyzer.generate_report(log_file)
    
    # Print summary
    print("\n=== Log Analysis Report ===")
    print(f"File: {report['file']}")
    print(f"Total lines: {report['total_lines']}")
    print(f"\nLog Levels:")
    for level, count in report['log_levels'].items():
        print(f"  {level}: {count}")
    
    print(f"\nErrors found: {len(report['errors'])}")
    if report['errors']:
        print("\nRecent errors:")
        for error in report['errors'][:3]:
            print(f"  Line {error['line_number']}: {error['message'][:80]}")
    
    print(f"\nUnique IP addresses: {len(report['ip_addresses'])}")
    
    if report.get('frequent_patterns'):
        print("\nMost frequent patterns:")
        for pattern, count in report['frequent_patterns'][:5]:
            print(f"  {pattern}: {count}")


if __name__ == "__main__":
    main()
