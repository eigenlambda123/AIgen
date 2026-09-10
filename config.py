import os
from pathlib import Path

# Workspace configuration
WORKSPACE_DIR = Path(
    os.getenv(
        "WORKSPACE_DIR",
        r"C:\Users\rmvilla\Documents\Books",
    )
).resolve()
WORKSPACE_DIR.mkdir(exist_ok=True, parents=True)

# Ollama API configuration
OLLAMA_API_URL = os.getenv(
    "OLLAMA_API_URL",
    "http://localhost:11434/api/chat",
)
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))

# Language model configuration
DEFAULT_MODELS = {
    "planner": os.getenv("MODEL_PLANNER", "qwen2.5:7b"),
    "text": os.getenv("MODEL_TEXT", "qwen2.5:7b"),
    "vision": os.getenv("MODEL_VISION", "qwen2.5vl:7b"),
}

# Agent configuration
MAX_AGENT_ITERATIONS = int(os.getenv("MAX_AGENT_ITERATIONS", "5"))
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "20"))

# Text truncation limits (characters)
TRUNCATION_LIMITS = {
    "file": int(os.getenv("TRUNCATE_FILE_CHARS", "3000")),
    "pdf": int(os.getenv("TRUNCATE_PDF_CHARS", "8000")),
    "ocr": int(os.getenv("TRUNCATE_OCR_CHARS", "4000")),
}

# Vision and OCR configuration
TESSERACT_PATH = os.getenv(
    "TESSERACT_PATH",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
)
DEFAULT_SCREENSHOT_SCALE = float(os.getenv("SCREENSHOT_SCALE", "0.6"))
DEFAULT_JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "80"))
DEFAULT_OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "eng")

# Tool execution limits
TOOL_TIMEOUTS = {
    "read_file": int(os.getenv("TIMEOUT_READ_FILE", "10")),
    "list_directory": int(os.getenv("TIMEOUT_LIST_DIRECTORY", "10")),
    "read_pdf": int(os.getenv("TIMEOUT_READ_PDF", "30")),
    "search_files": int(os.getenv("TIMEOUT_SEARCH_FILES", "30")),
    "capture_screenshot": int(os.getenv("TIMEOUT_CAPTURE_SCREENSHOT", "30")),
    "ocr_image_base64": int(os.getenv("TIMEOUT_OCR_IMAGE", "60")),
    "ocr_screen": int(os.getenv("TIMEOUT_OCR_SCREEN", "60")),
}

TOOL_OUTPUT_LIMITS = {
    "read_file": TRUNCATION_LIMITS["file"],
    "list_directory": int(os.getenv("TRUNCATE_DIRECTORY_CHARS", "8000")),
    "read_pdf": TRUNCATION_LIMITS["pdf"],
    "search_files": int(os.getenv("TRUNCATE_SEARCH_CHARS", "8000")),
    "capture_screenshot": 0,
    "ocr_image_base64": TRUNCATION_LIMITS["ocr"],
    "ocr_screen": TRUNCATION_LIMITS["ocr"],
}