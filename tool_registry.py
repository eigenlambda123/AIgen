from tools.file_tools import (
    list_directory,
    read_file,
    read_pdf,
    search_files,
)
from tools.ocr_tools import ocr_image_base64, ocr_screen
from tools.screen_tools import capture_screenshot
from config import TOOL_OUTPUT_LIMITS, TOOL_TIMEOUTS
from tool_framework import ToolDefinition

"""Central registry for the tools exposed to the agent and CLI."""

TOOL_DEFINITIONS = {
    "read_file": ToolDefinition(
        name="read_file",
        function=read_file,
        description="Read a text file inside the configured workspace.",
        capability="text",
        risk_level="low",
        timeout_seconds=TOOL_TIMEOUTS["read_file"],
        output_limit=TOOL_OUTPUT_LIMITS["read_file"],
        argument_types={"relative_path": str},
    ),
    "list_directory": ToolDefinition(
        name="list_directory",
        function=list_directory,
        description="List files and folders inside the configured workspace.",
        capability="text",
        risk_level="low",
        timeout_seconds=TOOL_TIMEOUTS["list_directory"],
        output_limit=TOOL_OUTPUT_LIMITS["list_directory"],
        argument_types={"relative_path": str},
    ),
    "read_pdf": ToolDefinition(
        name="read_pdf",
        function=read_pdf,
        description="Extract text from a PDF inside the configured workspace.",
        capability="text",
        risk_level="low",
        timeout_seconds=TOOL_TIMEOUTS["read_pdf"],
        output_limit=TOOL_OUTPUT_LIMITS["read_pdf"],
        argument_types={"relative_path": str},
    ),
    "search_files": ToolDefinition(
        name="search_files",
        function=search_files,
        description="Search workspace files for a text query.",
        capability="text",
        risk_level="low",
        timeout_seconds=TOOL_TIMEOUTS["search_files"],
        output_limit=TOOL_OUTPUT_LIMITS["search_files"],
        argument_types={
            "relative_path": str,
            "query": str,
        },
    ),
    "capture_screenshot": ToolDefinition(
        name="capture_screenshot",
        function=capture_screenshot,
        description="Capture a monitor or screen region as a JPEG image.",
        capability="vision",
        risk_level="medium",
        timeout_seconds=TOOL_TIMEOUTS["capture_screenshot"],
        output_limit=TOOL_OUTPUT_LIMITS["capture_screenshot"],
        argument_types=None,
    ),
    "ocr_image_base64": ToolDefinition(
        name="ocr_image_base64",
        function=ocr_image_base64,
        description="Extract text from a base64-encoded image using OCR.",
        capability="text",
        risk_level="medium",
        timeout_seconds=TOOL_TIMEOUTS["ocr_image_base64"],
        output_limit=TOOL_OUTPUT_LIMITS["ocr_image_base64"],
        argument_types={
            "b64_image": str,
            "lang": str,
        },
    ),
    "ocr_screen": ToolDefinition(
        name="ocr_screen",
        function=ocr_screen,
        description="Capture the screen and perform OCR.",
        capability="text",
        risk_level="medium",
        timeout_seconds=TOOL_TIMEOUTS["ocr_screen"],
        output_limit=TOOL_OUTPUT_LIMITS["ocr_screen"],
        argument_types=None,
    ),
}
