# System Architecture

This document describes the current `local-slm` architecture as implemented in
`agent.py`, `fs_tools.py`, `ollama_client.py`, and `config.py`.

## 1. End-to-end system flow

```mermaid
flowchart TD
    U[User input] --> A[run_agent]
    A --> M[Load config values<br/>DEFAULT_MODELS, MAX_AGENT_ITERATIONS]
    M --> P[Build planner messages]
    P --> L[Planner model<br/>qwen2.5:7b]
    L --> R[Raw assistant response]
    R --> X[extract_tool_call]

    X -->|No valid JSON object found| O[Return response to user]
    X -->|Tool JSON found| V[validate_tool_action]
    V -->|Invalid tool or args| O
    V -->|Valid action| T[Look up tool in TOOL_REGISTRY]
    T --> E[Execute selected tool]
    E --> F[build_tool_feedback]

    F --> C{Tool capability}
    C -->|text| FB[Format text tool output]
    C -->|vision| ER{Tool returned Error:?}
    ER -->|Yes| FB
    ER -->|No| VM[Vision model<br/>qwen2.5vl:7b]
    VM --> VS[Vision interpretation]
    VS --> FB

    FB --> B[Append tool feedback<br/>to planner messages]
    B --> I{Fewer than MAX_AGENT_ITERATIONS?}
    I -->|Yes| L
    I -->|No| Z[Return iteration-limit message]
    O --> UO[User-visible output]
    Z --> UO
```

### Runtime sequence

```mermaid
sequenceDiagram
    participant User
    participant Agent as agent.py
    participant Planner as Ollama planner
    participant Parser as extract_tool_call
    participant Registry as TOOL_REGISTRY
    participant Tool as Selected tool
    participant Vision as Ollama vision model

    User->>Agent: Submit request
    Agent->>Planner: System prompt + user request
    Planner-->>Agent: Plain answer or JSON tool action
    Agent->>Parser: Parse response
    alt No tool call
        Parser-->>Agent: None
        Agent-->>User: Return planner response
    else Valid tool call
        Parser-->>Agent: tool + args
        Agent->>Registry: Resolve tool
        Registry-->>Agent: Callable
        Agent->>Tool: Execute with args
        Tool-->>Agent: Result
        alt Vision-capable tool
            Agent->>Vision: Image + user request
            Vision-->>Agent: Image interpretation
        end
        Agent->>Planner: Tool output / interpretation
        Planner-->>Agent: Next action or final response
    end
```

The loop is capped at five iterations to prevent an indefinitely repeating
planner/tool cycle.

## 2. Model and routing architecture

```mermaid
flowchart LR
    Q[User request] --> PM[Planner routing]
    PM --> PModel[qwen2.5:7b<br/>planner]
    PModel --> Action[Selected tool action]
    Action --> Cap[get_tool_capability]
    Cap -->|text| TModel[qwen2.5:7b<br/>text/default]
    Cap -->|vision| VModel[qwen2.5vl:7b<br/>vision]
    TModel --> Feedback[Tool feedback]
    VModel --> Feedback
    Feedback --> PModel
```

`get_model_for_capability` uses the requested capability's configured model.
If no model is configured for that capability, it falls back to the planner
model.

## 3. Tool registry and shared boundaries

```mermaid
flowchart TD
    R[TOOL_REGISTRY] --> FS[list_directory]
    R --> RF[read_file]
    R --> RP[read_pdf]
    R --> SF[search_files]
    R --> CS[capture_screenshot]
    R --> OI[ocr_image_base64]
    R --> OS[ocr_screen]

    FS --> B[BASE_DIR]
    RF --> B
    RP --> B
    SF --> B
    B --> G[_get_safe_path]
    G --> S[Resolved path must remain<br/>inside workspace]

    CS --> Screen[Primary monitor or requested region]
    OI --> Image[Base64 image input]
    OS --> CS
    OS --> OI
```

The filesystem tools share this workspace boundary:

```text
C:\Users\rmvilla\Documents\Books
```

`_get_safe_path` resolves the requested path and rejects paths that resolve
outside `BASE_DIR`.

## 4. Individual tool architectures

### 4.1 `list_directory`

```mermaid
flowchart LR
    Input["relative_path = ."] --> Safe[_get_safe_path]
    Safe --> Exists{Path exists?}
    Exists -->|No| Err1[Return directory-not-found error]
    Exists -->|Yes| Dir{Is directory?}
    Dir -->|No| Err2[Return file-is-not-directory error]
    Dir -->|Yes| List[os.listdir]
    List --> Empty{Any entries?}
    Empty -->|No| EmptyOut[Return empty-directory message]
    Empty -->|Yes| Classify[Classify each entry as DIR or FILE]
    Classify --> Output[Return formatted listing]
```

### 4.2 `read_file`

```mermaid
flowchart LR
    Input[relative_path] --> Safe[_get_safe_path]
    Safe --> Checks{Exists and is file?}
    Checks -->|No| Error[Return descriptive error]
    Checks -->|Yes| Open["Open UTF-8<br/>errors=ignore"]
    Open --> Read[Read full text]
    Read --> Size{Length > 3,000 chars?}
    Size -->|No| Output[Return content]
    Size -->|Yes| Truncate[Keep first 3,000 chars]
    Truncate --> Notice[Append truncation notice]
    Notice --> Output
```

### 4.3 `read_pdf`

```mermaid
flowchart LR
    Input[relative_path] --> Safe[_get_safe_path]
    Safe --> Checks{Exists, is file,<br/>and .pdf suffix?}
    Checks -->|No| Error[Return descriptive error]
    Checks -->|Yes| Reader[Create PdfReader]
    Reader --> Pages[Iterate PDF pages]
    Pages --> Extract[Extract page text]
    Extract --> Label[Add page markers]
    Label --> Join[Join page text]
    Join --> Text{Extracted text present?}
    Text -->|No| Scan[Return scanned/image-based notice]
    Text -->|Yes| Size{Length > 8,000 chars?}
    Size -->|No| Output[Return extracted text]
    Size -->|Yes| Truncate[Keep first 8,000 chars]
    Truncate --> Notice[Append truncation notice]
    Notice --> Output
```

### 4.4 `search_files`

```mermaid
flowchart LR
    Input[relative_path, query,<br/>file_types, max_results] --> Safe[_get_safe_path]
    Safe --> CheckDir{Directory exists and is valid?}
    CheckDir -->|No| Error[Return directory error]
    CheckDir -->|Yes| Query{Query non-empty?}
    Query -->|No| Empty[Return empty-query error]
    Query -->|Yes| Walk[Recursively walk files]
    Walk --> Filter{Extension matches filter?}
    Filter -->|No| Skip[Skip file]
    Filter -->|Yes| Read[Read file content]
    Read --> Match{Query found?}
    Match -->|No| Skip
    Match -->|Yes| Lines[Collect matching line numbers]
    Lines --> Add[Append file path + lines]
    Add --> Limit{Reached max_results?}
    Limit -->|No| Walk
    Limit -->|Yes| Output[Return matching summary]
```

### 4.5 `capture_screenshot`

```mermaid
flowchart LR
    Input[region, scale, as_base64,<br/>jpg_quality] --> MSS[Open mss capture]
    MSS --> Monitor{Region supplied?}
    Monitor -->|No| Primary[Use primary monitor]
    Monitor -->|Yes| Custom[Build requested monitor rectangle]
    Primary --> Grab[Grab screen pixels]
    Custom --> Grab
    Grab --> Array[Convert MSS image to NumPy array]
    Array --> BGR[Convert BGRA to BGR with OpenCV]
    BGR --> Scale{0 < scale < 1?}
    Scale -->|Yes| Resize[Downscale with INTER_AREA]
    Scale -->|No| Encode[Encode as JPEG]
    Resize --> Encode
    Encode --> Success{Encoding succeeded?}
    Success -->|No| Error[Return encoding error]
    Success -->|Yes| Bytes[Get JPEG bytes]
    Bytes --> Format{as_base64?}
    Format -->|Yes| Base64[Base64-encode JPEG]
    Format -->|No| Raw[Return raw bytes]
```

### 4.6 `ocr_image_base64`

```mermaid
flowchart LR
    Input[Base64 image] --> Decode[base64.b64decode]
    Decode --> Open[Open bytes with PIL]
    Open --> RGB[Convert to RGB]
    RGB --> Array[Convert to NumPy array]
    Array --> Gray[Convert RGB to grayscale]
    Gray --> PIL[Create grayscale PIL image]
    PIL --> Tesseract[pytesseract.image_to_string<br/>using lang]
    Tesseract --> Strip[Strip whitespace]
    Strip --> Text{Text detected?}
    Text -->|No| None[Return no-text message]
    Text -->|Yes| Size{Length > max_chars?}
    Size -->|No| Output[Return OCR text]
    Size -->|Yes| Truncate[Keep max_chars]
    Truncate --> Notice[Append truncation notice]
    Notice --> Output
```

### 4.7 `ocr_screen`

```mermaid
flowchart LR
    Input[region, scale, lang,<br/>max_chars] --> Capture[capture_screenshot]
    Capture --> Error{Capture returned Error:?}
    Error -->|Yes| OutputError[Return capture error]
    Error -->|No| OCR[ocr_image_base64]
    OCR --> Output[Return recognized screen text]
```

## 5. External runtime dependencies

```mermaid
flowchart LR
    Agent[local-slm agent] -->|HTTP POST /api/chat| Ollama[Ollama-compatible server<br/>localhost:11434]
    Agent --> PyPDF[pypdf]
    Agent --> MSS[mss]
    Agent --> OpenCV[opencv-python]
    Agent --> Pillow[Pillow]
    Agent --> Tesseract[pytesseract]
    Tesseract --> Executable[Tesseract executable]
```

The Ollama server must provide the configured planner/text and vision models
(configurable via environment variables).

OCR additionally requires the Tesseract executable. The default location is:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

This can be overridden via the `TESSERACT_PATH` environment variable in `config.py`.

## 6. Configuration Management

All configuration values are centralized in `config.py` and can be overridden via environment variables:

```mermaid
flowchart TD
    Config[config.py<br/>Default values]
    Env[Environment Variables]
    
    Config -->|WORKSPACE_DIR| WS[Workspace path]
    Config -->|TESSERACT_PATH| TP[Tesseract path]
    Config -->|OLLAMA_API_URL| API[Ollama endpoint]
    Config -->|OLLAMA_TIMEOUT| TO[API timeout]
    Config -->|MODEL_PLANNER| MP[Planner model]
    Config -->|MODEL_TEXT| MT[Text model]
    Config -->|MODEL_VISION| MV[Vision model]
    Config -->|TRUNCATE_*_CHARS| TR[Truncation limits]
    Config -->|MAX_AGENT_ITERATIONS| MAI[Iteration limit]
    Config -->|SEARCH_MAX_RESULTS| SMR[Search limit]
    
    Env -->|Override| Config
    
    Config --> Agent[agent.py]
    Config --> Tools[fs_tools.py]
    Config --> Client[ollama_client.py]
```

All defaults are defined in `config.py` and can be customized via environment variables without code changes.
