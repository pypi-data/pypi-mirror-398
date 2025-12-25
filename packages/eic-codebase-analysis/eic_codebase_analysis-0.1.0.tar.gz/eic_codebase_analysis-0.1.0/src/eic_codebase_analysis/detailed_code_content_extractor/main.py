import sys
from pathlib import Path

# Allow running as a script
if __package__ is None and __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    __package__ = "eic_codebase_analysis.detailed_code_content_extractor"

import argparse
from typing import List, Optional

from .core import generate_detailed_markdown


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Extract directory structure and full file contents into a Markdown (.md) file "
            "for one or more repositories/directories."
        )
    )
    parser.add_argument(
        "--root",
        "-r",
        nargs="+",
        required=True,
        help="One or more root directories (repositories or subdirectories) to document.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="repository_contents.md",
        help="Output Markdown file path. Defaults to 'repository_contents.md'.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories (names starting with '.').",
    )
    parser.add_argument(
        "--exclude-dir",
        nargs="*",
        default=[".git", ".svn", ".hg", "node_modules", "__pycache__"],
        help="Directory names to exclude (exact names).",
    )
    parser.add_argument(
        "--exclude-file",
        nargs="*",
        default=[".DS_Store", "Thumbs.db"],
        help="File names to exclude (exact names).",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=200_000,
        help=(
            "Maximum number of bytes to read per file. "
            "Larger files are truncated to this size. Use a larger value or "
            "set to 0 to disable truncation."
        ),
    )
    parser.add_argument(
        "--strip-whitespace",
        action="store_true",
        help=(
            "Strip leading/trailing spaces from lines and collapse multiple "
            "blank lines in the resulting Markdown."
        ),
    )

    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    """Main entry point for CLI usage."""
    args = parse_args(argv)

    max_bytes: Optional[int]
    if args.max_bytes is not None and args.max_bytes <= 0:
        max_bytes = None
    else:
        max_bytes = args.max_bytes

    markdown = generate_detailed_markdown(
        roots=args.root,
        include_hidden=args.include_hidden,
        exclude_dirs=args.exclude_dir,
        exclude_files=args.exclude_file,
        max_bytes_per_file=max_bytes,
        strip_whitespace=args.strip_whitespace,
    )

    output_path = Path(args.output)
    output_path.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    main()
