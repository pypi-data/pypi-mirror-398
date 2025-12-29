# BifrostAI Python SDK

Official Python SDK for BifrostAPI — one API for various AI models (ChatGPT, Claude, Gemini).

## Get Your API Key

Subscribe to BifrostAPI on one of these platforms:
- [RapidAPI](https://rapidapi.com/bifrost/api/bifrostapi)

## Installation

```bash
pip install bifrost-ai
```

## Quick Start

```python
from bifrost import BifrostAI

client = BifrostAI(
    api_key="bfr-xxxxx",
    openai_key="sk-xxxxx",
    storage="memory"
)

response = client.chat("conv1", "Hello!", model="gpt-4")
print(response.content)
```

## Storage Options

The `storage` parameter is required when using methods with `conversation_id` (automatic history management).

| Method | Storage Required |
|--------|------------------|
| `client.chat()` | ✅ Yes |
| `client.chat_with_files()` | ✅ Yes |
| `client.chat_stream()` | ✅ Yes |
| `client.create_chat_completion()` | ❌ No |

**Storage backends:**

| Type | Format | Persistence |
|------|--------|-------------|
| Memory | `"memory"` | ❌ Lost on restart |
| File | `"file://path.json"` | ✅ Saved to disk |
| Redis | `"redis://localhost:6379"` | ✅ Saved to Redis |
| PostgreSQL | `"postgresql://user:pass@host/db"` | ✅ Saved to DB |

### High-level API (requires storage)
```python
client = BifrostAI(api_key="...", openai_key="...", storage="memory")

# SDK manages conversation history automatically
response = client.chat("conv1", "My name is Farid", model="gpt-4")
response = client.chat("conv1", "What is my name?", model="gpt-4")  # Remembers!
```

### Low-level API (no storage needed)
```python
client = BifrostAI(api_key="...", openai_key="...")

# You manage messages yourself
response = client.create_chat_completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Streaming

```python
for chunk in client.chat_stream("conv1", "Count 1 to 5", model="gpt-4"):
    print(chunk.content, end="", flush=True)
```

## File Upload

```python
# Simple - just pass file paths
response = client.chat_with_files(
    "conv1",
    "Summarize this document",
    files=["document.pdf"],  # Same folder
    model="gpt-4-turbo"
)
print(response.content)

# Full path
response = client.chat_with_files(
    "conv1",
    "What is in this file?",
    files=[r"C:\Users\You\Documents\report.pdf"],
    model="gpt-4-turbo"
)

# Multiple files
response = client.chat_with_files(
    "conv1",
    "Compare these documents",
    files=["doc1.pdf", "doc2.pdf"],
    model="gpt-4-turbo"
)
```

## License

MIT
