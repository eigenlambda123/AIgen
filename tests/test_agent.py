from unittest.mock import patch

from agent import (
    TOOL_REGISTRY,
    build_tool_feedback,
    generate_capability_prompt,
    generate_planner_prompt,
    get_model_for_capability,
    get_tool_capability,
    run_agent,
    validate_tool_action,
)


class TestToolCapability:
    def test_known_tool(self):
        """Verify that known tools return their configured capability."""
        assert get_tool_capability("read_file") == "text"

    def test_unknown_tool_defaults_to_text(self):
        """Verify that unknown tools default to the text capability."""
        assert get_tool_capability("unknown_tool") == "text"


class TestModelRouting:
    def test_known_capabilities(self):
        """Verify that known capabilities return their configured models."""
        models = {
            "planner": "planner-model",
            "text": "text-model",
            "vision": "vision-model",
        }

        assert get_model_for_capability("planner", models) == "planner-model"
        assert get_model_for_capability("text", models) == "text-model"
        assert get_model_for_capability("vision", models) == "vision-model"

    def test_unknown_capability_uses_planner(self):
        """Verify that unknown capabilities default to the planner model."""
        models = {"planner": "planner-model"}

        assert get_model_for_capability("unknown_capability", models) == "planner-model"


class TestToolActionValidation:
    def test_unknown_tool(self):
        """Verify that unknown tools are rejected."""
        valid, tool_name, tool_args = validate_tool_action({
            "tool": "does_not_exist",
            "args": {},
        })

        assert valid is False
        assert tool_name == ""
        assert tool_args == {}

    def test_invalid_args(self):
        """Verify that non-dictionary arguments are rejected."""
        valid, _, _ = validate_tool_action({
            "tool": "read_file",
            "args": "not-a-dictionary",
        })

        assert valid is False

    def test_missing_tool(self):
        """Verify that missing tool names are rejected."""
        valid, tool_name, tool_args = validate_tool_action({
            "args": {},
        })

        assert valid is False
        assert tool_name == ""
        assert tool_args == {}

    def test_non_string_tool(self):
        """Verify that non-string tool names are rejected."""
        valid, tool_name, tool_args = validate_tool_action({
            "tool": 123,
            "args": {},
        })

        assert valid is False
        assert tool_name == ""
        assert tool_args == {}

    def test_missing_args_default_to_empty_dictionary(self):
        """Verify that missing arguments default to an empty dictionary."""
        valid, tool_name, tool_args = validate_tool_action({
            "tool": "read_file",
        })

        assert valid is True
        assert tool_name == "read_file"
        assert tool_args == {}


class TestToolFeedback:
    @patch("agent.call_ollama")
    def test_text_tool(self, mock_call_ollama):
        """Verify that text tool output is returned directly."""
        result = build_tool_feedback(
            "read_file",
            "sample content",
            "Read the file",
            {"planner": "planner-model", "text": "text-model"},
        )

        assert result == "Tool output from 'read_file': sample content"
        mock_call_ollama.assert_not_called()

    @patch("agent.call_ollama")
    def test_vision_tool(self, mock_call_ollama):
        """Verify that vision tools route images to the configured model."""
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
    def test_vision_error_does_not_call_model(self, mock_call_ollama):
        """Verify that screenshot errors bypass the vision model."""
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


class TestPromptGeneration:
    def test_planner_prompt_contains_registered_tools(self):
        """Verify that the planner prompt includes all registered tools."""
        prompt = generate_planner_prompt()

        for tool_name in TOOL_REGISTRY:
            assert tool_name in prompt

        assert "Available tools:" in prompt

    def test_vision_capability_prompt(self):
        """Verify that vision prompts include image-specific instructions."""
        result = generate_capability_prompt("vision")

        assert "vision assistant" in result
        assert "image" in result

    def test_non_vision_capability_prompt(self):
        """Verify that non-vision prompts use the general assistant prompt."""
        assert generate_capability_prompt("text") == "You are a helpful assistant."


class TestRunAgent:
    @patch("agent.call_ollama")
    def test_returns_direct_response(self, mock_call_ollama):
        """Verify that run_agent returns a direct model response."""
        mock_call_ollama.return_value = "This is the final answer."

        result = run_agent("What is the answer?")

        assert result == "This is the final answer."
        mock_call_ollama.assert_called_once()


    @patch("agent.call_ollama")
    def test_executes_text_tool_then_returns_final_response(self, mock_call_ollama):
        """Verify that run_agent executes a text tool and returns the final response."""
        mock_call_ollama.side_effect = [
            '{"tool": "read_file", "args": {"relative_path": "notes.txt"}}',
            "The file contains useful notes.",
        ]

        with patch.dict(
            "agent.TOOL_REGISTRY",
            {"read_file": lambda relative_path: "sample file contents"},
            clear=True,
        ):
            result = run_agent("Read notes.txt")

        assert result == "The file contains useful notes."
        assert mock_call_ollama.call_count == 2

        first_call = mock_call_ollama.call_args_list[0]
        second_call = mock_call_ollama.call_args_list[1]

        assert first_call.kwargs["model"] == "qwen2.5:7b"

        second_messages = second_call.args[0]
        assert any(
            message.get("content") == "Tool output from 'read_file': sample file contents"
            for message in second_messages
        )

    @patch("agent.call_ollama")
    def test_returns_raw_response_for_invalid_tool(self, mock_call_ollama):
        """Verify that run_agent returns the raw response for an invalid tool."""
        raw_response = '{"tool": "unknown_tool", "args": {}}'
        mock_call_ollama.return_value = raw_response

        result = run_agent("Use an unknown tool")

        assert result == raw_response
        mock_call_ollama.assert_called_once()

    @patch("agent.call_ollama")
    def test_stops_after_maximum_iterations(self, mock_call_ollama):
        """Verify that run_agent stops after exceeding maximum iterations."""
        tool_response = (
            '{"tool": "read_file", "args": {"relative_path": "notes.txt"}}'
        )
        mock_call_ollama.return_value = tool_response

        with patch.dict(
            "agent.TOOL_REGISTRY",
            {"read_file": lambda relative_path: "sample contents"},
            clear=True,
        ):
            result = run_agent("Keep reading the file")

        assert result == "Agent exceeded maximum iteration steps."

    @patch("agent.call_ollama")
    def test_model_overrides_are_used(self, mock_call_ollama):
        """Verify that model overrides are respected in run_agent."""
        mock_call_ollama.return_value = "Final response"

        run_agent(
            "Answer this",
            model_overrides={"planner": "custom-planner"},
        )

        assert mock_call_ollama.call_args.kwargs["model"] == "custom-planner"

    @patch("agent.call_ollama")
    def test_executes_vision_tool(self, mock_call_ollama):
        """Verify that run_agent executes a vision tool and returns the final response."""
        mock_call_ollama.side_effect = [
            '{"tool": "capture_screenshot", "args": {}}',
            "The screen shows a terminal.",
            "Final answer about the screen.",
        ]

        with patch.dict(
            "agent.TOOL_REGISTRY",
            {"capture_screenshot": lambda: "base64-image"},
            clear=True,
        ), patch.dict(
            "agent.TOOL_CAPABILITY",
            {"capture_screenshot": "vision"},
            clear=True,
        ):
            result = run_agent("Describe my screen")

        assert result == "Final answer about the screen."
        assert mock_call_ollama.call_count == 3
