#local-slm

## Overview

`local-slm` is a local, self-contained implementation of a small language model (SLM) agent that can use a set of tools to perform tasks on the local machine. It is designed to run without requiring internet access, relying on locally available models and tools.

## Models

The default model configuration is defined in `agentv2.py`:

| Capability | Default model | Purpose |
| --- | --- | --- |
| Planner | `qwen2.5:7b` | Selects tools and composes the final response |
| Text | `qwen2.5:7b` | General text processing |
| Vision | `qwen2.5vl:7b` | Interprets captured images and screenshots |

Model names can be overridden when calling `run_agent`.

## Implemented tools

All tools operate through the registry in `fs_tools.py`.

| Tool | Capability | Description |
| --- | --- | --- |
| `list_directory` | Text | Lists files and folders under the configured workspace |
| `read_file` | Text | Reads text files, truncating output over 3,000 characters |
| `read_pdf` | Text | Extracts PDF page text, truncating output over 8,000 characters |
| `capture_screenshot` | Vision | Captures a monitor or selected screen region as base64 JPEG |
| `ocr_image_base64` | Text | Extracts text from a base64-encoded image using Tesseract |
| `ocr_screen` | Text | Captures the screen and performs OCR as a convenience operation |

The default filesystem workspace is (you can modify this in `fs_tools.py`):

```text
C:\Users\rmvilla\Documents\Books
```

Paths passed to filesystem tools are resolved and restricted to this workspace.

## Main modules

- `agent.py` — planner prompt, model routing, tool validation, and agent loop
- `fs_tools.py` — filesystem, PDF, screenshot, and OCR integrations
- `ollama_client.py` — local Ollama API calls and tool-call JSON extraction

## Dependencies

Install the packages listed in `requirements.txt`. The application expects:

- An Ollama-compatible server at `http://localhost:11434`
- The configured language models to be available locally
- Tesseract OCR installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`"

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed Mermaid diagrams covering
the end-to-end agent flow, model routing, registry, and each individual tool."

_This project is a work in progress and may be updated frequently. Please check the repository for the latest changes._
