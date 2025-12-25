# llm-kit

**llm-kit** is a unified, async-first Python toolkit for interacting with multiple
Large Language Model (LLM) providers through a consistent, provider-agnostic API.

It supports:

- Multiple LLM providers (OpenAI, Gemini, Anthropic, etc.)
- Text and structured JSON generation
- Multimodal inputs (PDFs, images, text files)
- Clean abstractions and strong typing

---

## ✨ Core Ideas

### 1. Outputs are explicit

LLMs generate **outputs**, not OCR results.

`llm-kit` exposes two primary operations:

- `generate_text` → free-form text
- `generate_json` → structured, schema-driven output

### 2. Inputs can be text **and/or files**

Files (PDFs, images, etc.) are **first-class inputs** and can be passed directly
to generation methods.

OCR and file parsing are treated as **provider implementation details**.

---

## 📦 Installation

```bash
pip install llm-kit
```

Optional provider support (example):

```bash
pip install llm-kit[openai]
pip install llm-kit[gemini]
```

---

## 🚀 Quick Start

### Text-only generation

```python
text = await llm.generate_text(
    prompt="Explain what power factor is in simple terms"
)
```

---

### Text generation with a file (PDF, image, etc.)

```python
from llm_kit.core import LLMFile

pdf = LLMFile(
    content=pdf_bytes,
    mime_type="application/pdf",
    filename="bill.pdf",
)

summary = await llm.generate_text(
    prompt="Summarize this electricity bill",
    files=[pdf],
)
```

---

### Structured JSON extraction

```python
schema = {
    "type": "object",
    "properties": {
        "consumer_name": {"type": "string"},
        "bill_amount": {"type": "number"},
        "due_date": {"type": "string"},
    },
    "required": ["consumer_name", "bill_amount"],
}

data = await llm.generate_json(
    prompt="Extract billing details from this document",
    schema=schema,
    files=[pdf],
)
```

---

## 🧠 Design Philosophy

- **Provider-agnostic**: No OpenAI/Gemini specifics in the public API
- **Async-first**: Built for modern Python backends
- **Composable**: Easy to plug into pipelines (FastAPI, background jobs, ETL)
- **Explicit contracts**: Clear separation of inputs, outputs, and providers

---

## 🧩 Core Abstractions

### `BaseLLMClient`

All providers implement the same interface:

```python
class BaseLLMClient:
    async def generate_text(...)
    async def generate_json(...)
```

### `LLMFile`

A provider-agnostic representation of file inputs:

```python
from llm_kit.core import LLMFile
```

---

## 🔌 Providers

Each provider is implemented as an adapter that conforms to `BaseLLMClient`.

Supported / planned:

- OpenAI
- Gemini
- Anthropic
- Local / OSS models (future)

---

## 🛠 Development

### Install dependencies

```bash
poetry install
```

### Format & lint

```bash
poetry run ruff check . --fix
poetry run black .
```

### Run tests

```bash
poetry run pytest
```

---

## 📍 Status

🚧 **Under active development**

The public API is stabilizing. Expect rapid iteration until `v1.0`.

---

## 📄 License

MIT License
