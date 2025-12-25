# Codebase Analysis Utils

## Overview

`eic-codebase-analysis` is a Python library designed to assist in the analysis of code repositories and large codebases. It leverages advanced analysis techniques and AI to provide deep insights into project structure, components, functionality, and documentation.

## Installation

```bash
pip install eic-codebase-analysis
```

## Tools

This library provides a set of modular tools for different analysis tasks:

### 1. Repository Structure Extractor
*   **Purpose**: Extracts the directory and file structure of repositories without including file contents.
*   **Output**: Markdown tree structure.
*   **Usage**:
    ```bash
    python -m eic_codebase_analysis.repository_structure_extractor.main --root ./path/to/repo
    ```
*   **Documentation**: [Read more](src/eic_codebase_analysis/repository_structure_extractor/README.md)

### 2. Detailed Code Content Extractor
*   **Purpose**: Generates a single Markdown document containing both the directory structure and the full contents of files (in code blocks). Ideal for RAG contexts.
*   **Output**: Markdown with file contents.
*   **Usage**:
    ```bash
    python -m eic_codebase_analysis.detailed_code_content_extractor.main --root ./path/to/repo
    ```
*   **Documentation**: [Read more](src/eic_codebase_analysis/detailed_code_content_extractor/README.md)

### 3. Repository File Metadata Generator
*   **Purpose**: Uses AI (Gemini) to generate descriptive metadata for each file. Can output as sidecar files, a single aggregate file, or per-folder summaries.
*   **Output**: AI-generated summaries and documentation for files.
*   **Usage**:
    ```bash
    python -m eic_codebase_analysis.repository_file_metadata_generator.main --root ./path/to/repo --model gemini-1.5-pro
    ```
*   **Documentation**: [Read more](src/eic_codebase_analysis/repository_file_metadata_generator/README.md)

### 4. Hierarchical Project Metadata Generator
*   **Purpose**: Generates AI metadata at three levels: File (sidecar), Folder (summary of contents), and Project (high-level overview).
*   **Output**: Hierarchical Markdown documentation (`.ai-meta.md`, `.folder-ai-meta.md`, `project.ai-meta.md`).
*   **Usage**:
    ```bash
    python -m eic_codebase_analysis.hierarchical_project_metadata_generator.main --root ./path/to/repo --model gemini-1.5-pro
    ```
*   **Documentation**: [Read more](src/eic_codebase_analysis/hierarchical_project_metadata_generator/README.md)

## Integration

These tools are designed to be part of a broader ecosystem of AI-driven development tools. They can be integrated with existing libraries for Retrieval Augmented Generation (RAG) and dataset preparation.

## Requirements

*   Python 3.x
*   `google-generativeai` (for AI-powered tools)
