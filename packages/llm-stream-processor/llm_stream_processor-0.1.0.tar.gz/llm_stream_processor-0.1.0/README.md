# 🌊 LLM Stream Processor

<p align="center">
  <a href="https://pypi.org/project/llm-stream-processor/"><img src="https://img.shields.io/pypi/v/llm-stream-processor?color=blue&label=PyPI" alt="PyPI"></a>
  <a href="https://pypi.org/project/llm-stream-processor/"><img src="https://img.shields.io/pypi/pyversions/llm-stream-processor" alt="Python Versions"></a>
  <a href="https://github.com/DevOpRohan/llm_stream_processor/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
  <a href="https://github.com/DevOpRohan/llm_stream_processor"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
</p>

<p align="center">
  <strong>A callback-driven, prefix-safe, lazy LLM stream sanitization library.</strong>
</p>

<p align="center">
  Real-time filtering, redaction, and control of streaming LLM outputs with sub-microsecond overhead.
</p>

---

## ✨ Features

- 🔒 **Prefix-Safe Pattern Matching** — Uses Aho-Corasick automaton to ensure no partial sensitive content leaks before full match confirmation
- ⚡ **Ultra-Low Latency** — Target <5μs per-token overhead, designed for real-time streaming
- 🔄 **Sync & Async Support** — Works seamlessly with both synchronous and asynchronous LLM SDKs
- 🎯 **Flexible Actions** — PASS, DROP, REPLACE, HALT, or CONTINUE_DROP/PASS based on pattern matches
- 📊 **History Tracking** — Optional input/output/action history for debugging and analytics
- 🔌 **Runtime Updates** — Dynamically register/deregister patterns without restarting streams

## 📦 Installation

```bash
pip install llm-stream-processor
```

For development:

```bash
git clone https://github.com/DevOpRohan/llm_stream_processor.git
cd llm_stream_processor
pip install -e .
```

## 🚀 Quickstart

```python
from stream_processor import KeywordRegistry, llm_stream_processor, replace, halt

# Create a registry and register pattern callbacks
reg = KeywordRegistry()
reg.register("secret", lambda ctx: replace("[REDACTED]"))
reg.register("STOP", halt)  # Halt stream on this keyword

@llm_stream_processor(reg, yield_mode="token")
def generate_response():
    yield "The secret password is hidden. "
    yield "Do not STOP here."
    yield "This won't be seen."

# Consume the filtered stream
for token in generate_response():
    print(token, end="", flush=True)
# Output: The [REDACTED] password is hidden. Do not 
```

## 📖 API Reference

### Core Classes

| Class | Description |
|-------|-------------|
| `KeywordRegistry` | Register/deregister keywords and their callbacks, compiles to Aho-Corasick automaton |
| `StreamProcessor` | Low-level processor for character-by-character filtering |
| `ActionContext` | Context passed to callbacks with keyword, buffer, position, and history |
| `StreamHistory` | Tracks input/output/actions for debugging |

### Decorator

```python
@llm_stream_processor(registry, yield_mode='token', record_history=True)
```

| Parameter | Options | Description |
|-----------|---------|-------------|
| `registry` | KeywordRegistry | Registry with registered patterns |
| `yield_mode` | `'char'`, `'token'`, `'chunk:N'` | Output mode: per-character, per-token, or N-char chunks |
| `record_history` | `True`/`False` | Enable/disable history tracking |

### Action Helpers

| Function | Description |
|----------|-------------|
| `drop()` | Remove the matched keyword from output |
| `replace(text)` | Replace matched keyword with custom text |
| `halt()` | Immediately abort the stream |
| `passthrough()` | Leave matched keyword unchanged (no-op) |
| `continuous_drop()` | Start dropping all content until `continuous_pass` |
| `continuous_pass()` | Resume normal output after `continuous_drop` |

## 🎯 Use Cases

### PII Redaction

```python
import re
from stream_processor import KeywordRegistry, llm_stream_processor, replace

reg = KeywordRegistry()

# Redact email-like patterns (register common domains)
for domain in ["@gmail.com", "@yahoo.com", "@outlook.com"]:
    reg.register(domain, lambda ctx: replace("@[REDACTED]"))

# Redact SSN patterns
reg.register("SSN:", lambda ctx: replace("SSN: [REDACTED]"))
```

### Content Moderation (Drop Segments)

```python
from stream_processor import KeywordRegistry, llm_stream_processor, continuous_drop, continuous_pass

reg = KeywordRegistry()

# Drop internal "thinking" blocks
reg.register("<think>", continuous_drop)
reg.register("</think>", continuous_pass)

@llm_stream_processor(reg, yield_mode="token")
def llm_stream():
    yield "Hello! <think>internal reasoning here</think>Here's my response."

print("".join(llm_stream()))
# Output: Hello! </think>Here's my response.
```

### Async Streaming (OpenAI Pattern)

```python
import asyncio
from stream_processor import KeywordRegistry, llm_stream_processor, replace

reg = KeywordRegistry()
reg.register("API_KEY", lambda ctx: replace("[HIDDEN]"))

@llm_stream_processor(reg, yield_mode="token")
async def stream_chat():
    # Simulating async LLM response chunks
    chunks = ["Your ", "API_KEY ", "is safe."]
    for chunk in chunks:
        yield chunk
        await asyncio.sleep(0.1)

async def main():
    async for token in stream_chat():
        print(token, end="", flush=True)

asyncio.run(main())
```

## 🏗️ Architecture

```
Token Generator (sync/async)
         │
         ▼
@llm_stream_processor    ← Decorator API
         │
         ▼
   StreamProcessor       ← Character-level engine
   ┌──────────────┐
   │ Aho-Corasick │
   │  Automaton   │
   └──────────────┘
         │
         ▼
  Lazy Buffer + Callbacks
         │
         ▼
   Re-packer (char/token/chunk)
         │
         ▼
      Consumer
```

For detailed architecture, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 🧪 Development

```bash
# Install in editable mode
pip install -e .

# Run tests
python -m pytest tests/ -v

# Run the example
python -m examples.example
```

## 📚 Documentation

- **Problem Statement**: [docs/PROBLEM.md](docs/PROBLEM.md)
- **Architecture & Design**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Contributing Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code of Conduct
- Development setup
- Submitting pull requests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Aho-Corasick algorithm for efficient multi-pattern matching
- Inspired by the need for real-time LLM output sanitization in production systems
