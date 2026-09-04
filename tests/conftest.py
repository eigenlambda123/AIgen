import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_workspace():
    """Create a temporary directory for testing purposes."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_text_file(temp_workspace):
    """Create a sample text file in the temporary workspace."""
    file_path = temp_workspace / "sample.txt"
    content = "This is a sample text file for testing."
    file_path.write_text(content)
    yield file_path


@pytest.fixture
def sample_large_file(temp_workspace):
    """Create a sample large text file in the temporary workspace."""
    file_path = temp_workspace / "large_file.txt"
    # Create a file larger than the default truncation limit.
    content = "x" * 10000
    file_path.write_text(content)
    yield file_path


@pytest.fixture
def mock_ollama_response():
    """Mock the response from the Ollama API to simulate API calls."""
    return {
        "message": {
            "role": "assistant",
            "content": '{"tool": "list_directory", "args": {"relative_path": "."}}'
        }
    }


@pytest.fixture
def mock_config(monkeypatch):
    """Mock the configuration values for testing purposes."""
    config_values = {
        "WORKSPACE_DIR": Path(tempfile.gettempdir()) / "test_workspace",
        "TESSERACT_PATH": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        "OLLAMA_TIMEOUT": 30,
        "TRUNCATION_LIMITS": {"file": 3000, "pdf": 8000, "ocr": 4000},
    }

    # Mock the config module values.
    for key, value in config_values.items():
        monkeypatch.setattr("config." + key, value)

    return config_values
