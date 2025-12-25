import sys
from pathlib import Path

# Allow running as a script
if __package__ is None and __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    __package__ = "eic_codebase_analysis.repository_structure_extractor"

import argparse
from typing import List
from pathlib import Path

from .generator import generate_repository_structure_markdown


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract the structure of one or more repositories/directories into a Markdown (.md) file."
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
        default="repository_structure.md",
        help="Output Markdown file path. Defaults to 'repository_structure.md'.",
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
        help="Directory names to exclude (exact names). Defaults: .git, .svn, .hg, node_modules, __pycache__.",
    )
    parser.add_argument(
        "--exclude-file",
        nargs="*",
        default=[".DS_Store", "Thumbs.db"],
        help="File names to exclude (exact names). Defaults: .DS_Store, Thumbs.db.",
    )

    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    """Main entry point for CLI usage."""
    args = parse_args(argv)

    markdown = generate_repository_structure_markdown(
        roots=args.root,
        include_hidden=args.include_hidden,
        exclude_dirs=args.exclude_dir,
        exclude_files=args.exclude_file,
    )

    output_path = Path(args.output)
    output_path.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    main()
