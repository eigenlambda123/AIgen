import os
from pypdf import PdfReader
from pathlib import Path
from typing import Union, Optional, Tuple

import io
import base64
from mss import mss
import numpy as np
import cv2
from PIL import Image
import pytesseract

# Import configuration
from config import WORKSPACE_DIR, TESSERACT_PATH, TRUNCATION_LIMITS, SEARCH_MAX_RESULTS, DEFAULT_SCREENSHOT_SCALE, DEFAULT_JPEG_QUALITY, DEFAULT_OCR_LANGUAGE

# pytesseract configuration: use Tesseract path from config
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Alias BASE_DIR from config for backward compatibility
BASE_DIR = WORKSPACE_DIR

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
        max_chars = TRUNCATION_LIMITS["file"]
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
        max_chars = TRUNCATION_LIMITS["pdf"]
        if len(content) > max_chars:
            return content[:max_chars] + f"\n\n[... Truncated: PDF exceeds {max_chars} characters ...]"
        return content
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


def search_files(
    relative_path: str,
    query: str = "",
    file_types: Optional[Union[str, list[str]]] = None,
    max_results: int = SEARCH_MAX_RESULTS,
    case_sensitive: bool = False
) -> str:
    """
    Searches for a query string in files under a specified workplace directory.
    Args:
        relative_path: The workplace directory to search in.
        query: The string to search for in files.
        file_types: Optional list of file extensions to filter by (e.g., ['.txt', '.md']).
        max_results: Maximum number of matching files to return.
        case_sensitive: Whether the search should be case-sensitive.
    Returns:
        A string listing matching files and line numbers, or an error message.
    """
    try:
        if not query:
            return "Error: Search query cannot be empty."

        # get the safe path and validate it
        root = _get_safe_path(relative_path)
        if not root.exists():
            return f"Error: Directory '{relative_path}' does not exist."
        if not root.is_dir():
            return f"Error: '{relative_path}' is a file, not a directory."
        
        # set default file types if none provided
        if file_types is None:
            file_types = [".txt", ".md", ".py", ".json", ".csv", ".log"]
        elif isinstance(file_types, str):
            file_types = [file_types]

        normalized_types = {t.lower() for t in file_types if isinstance(t, str) and t}

        # walk the directory tree and search for matching files
        search_query = query if case_sensitive else query.lower()
        matches = []
        # use rglob to recursively find files matching the specified types
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            # check file type filter
            ext = file_path.suffix.lower()
            if ext not in normalized_types:
                continue

            try:
                # read the file content
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue  # skip files that can't be read

            # check if the search query is in the content
            haystack = content if case_sensitive else content.lower()
            if search_query not in haystack:
                continue

            # if we have a match, record the file path and line numbers
            lines = content.splitlines()
            hit_lines = []
            for i, line in enumerate(lines, start=1):
                line_text = line if case_sensitive else line.lower()
                if search_query in line_text:
                    hit_lines.append(str(i))  # store line numbers (1-based)

            # if we have hits, add to matches (records the matches we found)
            if hit_lines:
                relative_file_path = str(file_path.relative_to(root))
                matches.append(f"[{relative_file_path}] Lines: {', '.join(hit_lines)}")

        # if no matches found
        if not matches:
            return f"No matches found for query '{query}' in directory '{relative_path}'."


        return "\n".join(matches[:max_results])

    except Exception as e:
        return f"Error during search: {str(e)}"


# screenshot and OCR tools
def capture_screenshot(
    region: Optional[Tuple[int, int, int, int]] = None, 
    scale: float = DEFAULT_SCREENSHOT_SCALE, 
    as_base64: bool = True, 
    jpg_quality: int = DEFAULT_JPEG_QUALITY
) -> Union[str, bytes]:
    """
    Captures a screenshot of the specified region (or full screen if None) and returns it as a base64-encoded string.
   
    Args:
        region: Optional tuple (left, top, width, height). If None, capture full primary monitor.
        scale: Float in (0,1] to downscale the image for smaller size / faster OCR.
        as_base64: If True return a base64-encoded PNG/JPEG string; otherwise return raw bytes.
        jpg_quality: JPEG quality (1-100) used if returning JPEG bytes.

    Returns:
        On success: base64 string (if as_base64 True) or raw bytes of image.
        On error: string beginning with "Error:" describing the problem.
    """ 

    try:
        with mss() as sct:
            # choose monitor 1 (primary). If region provided, override monitor dict
            monitor = sct.monitors[1]
            if region:
                left, top, width, height = region
                monitor = {"left": int(left), "top": int(top), "width": int(width), "height": int(height)}
            
            # grab() returns an MSSImage; convert to numpy array (BGRA)
            sct_img = np.array(sct.grab(monitor))

            # convert BGRA to BGR (drop alpha)
            img_bgr = cv2.cvtColor(sct_img, cv2.COLOR_BGRA2BGR)

            # optionally downscale to reduce size/costs
            if scale and scale > 0 and scale < 1.0:
                new_w = int(img_bgr.shape[1] * scale)
                new_h = int(img_bgr.shape[0] * scale)
                img_bgr = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)

            # encode to JPEG
            success, buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), int(jpg_quality)])
            if not success:
                return "Error: Failed to encode image to JPEG."

            # return as base64 or raw bytes
            img_bytes = buf.tobytes()
            if as_base64:
                return base64.b64encode(img_bytes).decode("ascii")
            return img_bytes

    except Exception as e:
        return f"Error: {str(e)}"


def ocr_image_base64(b64_image: str, lang: str = "eng", max_chars: Optional[int] = None) -> str:
    """Extracts text from a base64-encoded image using Tesseract OCR."""
    if max_chars is None:
        max_chars = TRUNCATION_LIMITS["ocr"]
    try:
        # convert the base64 string back to image bytes
        image_bytes = base64.b64decode(b64_image)
        
        # open those bytes as an image
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
        # convert to grayscale for better OCR accuracy
        image_array = np.array(image)
        gray_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        ocr_image = Image.fromarray(gray_image)

        # ask tesseract to extract text from the image
        text = pytesseract.image_to_string(ocr_image, lang=lang)

        text = text.strip()

        if not text:
            return "No text detected in the image."

        if len(text) > max_chars:
            return text[:max_chars] + f"\n\n[... Truncated: text exceeds {max_chars} characters ...]"

        return text

    except Exception as e:
        return f"Error during OCR: {str(e)}"

def ocr_screen(
    region: Optional[Tuple[int, int, int, int]] = None, 
    scale: float = DEFAULT_SCREENSHOT_SCALE, 
    lang: str = DEFAULT_OCR_LANGUAGE, 
    max_chars: int = TRUNCATION_LIMITS["ocr"]
) -> str:
    """Captures a screenshot of the screenand performs OCR on it.
    This is a connector function that combines capture_screenshot and ocr_image for convenience."""
    screenshot = capture_screenshot(region=region, scale=scale, as_base64=True)

    if isinstance(screenshot, str) and screenshot.startswith("Error:"):
        return screenshot

    return ocr_image_base64(screenshot, lang=lang, max_chars=max_chars)


TOOL_REGISTRY = {
    'read_file': read_file,
    'list_directory': list_directory,
    'read_pdf': read_pdf,
    'search_files': search_files,
    'capture_screenshot': capture_screenshot,
    'ocr_image_base64': ocr_image_base64,
    'ocr_screen': ocr_screen,
        
}

TOOL_CAPABILITY = {
    "list_directory": "text",
    "read_file": "text",
    "read_pdf": "text",
    "search_files": "text",
    "capture_screenshot": "vision",
    "ocr_image_base64": "text",
    "ocr_screen": "text",
}