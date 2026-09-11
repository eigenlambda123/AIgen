import pytest
import time

from tool_registry import TOOL_DEFINITIONS
from tool_framework import (
    ToolDefinition,
    execute_tool,
    requires_confirmation,
)


@pytest.mark.parametrize(
    "tool_name",
    list(TOOL_DEFINITIONS),
)
def test_registered_tool_has_complete_metadata(tool_name):
    """Verify that each registered tool has complete metadata and a callable function."""
    definition = TOOL_DEFINITIONS[tool_name]

    assert definition.name == tool_name
    assert callable(definition.function)
    assert definition.description
    assert definition.capability in {"text", "vision"}
    assert definition.risk_level in {"low", "medium", "high"}
    assert definition.timeout_seconds > 0
    assert definition.output_limit >= 0


@pytest.mark.parametrize(
    ("tool_name", "capability", "risk_level"),
    [
        ("read_file", "text", "low"),
        ("list_directory", "text", "low"),
        ("read_pdf", "text", "low"),
        ("search_files", "text", "low"),
        ("capture_screenshot", "vision", "medium"),
        ("ocr_image_base64", "text", "medium"),
        ("ocr_screen", "text", "medium"),
    ],
)
def test_tool_metadata_values(tool_name, capability, risk_level):
    """Verify that each registered tool has the expected capability and risk level."""
    definition = TOOL_DEFINITIONS[tool_name]

    assert definition.capability == capability
    assert definition.risk_level == risk_level


def test_execute_tool_logs_safe_completion(caplog):
    """Verify that execute_tool logs the start and completion of a tool execution, without logging sensitive argument values."""
    definition = ToolDefinition(
        name="read_file",
        function=lambda relative_path: "contents",
        description="Read a file.",
        capability="text",
        risk_level="low",
        timeout_seconds=5,
        output_limit=100,
        argument_types={"relative_path": str},
    )

    with caplog.at_level("INFO", logger="tool_framework"):
        result = execute_tool(
            definition,
            {"relative_path": "private-notes.txt"},
        )

    assert result == "contents"
    assert "Tool started" in caplog.text
    assert "Tool completed" in caplog.text
    assert "relative_path" in caplog.text
    assert "str" in caplog.text
    assert "private-notes.txt" not in caplog.text


def test_execute_tool_logs_failure(caplog):
    """Verify that execute_tool logs failure when a tool raises an exception."""
    def failing_tool():
        raise ValueError("tool failed")

    definition = ToolDefinition(
        name="failing_tool",
        function=failing_tool,
        description="Failing test tool.",
        capability="text",
        risk_level="low",
        timeout_seconds=5,
        output_limit=100,
    )

    with caplog.at_level("INFO", logger="tool_framework"):
        with pytest.raises(ValueError, match="tool failed"):
            execute_tool(definition, {})

    assert "Tool failed" in caplog.text
    assert "failing_tool" in caplog.text


def test_execute_tool_logs_timeout(caplog):
    """Verify that execute_tool logs timeout when a tool exceeds its timeout."""
    def slow_tool():
        time.sleep(0.2)
        return "finished"

    definition = ToolDefinition(
        name="slow_tool",
        function=slow_tool,
        description="Slow test tool.",
        capability="text",
        risk_level="low",
        timeout_seconds=0.01,
        output_limit=100,
    )

    with caplog.at_level("INFO", logger="tool_framework"):
        with pytest.raises(TimeoutError, match="exceeded"):
            execute_tool(definition, {})

    assert "Tool timed out" in caplog.text
    assert "slow_tool" in caplog.text


def test_read_file_declares_relative_path_argument():
    """Verify that the 'read_file' tool declares a 'relative_path' argument of type str."""
    definition = TOOL_DEFINITIONS["read_file"]

    assert definition.argument_types == {
        "relative_path": str,
    }


def test_capture_screenshot_has_no_simple_argument_schema():
    """Verify that the 'capture_screenshot' tool does not declare a simple argument schema."""
    definition = TOOL_DEFINITIONS["capture_screenshot"]

    assert definition.argument_types is None


def test_tool_definition_metadata_is_immutable():
    """Verify that the metadata of a ToolDefinition instance is immutable after creation."""
    definition = ToolDefinition(
        name="test_tool",
        function=lambda: "result",
        description="Test tool.",
        capability="text",
        risk_level="low",
        timeout_seconds=5,
        output_limit=100,
    )

    with pytest.raises(AttributeError):
        definition.risk_level = "high"