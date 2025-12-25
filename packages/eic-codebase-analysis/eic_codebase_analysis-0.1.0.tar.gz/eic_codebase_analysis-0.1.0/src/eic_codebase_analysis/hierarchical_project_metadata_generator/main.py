import sys
from pathlib import Path

# Allow running as a script
if __package__ is None and __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    __package__ = "eic_codebase_analysis.hierarchical_project_metadata_generator"

import argparse
from typing import List, Optional

from .generator import generate_and_write_hierarchical_metadata


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate hierarchical (file, folder, project) AI (Gemini) "
            "metadata for one or more repositories/directories, writing "
            "separate markdown files for each level."
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
        "--no-file-structure",
        action="store_false",
        dest="analyze_file_structure",
        help=(
            "Disable deep analysis of methods, variables, interfaces and "
            "dependencies on file level."
        ),
    )

    parser.add_argument(
        "--no-folder-components",
        action="store_false",
        dest="analyze_folder_components",
        help=(
            "Disable extended component and dependency analysis on folder level."
        ),
    )

    parser.add_argument(
        "--no-project-overview",
        action="store_false",
        dest="analyze_project_overview",
        help=(
            "Disable extended macro-component and use case overview on project level."
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

    generate_and_write_hierarchical_metadata(
        roots=args.root,
        model=args.model,
        api_key=args.api_key,
        include_hidden=args.include_hidden,
        exclude_dirs=args.exclude_dir,
        exclude_files=args.exclude_file,
        max_bytes_per_file=max_bytes,
        analyze_file_structure=args.analyze_file_structure,
        analyze_folder_components=args.analyze_folder_components,
        analyze_project_overview=args.analyze_project_overview,
    )


if __name__ == "__main__":
    main()
