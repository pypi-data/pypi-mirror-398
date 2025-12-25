import os
from pathlib import Path
from typing import Iterable, List, Set, Optional, Dict

from .utils import (
    walk_files,
    read_file_with_limit,
    guess_language_from_suffix,
    format_markdown_header,
)
from .gemini_utils import (
    configure_gemini,
    build_file_prompt,
    build_folder_prompt,
    build_project_prompt,
    build_compression_prompt,
    generate_text,
    generate_chat_response,
)


def compress_summary(text: str, model, max_len: int = 400) -> str:
    """
    Compress a summary text to be under max_len characters.
    First tries to keep it as is if short enough.
    If longer, uses the AI model to summarize it.
    Fallback to truncation if AI fails.
    """
    text = text.strip()
    if len(text) <= max_len:
        return text

    # Use AI to compress
    try:
        prompt = build_compression_prompt(text, max_len)
        compressed = generate_text(model, prompt)
        if compressed and compressed.strip():
            return compressed.strip()
    except Exception:
        # If AI generation fails, fall back to truncation
        pass

    return text[:max_len] + "..."


def generate_and_write_hierarchical_metadata(
    roots: Iterable[str],
    model: str,
    api_key: Optional[str] = None,
    include_hidden: bool = False,
    exclude_dirs: Iterable[str] | None = None,
    exclude_files: Iterable[str] | None = None,
    max_bytes_per_file: Optional[int] = 200_000,
    analyze_file_structure: bool = True,
    analyze_folder_components: bool = True,
    analyze_project_overview: bool = True,
) -> None:
    """
    Generate hierarchical project metadata (file, folder, project levels)
    for the specified roots and write separate markdown files:

    - Per file:    <file>.ai-meta.md
    - Per folder:  <folder_name>.folder-ai-meta.md
    - Per project: project.ai-meta.md at each root
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

    # 1) Scan all files to build the structure (but don't generate yet)
    folder_children: Dict[Path, List[Path]] = {}

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
            folder_children.setdefault(folder, []).append(fpath)

    # 2) Process folders bottom-up (Deepest first)
    #    This now includes generating file summaries within the folder context.
    file_summaries: Dict[Path, str] = {}
    folder_summaries: Dict[Path, str] = {}

    all_folders: Set[Path] = set(folder_children.keys())
    folder_depths: Dict[Path, int] = {}

    for root in roots_list:
        for folder in all_folders:
            if folder.is_relative_to(root):
                rel = folder.relative_to(root)
                depth = len(rel.parts)
                folder_depths[folder] = depth

    sorted_folders = sorted(all_folders, key=lambda p: -folder_depths.get(p, 0))

    for folder in sorted_folders:
        # --- File Generation Session (Contextual) ---
        files_in_folder = sorted(folder_children.get(folder, []))
        
        # Start a new chat session for this folder's files
        # This preserves context between files in the same folder
        chat_session = gemini_model.start_chat(history=[])

        for fpath in files_in_folder:
            rel = fpath.as_posix() # Just use path string for display/prompt
            # Note: relative path calculation might be tricky if roots are multiple
            # We can try to find the root it belongs to
            for r in roots_list:
                if fpath.is_relative_to(r):
                    rel = fpath.relative_to(r).as_posix()
                    break
            
            language = guess_language_from_suffix(fpath)

            try:
                content, truncated = read_file_with_limit(fpath, max_bytes_per_file)
            except OSError:
                continue

            prompt = build_file_prompt(
                rel,
                language,
                content,
                analyze_structure=analyze_file_structure,
            )
            
            # Use chat session
            summary = generate_chat_response(chat_session, prompt)
            
            if not summary.strip():
                continue

            if truncated:
                summary += (
                    "\n\n> Note: file contents were truncated for analysis due to size limits."
                )

            file_summaries[fpath] = summary

            # Write per-file sidecar
            sidecar_path = fpath.with_suffix(f"{fpath.suffix}.ai-meta.md")
            if fpath.suffix == "":
                sidecar_path = fpath.with_name(f"{fpath.name}.ai-meta.md")

            lines: List[str] = []
            lines.append(format_markdown_header(f"Metadata: `{rel}`", 1))
            lines.append("")
            lines.append(summary)
            lines.append("")
            sidecar_path.write_text("\n".join(lines), encoding="utf-8")

        # --- Folder Summary Generation (Hierarchical) ---
        # We collect summaries of files and subfolders to generate the folder description.
        # This is done via a FRESH stateless request (generate_text) to ensure we rely
        # on the abstraction/summaries, not the raw history of the chat session.
        
        items_desc: List[str] = []

        # Direct files (we just processed them)
        for fpath in files_in_folder:
            fsummary = file_summaries.get(fpath)
            if fsummary:
                items_desc.append(
                    f"- File `{fpath.name}`\n{compress_summary(fsummary, gemini_model, 400)}"
                )
            else:
                items_desc.append(f"- File `{fpath.name}`")

        # Subfolders (their summaries should already be computed due to bottom-up order)
        subfolders = sorted(
            [p for p in all_folders if p.parent == folder],
            key=lambda p: p.name,
        )
        for sub in subfolders:
            sub_summary = folder_summaries.get(sub)
            if sub_summary:
                items_desc.append(
                    f"- Subfolder `{sub.name}`\n{compress_summary(sub_summary, gemini_model, 400)}"
                )
            else:
                items_desc.append(f"- Subfolder `{sub.name}`")

        if not items_desc:
            continue

        items_block = "\n".join(items_desc)
        folder_rel_str = str(folder)
        prompt = build_folder_prompt(
            folder_rel_str,
            items_block,
            analyze_components=analyze_folder_components,
        )
        
        # Stateless call for folder summary
        folder_summary = generate_text(gemini_model, prompt)
        
        if not folder_summary.strip():
            continue

        folder_summaries[folder] = folder_summary

        # Write folder-level metadata file
        lines: List[str] = []
        lines.append(format_markdown_header(f"Folder metadata: `{folder.name}`", 1))
        lines.append("")
        lines.append(
            "This document contains AI-generated metadata summaries for files "
            "and subfolders in this folder."
        )
        lines.append("")
        lines.append(folder_summary)
        lines.append("")

        sidecar_name = f"{folder.name}.folder-ai-meta.md"
        sidecar_path = folder / sidecar_name
        sidecar_path.write_text("\n".join(lines), encoding="utf-8")

    # 3) Project-level metadata: generate and write project.ai-meta.md per root
    for root in roots_list:
        if not root.exists() or not root.is_dir():
            continue

        top_folders = sorted(
            {f for f in folder_summaries.keys() if f.parent == root},
            key=lambda p: p.name,
        )
        if not top_folders:
            continue

        lines_for_prompt: List[str] = []
        for f in top_folders:
            summary = folder_summaries.get(f, "")
            if not summary:
                continue
            lines_for_prompt.append(
                f"- Folder `{f.name}`\n{compress_summary(summary, gemini_model, 600)}"
            )

        if not lines_for_prompt:
            continue

        folder_summaries_block = "\n".join(lines_for_prompt)
        prompt = build_project_prompt(
            root.name,
            folder_summaries_block,
            analyze_overview=analyze_project_overview,
        )
        proj_summary = generate_text(gemini_model, prompt)
        if not proj_summary.strip():
            continue

        # Write project-level metadata file at root
        lines: List[str] = []
        lines.append(format_markdown_header(f"Project metadata: `{root.name}`", 1))
        lines.append("")
        lines.append(
            "This document contains a high-level AI-generated summary of the project, "
            "based on its top-level folders."
        )
        lines.append("")
        lines.append(proj_summary)
        lines.append("")

        project_meta_path = root / "project.ai-meta.md"
        project_meta_path.write_text("\n".join(lines), encoding="utf-8")
