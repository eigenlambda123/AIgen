import base64
import io
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image
import pytesseract

from config import (
    DEFAULT_OCR_LANGUAGE,
    DEFAULT_SCREENSHOT_SCALE,
    TESSERACT_PATH,
    TRUNCATION_LIMITS,
)
from tools.screen_tools import capture_screenshot


pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def ocr_image_base64(
    b64_image: str,
    lang: str = "eng",
    max_chars: Optional[int] = None,
) -> str:
    """
    Extract text from a base64-encoded image using Tesseract OCR.
    
    Args:
        b64_image (str): A base64-encoded image.
        lang (str): The language to use for OCR.
        max_chars (int): The maximum number of characters to return.

    Returns:
        str: The extracted text or an error message.
    """
    if max_chars is None:
        max_chars = TRUNCATION_LIMITS["ocr"]
    if not isinstance(b64_image, str) or not b64_image:
        return "Error: b64_image must be a non-empty string."
    if not isinstance(max_chars, int) or isinstance(max_chars, bool):
        return "Error: max_chars must be an integer."
    if max_chars < 1:
        return "Error: max_chars must be greater than zero."

    try:
        image_bytes = base64.b64decode(b64_image)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_array = np.array(image)
        gray_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        text = pytesseract.image_to_string(Image.fromarray(gray_image), lang=lang).strip()
        if not text:
            return "No text detected in the image."
        if len(text) > max_chars:
            return (
                text[:max_chars]
                + f"\n\n[... Truncated: text exceeds {max_chars} characters ...]"
            )
        return text
    except Exception as error:
        return f"Error during OCR: {error}"


def ocr_screen(
    region: Optional[Tuple[int, int, int, int]] = None,
    scale: float = DEFAULT_SCREENSHOT_SCALE,
    lang: str = DEFAULT_OCR_LANGUAGE,
    max_chars: int = TRUNCATION_LIMITS["ocr"],
) -> str:
    """
    Capture the screen and perform OCR.
    
    Args:
        region (tuple): A tuple of (left, top, width, height) to capture a specific region.
        scale (float): The scale factor for the screenshot.
        lang (str): The language to use for OCR.
        max_chars (int): The maximum number of characters to return.

    Returns:
        str: The extracted text or an error message.
    """
    if max_chars < 1:
        return "Error: max_chars must be greater than zero."
    screenshot = capture_screenshot(region=region, scale=scale, as_base64=True)
    if isinstance(screenshot, str) and screenshot.startswith("Error:"):
        return screenshot
    return ocr_image_base64(screenshot, lang=lang, max_chars=max_chars)


__all__ = ["ocr_image_base64", "ocr_screen"]
