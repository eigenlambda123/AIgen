from dataclasses import dataclass
from typing import Any, Callable, Mapping


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