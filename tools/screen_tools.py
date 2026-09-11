import base64
from typing import Optional, Tuple, Union

import cv2
import numpy as np
from mss import mss

from config import DEFAULT_JPEG_QUALITY, DEFAULT_SCREENSHOT_SCALE


def capture_screenshot(
    region: Optional[Tuple[int, int, int, int]] = None,
    scale: float = DEFAULT_SCREENSHOT_SCALE,
    as_base64: bool = True,
    jpg_quality: int = DEFAULT_JPEG_QUALITY,
) -> Union[str, bytes]:
    """
    Capture a monitor or screen region and encode it as JPEG.
    
    
    Args:
        region (tuple): A tuple of (left, top, width, height) to capture a specific region.
        scale (float): The scale factor for the screenshot.
        as_base64 (bool): Whether to return the image as a base64-encoded string.
        jpg_quality (int): The quality of the JPEG image.

    Returns:
        str or bytes: The captured screenshot as a base64-encoded string or bytes.
    """
    try:
        if not isinstance(scale, (int, float)) or isinstance(scale, bool):
            return "Error: scale must be a number."
        if not 0 < scale <= 1:
            return "Error: scale must be greater than 0 and no greater than 1."
        if not isinstance(jpg_quality, int) or isinstance(jpg_quality, bool):
            return "Error: jpg_quality must be an integer."
        if not 1 <= jpg_quality <= 100:
            return "Error: jpg_quality must be between 1 and 100."
        if region is not None:
            if (
                not isinstance(region, tuple)
                or len(region) != 4
                or not all(isinstance(value, int) for value in region)
            ):
                return (
                    "Error: region must be a tuple of four integers "
                    "(left, top, width, height)."
                )
            left, top, width, height = region
            if width <= 0 or height <= 0:
                return "Error: region width and height must be greater than zero."

        with mss() as sct:
            monitor = sct.monitors[1]
            if region:
                left, top, width, height = region
                monitor = {
                    "left": int(left),
                    "top": int(top),
                    "width": int(width),
                    "height": int(height),
                }

            sct_img = np.array(sct.grab(monitor))
            if not isinstance(sct_img, np.ndarray):
                img_bgr = np.asarray(sct_img)
            elif sct_img.ndim == 3 and sct_img.shape[2] == 4:
                img_bgr = cv2.cvtColor(sct_img, cv2.COLOR_BGRA2BGR)
            else:
                img_bgr = sct_img

            if (
                scale
                and scale < 1.0
                and hasattr(img_bgr, "shape")
                and len(getattr(img_bgr, "shape", ())) >= 2
            ):
                new_w = int(img_bgr.shape[1] * scale)
                new_h = int(img_bgr.shape[0] * scale)
                img_bgr = cv2.resize(
                    img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA
                )

            success, buffer = cv2.imencode(
                ".jpg",
                img_bgr,
                [int(cv2.IMWRITE_JPEG_QUALITY), int(jpg_quality)],
            )
            if not success:
                return "Error: Failed to encode image to JPEG."

            image_bytes = buffer.tobytes()
            if as_base64:
                return base64.b64encode(image_bytes).decode("ascii")
            return image_bytes
    except Exception as error:
        return f"Error: {error}"


__all__ = ["capture_screenshot"]
