import os
from pathlib import Path
from typing import Iterable, List, Set, Optional, Tuple, Dict

from .utils import (
    walk_files,
    read_file_with_limit,
    maybe_strip_whitespace_block,
    guess_language_from_suffix,
    format_markdown_header,
)
from .gemini_utils import (
    configure_gemini,
    generate_metadata_for_file,
)


def generate_file_metadata_markdown(
    roots: Iterable[str],
    model: str,
    api_key: Optional[str] = None,
    include_hidden: bool = False,
    exclude_dirs: Iterable[str] | None = None,
    exclude_files: Iterable[str] | None = None,
    max_bytes_per_file: Optional[int] = 200_000,
    strip_whitespace: bool = False,
    output_mode: str = "aggregate",
    analyze_file_structure: bool = True,
) -> str:
    """
    Generate metadata descriptions for files in the provided roots.

    Parameters:
      roots: Iterable of paths to repositories or directories.
      model: Gemini model name (e.g., 'gemini-1.5-pro').
      api_key: API key for Gemini. If None, GOOGLE_API_KEY env var is used.
      include_hidden: Whether to include hidden files/directories.
      exclude_dirs: Iterable of directory names to exclude.
      exclude_files: Iterable of file names to exclude.
      max_bytes_per_file: Maximum bytes read per file; None means unlimited.
      strip_whitespace: If True, trim spaces and collapse blank lines in
                        the final aggregated markdown output.
      output_mode: 'per-file', 'aggregate', or 'folder'.
      analyze_file_structure: If True, ask the model to explicitly describe
                              methods, variables, sub-components, interfaces,
                              and dependencies in each file.

    Returns:
      A Markdown string containing metadata for all processed files (useful
      in 'aggregate' mode). In 'per-file' or 'folder' mode, the returned
      string is an aggregation of the same metadata written to individual
      files.
    """
    roots_list = [Path(r) for r in roots]
    if not roots_list:
        raise ValueError("At least one root directory must be provided.")

    exclude_dirs_set: Set[str] = set(exclude_dirs or [])
    exclude_files_set: Set[str] = set(exclude_files or [])

    if api_key is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "API key must be provided via --api-key or GOOGLE_API_KEY environment variable."
        )

    gemini_model = configure_gemini(api_key=api_key, model_name=model)

    file_entries: List[Tuple[Path, Path]] = []
    for root in roots_list:
        if not root.exists() or not root.is_dir():
            continue
        files = walk_files(
            root=root,
            include_hidden=include_hidden,
            exclude_dirs=exclude_dirs_set,
            exclude_files=exclude_files_set,
        )
        for fpath in files:
            file_entries.append((root, fpath))

    lines: List[str] = []

    if output_mode == "aggregate":
        lines.append("# Repository File Metadata")
        lines.append("")
        lines.append(
            "This document contains AI-generated metadata summaries for each file "
            "in the specified repositories or directories."
        )
        lines.append("")
        lines.append(f"- Gemini model: `{model}`")
        lines.append(f"- Include hidden: `{include_hidden}`")
        lines.append(f"- Excluded directories: `{sorted(exclude_dirs_set)}`")
        lines.append(f"- Excluded files: `{sorted(exclude_files_set)}`")
        if max_bytes_per_file is not None:
            lines.append(f"- Max bytes per file: `{max_bytes_per_file}`")
        else:
            lines.append("- Max bytes per file: `unlimited`")
        lines.append("")

    # Folder mode: accumulate per-folder sections in memory, then write
    folder_sections: Dict[Path, List[str]] = {}
    if output_mode == "folder":
        # Initialize the mapping with empty lists
        for root, fpath in file_entries:
            folder = fpath.parent
            if folder not in folder_sections:
                folder_sections[folder] = []

    for root, fpath in file_entries:
        rel = fpath.relative_to(root).as_posix()
        language = guess_language_from_suffix(fpath)

        try:
            content, truncated = read_file_with_limit(fpath, max_bytes_per_file)
        except OSError as exc:
            if output_mode == "aggregate":
                error_block = [
                    format_markdown_header(f"`{rel}`", 2),
                    "",
                    "> Error: could not read file due to OS error.",
                    f"> Path: `{fpath}`",
                    f"> Detail: `{exc}`",
                    "",
                ]
                lines.extend(error_block)
            continue

        metadata_md = generate_metadata_for_file(
            model=gemini_model,
            relative_path=rel,
            language=language,
            content=content,
            analyze_file_structure=analyze_file_structure,
        )

        if not metadata_md.strip():
            continue

        if truncated:
            metadata_md += (
                "\n\n> Note: file contents were truncated for analysis due to size limits."
            )

        if output_mode == "aggregate":
            lines.append(format_markdown_header(f"`{rel}`", 2))
            lines.append("")
            lines.append(metadata_md)
            lines.append("")
        elif output_mode == "per-file":
            lines.append(format_markdown_header(f"`{rel}`", 2))
            lines.append("")
            lines.append(metadata_md)
            lines.append("")
        elif output_mode == "folder":
            folder = fpath.parent
            rel_in_folder = fpath.name
            section_lines = folder_sections.setdefault(folder, [])
            section_lines.append(format_markdown_header(f"`{rel_in_folder}`", 2))
            section_lines.append("")
            section_lines.append(metadata_md)
            section_lines.append("")
        else:
            raise ValueError(f"Unsupported output_mode: {output_mode}")

    if output_mode == "folder":
        # Write one metadata file per folder
        for folder, section_lines in folder_sections.items():
            if not section_lines:
                continue
            folder_header: List[str] = []
            folder_rel = folder
            folder_header.append(
                format_markdown_header(f"Folder metadata: `{folder_rel.name}`", 1)
            )
            folder_header.append("")
            folder_header.append(
                "This document contains AI-generated metadata summaries for "
                "files in this folder."
            )
            folder_header.append("")
            all_lines = folder_header + section_lines
            folder_text = "\n".join(all_lines)
            sidecar_name = f"{folder.name}.folder-ai-meta.md"
            sidecar_path = folder / sidecar_name
            sidecar_path.write_text(folder_text, encoding="utf-8")

        # Also return a synthetic aggregate (useful for logging or caller usage)
        all_agg_lines: List[str] = []
        for folder, section_lines in folder_sections.items():
            if not section_lines:
                continue
            all_agg_lines.append(format_markdown_header(f"{folder}", 1))
            all_agg_lines.append("")
            all_agg_lines.extend(section_lines)
        text = "\n".join(all_agg_lines)
        if strip_whitespace:
            text = maybe_strip_whitespace_block(text)
        return text

    text = "\n".join(lines)
    if strip_whitespace:
        text = maybe_strip_whitespace_block(text)
    return text


def write_per_file_metadata(
    roots: Iterable[str],
    model: str,
    api_key: Optional[str] = None,
    include_hidden: bool = False,
    exclude_dirs: Iterable[str] | None = None,
    exclude_files: Iterable[str] | None = None,
    max_bytes_per_file: Optional[int] = 200_000,
    analyze_file_structure: bool = True,
) -> None:
    """
    Generate and write a sidecar .ai-meta.md file next to each processed file.

    The sidecar file name is `<original_name>.ai-meta.md`. Existing files
    with the same name are overwritten.
    """
    roots_list = [Path(r) for r in roots]
    if not roots_list:
        raise ValueError("At least one root directory must be provided.")

    exclude_dirs_set: Set[str] = set(exclude_dirs or [])
    exclude_files_set: Set[str] = set(exclude_files or [])

    if api_key is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "API key must be provided via --api-key or GOOGLE_API_KEY environment variable."
        )

    gemini_model = configure_gemini(api_key=api_key, model_name=model)

    for root in roots_list:
        if not root.exists() or not root.is_dir():
            continue

        files = walk_files(
            root=root,
            include_hidden=include_hidden,
            exclude_dirs=exclude_dirs_set,
            exclude_files=exclude_files_set,
        )

        for fpath in files:
            rel = fpath.relative_to(root).as_posix()
            language = guess_language_from_suffix(fpath)

            try:
                content, truncated = read_file_with_limit(fpath, max_bytes_per_file)
            except OSError:
                continue

            metadata_md = generate_metadata_for_file(
                model=gemini_model,
                relative_path=rel,
                language=language,
                content=content,
                analyze_file_structure=analyze_file_structure,
            )

            if not metadata_md.strip():
                continue

            if truncated:
                metadata_md += (
                    "\n\n> Note: file contents were truncated for analysis due to size limits."
                )

            lines: List[str] = []
            lines.append(format_markdown_header(f"Metadata: `{rel}`", 1))
            lines.append("")
            lines.append(metadata_md)
            lines.append("")
            body = "\n".join(lines)

            sidecar_path = fpath.with_suffix(f"{fpath.suffix}.ai-meta.md")
            if fpath.suffix == "":
                sidecar_path = fpath.with_name(f"{fpath.name}.ai-meta.md")

            sidecar_path.write_text(body, encoding="utf-8")


def write_per_folder_metadata(
    roots: Iterable[str],
    model: str,
    api_key: Optional[str] = None,
    include_hidden: bool = False,
    exclude_dirs: Iterable[str] | None = None,
    exclude_files: Iterable[str] | None = None,
    max_bytes_per_file: Optional[int] = 200_000,
    analyze_file_structure: bool = True,
) -> None:
    """
    Generate and write a .folder-ai-meta.md file for each directory.

    Each folder-level file contains AI-generated metadata sections for
    all files directly in that folder (respecting include/exclude rules).
    """
    roots_list = [Path(r) for r in roots]
    if not roots_list:
        raise ValueError("At least one root directory must be provided.")

    exclude_dirs_set: Set[str] = set(exclude_dirs or [])
    exclude_files_set: Set[str] = set(exclude_files or [])

    if api_key is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "API key must be provided via --api-key or GOOGLE_API_KEY environment variable."
        )

    gemini_model = configure_gemini(api_key=api_key, model_name=model)

    folder_sections: Dict[Path, List[str]] = {}

    for root in roots_list:
        if not root.exists() or not root.is_dir():
            continue

        files = walk_files(
            root=root,
            include_hidden=include_hidden,
            exclude_dirs=exclude_dirs_set,
            exclude_files=exclude_files_set,
        )

        for fpath in files:
            folder = fpath.parent
            rel_in_folder = fpath.name
            rel_full = fpath.relative_to(root).as_posix()
            language = guess_language_from_suffix(fpath)

            try:
                content, truncated = read_file_with_limit(fpath, max_bytes_per_file)
            except OSError:
                continue

            metadata_md = generate_metadata_for_file(
                model=gemini_model,
                relative_path=rel_full,
                language=language,
                content=content,
                analyze_file_structure=analyze_file_structure,
            )

            if not metadata_md.strip():
                continue

            if truncated:
                metadata_md += (
                    "\n\n> Note: file contents were truncated for analysis due to size limits."
                )

            section_lines = folder_sections.setdefault(folder, [])
            section_lines.append(format_markdown_header(f"`{rel_in_folder}`", 2))
            section_lines.append("")
            section_lines.append(metadata_md)
            section_lines.append("")

    for folder, section_lines in folder_sections.items():
        if not section_lines:
            continue
        header_lines: List[str] = []
        header_lines.append(
            format_markdown_header(f"Folder metadata: `{folder.name}`", 1)
        )
        header_lines.append("")
        header_lines.append(
            "This document contains AI-generated metadata summaries for files in this folder."
        )
        header_lines.append("")
        all_lines = header_lines + section_lines
        folder_text = "\n".join(all_lines)
        sidecar_name = f"{folder.name}.folder-ai-meta.md"
        sidecar_path = folder / sidecar_name
        sidecar_path.write_text(folder_text, encoding="utf-8")
