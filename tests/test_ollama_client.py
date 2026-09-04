from unittest.mock import Mock, patch

import pytest

from config import OLLAMA_API_URL
from ollama_client import call_ollama, extract_tool_call


class TestExtractToolCall:
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

    @pytest.mark.parametrize(
        "response",
        [
            "This is not JSON at all.",
            '{"tool": }',
            "```json\n{invalid json}\n```",
        ],
    )
    def test_invalid_json_returns_none(self, response):
        """Verify that extract_tool_call returns None for invalid JSON."""
        assert extract_tool_call(response) is None

    def test_json_array_returns_none(self):
        """Verify that extract_tool_call returns None for JSON arrays."""
        response = "[{'tool': 'read_file', 'args': {'relative_path': 'test.txt'}}]"
        assert extract_tool_call(response) is None


class TestCallOllama:
    """Test cases for the call_ollama function in ollama_client.py."""

    @patch("ollama_client.requests.post")
    def test_call_ollama_success(self, mock_post):
        """Verify that call_ollama correctly processes a successful response from the Ollama API."""
        # Mock the response from requests.post.
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {
                "content": "This is a successful response."
            },
        }
        mock_post.return_value = mock_response

        # Call the function.
        messages = [{"role": "user", "content": "Hello Ollama!"}]
        result = call_ollama(
            messages=messages,
            model="test-model",
            timeout=15,
        )

        # Assert that the result is as expected.
        assert result == "This is a successful response."
        mock_post.assert_called_once_with(
            OLLAMA_API_URL,
            json={
                "model": "test-model",
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.0}
            },
            timeout=15
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("ollama_client.requests.post")
    def test_http_error_is_propagated(self, mock_post):
        """Verify that call_ollama raises an exception when the HTTP request fails."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = RuntimeError("HTTP error")
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="HTTP error"):
            call_ollama(
                messages=[{"role": "user", "content": "Hello Ollama!"}],
                model="test-model",
            )

    @patch("ollama_client.requests.post")
    def test_unexpected_response_format_raises_runtime_error(self, mock_post):
        """Verify that call_ollama raises a RuntimeError for unexpected response formats."""
        mock_response = Mock()
        mock_response.json.return_value = {"unexpected": "format"}
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="Unexpected response format from Ollama API"):
            call_ollama(
                messages=[{"role": "user", "content": "Hello Ollama!"}],
                model="test-model",
            )

    @patch("ollama_client.requests.post")
    def test_fallback_content_response_format(self, mock_post):
        """Verify that call_ollama returns fallback content when the response format is unexpected but contains a string."""
        mock_response = Mock()
        mock_response.json.return_value = {"content": "Fallback content"}
        mock_post.return_value = mock_response

        result = call_ollama(
            messages=[{"role": "user", "content": "Hello Ollama!"}],
            model="test-model",
        )
        assert result == "Fallback content"

    @patch("ollama_client.requests.post")
    def test_configurable_api_url_and_default_timeout(self, mock_post, monkeypatch):
        """Verify that call_ollama uses the configured API URL and default timeout."""
        monkeypatch.setattr("ollama_client.OLLAMA_API_URL", "http://mocked-ollama-api")
        monkeypatch.setattr("ollama_client.OLLAMA_TIMEOUT", 20)

        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {
                "content": "Response from mocked API."
            },
        }
        mock_post.return_value = mock_response

        result = call_ollama(
            messages=[{"role": "user", "content": "Hello Ollama!"}],
            model="test-model",
        )

        assert result == "Response from mocked API."
        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == "http://mocked-ollama-api"
        assert mock_post.call_args[1]["timeout"] == 20
