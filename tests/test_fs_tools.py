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
    """Test cases for the _get_safe_path function to ensure path security and sandboxing."""

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


# ============================================================================
# Tests for list_directory
# ============================================================================

class TestListDirectory:
    """Test cases for the list_directory tool to ensure correct directory listing behavior."""

    def test_list_directory_empty(self, temp_workspace, monkeypatch):
        """Test listing an empty directory."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        result = list_directory(".")
        assert "empty" in result.lower()

    def test_list_directory_with_files(self, temp_workspace, monkeypatch):
        """Verify that files and directories are listed correctly."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        # Create some files and directories
        (temp_workspace / "file1.txt").write_text("File 1 content")
        (temp_workspace / "file2.py").write_text("File 2 content")
        (temp_workspace / "subdir").mkdir()

        result = list_directory(".")
        assert "file1.txt" in result
        assert "file2.py" in result
        assert "subdir" in result
        assert "[FILE]" in result or "[DIR]" in result

    def test_list_directory_nonexistent(self, temp_workspace, monkeypatch):
        """Verify that listing a non-existent directory returns an error message."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        # Test listing a non-existent directory
        result = list_directory("nonexistent_dir")
        assert "Error" in result or "not found" in result

    def test_list_directory_file_path(self, temp_workspace, monkeypatch, sample_text_file):
        """Verify error when treating a file path as a directory."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        result = list_directory(f"{sample_text_file.name}")
        assert "Error" in result or "not a directory" in result


# ============================================================================
# Tests for read_file
# ============================================================================

class TestReadFile:

    def test_read_file_success(self, temp_workspace, monkeypatch, sample_text_file):
        """Verify that reading a valid text file returns its content, otherwise returns an error message.""" 
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        # read the sample text file
        result = read_file("sample.txt")
        assert "sample text file" in result
        assert "Error" not in result

    def test_read_file_truncation(self, temp_workspace, monkeypatch, sample_large_file):
        """Verify that reading a large file triggers truncation and returns a truncated message."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        result = read_file("large_file.txt")
        assert "Truncated" in result
        assert len(result) <= 5000 # should be truncated to 3000 + some extra text for truncation message

    def test_read_file_nonexistent(self, temp_workspace, monkeypatch):
        """Verify that reading a non-existent file returns an error."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        result = read_file("nonexistent.txt")
        assert "Error" in result or "not found" in result

    def test_read_file_directory_error(self, temp_workspace, monkeypatch):
        """Verify that attempting to read a directory returns an error."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        # create a directory instead of a file and test reading it
        (temp_workspace / "mydir").mkdir()
        result = read_file("mydir")
        assert "Error" in result or "not a file" in result