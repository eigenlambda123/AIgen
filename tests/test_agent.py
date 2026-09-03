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


@patch("agent.call_ollama")
def test_build_tool_feedback_vision(mock_call_ollama):
    """Verify vision tools route images to the configured vision model."""
    mock_call_ollama.return_value = "A screenshot showing a terminal window."

    result = build_tool_feedback(
        "capture_screenshot",
        "base64-image-data",
        "Describe what is on my screen",
        {
            "planner": "planner-model",
            "text": "text-model",
            "vision": "vision-model",
        },
    )

    assert result == (
        "Tool output from 'capture_screenshot' "
        "(vision interpretation): A screenshot showing a terminal window."
    )

    mock_call_ollama.assert_called_once()

    call_args = mock_call_ollama.call_args
    messages = call_args.args[0]

    assert call_args.kwargs["model"] == "vision-model"
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "User request: Describe what is on my screen"
    assert messages[1]["images"] == ["base64-image-data"]


@patch("agent.call_ollama")
def test_build_tool_feedback_vision_error_does_not_call_model(mock_call_ollama):
    """Verify screenshot errors are returned without invoking the vision model."""
    result = build_tool_feedback(
        "capture_screenshot",
        "Error: Screenshot failed",
        "Describe what is on my screen",
        {
            "planner": "planner-model",
            "vision": "vision-model",
        },
    )

    assert result == (
        "Tool output from 'capture_screenshot': Error: Screenshot failed"
    )
    mock_call_ollama.assert_not_called()