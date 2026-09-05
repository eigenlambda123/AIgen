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

## Installation and Quick Start

### 1. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Install and prepare Ollama

Install Ollama, then start the server:

```powershell
ollama serve
```

Pull the configured models:

```powershell
ollama pull qwen2.5:7b
ollama pull qwen2.5vl:7b
```

Tesseract OCR is required for OCR features. The default path is
`C:\Program Files\Tesseract-OCR\tesseract.exe`; it can be changed with
`TESSERACT_PATH`.

### 4. Start the interactive CLI

```powershell
python app.py
```

The CLI accepts natural-language requests and supports the commands below.

### Configuration via Environment Variables

All settings can be overridden without code changes:

```powershell
# Example: customize workspace and models
$env:WORKSPACE_DIR = "C:\My\Custom\Path"
$env:MODEL_PLANNER = "llama2:13b"
$env:OLLAMA_TIMEOUT = "600"
$env:TRUNCATE_FILE_CHARS = "5000"

python app.py
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed Mermaid diagrams covering the end-to-end agent flow, model routing, registry, and each individual tool.

## CLI Commands

Run the assistant with:

```powershell
python app.py
```

| Command | Description |
| --- | --- |
| `/help` | Show available commands |
| `/config` | Show active non-secret configuration |
| `/exit` | Exit the assistant |
| `/quit` | Alias for `/exit` |

Example:

```text
You: /config
You: List the files in my workspace
You: /exit
```

The CLI displays a `Working...` message while processing requests and reports
connection, timeout, HTTP, and unexpected-response errors separately.

## Troubleshooting

### Ollama connection error

Verify that Ollama is running:

```powershell
ollama serve
```

Then verify that the required models are installed:

```powershell
ollama list
```

If necessary, pull them again:

```powershell
ollama pull qwen2.5:7b
ollama pull qwen2.5vl:7b
```

### Request timeout

Increase the timeout for long-running requests:

```powershell
$env:OLLAMA_TIMEOUT = "600"
python app.py
```

### Custom workspace

Set a different sandboxed workspace:

```powershell
$env:WORKSPACE_DIR = "C:\My\Custom\Path"
python app.py
```

All filesystem operations remain restricted to the configured workspace.

### OCR errors

If Tesseract is installed in a non-default location:

```powershell
$env:TESSERACT_PATH = "C:\Path\To\tesseract.exe"
python app.py
```

## Running Tests

Run the complete test suite:

```powershell
.\venv\Scripts\python.exe -m pytest
```

Run tests with coverage:

```powershell
.\venv\Scripts\python.exe -m pytest `
  --cov=agent `
  --cov=fs_tools `
  --cov=ollama_client `
  --cov=app `
  --cov-report=term-missing
```

The project targets at least 80% overall test coverage.

_This project is a work in progress and may be updated frequently. Please check the repository for the latest changes._
