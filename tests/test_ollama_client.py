import json
from unittest.mock import Mock, patch

import pytest

from ollama_client import call_ollama, extract_tool_call

class TestExtractTollCall:
    """Test cases for the extract_tool_call function in ollama_client.py."""

    def test_extract_plain_json(self):
        """Verify that extract_tool_call correctly extracts a JSON object from plain text."""
        response = '{"tool": "read_file", "args": {"relative_path": "test.txt"}}'

        result = extract_tool_call(response)

        assert result == {
            "tool": "read_file",
            "args": {"relative_path": "test.txt"}
        }

    
    def test_extract_fenced_json(self):
        """Verify that extract_tool_call correctly extracts a JSON object from fenced code blocks."""
        response = '```json\n{"tool": "list_directory", "args": {"relative_path": "."}}\n```'

        result = extract_tool_call(response)

        assert result == {
            "tool": "list_directory",
            "args": {"relative_path": "."}
        }

    def test_extract_json_embedded_in_text(self):
        """Verify that extract_tool_call correctly extracts a JSON object embedded in text."""
        response = (
            'I will inspect the file now: '
            '{"tool": "read_file", "args": {"relative_path": "test.txt"}}'
        )

        result = extract_tool_call(response)

        assert result == {
            "tool": "read_file",
            "args": {"relative_path": "test.txt"}
        }

    @pytest.mark.parametrize("response", [
        "This is not JSON at all.",
        '{"tool": }',
        "```json\n{invalid json}\n```",
    ])
    def test_invalid_json_returns_none(self, response):
        """Verify that extract_tool_call returns None for invalid JSON."""
        assert extract_tool_call(response) is None

    def test_json_array_returns_none(self):
        """Verify that extract_tool_call returns None for JSON arrays."""
        response = "[{'tool': 'read_file', 'args': {'relative_path': 'test.txt'}}]"
        assert extract_tool_call(response) is None