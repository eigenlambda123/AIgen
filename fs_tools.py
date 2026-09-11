"""Compatibility imports for the domain-specific tool modules.

New code should import implementations from ``tools.file_tools``,
``tools.screen_tools``, or ``tools.ocr_tools``.
"""

from tools.file_tools import (
    BASE_DIR,
    _get_safe_path,
    list_directory,
    read_file,
    read_pdf,
    search_files,
)
from tools.ocr_tools import ocr_image_base64, ocr_screen
from tools.screen_tools import capture_screenshot


def __getattr__(name: str):
    """Provide a compatibility import for the old metadata registry path."""
    if name == "TOOL_DEFINITIONS":
        from tool_registry import TOOL_DEFINITIONS

        return TOOL_DEFINITIONS
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BASE_DIR",
    "_get_safe_path",
    "list_directory",
    "read_file",
    "read_pdf",
    "search_files",
    "capture_screenshot",
    "ocr_image_base64",
    "ocr_screen",
]
