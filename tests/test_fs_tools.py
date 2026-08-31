import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from fs_tools import (
    list_directory,
    read_file,
    read_pdf,
    search_files,
    capture_screenshot,
    ocr_image_base64,
    ocr_screen,
    _get_safe_path,
)

# ============================================================================
# Tests for _get_safe_path (path sandboxing security function)
# ============================================================================

class TestGetSafePath:

    def test_safe_path_inside_workspace(self, temp_workspace, monkeypatch):
        """Verify that valid paths inside the workspace are returned correctly."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        # create a subdirectory
        subdir = temp_workspace / "subdir"
        subdir.mkdir()
        
        result = _get_safe_path(str(subdir))
        assert result == subdir

    def test_safe_path_prevents_directory_traversal(self, temp_workspace, monkeypatch):
        """Verify that directory traversal attempts are blocked."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        # Attempt to traverse outside the workspace
        with pytest.raises(PermissionError):
            _get_safe_path("../../outside_workspace")

    def test_safe_path_blocks_absolute_paths(self, temp_workspace, monkeypatch):
        """Verify that absolute paths outside the workspace are blocked."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        with pytest.raises(PermissionError):
            _get_safe_path("C:\\Windows\\System32")
