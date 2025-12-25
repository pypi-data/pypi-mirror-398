import sys
from pathlib import Path

# Allow running as a script
if __package__ is None and __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    __package__ = "eic_codebase_analysis.repository_file_metadata_generator"

import argparse
from typing import List, Optional

from .generator import (
    generate_file_metadata_markdown,
    write_per_file_metadata,
    write_per_folder_metadata,
)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate AI (Gemini) metadata for repository files in Markdown "
            "form, either per-file, per-folder, or as a single aggregated document."
        )
    )

    parser.add_argument(
        "--root",
        "-r",
        nargs="+",
        required=True,
        help="One or more root directories (repositories or subdirectories) to analyze.",
    )

    parser.add_argument(
        "--model",
        "-m",
        type=str,
        required=True,
        help="Gemini model name to use (e.g., 'gemini-1.5-pro').",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help=(
            "API key for Gemini. If omitted, GOOGLE_API_KEY environment "
            "variable is used."
        ),
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="repository_file_metadata.md",
        help=(
            "Output Markdown file path for aggregated mode. "
            "Defaults to 'repository_file_metadata.md'. "
            "Ignored in per-file and folder modes."
        ),
    )

    parser.add_argument(
        "--output-mode",
        choices=["per-file", "aggregate", "folder"],
        default="aggregate",
        help=(
            "Output mode: 'per-file' to create sidecar .ai-meta.md files "
            "next to each file, 'folder' to create .folder-ai-meta.md files "
            "per directory, or 'aggregate' to create a single markdown "
            "document with metadata for all files."
        ),
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
        help=(
            "Directory names to exclude (exact names). "
            "Defaults: .git, .svn, .hg, node_modules, __pycache__."
        ),
    )

    parser.add_argument(
        "--exclude-file",
        nargs="*",
        default=[".DS_Store", "Thumbs.db"],
        help=(
            "File names to exclude (exact names). "
            "Defaults: .DS_Store, Thumbs.db."
        ),
    )

    parser.add_argument(
        "--max-bytes",
        type=int,
        default=200_000,
        help=(
            "Maximum number of bytes to read per file for analysis. "
            "Larger files are truncated to this size. Use a larger value or "
            "set to 0 to disable truncation."
        ),
    )

    parser.add_argument(
        "--strip-whitespace",
        action="store_true",
        help=(
            "Strip leading/trailing spaces from lines and collapse multiple "
            "blank lines in the aggregated Markdown output."
        ),
    )

    parser.add_argument(
        "--no-file-structure",
        action="store_false",
        dest="analyze_file_structure",
        help=(
            "Disable deep analysis of methods, variables, interfaces and "
            "dependencies on file level."
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

    if args.output_mode == "per-file":
        write_per_file_metadata(
            roots=args.root,
            model=args.model,
            api_key=args.api_key,
            include_hidden=args.include_hidden,
            exclude_dirs=args.exclude_dir,
            exclude_files=args.exclude_file,
            max_bytes_per_file=max_bytes,
            analyze_file_structure=args.analyze_file_structure,
        )
    elif args.output_mode == "folder":
        write_per_folder_metadata(
            roots=args.root,
            model=args.model,
            api_key=args.api_key,
            include_hidden=args.include_hidden,
            exclude_dirs=args.exclude_dir,
            exclude_files=args.exclude_file,
            max_bytes_per_file=max_bytes,
            analyze_file_structure=args.analyze_file_structure,
        )
    else:
        markdown = generate_file_metadata_markdown(
            roots=args.root,
            model=args.model,
            api_key=args.api_key,
            include_hidden=args.include_hidden,
            exclude_dirs=args.exclude_dir,
            exclude_files=args.exclude_file,
            max_bytes_per_file=max_bytes,
            strip_whitespace=args.strip_whitespace,
            output_mode="aggregate",
            analyze_file_structure=args.analyze_file_structure,
        )
        output_path = Path(args.output)
        output_path.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    main()
