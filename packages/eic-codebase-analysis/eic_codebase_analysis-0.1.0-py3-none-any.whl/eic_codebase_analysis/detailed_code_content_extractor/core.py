from pathlib import Path
from typing import List, Set, Optional, Iterable

from .utils import (
    format_markdown_header,
    guess_language_from_suffix,
    walk_files
)


def _build_tree_section(
    root: Path,
    files: List[Path],
    base_level: int = 2,
) -> List[str]:
    """
    Build a simple tree section for the given root and list of files.

    This is lighter-weight than Script 1 but gives enough structure
    to orient readers and downstream tools.
    """
    lines: List[str] = []
    root = root.resolve()
    lines.append(format_markdown_header(f"Root: {root.name} (Structure)", base_level))
    lines.append("")

    # Represent as nested bullets relative to root
    lines.append(f"- `{root.name}/`")

    # Use a set to track which directories have been printed
    printed_dirs: Set[Path] = set()

    for fpath in files:
        rel = fpath.relative_to(root)
        parts = list(rel.parts)
        # All but last are directories
        current_dir = root
        depth = 1  # already printed root with depth 0

        for part in parts[:-1]:
            current_dir = current_dir / part
            if current_dir not in printed_dirs:
                indent = "  " * depth
                lines.append(f"{indent}- `{part}/`")
                printed_dirs.add(current_dir)
            depth += 1

        # Print file
        file_name = parts[-1]
        indent = "  " * depth
        lines.append(f"{indent}- `{file_name}`")

    lines.append("")
    return lines


def _build_content_section_for_root(
    root: Path,
    files: List[Path],
    max_bytes_per_file: Optional[int],
    base_level: int = 2,
) -> List[str]:
    """
    Build the detailed content section for a given root and list of files.

    Each file gets its own sub-section, with full contents or truncated
    if above max_bytes_per_file.
    """
    lines: List[str] = []
    root = root.resolve()
    lines.append(format_markdown_header(f"Root: {root.name} (Contents)", base_level))
    lines.append("")

    for fpath in files:
        rel = fpath.relative_to(root)
        header = format_markdown_header(f"`{rel.as_posix()}`", base_level + 1)
        lines.append(header)
        lines.append("")

        language = guess_language_from_suffix(fpath)

        try:
            # Read file content with a size guard
            if max_bytes_per_file is not None:
                # Read only up to max_bytes_per_file bytes, then stop
                with open(fpath, "rb") as bf:
                    raw = bf.read(max_bytes_per_file + 1)
                truncated = len(raw) > max_bytes_per_file
                raw = raw[:max_bytes_per_file]
                text = raw.decode("utf-8", errors="replace")
            else:
                text = fpath.read_text(encoding="utf-8", errors="replace")
                truncated = False
        except OSError as exc:
            lines.append("> Error: could not read file due to OS error.")
            lines.append(f"> Path: `{fpath}`")
            lines.append(f"> Detail: `{exc}`")
            lines.append("")
            continue

        # Emit fenced code block
        fence_lang = language if language else ""
        lines.append(f"```")
        lines.append(text)
        lines.append("```")
        lines.append("")

        if truncated:
            lines.append(
                f"> Note: file was truncated to {max_bytes_per_file} bytes for export."
            )
            lines.append("")

    return lines


def generate_detailed_markdown(
    roots: Iterable[str],
    include_hidden: bool = False,
    exclude_dirs: Iterable[str] | None = None,
    exclude_files: Iterable[str] | None = None,
    max_bytes_per_file: Optional[int] = 200_000,
    strip_whitespace: bool = False,
) -> str:
    """
    Generate a Markdown document that includes:

    - Directory structure for each root.
    - Full or truncated contents of each file.

    Parameters:
        roots: Iterable of paths to repositories or directories.
        include_hidden: Whether to include hidden files/directories.
        exclude_dirs: Iterable of directory names to exclude.
        exclude_files: Iterable of file names to exclude.
        max_bytes_per_file: Optional hard limit per file in bytes. If None,
                            files are read entirely.
        strip_whitespace: If True, trim surrounding spaces and collapse
                          multiple blank lines in the final output.
    """
    roots_list = [Path(r).resolve() for r in roots]
    if not roots_list:
        raise ValueError("At least one root directory must be provided.")

    exclude_dirs_set: Set[str] = set(exclude_dirs or [])
    exclude_files_set: Set[str] = set(exclude_files or [])

    lines: List[str] = []

    # Document header
    lines.append("# Repository Structure and Contents")
    lines.append("")
    lines.append(
        "This document contains both a structural overview and detailed contents "
        "of the specified repositories or directories."
    )
    lines.append("")
    lines.append(f"- Include hidden: `{include_hidden}`")
    lines.append(f"- Excluded directories: `{sorted(exclude_dirs_set)}`")
    lines.append(f"- Excluded files: `{sorted(exclude_files_set)}`")
    if max_bytes_per_file is not None:
        lines.append(f"- Max bytes per file: `{max_bytes_per_file}`")
    else:
        lines.append("- Max bytes per file: `unlimited`")
    lines.append("")

    # Per-root sections
    for idx, root in enumerate(roots_list, start=1):
        if not root.exists() or not root.is_dir():
            lines.append(format_markdown_header(f"Root {idx}: {root}", 2))
            lines.append("")
            lines.append(
                f"> Warning: path `{root}` does not exist or is not a directory."
            )
            lines.append("")
            continue

        files = walk_files(
            root=root,
            include_hidden=include_hidden,
            exclude_dirs=exclude_dirs_set,
            exclude_files=exclude_files_set,
        )

        # Structure section
        lines.extend(_build_tree_section(root, files, base_level=2))

        # Content section
        lines.extend(
            _build_content_section_for_root(
                root, files, max_bytes_per_file=max_bytes_per_file, base_level=2
            )
        )

    # Post-process whitespace if requested
    text = "\n".join(lines)
    if strip_whitespace:
        # Strip trailing/leading spaces on each line
        stripped_lines = [ln.strip() for ln in text.splitlines()]

        # Remove leading/trailing completely empty lines
        from itertools import dropwhile

        def is_not_empty(s: str) -> bool:
            return s != ""

        stripped_lines = list(
            dropwhile(lambda s: s == "", stripped_lines)
        )
        while stripped_lines and stripped_lines[-1] == "":
            stripped_lines.pop()

        # Collapse multiple consecutive empty lines into one
        final_lines: List[str] = []
        previous_empty = False
        for ln in stripped_lines:
            if ln == "":
                if previous_empty:
                    continue
                previous_empty = True
            else:
                previous_empty = False
            final_lines.append(ln)

        text = "\n".join(final_lines)

    return text
