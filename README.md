# ΛIgen

## Overview

`ΛIgen` is a local, self-contained implementation of a small language model (SLM) agent that can use a set of tools to perform tasks on the local machine. It is designed to run without requiring internet access, relying on locally available models and tools.

## Configuration

All configuration values are centralized in `config.py` and can be overridden via environment variables.

### Models

| Capability | Default model | Env Variable | Purpose |
| --- | --- | --- | --- |
| Planner | `qwen2.5:7b` | `MODEL_PLANNER` | Selects tools and composes the final response |
| Text | `qwen2.5:7b` | `MODEL_TEXT` | General text processing |
| Vision | `qwen2.5vl:7b` | `MODEL_VISION` | Interprets captured images and screenshots |

Model names can be overridden via environment variables or when calling `run_agent()`.

### Workspace & Paths

| Setting | Default | Env Variable |
| --- | --- | --- |
| Workspace directory | `C:\Users\rmvilla\Documents\Books` | `WORKSPACE_DIR` |
| Tesseract OCR path | `C:\Program Files\Tesseract-OCR\tesseract.exe` | `TESSERACT_PATH` |

### Text Processing

| Setting | Default | Env Variable |
| --- | --- | --- |
| File truncation limit | 3,000 characters | `TRUNCATE_FILE_CHARS` |
| PDF truncation limit | 8,000 characters | `TRUNCATE_PDF_CHARS` |
| OCR text limit | 4,000 characters | `TRUNCATE_OCR_CHARS` |

### API & Agent

| Setting | Default | Env Variable |
| --- | --- | --- |
| Ollama API URL | `http://localhost:11434/api/chat` | `OLLAMA_API_URL` |
| API timeout | 300 seconds | `OLLAMA_TIMEOUT` |
| Max agent iterations | 5 | `MAX_AGENT_ITERATIONS` |
| Search results limit | 20 | `SEARCH_MAX_RESULTS` |

## Implemented Tools

All tools operate through the registry in `fs_tools.py` and are fully type-hinted.

| Tool | Capability | Description |
| --- | --- | --- |
| `list_directory(path)` | Text | Lists files and folders under the configured workspace |
| `read_file(path)` | Text | Reads text files (configurable truncation via `TRUNCATE_FILE_CHARS`) |
| `read_pdf(path)` | Text | Extracts PDF page text (configurable truncation via `TRUNCATE_PDF_CHARS`) |
| `search_files(path, query, file_types, max_results)` | Text | Recursively searches files for a query with configurable result limits |
| `capture_screenshot(region, scale, as_base64, jpg_quality)` | Vision | Captures screen region as base64 JPEG with configurable quality and scale |
| `ocr_image_base64(image, lang, max_chars)` | Text | Extracts text from base64-encoded image using Tesseract OCR |
| `ocr_screen(region, scale, lang, max_chars)` | Text | Captures screen and performs OCR as a convenience operation |

**Workspace Sandboxing:** All file operations are restricted to the configured `WORKSPACE_DIR` for security. Paths are validated before access.

## Main Modules

- `config.py` — centralized configuration management with environment variable overrides
- `agent.py` — planner prompt, model routing, tool validation, and ReAct agent loop with logging
- `fs_tools.py` — filesystem, PDF, screenshot, and OCR integrations (fully type-hinted)
- `ollama_client.py` — local Ollama API calls with configurable timeout and tool-call JSON extraction

## Dependencies

Install the packages listed in `requirements.txt`. The application expects:

- An Ollama-compatible server running (default: `http://localhost:11434`, configurable via `OLLAMA_API_URL`)
- The configured language models available locally (configurable via `MODEL_*` env vars)
- Tesseract OCR installed (default: `C:\Program Files\Tesseract-OCR\tesseract.exe`, configurable via `TESSERACT_PATH`)

### Configuration via Environment Variables

All settings can be overridden without code changes:

```bash
# Example: customize workspace and models
$env:WORKSPACE_DIR = "C:\My\Custom\Path"
$env:MODEL_PLANNER = "llama2:13b"
$env:OLLAMA_TIMEOUT = "600"
$env:TRUNCATE_FILE_CHARS = "5000"

python agent.py
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed Mermaid diagrams covering the end-to-end agent flow, model routing, registry, and each individual tool.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama server (if not running)
ollama serve

# 3. Run a query
python -c "from agent import run_agent; print(run_agent('List files in current workspace'))"
```

_This project is a work in progress and may be updated frequently. Please check the repository for the latest changes._
