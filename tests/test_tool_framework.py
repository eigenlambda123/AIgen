import pytest
import time

from tool_framework import ToolDefinition, execute_tool


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