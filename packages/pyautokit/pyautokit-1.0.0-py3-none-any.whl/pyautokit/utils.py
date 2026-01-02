"""Utility functions across PyAutokit."""

import hashlib
from pathlib import Path
from typing import List, Any
from datetime import datetime
import json


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes."""
    return file_path.stat().st_size / (1024 * 1024)


def get_file_extension(file_path: Path) -> str:
    """Get file extension without dot."""
    return file_path.suffix.lstrip(".").lower() or "no_extension"


def get_file_creation_date(file_path: Path) -> str:
    """Get file creation date as YYYY-MM-DD."""
    timestamp = file_path.stat().st_mtime
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")


def get_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate file hash."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def load_json(file_path: Path) -> dict:
    """Safely load JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")


def save_json(data: Any, file_path: Path, indent: int = 2) -> None:
    """Save data to JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=indent)


def get_all_files(
    directory: Path,
    recursive: bool = True,
    extensions: List[str] = None
) -> List[Path]:
    """Get all files in directory."""
    directory = Path(directory)
    if not directory.is_dir():
        return []

    pattern = "**/*" if recursive else "*"
    files = [f for f in directory.glob(pattern) if f.is_file()]

    if extensions:
        exts = {ext.lower().lstrip(".") for ext in extensions}
        files = [f for f in files if get_file_extension(f) in exts]

    return sorted(files)