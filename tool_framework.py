from dataclasses import dataclass
from typing import Any, Callable, Mapping
import inspect
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError


ToolCallable = Callable[..., Any]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolDefinition:
    """Describe a tool and the rules governing its execution."""

    name: str
    function: ToolCallable
    description: str
    capability: str
    risk_level: str
    timeout_seconds: float
    output_limit: int
    requires_confirmation: bool = False
    argument_types: Mapping[str, type] | None = None


def validate_tool_arguments(
    definition: ToolDefinition,
    arguments: dict[str, Any],
) -> tuple[bool, str]:
    """Validate arguments before invoking a tool.

    Args:
        definition: Metadata for the selected tool.
        arguments: Arguments supplied by the planner.

    Returns:
        A tuple containing whether the arguments are valid and an error
        message when they are invalid.
    """
    signature = inspect.signature(definition.function)
    parameters = signature.parameters

    for argument_name in arguments:
        if argument_name not in parameters:
            return (
                False,
                f"Unknown argument '{argument_name}' for tool "
                f"'{definition.name}'.",
            )

    for parameter_name, parameter in parameters.items():
        if parameter_name not in arguments:
            if parameter.default is inspect.Parameter.empty:
                return (
                    False,
                    f"Missing required argument '{parameter_name}' "
                    f"for tool '{definition.name}'.",
                )
            continue

        value = arguments[parameter_name]

        if (
            definition.argument_types is not None
            and parameter_name in definition.argument_types
        ):
            expected_type = definition.argument_types[parameter_name]

            if not isinstance(value, expected_type):
                return (
                    False,
                    f"Argument '{parameter_name}' for tool "
                    f"'{definition.name}' must be of type "
                    f"{expected_type.__name__}.",
                )

    return True, ""


def execute_tool(
    definition: ToolDefinition,
    arguments: dict[str, Any],
) -> Any:
    """Execute a tool with timeout, output limits, and audit logging.

    Args:
        definition: Metadata for the selected tool.
        arguments: Validated tool arguments.

    Returns:
        The tool result, possibly truncated when it is textual.

    Raises:
        TimeoutError: If the tool exceeds its configured timeout.
        Exception: If the tool itself raises an exception.
    """
    started_at = time.perf_counter()
    argument_summary = summarize_arguments(arguments)

    logger.info(
        "Tool started: name=%s risk=%s arguments=%s",
        definition.name,
        definition.risk_level,
        argument_summary,
    )

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(definition.function, **arguments)

            try:
                result = future.result(timeout=definition.timeout_seconds)
            except FutureTimeoutError as error:
                future.cancel()
                duration = time.perf_counter() - started_at

                logger.warning(
                    "Tool timed out: name=%s duration=%.3fs timeout=%.3fs",
                    definition.name,
                    duration,
                    definition.timeout_seconds,
                )

                raise TimeoutError(
                    f"Tool '{definition.name}' exceeded its "
                    f"{definition.timeout_seconds:g}-second timeout."
                ) from error

        if (
            isinstance(result, str)
            and definition.output_limit > 0
            and len(result) > definition.output_limit
        ):
            result = (
                result[:definition.output_limit]
                + f"\n\n[... Truncated: tool output exceeds "
                f"{definition.output_limit} characters ...]"
            )

        duration = time.perf_counter() - started_at

        logger.info(
            "Tool completed: name=%s duration=%.3fs result_type=%s",
            definition.name,
            duration,
            type(result).__name__,
        )

        return result

    except TimeoutError:
        raise
    except Exception:
        duration = time.perf_counter() - started_at

        logger.exception(
            "Tool failed: name=%s duration=%.3fs",
            definition.name,
            duration,
        )
        raise


def summarize_arguments(arguments: dict[str, Any]) -> dict[str, str]:
    """Return argument names and types without exposing argument values."""
    return {
        name: type(value).__name__
        for name, value in arguments.items()
    }

def requires_confirmation(definition: ToolDefinition) -> bool:
    """Return whether a tool requires user confirmation before execution."""
    return definition.requires_confirmation