from pathlib import Path
from typing import Set, List, Optional, Tuple
import os

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


def guess_language_from_suffix(path: Path) -> str:
    """
    Guess a code fence language from file suffix for better syntax highlighting.

    The mapping is intentionally small and generic; unknown types fall back to ''.
    """
    ext = path.suffix.lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".jsx": "jsx",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".cxx": "cpp",
        ".cc": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".json": "json",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".toml": "toml",
        ".sh": "bash",
        ".bash": "bash",
        ".ps1": "powershell",
        ".md": "markdown",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".sql": "sql",
        ".xml": "xml",
        ".kt": "kotlin",
        ".swift": "swift",
    }
    return mapping.get(ext, "")


def walk_files(
    root: Path,
    include_hidden: bool,
    exclude_dirs: Set[str],
    exclude_files: Set[str],
) -> List[Path]:
    """
    Walk a root directory and return a sorted list of file paths
    honoring hidden/include and exclude rules.
    """
    files: List[Path] = []

    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)

        # Skip hidden directories if requested
        if not include_hidden and is_hidden(current_path) and current_path != root:
            continue

        # Filter and sort directories in-place to keep traversal deterministic
        dirnames[:] = sorted(
            d
            for d in dirnames
            if not should_skip_dir(d, exclude_dirs)
            and (include_hidden or not d.startswith("."))
        )

        # Filter and collect file paths
        for fname in sorted(filenames):
            if should_skip_file(fname, exclude_files):
                continue
            if not include_hidden and fname.startswith("."):
                continue
            files.append(Path(current_root) / fname)

    # Sort by relative path for stable ordering
    files.sort()
    return files


def read_file_with_limit(
    path: Path,
    max_bytes_per_file: Optional[int],
) -> Tuple[str, bool]:
    """
    Read text content from file with an optional byte limit.

    Returns:
      (text, truncated_flag)
    """
    if max_bytes_per_file is not None:
        with open(path, "rb") as bf:
            raw = bf.read(max_bytes_per_file + 1)
        truncated = len(raw) > max_bytes_per_file
        raw = raw[:max_bytes_per_file]
        text = raw.decode("utf-8", errors="replace")
        return text, truncated
    text = path.read_text(encoding="utf-8", errors="replace")
    return text, False


def maybe_strip_whitespace_block(text: str) -> str:
    """
    Strip leading/trailing spaces per line and collapse multiple blank
    lines into one.
    """
    from itertools import dropwhile

    lines = [ln.strip() for ln in text.splitlines()]

    # Remove leading empty lines
    lines = list(dropwhile(lambda s: s == "", lines))

    # Remove trailing empty lines
    while lines and lines[-1] == "":
        lines.pop()

    # Collapse multiple consecutive empty lines into one
    final_lines: List[str] = []
    previous_empty = False
    for ln in lines:
        if ln == "":
            if previous_empty:
                continue
            previous_empty = True
        else:
            previous_empty = False
        final_lines.append(ln)

    return "\n".join(final_lines)
