# AIrab – Local Research Assistant

Privacy-first local RAG desktop assistant for PDF and text document analysis using PyQt6 and Qwen2.5.

## Overview

AIrab is a desktop research assistant that enables local document analysis with retrieval-augmented generation (RAG).  
Users can upload PDF or text files, ask questions across multiple documents, and receive answers from a locally hosted language model without sending data to external cloud services.

The project demonstrates practical LLM integration, local inference, desktop UI engineering, and privacy-oriented application design.

## Key Features

- Local inference using Qwen2.5 in GGUF format.
- Multi-document analysis across PDF and text files.
- Retrieval-augmented question answering.
- PyQt6 desktop interface.
- Encrypted local chat history.
- Offline workflow after initial model download.
- Optional speech-to-text support with Vosk.

## Why This Project Matters

Many AI assistants depend on cloud APIs, which can be limiting for private documents, offline use, or cost-sensitive workflows.  
AIrab explores a local-first alternative by combining a desktop application with a locally hosted LLM and lightweight document retrieval.

## Architecture

### UI Layer
- PyQt6 desktop application for chat, file upload, and interaction.

### LLM Layer
- `llama-cpp-python` server hosting Qwen2.5 locally.
- OpenAI-compatible client for application integration.

### Retrieval Layer
- Extracts text from uploaded PDF and text files.
- Builds lightweight context from document content for question answering.

### Storage / Security
- Chat history stored locally.
- Password-encrypted persistence.
- No cloud API dependency during normal use.

## Tech Stack

- **Language:** Python
- **UI:** PyQt6
- **LLM runtime:** llama.cpp / `llama-cpp-python`
- **Model:** Qwen2.5-0.5B-Instruct-GGUF
- **Document parsing:** PyMuPDF
- **Security:** cryptography, keyring
- **Speech-to-text:** Vosk

## Project Structure

```text
src/
├── main_window.py     # PyQt6 desktop UI
├── llm_client.py      # OpenAI-compatible local client
├── speech.py          # Optional Vosk speech-to-text
└── utils.py           # Encryption and local storage helpers

requirements.txt
README.md
```

## Setup

### Prerequisites
- Python 3.12+
- Approximately 400 MB disk space for the model

### 1. Clone the repository
```bash
git clone https://github.com/ali76-AFK/Local-Research-Assistant.git
cd Local-Research-Assistant
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Download the model
```bash
pip install huggingface-hub
huggingface-cli download Qwen/Qwen2.5-0.5B-Instruct-GGUF \
  Qwen2.5-0.5B-Instruct-Q4_K_M.gguf \
  --local-dir models
```

### 3. Start the local LLM server
```bash
python -m llama_cpp.server \
  --model models/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --n_ctx 2048 \
  --n_threads 4
```

### 4. Launch the GUI
```bash
python airab.py
```

## Performance

- Local CPU inference at roughly 60 to 65 tokens per second.
- Supports multi-document analysis across up to 3 uploaded files per chat.
- Designed for lightweight local usage on a standard development machine.

## Security

- Password-encrypted local chat history.
- Local-only inference over `localhost`.
- No cloud API dependency for document analysis after setup.
- Data directory excluded from Git tracking.

## Future Improvements

- Better retrieval chunking and ranking.
- More robust multi-document context handling.
- Richer citation and source-tracing support.
- Improved document preview and session management.
- Packaging for easier desktop distribution.

## License

MIT License.
