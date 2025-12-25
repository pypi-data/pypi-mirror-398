try:
    import google.generativeai as genai
except ImportError as exc:  # pragma: no cover - dependency error
    raise RuntimeError(
        "google-generativeai package is required. "
        "Install via: pip install google-generativeai"
    ) from exc


def configure_gemini(api_key: str, model_name: str):
    """
    Configure the Gemini client and return a model handle.
    """
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


def build_gemini_prompt(
    relative_path: str,
    language: str,
    content: str,
    analyze_file_structure: bool = True,
) -> str:
    """
    Build a prompt for Gemini that asks for file-level metadata suitable
    for AI navigation of the repository.
    """
    language_hint = language if language else "plain text"

    base = (
        "You are an assistant helping to document a software repository.\n"
        "Given the contents of a single file, produce a concise markdown "
        "section that explains what the file does and what it contains.\n\n"
        "Requirements:\n"
        "- Begin with a short one-sentence summary of the file's purpose.\n"
        "- Then add a bullet list describing the main responsibilities, "
        "key functions/classes, and any notable patterns or dependencies.\n"
        "- Keep the description focused on behavior and intent rather than "
        "repeating code.\n"
        "- Avoid restating the entire code; only describe it.\n"
        "- Use markdown, but no top-level heading (no leading '#').\n\n"
    )

    if analyze_file_structure:
        extra = (
            "Additionally, when analyzing this file, explicitly identify and describe:\n"
            "- Public and important methods/functions: their purpose, inputs, outputs, "
            "and how the internal logic transforms inputs into outputs.\n"
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


def generate_metadata_for_file(
    model,
    relative_path: str,
    language: str,
    content: str,
    analyze_file_structure: bool = True,
) -> str:
    """
    Call Gemini to generate a metadata description for a single file.

    Returns the markdown snippet produced by the model.
    """
    prompt = build_gemini_prompt(
        relative_path=relative_path,
        language=language,
        content=content,
        analyze_file_structure=analyze_file_structure,
    )
    response = model.generate_content(prompt)
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
