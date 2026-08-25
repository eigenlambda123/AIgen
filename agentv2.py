import json
import requests
import os
import inspect
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


def read_file(relative_path: str) -> str:
    """Reads and returns the text content of a file within the workplace"""
    try:
        target_path = _get_safe_path(relative_path)
        if not target_path.exists():
            return f"Error: File '{relative_path}' does not exist."
        if not target_path.is_file():
            return f"Error: '{relative_path}' is a directory, not a file."

        # read text content safely
        with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # we set max characters to truncate large files to fit inside the model context window
        max_chars = 3000
        if len(content) > max_chars:
            return content[:max_chars] + f"\n\n[... Truncated: file exceeds {max_chars} characters ...]"
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


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
    'read_file': read_file,
   'list_directory': list_directory,
   'calculator': calculator ,
}

# dynamic tool schema & system prompt construction
def generate_system_prompt() -> str:
    tool_descriptions = []
    for name, func in TOOL_REGISTRY.items():
        doc = func.__doc__ or "No description available."
        # inspect object/function detail
        sig = inspect.signature(func)
        tool_descriptions.append(f"- {name}{sig}: {doc}")

    tools_formatted = "\n".join(tool_descriptions)

    return f"""You are an assistant that helps users manage and inspect local files.

Available tools:
{tools_formatted}

INSTRUCTIONS:
1. To use a tool, output ONLY a single valid JSON object matching this exact structure:
{{
    "tool": "tool_name",
    "args": {{"arg_name"": "value"}}
}}

2. Never output text before or after the JSON when involking a tool.
3. Once you recieve the tool results, answer that user's question directly in plain text.
    """

# Ollama REST API Client & ReAct Loop
def call_ollama(messages: list, model: str =  "qwen2.5:7b") -> str:
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": messages, 
            "stream": False,
            "options": {"temperature": 0.0}
        }
    )
    # extract ai response
    return response.json()["message"]["content"] 

def run_agent(user_query: str):
    messages = [
        {"role": "system", "content": generate_system_prompt()},
        {"role": "user", "content": user_query}
    ]

    print(f"User Question: {user_query}\n")

    # ReAct loop (max 5 iterations to prevent infinite loops)
    for _ in range(5):
        raw_response = call_ollama(messages).strip()
        messages.append({"role": "assistant", "content":raw_response})

        # check if model wants to call a tool via JSON
        try:
            action = json.loads(raw_response)
            tool_name = action.get("tool")
            tool_args = action.get("args", {})

            if tool_name in TOOL_REGISTRY:
                print(f"[Agent Execution] Invoking tool '{tool_name}' with args: {tool_args}")
                tool_result = TOOL_REGISTRY[tool_name](**tool_args)
                print(f"[Tool Output]\n{tool_result}\n")

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

# tests
print("-"*50)
print("Response:\n", run_agent("hi!"))
print("-"*50)
print("Response:\n", run_agent("what is 1+1?"))
print("-"*50)
print("Response:\n", run_agent("Check what files are in my workplace directory and tell me what the note about rm villa says"))