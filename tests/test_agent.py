from unittest.mock import patch

from agent import (
    get_tool_capability,
    get_model_for_capability,
    validate_tool_action,
    build_tool_feedback,
)   


def test_get_tool_capability_known_tool():
    """Verify that get_tool_capability returns the correct capability for a known tool."""
    assert get_tool_capability("read_file") == "text"

def test_get_tool_capability_unknown_tool_defaults_to_text():
    """Verify that get_tool_capability defaults to 'text' for an unknown tool."""
    assert get_tool_capability("unknown_tool") == "text"

def test_get_model_for_capability():
    """Verify that get_model_for_capability returns the correct model for known capabilities."""
    models = {
        "planner": "planner-model",
        "text": "text-model",
        "vision": "vision-model",
    }

    assert get_model_for_capability("planner", models) == "planner-model"
    assert get_model_for_capability("text", models) == "text-model"
    assert get_model_for_capability("vision", models) == "vision-model"

def test_get_model_for_unknown_capability_uses_planner():
    """Verify that get_model_for_capability defaults to the planner model for unknown capabilities."""
    models = {"planner": "planner-model"}
    assert get_model_for_capability("unknown_capability", models) == "planner-model"

def test_validate_tool_action_unknown_tool():
    """Verify that validate_tool_action correctly handles unknown tools."""
    valid, tool_name, tool_args = validate_tool_action({
        "tool": "does_not_exist",
        "args": {},
    })

    assert valid is False
    assert tool_name == ""
    assert tool_args == {}

def test_validate_tool_action_invalid_args():
    """Verify that validate_tool_action correctly handles invalid arguments."""
    valid, tool_name, tool_args = validate_tool_action({
        "tool": "read_file",
        "args": "not-a-dictionary",
    })

    assert valid is False

@patch("agent.call_ollama")
def test_build_tool_feedback_text(mock_call_ollama):
    """Verify that build_tool_feedback returns the correct feedback for a text tool."""
    result = build_tool_feedback(
        "read_file",
        "sample content",
        "Read the file",
        {"planner": "planner-model", "text": "text-model"},
    )

    assert result == "Tool output from 'read_file': sample content"
    mock_call_ollama.assert_not_called()