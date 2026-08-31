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
    """Test cases for the read_file tool to ensure correct file reading behavior."""

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


# ============================================================================
# Tests for read_pdf
# ============================================================================

class TestReadPDF:
    """Test cases for the read_pdf tool to ensure correct PDF reading behavior."""

    def test_read_pdf_nonexistent(self, temp_workspace, monkeypatch):
        """Verify that reading a non-existent PDF file returns an error."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        result = read_pdf("nonexistent.pdf")
        assert "Error" in result or "not found" in result

    def test_read_pdf_wrong_extension(self, temp_workspace, monkeypatch):
        """Verify that reading a file with a non-PDF extension returns an error."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        # create a text file instead of a PDF
        (temp_workspace / "not_a_pdf.txt").write_text("This is not a PDF.")
        result = read_pdf("not_a_pdf.txt")
        assert "Error" in result or "not a PDF" in result

    @patch("fs_tools.PdfReader")
    def test_read_pdf_success(self, mock_pdf_reader, temp_workspace, monkeypatch):
        """Verify successful PDF reading with mock PDFReader."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        # create a dummy PDF file
        (temp_workspace / "dummy.pdf").write_bytes(b"%PDF-1.4\n%Dummy PDF content")

        # mock the PDFReader to simulate reading a PDF file
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Mocked PDF content"
        mock_pdf_reader.return_value.pages = [mock_page]

        result = read_pdf("dummy.pdf")
        assert "Mocked PDF content" in result


# ============================================================================
# Tests for search_files
# ============================================================================

class TestSearchFiles:
    """Test cases for the search_files tool to ensure correct file searching behavior."""

    def test_search_files_empty_query(self, temp_workspace, monkeypatch):
        """Verify that searching with an empty query returns an error."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        result = search_files(".", query="")
        assert "Error" in result or "cannot be empty" in result

    def test_search_files_no_matches(self, temp_workspace, monkeypatch):
        """Verify 'No matches' when searching for a query that does not exist in any files.""" 
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        # create a file with content that does not match the search query
        (temp_workspace / "file1.txt").write_text("This is a test file.")
        result = search_files(".", query="nonexistent")
        assert "No matches" in result or "not found" in result

    def test_search_files_found(self, temp_workspace, monkeypatch):
        """Verify that searching for a query that exists in a file returns the correct match information."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        # create a file with content that matches the search query
        (temp_workspace / "file1.txt").write_text("This is a test file.")
        result = search_files(".", query="test")
        assert "file1.txt" in result
        assert "Line" in result or "1" in result  # should indicate line number of match

    def test_search_files_case_sensitive(self, temp_workspace, monkeypatch):
        """Verify that the search is case-insensitive by default."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        # create a file with mixed case content
        (temp_workspace / "file1.txt").write_text("This is a Test file.")
        result = search_files(".", query="test")
        assert "file1.txt" in result

    def test_search_files_case_sensitive_option(self, temp_workspace, monkeypatch):
        """Verify that the search respects the case_sensitive option when set to True."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        # create a file with mixed case content
        (temp_workspace / "file1.txt").write_text("This is a Test file.")
        result = search_files(".", query="test", case_sensitive=True)
        assert "No matches" in result or "not found" in result

    def test_search_files_filter_by_type(self, temp_workspace, monkeypatch):
        """Verify that the search can filter results by file type."""
        monkeypatch.setattr("fs_tools.BASE_DIR", temp_workspace)

        # create files with different extensions/types
        (temp_workspace / "file1.txt").write_text("This is a test file.")
        (temp_workspace / "file2.py").write_text("print('Hello')")
        result = search_files(".", query="test", file_types=".txt")
        assert "file1.txt" in result
        assert "file2.py" not in result

