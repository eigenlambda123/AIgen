import os
from pypdf import PdfReader
from pathlib import Path

import io
import base64
from mss import mss
import numpy as np
import cv2
from PIL import Image
import pytesseract

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


def capture_screenshot(region=None, scale=0.6, as_base64=True, jpg_quality=80):
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

TOOL_REGISTRY = {
    'read_file': read_file,
    'list_directory': list_directory,
    'read_pdf': read_pdf,
    'capture_screenshot': capture_screenshot,
    'calculator': calculator,
}

TOOL_CAPABILITY = {
    "read_file": "text",
    "list_directory": "text",
    "read_pdf": "text",
    "calculator": "text",
    "capture_screenshot": "vision",
}