try:
    import google.generativeai as genai
except ImportError as exc:  # pragma: no cover - dependency error
    raise RuntimeError(
        "google-generativeai package is required. "
        "Install via: pip install google-generativeai"
    ) from exc


def configure_gemini(api_key: str, model_name: str):
    """Configure the Gemini client and return a model handle."""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


def build_file_prompt(
    relative_path: str,
    language: str,
    content: str,
    analyze_structure: bool = True,
) -> str:
    """Prompt to describe a single file."""
    language_hint = language if language else "plain text"

    base = (
        "You are documenting a software repository.\n"
        "Given the contents of a single file, produce a concise markdown "
        "section that explains what the file does and what it contains.\n\n"
        "General requirements:\n"
        "- Begin with a short one-sentence summary of the file's purpose.\n"
        "- Then add a bullet list describing the main responsibilities, "
        "key functions/classes, and any notable patterns or dependencies.\n"
        "- Focus on behavior and intent rather than repeating code.\n"
        "- Use markdown, but no top-level heading (no leading '#').\n\n"
    )

    if analyze_structure:
        extra = (
            "When analyzing this file, explicitly identify and describe:\n"
            "- Public and important methods/functions: their purpose, inputs, outputs, "
            "and how internal logic transforms inputs into outputs.\n"
            "- Important variables, state, and configuration: what they control and how "
            "they influence behavior.\n"
            "- Sub-components (helpers, inner classes, hooks, custom widgets, etc.) and "
            "how they collaborate.\n"
            "- The file's interface: how other parts of the project are expected to call "
            "or use this file (public API surface, exported symbols).\n"
            "- Dependencies: focus on parameters and injected objects to infer which "
            "other modules, services, or external APIs this file depends on.\n"
            "- If the file implements a specific role (e.g. controller, repository, UI "
            "component, adapter), name that role explicitly.\n\n"
        )
    else:
        extra = ""

    tail = (
        f"File path: `{relative_path}`\n"
        f"Detected language: {language_hint}\n\n"
        "File contents:\n"
        "----------------\n"
        f"{content}\n"
        "----------------\n"
    )

    return base + extra + tail


def build_folder_prompt(
    folder_path: str,
    items_summary: str,
    analyze_components: bool = True,
) -> str:
    """Prompt to describe a folder based on summaries of its contents."""
    base = (
        "You are documenting a software repository.\n"
        "Given a list of files and subfolders in a folder and their summaries, "
        "produce a concise markdown section that explains what the folder is "
        "for and what it contains.\n\n"
        "General requirements:\n"
        "- Start with a short paragraph summarizing the folder's purpose.\n"
        "- Then provide a bullet list highlighting key files and subfolders "
        "and their roles.\n"
        "- Do not restate all details; keep it concise but informative.\n"
        "- Use markdown, but no top-level heading (no leading '#').\n\n"
    )

    if analyze_components:
        extra = (
            "Additionally, for this folder:\n"
            "- Identify micro-components and sub-components implemented here "
            "(e.g. UI widgets, services, repositories, helpers).\n"
            "- Describe any interfaces or contracts exposed from this folder "
            "to the rest of the project.\n"
            "- Provide an aggregate summary of functionality across all files: "
            "main responsibilities, workflows, and behaviors.\n"
            "- Mention key technologies, frameworks, protocols, and data formats used.\n"
            "- Describe external dependencies (databases, APIs, message brokers, "
            "third-party services, libraries) that code in this folder relies on.\n"
            "- If this folder mainly contains subfolders (a module with submodules), "
            "treat each subfolder as a logical component and summarize its role briefly.\n\n"
        )
    else:
        extra = ""

    tail = (
        f"Folder path: `{folder_path}`\n\n"
        "Content summaries:\n"
        "----------------\n"
        f"{items_summary}\n"
        "----------------\n"
    )

    return base + extra + tail


def build_project_prompt(
    project_name: str,
    folder_summaries: str,
    analyze_overview: bool = True,
) -> str:
    """Prompt to describe the whole project based on folder-level summaries."""
    base = (
        "You are documenting a software project.\n"
        "Given the summaries of its top-level folders and their roles, "
        "produce a concise markdown section that describes the overall "
        "purpose, architecture, and main components of the project.\n\n"
        "General requirements:\n"
        "- Start with a short high-level overview paragraph.\n"
        "- Then add a bullet list describing key subsystems or areas and "
        "how they fit together.\n"
        "- Keep it concise and suitable as a top-level project overview.\n"
        "- Use markdown, but no top-level heading (no leading '#').\n\n"
    )

    if analyze_overview:
        extra = (
            "Additionally, for this project-level overview:\n"
            "- Identify macro-components (domains/modules) based on the top-level folders.\n"
            "- Describe the main APIs (internal and external) exposed or consumed "
            "by the project.\n"
            "- Explain relationships and data flows between macro-components "
            "(which modules call which others, at a conceptual level).\n"
            "- Describe typical users or clients of the system and how they "
            "interact with the project (UI, APIs, integrations).\n"
            "- Outline key business processes and data flows implemented by the project.\n"
            "- From the structure and responsibilities, infer main use cases "
            "that this project supports and group them logically.\n\n"
        )
    else:
        extra = ""

    tail = (
        f"Project name: `{project_name}`\n\n"
        "Folder summaries:\n"
        "----------------\n"
        f"{folder_summaries}\n"
        "----------------\n"
    )

    return base + extra + tail


def build_compression_prompt(text: str, max_len_chars: int = 400) -> str:
    """Prompt to compress a text summary."""
    return (
        "You are a technical editor.\n"
        f"Compress the following technical summary into a concise version shorter than {max_len_chars} characters.\n"
        "Preserve the key responsibilities, main components, and architectural role.\n"
        "Do not lose critical information about what the code does.\n"
        "Return ONLY the compressed summary, no preamble.\n\n"
        "Original summary:\n"
        "----------------\n"
        f"{text}\n"
        "----------------\n"
    )


def generate_text(model, prompt: str) -> str:
    """Call Gemini with a prompt and return plain text."""
    response = model.generate_content(prompt)
    return _extract_text(response)


def generate_chat_response(chat, prompt: str) -> str:
    """Send a message to a chat session and return plain text."""
    response = chat.send_message(prompt)
    return _extract_text(response)


def _extract_text(response) -> str:
    if hasattr(response, "text") and response.text:
        return response.text
    try:
        candidates = getattr(response, "candidates", [])
        if candidates:
            content_obj = getattr(candidates[0], "content", None)
            if content_obj and hasattr(content_obj, "parts"):
                texts = [getattr(p, "text", "") for p in content_obj.parts]
                return "\n".join(t for t in texts if t)
    except Exception:
        pass
    return ""
