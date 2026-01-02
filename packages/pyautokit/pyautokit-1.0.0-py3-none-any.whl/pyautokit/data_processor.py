"""Data processing and transformation utilities.

Features:
- CSV <-> JSON conversion
- Data filtering and transformation
- Aggregation functions
- Deduplication
- Batch processing
"""

import argparse
import sys
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from .logger import setup_logger
from .config import Config
from .utils import load_json, save_json

logger = setup_logger("DataProcessor", level=Config.LOG_LEVEL)


class DataProcessor:
    """Data processing and transformation."""

    @staticmethod
    def csv_to_json(csv_path: Path, output_path: Optional[Path] = None) -> List[Dict]:
        """Convert CSV to JSON.
        
        Args:
            csv_path: Input CSV file path
            output_path: Optional output JSON path
            
        Returns:
            List of dictionaries
        """
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        if output_path:
            save_json(data, output_path)
            logger.info(f"Converted {csv_path} -> {output_path}")
        
        return data

    @staticmethod
    def json_to_csv(json_path: Path, output_path: Optional[Path] = None) -> None:
        """Convert JSON to CSV.
        
        Args:
            json_path: Input JSON file path
            output_path: Output CSV path
        """
        data = load_json(json_path)
        
        if not data:
            logger.error("No data to convert")
            return
        
        if not output_path:
            output_path = json_path.with_suffix('.csv')
        
        keys = data[0].keys() if isinstance(data, list) else data.keys()
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            if isinstance(data, list):
                writer.writerows(data)
            else:
                writer.writerow(data)
        
        logger.info(f"Converted {json_path} -> {output_path}")

    @staticmethod
    def filter_data(
        data: List[Dict],
        filters: Dict[str, Any]
    ) -> List[Dict]:
        """Filter data by criteria.
        
        Args:
            data: List of dictionaries
            filters: Dict of {field: value} filters
            
        Returns:
            Filtered data
        """
        filtered = []
        for item in data:
            match = True
            for key, value in filters.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                filtered.append(item)
        
        logger.info(f"Filtered {len(data)} -> {len(filtered)} items")
        return filtered

    @staticmethod
    def aggregate(
        data: List[Dict],
        field: str,
        operation: str = "sum"
    ) -> float:
        """Aggregate numeric field.
        
        Args:
            data: List of dictionaries
            field: Field to aggregate
            operation: Operation (sum, avg, min, max, count)
            
        Returns:
            Aggregated value
        """
        values = [float(item[field]) for item in data if field in item]
        
        if not values:
            return 0.0
        
        if operation == "sum":
            return sum(values)
        elif operation == "avg":
            return sum(values) / len(values)
        elif operation == "min":
            return min(values)
        elif operation == "max":
            return max(values)
        elif operation == "count":
            return len(values)
        else:
            logger.warning(f"Unknown operation: {operation}")
            return 0.0

    @staticmethod
    def deduplicate(
        data: List[Dict],
        key: Optional[str] = None
    ) -> List[Dict]:
        """Remove duplicates.
        
        Args:
            data: List of dictionaries
            key: Optional key field for deduplication
            
        Returns:
            Deduplicated data
        """
        if key:
            seen = set()
            unique = []
            for item in data:
                if key in item:
                    value = item[key]
                    if value not in seen:
                        seen.add(value)
                        unique.append(item)
            logger.info(f"Deduplicated by {key}: {len(data)} -> {len(unique)}")
            return unique
        else:
            # Deduplicate by entire dict
            unique = [dict(t) for t in {tuple(d.items()) for d in data}]
            logger.info(f"Deduplicated: {len(data)} -> {len(unique)}")
            return unique

    @staticmethod
    def transform(
        data: List[Dict],
        transformations: Dict[str, Callable]
    ) -> List[Dict]:
        """Transform data fields.
        
        Args:
            data: List of dictionaries
            transformations: Dict of {field: transform_function}
            
        Returns:
            Transformed data
        """
        transformed = []
        for item in data:
            new_item = item.copy()
            for field, func in transformations.items():
                if field in new_item:
                    try:
                        new_item[field] = func(new_item[field])
                    except Exception as e:
                        logger.warning(f"Transform failed for {field}: {e}")
            transformed.append(new_item)
        
        return transformed


def main() -> int:
    """CLI for data processor."""
    parser = argparse.ArgumentParser(
        description="Data processing and transformation utilities",
        epilog="Examples:\n"
               "  %(prog)s convert data.csv --to json\n"
               "  %(prog)s convert data.json --to csv\n"
               "  %(prog)s filter data.json --field status=active\n"
               "  %(prog)s aggregate data.json --field price --operation avg\n"
               "  %(prog)s dedupe data.json --key email\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert between formats")
    convert_parser.add_argument("input", help="Input file path")
    convert_parser.add_argument(
        "--to",
        choices=["json", "csv"],
        required=True,
        help="Output format"
    )
    convert_parser.add_argument(
        "--output",
        "-o",
        help="Output file path (auto-generated if not provided)"
    )
    
    # Filter command
    filter_parser = subparsers.add_parser("filter", help="Filter data")
    filter_parser.add_argument("input", help="Input JSON file")
    filter_parser.add_argument(
        "--field",
        "-f",
        action="append",
        help="Filter field=value (can specify multiple)"
    )
    filter_parser.add_argument(
        "--output",
        "-o",
        help="Output file path"
    )
    
    # Aggregate command
    agg_parser = subparsers.add_parser("aggregate", help="Aggregate data")
    agg_parser.add_argument("input", help="Input JSON file")
    agg_parser.add_argument(
        "--field",
        required=True,
        help="Field to aggregate"
    )
    agg_parser.add_argument(
        "--operation",
        choices=["sum", "avg", "min", "max", "count"],
        default="sum",
        help="Aggregation operation"
    )
    
    # Deduplicate command
    dedupe_parser = subparsers.add_parser("dedupe", help="Remove duplicates")
    dedupe_parser.add_argument("input", help="Input JSON file")
    dedupe_parser.add_argument(
        "--key",
        help="Key field for deduplication"
    )
    dedupe_parser.add_argument(
        "--output",
        "-o",
        help="Output file path"
    )
    
    # Global options
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
    
    processor = DataProcessor()
    
    # Execute command
    if args.command == "convert":
        input_path = Path(args.input)
        output_path = Path(args.output) if args.output else None
        
        if args.to == "json":
            data = processor.csv_to_json(input_path, output_path)
            if not output_path:
                print(json.dumps(data, indent=2))
        else:  # csv
            processor.json_to_csv(input_path, output_path)
        
        print(f"✅ Converted {input_path} to {args.to}")
        return 0
    
    elif args.command == "filter":
        data = load_json(Path(args.input))
        
        # Parse filters
        filters = {}
        if args.field:
            for f in args.field:
                if "=" in f:
                    key, value = f.split("=", 1)
                    filters[key] = value
        
        filtered = processor.filter_data(data, filters)
        
        if args.output:
            save_json(filtered, Path(args.output))
            print(f"✅ Filtered data saved to {args.output}")
        else:
            print(json.dumps(filtered, indent=2))
        
        return 0
    
    elif args.command == "aggregate":
        data = load_json(Path(args.input))
        result = processor.aggregate(data, args.field, args.operation)
        print(f"{args.operation}({args.field}) = {result}")
        return 0
    
    elif args.command == "dedupe":
        data = load_json(Path(args.input))
        unique = processor.deduplicate(data, args.key)
        
        if args.output:
            save_json(unique, Path(args.output))
            print(f"✅ Deduplicated data saved to {args.output}")
        else:
            print(json.dumps(unique, indent=2))
        
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
