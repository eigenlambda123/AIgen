import json
import inspect
import re

from fs_tools import TOOL_REGISTRY
from ollama_client import call_ollama, extract_tool_call

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
    "args": {{"arg_name": "value"}}
}}

2. Never output text before or after the JSON when invoking a tool.
3. Once you receive the tool results, answer that user's question directly in plain text.
    """



def run_agent(user_query: str):
    """Runs the agent loop to process a user query, invoking tools as needed."""
    messages = [
        {"role": "system", "content": generate_system_prompt()},
        {"role": "user", "content": user_query}
    ]

    print(f"User Question: {user_query}\n")
    
   # ReAct loop (max 5 iterations to prevent infinite loops)
    for _ in range(5):
        raw_response = call_ollama(messages).strip()
        messages.append({"role": "assistant", "content": raw_response})

        # check if the model's response contains a tool call
        action = extract_tool_call(raw_response)
        if action is None:
            # if no tool call is detected, return the model's response directly
            return raw_response

        tool_name = action.get("tool")
        tool_args = action.get("args", {})

        if not isinstance(tool_name, str) or tool_name not in TOOL_REGISTRY:
            return raw_response

        if not isinstance(tool_args, dict):
            return raw_response

        print(f"[Agent Execution] Invoking tool '{tool_name}' with args: {tool_args}")
        tool_result = TOOL_REGISTRY[tool_name](**tool_args)
        print(f"[Tool Output]\n{tool_result}\n")

        messages.append({
            "role": "user",
            "content": f"Tool output from '{tool_name}': {tool_result}"
        })
        continue

    return "Agent exceeded maximum iteration steps."

if __name__ == "__main__":
    # print("-" * 50)
    # print("Response:\n", run_agent("hi!"))
    # print("-" * 50)
    # print("Response:\n", run_agent("What is 1+1? after answering, then check what files are in my workplace directory and tell me what the note about rm villa says"))
    # print("-" * 50)
    # print("Response:\n", run_agent("Look inside the School directory, there you will find another directory called environmental_science, inside that you will find a pdf file called ENVI_SCI-ASYNCHRONOUS-MODULE-1, I want you to read the contents of that pdf file and summarize it for me"))
    print(run_agent("Look at my screen and tell me what you're seeing"))