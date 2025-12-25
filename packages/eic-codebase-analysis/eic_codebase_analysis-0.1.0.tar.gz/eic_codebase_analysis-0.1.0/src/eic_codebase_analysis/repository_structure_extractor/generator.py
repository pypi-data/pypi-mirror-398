import os
from pathlib import Path
from typing import Iterable, List, Set

from .utils import (
    is_hidden,
    should_skip_dir,
    should_skip_file,
    format_markdown_header,
)


def _build_tree_for_root(
    root: Path,
    include_hidden: bool,
    exclude_dirs: Set[str],
    exclude_files: Set[str],
    base_level: int = 2,
) -> List[str]:
    """
    Build a Markdown tree for a single root directory.

    The structure is represented as nested bullet lists:
    - Directories are suffixed with a trailing slash.
    - Indentation is done with two spaces per level.
    """
    lines: List[str] = []

    root = root.resolve()
    root_title = root.name
    lines.append(format_markdown_header(f"Root: {root_title}", base_level))
    lines.append("")
    lines.append(f"- `{root.name}/`")

    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)
        if not include_hidden and is_hidden(current_path) and current_path != root:
            continue

        # Filter and sort directories
        dirnames[:] = sorted(
            [
                d
                for d in dirnames
                if not should_skip_dir(d, exclude_dirs)
                and (include_hidden or not d.startswith("."))
            ]
        )

        # Sort files
        filenames = sorted(
            [
                f
                for f in filenames
                if not should_skip_file(f, exclude_files)
                and (include_hidden or not f.startswith("."))
            ]
        )

        # Compute indentation level relative to root
        rel_path = current_path.relative_to(root)
        depth = 0 if rel_path == Path(".") else len(rel_path.parts)
        indent = "  " * (depth + 1)  # +1 because root already has one level

        # Add directories
        for d in dirnames:
            lines.append(f"{indent}- `{d}/`")

        # Add files
        for f in filenames:
            lines.append(f"{indent}- `{f}`")

    lines.append("")
    return lines


def generate_repository_structure_markdown(
    roots: Iterable[str],
    include_hidden: bool = False,
    exclude_dirs: Iterable[str] | None = None,
    exclude_files: Iterable[str] | None = None,
) -> str:
    """
    Generate a Markdown representation of the directory structure for given roots.

    Parameters:
        roots: Iterable of paths to repositories or directories.
        include_hidden: Whether to include hidden files/directories (starting with '.').
        exclude_dirs: Iterable of directory names to exclude (exact name match).
        exclude_files: Iterable of file names to exclude (exact name match).

    Returns:
        A Markdown string documenting the structure of the provided roots.
    """
    exclude_dirs_set: Set[str] = set(exclude_dirs or [])
    exclude_files_set: Set[str] = set(exclude_files or [])

    roots_list = [Path(r) for r in roots]
    if not roots_list:
        raise ValueError("At least one root directory must be provided.")

    lines: List[str] = []
    lines.append("# Repository Structure Overview")
    lines.append("")
    lines.append("This document describes the directory and file structure of the specified repositories or directories.")
    lines.append("It does not include file contents, only paths and hierarchy.")
    lines.append("")

    for idx, root in enumerate(roots_list, start=1):
        if not root.exists() or not root.is_dir():
            lines.append(format_markdown_header(f"Root {idx}: {root}", 2))
            lines.append("")
            lines.append(f"> Warning: path `{root}` does not exist or is not a directory.")
            lines.append("")
            continue

        tree_lines = _build_tree_for_root(
            root=root,
            include_hidden=include_hidden,
            exclude_dirs=exclude_dirs_set,
            exclude_files=exclude_files_set,
            base_level=2,
        )
        lines.extend(tree_lines)

    return "\n".join(lines)
