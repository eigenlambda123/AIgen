import os
from pypdf import PdfReader
from pathlib import Path

# target base directory
BASE_DIR = Path("C:\\Users\\rmvilla\\Documents\\Books").resolve()
BASE_DIR.mkdir(exist_ok=True)

# helper for path sandboxing
def _get_safe_path(relative_path: str) -> Path:
    """Ensures the target path remains strictly inside BASE_DIR"""
    target_path = (BASE_DIR / relative_path).resolve()
    if not str(target_path).startswith(str(BASE_DIR)):
        raise PermissionError(f"Access denied: Path '{relative_path}' is outside workspace scope.")
    return target_path


# file system tools
def list_directory(relative_path: str = ".") -> str:
    """List files and folders inside a specified workplace directory."""
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
    except Exception as e:
        return f"Error listing directory: {str(e)}"


def read_file(relative_path: str) -> str:
    """Reads and returns the text content of a file within the workplace"""
    try:
        target_path = _get_safe_path(relative_path)
        if not target_path.exists():
            return f"Error: File '{relative_path}' does not exist."
        if not target_path.is_file():
            return f"Error: '{relative_path}' is a directory, not a file."

        # read text content safely
        with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # we set max characters to truncate large files to fit inside the model context window
        max_chars = 3000
        if len(content) > max_chars:
            return content[:max_chars] + f"\n\n[... Truncated: file exceeds {max_chars} characters ...]"
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


def read_pdf(relative_path: str) -> str:
    """Reads and returns the text content of a PDF file within the workplace"""
    try:
        target_path = _get_safe_path(relative_path)
        if not target_path.exists():
            return f"Error: File '{relative_path}' does not exist."
        if not target_path.is_file():
            return f"Error: '{relative_path}' is a directory, not a file."
        if target_path.suffix.lower() != ".pdf":
            return f"Error: '{relative_path}' is not a PDF file."

        # extract the pages and text of the PDF
        reader = PdfReader(str(target_path))
        pages_text = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages_text.append(f"\n--- Page {i} ---\n{text}")

        # after extracting, join and truncate if necessary
        content = "".join(pages_text).strip()
        if not content:
            return "No extractable text found (this PDF may be scanned/image-based)."

        # set maximum characters to truncate large PDFs to fit inside the model context window
        max_chars = 8000
        if len(content) > max_chars:
            return content[:max_chars] + f"\n\n[... Truncated: PDF exceeds {max_chars} characters ...]"
        return content
    except Exception as e:
        return f"Error reading PDF: {str(e)}"



def calculator(expression: str) -> str:
    """Evaluates a mathematical expression"""
    try:
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters"
        return str(eval(expression))
    except Exception as e:
        return f"Error: {str(e)}"


TOOL_REGISTRY = {
    'read_file': read_file,
    'list_directory': list_directory,
    'read_pdf': read_pdf,
    'calculator': calculator,
}
