import json
import requests
import os
from pathlib import Path 

# target base directory
BASE_DIR = Path("C:\\Users\\rmvilla\\Documents\\Books").resolve()
BASE_DIR.mkdir(exist_ok=True)

# helper for path sandboxing
def _get_safe_path(relative_path: str) -> Path:
    """Ensures the target path remains strictly inside BASE_DIR"""
    target_path = (BASE_DIR / relative_path).resolve()
    if not str(target_path).startswith(str(BASE_DIR)):
        raise PermissionError(f"Access denied: Path '{relative_path}' is outside workspace scope.")
    return target_path


# direct LLM call via ollama REST API
def call_ollama(messages: list, model: str =  "qwen2.5:7b") -> str:
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": model, "messages": messages, "stream": False}
    )
    # extract ai response
    return response.json()["message"]["content"] 

# tool definitions

# file system tools
def list_directory(relative_path: str = ".") -> str:
    """List files and folders inside a specified workplace directory."""
    try:
        target_path = _get_safe_path(relative_path)
        if not target_path.exists():
            return f"Error: Directory '{relative_path}' does not exist."
        if not target_path.is_dir():
            return f"Error: '{relative_path}' is a file, not a directory."

        items = os.listdir(target_path)
        if not items:
            return f"Directory '{relative_path}' is empty."

        formatted = []
        for item in items:
            full_item = target_path / item
            kind = "DIR " if full_item.is_dir() else "FILE"
            formatted.append(f"[{kind}] {item}")
        return "\n".join(formatted)
    except Exception as e:
        return f"Error listing directory: {str(e)}"


def calculator(expression: str) -> str:
    """"Evaluates a mathematical expression"""
    try:
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters"
        return str(eval(expression))
    except Exception as e:
        return f"Error: {str:e}"

TOOL_REGISTRY = {
   'calculator': calculator ,
   'list_directory': list_directory
}

# system prompt for specifying JSON tool-calling format
SYSTEM_PROMPT = """You are a helpful assistant with access to tools.

Available tools:
- calculator(expression: str): Evaluates a mathematical expression.

To use a tool, respond ONLY with a JSON object in this format:
{
    "tool": "tool_name",
    "args": {"arg_name": "value"}
}

If you do not need to use a  tool, respond with your final message as plain text.
"""

# custom ReAct agent execution loop
def run_agent(user_query: str):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]

    # ReAct loop (max 5 iterations to prevent infinite loops)
    for _ in range(5):
        raw_response = call_ollama(messages)
        messages.append({"role": "assistant", "content":raw_response})

        # check if model wants to call a tool via JSON
        try:
            action = json.loads(raw_response)
            tool_name = action.get("tool")
            tool_args = action.get("args", {})

            if tool_name in TOOL_REGISTRY:
                print(f"[Agent Execution] Invoking tool '{tool_name}' with args: {tool_args}")
                tool_result = TOOL_REGISTRY[tool_name](**tool_args)

                # append tool result back to model context
                messages.append({
                    "role": "user",
                    "content": f"Tool output from '{tool_name}': {tool_result}"
                })
                continue
        except (json.JSONDecodeError, TypeError):
            # model output was not JSON -> it's the final text answer
            return raw_response

    return "Agent exceeded maximum iteration steps."

# texts
print("Response:\n", run_agent("hi!"))
print("Response:\n", run_agent("what is 1+1?"))