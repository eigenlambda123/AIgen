import logging
import os
from pathlib import Path
from typing import Optional, Union

from pypdf import PdfReader

from config import SEARCH_MAX_RESULTS, TRUNCATION_LIMITS, WORKSPACE_DIR


logger = logging.getLogger(__name__)
BASE_DIR = WORKSPACE_DIR


def _get_safe_path(relative_path: str) -> Path:
    """
    Ensure the target path remains inside the configured workspace.
    
    Args:
        relative_path (str): The path to the file or directory.

    Returns:
        Path: The resolved path.

    Raises:
        PermissionError: If the path is outside the workspace.
    """
    target_path = (BASE_DIR / relative_path).resolve()
    if not str(target_path).startswith(str(BASE_DIR)):
        raise PermissionError(
            f"Access denied: Path '{relative_path}' is outside workspace scope."
        )
    return target_path


def list_directory(relative_path: str = ".") -> str:
    """
    List files and folders inside the configured workspace.
    
    Args:
        relative_path (str): The path to the directory to list.

    Returns:
        str: The list of files and folders or an error message.
    """
    try:
        target_path = _get_safe_path(relative_path)
        if not target_path.exists():
            return f"Error: Directory '{relative_path}' does not exist."
        if not target_path.is_dir():
            return f"Error: '{relative_path}' is a file, not a directory."

        items = os.listdir(target_path)
        if not items:
            return f"Directory '{relative_path}' is empty."

        formatted = []
        for item in items:
            full_item = target_path / item
            kind = "DIR " if full_item.is_dir() else "FILE"
            formatted.append(f"[{kind}] {item}")
        return "\n".join(formatted)
    except Exception as error:
        return f"Error listing directory: {error}"


def read_file(relative_path: str) -> str:
    """
    Read a text file inside the configured workspace.
    
    Args:
        relative_path (str): The path to the text file.

    Returns:
        str: The file's content or an error message.
    """
    try:
        target_path = _get_safe_path(relative_path)
        if not target_path.exists():
            return f"Error: File '{relative_path}' does not exist."
        if not target_path.is_file():
            return f"Error: '{relative_path}' is a directory, not a file."

        with open(target_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()

        max_chars = TRUNCATION_LIMITS["file"]
        if len(content) > max_chars:
            return (
                content[:max_chars]
                + f"\n\n[... Truncated: file exceeds {max_chars} characters ...]"
            )
        return content
    except Exception as error:
        return f"Error reading file: {error}"


def read_pdf(relative_path: str) -> str:
    """
    Extract text from a PDF inside the configured workspace.
    
    Args:
        relative_path (str): The path to the PDF file.

    Returns:
        str: The extracted text or an error message.
    """
    try:
        target_path = _get_safe_path(relative_path)
        if not target_path.exists():
            return f"Error: File '{relative_path}' does not exist."
        if not target_path.is_file():
            return f"Error: '{relative_path}' is a directory, not a file."
        if target_path.suffix.lower() != ".pdf":
            return f"Error: '{relative_path}' is not a PDF file."

        reader = PdfReader(str(target_path))
        pages_text = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages_text.append(f"\n--- Page {page_number} ---\n{text}")

        content = "".join(pages_text).strip()
        if not content:
            return "No extractable text found (this PDF may be scanned/image-based)."

        max_chars = TRUNCATION_LIMITS["pdf"]
        if len(content) > max_chars:
            return (
                content[:max_chars]
                + f"\n\n[... Truncated: PDF exceeds {max_chars} characters ...]"
            )
        return content
    except Exception as error:
        return f"Error reading PDF: {error}"


def search_files(
    relative_path: str,
    query: str = "",
    file_types: Optional[Union[str, list[str]]] = None,
    max_results: int = SEARCH_MAX_RESULTS,
    case_sensitive: bool = False,
) -> str:
    """
    Search workspace files for a text query.

    Args:
        relative_path (str): The path to the directory to search.
        query (str): The text to search for.
        file_types (list[str]): The types of files to search.
        max_results (int): The maximum number of results to return.
        case_sensitive (bool): Whether the search should be case-sensitive.

    Returns:
        str: The search results or an error message.

    Raises:
        PermissionError: If the path is outside the workspace.
    """
    try:
        if not isinstance(relative_path, str):
            return "Error: relative_path must be a string."
        if not isinstance(query, str):
            return "Error: query must be a string."
        if not isinstance(max_results, int) or isinstance(max_results, bool):
            return "Error: max_results must be an integer."
        if max_results < 1:
            return "Error: max_results must be greater than zero."
        if not query:
            return "Error: Search query cannot be empty."

        root = _get_safe_path(relative_path)
        if not root.exists():
            return f"Error: Directory '{relative_path}' does not exist."
        if not root.is_dir():
            return f"Error: '{relative_path}' is a file, not a directory."

        if file_types is None:
            file_types = [".txt", ".md", ".py", ".json", ".csv", ".log"]
        elif isinstance(file_types, str):
            file_types = [file_types]

        normalized_types = {
            file_type.lower()
            for file_type in file_types
            if isinstance(file_type, str) and file_type
        }
        search_query = query if case_sensitive else query.lower()
        matches = []

        for file_path in root.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() not in normalized_types:
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                    content = file.read()
            except (PermissionError, OSError, UnicodeError) as error:
                logger.warning("Skipping unreadable file %s: %s", file_path, error)
                continue

            haystack = content if case_sensitive else content.lower()
            if search_query not in haystack:
                continue

            lines = content.splitlines()
            hit_lines = [
                str(line_number)
                for line_number, line in enumerate(lines, start=1)
                if search_query in (line if case_sensitive else line.lower())
            ]
            if hit_lines:
                relative_file_path = str(file_path.relative_to(root))
                matches.append(
                    f"[{relative_file_path}] Lines: {', '.join(hit_lines)}"
                )

        if not matches:
            return f"No matches found for query '{query}' in directory '{relative_path}'."
        return "\n".join(matches[:max_results])
    except Exception as error:
        return f"Error during search: {error}"


__all__ = [
    "_get_safe_path",
    "BASE_DIR",
    "list_directory",
    "read_file",
    "read_pdf",
    "search_files",
]
