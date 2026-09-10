from dataclasses import dataclass
from typing import Any, Callable, Mapping
import inspect


ToolCallable = Callable[..., Any]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    function: ToolCallable
    description: str
    capability: str
    risk_level: str
    timeout_seconds: float
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