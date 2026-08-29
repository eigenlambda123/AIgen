import json
import inspect
import re
import logging
from typing import Any, Dict, Tuple

from fs_tools import TOOL_REGISTRY, TOOL_CAPABILITY
from ollama_client import call_ollama, extract_tool_call
from config import DEFAULT_MODELS, MAX_AGENT_ITERATIONS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# dynamic tool schema & system prompt construction
def generate_planner_prompt() -> str:
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


def generate_capability_prompt(capability: str) -> str:
    if capability == "vision":
        return "You are a vision assistant. Describe exactly what is visible in the provided image."
    return "You are a helpful assistant."

def get_tool_capability(tool_name: str) -> str:
    # return the capability associated with a tool, defaulting to "text" if not found
    return TOOL_CAPABILITY.get(tool_name, "text")

def get_model_for_capability(capability: str, models: Dict[str, str]) -> str:
    """Returns the model name for a given capability, defaulting to the planner model if not found."""
    if capability in models:
        return models[capability]
    return models.get("planner", DEFAULT_MODELS["planner"])

def build_tool_feedback(
    tool_name: str,
    tool_result: Any,
    user_query: str,
    models: Dict[str, str]
) -> str:
    """Builds a message for the model based on the tool's output and the user's query."""
    capability = get_tool_capability(tool_name)
    routed_model = get_model_for_capability(capability, models)
    logger.debug(f"[Model Router] tool={tool_name} capability={capability} model={routed_model}")

    if capability == "vision":
        if isinstance(tool_result, str) and tool_result.startswith("Error:"):
            return f"Tool output from '{tool_name}': {tool_result}"

        vision_messages = [
            {"role": "system", "content": generate_capability_prompt(capability)},
            {
                "role": "user",
                "content": f"User request: {user_query}",
                "images": [tool_result] # base64-encoded image string
            }
        ]
        vision_model = get_model_for_capability(capability, models)
        vision_summary = call_ollama(vision_messages, model=vision_model).strip()
        return f"Tool output from '{tool_name}' (vision interpretation): {vision_summary}"

    return f"Tool output from '{tool_name}': {tool_result}"

def validate_tool_action(action: dict) -> Tuple[bool, str, dict]:
    tool_name = action.get("tool")
    tool_args = action.get("args", {})

    if not isinstance(tool_name, str):
        return False, "", {}
    if tool_name not in TOOL_REGISTRY:
        return False, "", {}
    if not isinstance(tool_args, dict):
        return False, "", {}

    return True, tool_name, tool_args

def run_agent(user_query: str, model_overrides: Dict[str, str] = None) -> str:
    """Runs the agent loop to process a user query, invoking tools as needed."""
    models = dict(DEFAULT_MODELS)
    if model_overrides:
        models.update(model_overrides)

    planner_messages = [
        {"role": "system", "content": generate_planner_prompt()},
        {"role": "user", "content": user_query}
    ]

    logger.info(f"User Question: {user_query}")
    
   # ReAct loop (max 5 iterations to prevent infinite loops)
    for _ in range(MAX_AGENT_ITERATIONS):
        planner_model = get_model_for_capability("planner", models)
        logger.debug(f"[Model Router] planner -> {planner_model}")
        raw_response = call_ollama(planner_messages, model=planner_model).strip()
        planner_messages.append({"role": "assistant", "content": raw_response})

        # check if the model's response contains a tool call
        action = extract_tool_call(raw_response)
        if action is None:
            # if no tool call is detected, return the model's response directly
            return raw_response

        # Validate the tool action
        ok, tool_name, tool_args = validate_tool_action(action)
        if not ok:
            return raw_response

        logger.info(f"[Agent Execution] Invoking tool '{tool_name}' with args: {tool_args}")
        tool_result = TOOL_REGISTRY[tool_name](**tool_args)
        logger.debug(f"[Tool Output]\n{tool_result}")

        feedback = build_tool_feedback(
            tool_name,
            tool_result, 
            user_query, 
            models
        )

        logger.debug(f"[Tool Feedback]\n{feedback}")
        planner_messages.append({"role": "user", "content": feedback})

    return "Agent exceeded maximum iteration steps."

if __name__ == "__main__":
    # print("Response:\n", run_agent("hi!"))
    # print("Response:\n", run_agent("List the current files and directory, Look inside the School directory, there you will find another directory called environmental_science, inside that you will find a pdf file called ENVI_SCI-ASYNCHRONOUS-MODULE-1, I want you to read the contents of that pdf file and summarize it for me"))
    # print(run_agent("Look at my screen and tell me what you're seeing, after that, take a screenshot of my screen and then read the text from that screenshot and summarize it for me"))
    print(run_agent("Look in the current workspace for 'rm villa' and show me the files and line numbers where it appears."))