from pathlib import Path
from typing import Set

def is_hidden(path: Path) -> bool:
    """Return True if the file or directory is hidden (starts with a dot)."""
    return path.name.startswith(".")


def should_skip_dir(dirname: str, exclude_dirs: Set[str]) -> bool:
    """Return True if directory should be skipped."""
    return dirname in exclude_dirs


def should_skip_file(filename: str, exclude_files: Set[str]) -> bool:
    """Return True if file should be skipped."""
    return filename in exclude_files


def format_markdown_header(title: str, level: int = 1) -> str:
    """Return a Markdown header line."""
    hashes = "#" * max(level, 1)
    return f"{hashes} {title}"
