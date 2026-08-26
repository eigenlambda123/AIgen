import requests
import json
import re


def call_ollama(messages: list, model: str = "qwen2.5:7b") -> str:
    """Call a local Ollama-compatible REST API and return assistant text content.

    Raises a RuntimeError when the HTTP call fails or the response is unexpected.
    """
    resp = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.0}
        },
        timeout=300
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


def extract_tool_call(raw_response: str):
    """Extracts a tool call JSON object from raw model text, or returns None."""
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
