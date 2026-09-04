import requests
import json
import re
from typing import Any, Optional

from config import OLLAMA_API_URL, OLLAMA_TIMEOUT


def call_ollama(
    messages: list[dict[str, Any]],
    model: str = "qwen2.5:7b",
    timeout: int | None = None,
) -> str:
    """Send a chat request to the local Ollama API.

    Args:
        messages: Chat messages containing ``role`` and ``content`` fields.
        model: Ollama model name to use.
        timeout: Request timeout in seconds. If None, the configured
            ``OLLAMA_TIMEOUT`` value is used.

    Returns:
        The assistant's text response.

    Raises:
        requests.RequestException: If the HTTP request fails.
        RuntimeError: If the response does not contain usable content.
    """
    if timeout is None:
        timeout = OLLAMA_TIMEOUT
    
    resp = requests.post(
        OLLAMA_API_URL,
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.0}
        },
        timeout=timeout
    )
    resp.raise_for_status()
    data = resp.json()
    # defensive extraction
    try:
        return data["message"]["content"]
    except Exception:
        # fall back to anything that looks like content
        if isinstance(data, dict):
            for k in ("content", "message", "text"):
                v = data.get(k)
                if isinstance(v, str):
                    return v
        raise RuntimeError("Unexpected response format from Ollama API")


def extract_tool_call(raw_response: str) -> Optional[dict[str, Any]]:
    """Extract a tool-call object from model-generated text.

    The response may be plain JSON, fenced JSON, or text containing an
    embedded JSON object.

    Args:
        raw_response: Raw text returned by the language model.

    Returns:
        A dictionary containing the extracted JSON object, or None when
        no valid JSON object can be found.
    """
    text = (raw_response or "").strip()
    if not text:
        return None

    # remove fenced code blocks (```json ... ```) to isolate potential JSON
    fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.DOTALL)
    candidates = [fenced, text]

    for candidate in candidates:
        # try parse whole candidate
        try:
            obj = json.loads(candidate)
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(obj, dict):
                return obj

        # try to find first {...} substring
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            inner = candidate[start:end + 1]
            try:
                obj = json.loads(inner)
            except json.JSONDecodeError:
                continue
            else:
                if isinstance(obj, dict):
                    return obj

    return None
