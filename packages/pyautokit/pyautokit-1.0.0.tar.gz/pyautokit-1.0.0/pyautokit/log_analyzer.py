"""Log file analysis and parsing utility."""

import argparse
import re
from pathlib import Path
from typing import List, Dict, Optional, Pattern
from collections import Counter, defaultdict
from datetime import datetime
from .logger import setup_logger
from .config import Config
from .utils import save_json

logger = setup_logger("LogAnalyzer", level=Config.LOG_LEVEL)


class LogAnalyzer:
    """Analyze and parse log files."""

    # Common log patterns
    PATTERNS = {
        "timestamp": r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}",
        "ip": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "error": r"\b(ERROR|CRITICAL|FATAL)\b",
        "warning": r"\b(WARNING|WARN)\b",
        "url": r"https?://[^\s]+",
    }

    def __init__(self):
        """Initialize log analyzer."""
        self.compiled_patterns = {
            name: re.compile(pattern)
            for name, pattern in self.PATTERNS.items()
        }

    def parse_log_file(
        self,
        file_path: Path,
        encoding: str = "utf-8"
    ) -> List[str]:
        """Parse log file into lines.
        
        Args:
            file_path: Path to log file
            encoding: File encoding
            
        Returns:
            List of log lines
        """
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Failed to read log file: {e}")
            return []

    def extract_pattern(
        self,
        lines: List[str],
        pattern: Pattern
    ) -> List[str]:
        """Extract matches for pattern.
        
        Args:
            lines: Log lines
            pattern: Compiled regex pattern
            
        Returns:
            List of matches
        """
        matches = []
        for line in lines:
            found = pattern.findall(line)
            matches.extend(found)
        return matches

    def count_log_levels(self, lines: List[str]) -> Dict[str, int]:
        """Count occurrences of log levels.
        
        Args:
            lines: Log lines
            
        Returns:
            Dict of {level: count}
        """
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        counts = Counter()
        
        for line in lines:
            for level in levels:
                if level in line.upper():
                    counts[level] += 1
                    break
        
        return dict(counts)

    def extract_errors(
        self,
        lines: List[str],
        context_lines: int = 2
    ) -> List[Dict[str, any]]:
        """Extract error messages with context.
        
        Args:
            lines: Log lines
            context_lines: Lines of context to include
            
        Returns:
            List of error dicts with context
        """
        errors = []
        error_pattern = self.compiled_patterns["error"]
        
        for i, line in enumerate(lines):
            if error_pattern.search(line):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                
                errors.append({
                    "line_number": i + 1,
                    "message": line,
                    "context": lines[start:end],
                })
        
        return errors

    def analyze_timestamps(
        self,
        lines: List[str]
    ) -> Dict[str, any]:
        """Analyze timestamp distribution.
        
        Args:
            lines: Log lines
            
        Returns:
            Timestamp analysis dict
        """
        timestamps = self.extract_pattern(
            lines,
            self.compiled_patterns["timestamp"]
        )
        
        if not timestamps:
            return {"count": 0}
        
        hourly = defaultdict(int)
        for ts_str in timestamps:
            try:
                # Try parsing ISO format
                ts = datetime.fromisoformat(ts_str.replace(" ", "T"))
                hourly[ts.hour] += 1
            except ValueError:
                continue
        
        return {
            "count": len(timestamps),
            "first": timestamps[0] if timestamps else None,
            "last": timestamps[-1] if timestamps else None,
            "hourly_distribution": dict(hourly),
        }

    def find_frequent_patterns(
        self,
        lines: List[str],
        min_occurrences: int = 5
    ) -> List[tuple]:
        """Find frequently occurring patterns.
        
        Args:
            lines: Log lines
            min_occurrences: Minimum occurrences threshold
            
        Returns:
            List of (pattern, count) tuples
        """
        # Simple word-based frequency
        words = Counter()
        for line in lines:
            # Extract words (alphanumeric sequences)
            line_words = re.findall(r'\b\w{4,}\b', line.lower())
            words.update(line_words)
        
        return [
            (word, count)
            for word, count in words.most_common()
            if count >= min_occurrences
        ]

    def generate_report(
        self,
        file_path: Path
    ) -> Dict[str, any]:
        """Generate comprehensive log analysis report.
        
        Args:
            file_path: Path to log file
            
        Returns:
            Analysis report dict
        """
        lines = self.parse_log_file(file_path)
        
        if not lines:
            return {"error": "No lines found or failed to read file"}
        
        report = {
            "file": str(file_path),
            "total_lines": len(lines),
            "log_levels": self.count_log_levels(lines),
            "errors": self.extract_errors(lines),
            "timestamps": self.analyze_timestamps(lines),
            "ip_addresses": list(set(self.extract_pattern(
                lines,
                self.compiled_patterns["ip"]
            ))),
            "frequent_patterns": self.find_frequent_patterns(lines)[:10],
        }
        
        logger.info(f"Analysis complete: {len(lines)} lines processed")
        return report


def main() -> None:
    """CLI for log analyzer."""
    parser = argparse.ArgumentParser(description="Log analysis utility")
    parser.add_argument("file", help="Log file path")
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON report path"
    )
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Show only errors"
    )
    
    args = parser.parse_args()
    
    analyzer = LogAnalyzer()
    
    if args.errors_only:
        lines = analyzer.parse_log_file(Path(args.file))
        errors = analyzer.extract_errors(lines)
        for error in errors:
            print(f"Line {error['line_number']}: {error['message']}")
    else:
        report = analyzer.generate_report(Path(args.file))
        
        if args.output:
            save_json(report, Config.DATA_DIR / args.output)
            logger.info(f"Report saved to {args.output}")
        else:
            print(f"Total lines: {report['total_lines']}")
            print(f"Log levels: {report['log_levels']}")
            print(f"Errors found: {len(report['errors'])}")
            print(f"Unique IPs: {len(report['ip_addresses'])}")


if __name__ == "__main__":
    main()