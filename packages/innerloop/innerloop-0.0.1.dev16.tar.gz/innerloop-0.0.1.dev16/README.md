# InnerLoop

[![PyPI](https://img.shields.io/pypi/v/innerloop.svg)](https://pypi.org/project/innerloop/)
[![Python](https://img.shields.io/pypi/pyversions/innerloop.svg)](https://pypi.org/project/innerloop/)
[![License](https://img.shields.io/github/license/botassembly/innerloop.svg)](LICENSE)

**Pure Python SDK for LLM agent loops.**

```bash
uv add innerloop   # or: pip install innerloop
```

## Why InnerLoop?

- **The agentic loop** — The loop is the fundamental building block. Tools, iteration, and structured output handled for you.
- **Pure Python** — No Node.js, no subprocess, no external service. Just `uv add` or `pip install` and go.
- **Auditable** — Minimal codebase, optional dependencies. Easy to review and trust.
- **Provider agnostic** — Same API across 20+ providers: Anthropic, OpenAI, Google, Azure, Mistral, xAI, Groq, Ollama, and more.
- **Built-in tools** — File system, bash, web, and todos.
- **Skills** — Claude Code-compatible prompt templates for domain expertise on demand.
- **Context overflow protection** — Protect your agent's context window with automatic tool truncation.
- **Security-conscious** — Workdir sandboxing for file tools. Bash allow/deny lists.
- **Structured output** — Pydantic, msgspec, dict, or JSON Schema with validation retries.
- **Sessions** — JSONL persistence. Human-readable. Resume anytime.
- **Observability** — stdlib logging with OpenTelemetry, Logfire, and Weave integration.
- **Flexible API** — Sync or async. Streaming or blocking. Agent loop or single-shot call.

## Quick Start

Create a loop with tools and let it run until the task is done.

```python
from innerloop import Loop, tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: 72°F"

loop = Loop(model="anthropic/claude-haiku-4-5", tools=[get_weather])
response = loop.run("What's the weather in NYC and LA?")
```

## Any Provider

Switch providers by changing the model string.

```python
Loop(model="anthropic/claude-haiku-4-5")
Loop(model="openai/gpt-5-mini")
Loop(model="google/gemini-2.5-flash")
Loop(model="azure/gpt-5-mini", base_url="https://example.openai.azure.com")
Loop(model="mistral/mistral-large-latest")
Loop(model="xai/grok-4-1-fast-reasoning")
Loop(model="deepseek/deepseek-reasoner")
Loop(model="groq/openai/gpt-oss-120b")
Loop(model="ollama/qwen3:8b")
Loop(model="openrouter/openai/gpt-oss-120b")
```

## Structured Output

Force the model to return validated data with automatic retries on failure.

```python
from pydantic import BaseModel
from innerloop import Loop

class City(BaseModel):
    name: str
    country: str
    population: int

loop = Loop(model="openai/gpt-5-mini")
response = loop.run("Tell me about Tokyo", response_format=City, validation_retries=3)
print(response.output)  # City(name='Tokyo', country='Japan', population=13929286)
```

## Sessions

Keep conversation history across multiple calls with automatic JSONL persistence.

```python
loop = Loop(model="anthropic/claude-haiku-4-5")

with loop.session() as ask:
    ask("Remember: the secret word is 'banana'")
    response = ask("What's the secret word?")

print(response.session_id)  # "20251207144323-SA9MWJ"
```

Resume anytime:

```python
loop = Loop(model="anthropic/claude-haiku-4-5", session="20251207144323-SA9MWJ")
```

## Streaming

Get tokens as they arrive for responsive interfaces.

```python
from innerloop import Loop, TextEvent

loop = Loop(model="anthropic/claude-haiku-4-5")

for event in loop.stream("Write a poem"):
    if isinstance(event, TextEvent):
        print(event.text, end="", flush=True)
```

## Async

Use async/await for non-blocking I/O.

```python
response = await loop.arun("Hello!")

async for event in loop.astream("Write a story"):
    ...
```

## Vision

Analyze images with vision-capable models.

```python
from innerloop import Loop

loop = Loop(model="anthropic/claude-3-5-haiku-latest")  # Or openai/gpt-4o-mini, google/gemini-2.0-flash
response = loop.run(
    prompt="What do you see in this image?",
    images=["https://example.com/photo.jpg"]
)
```

Works with local files, multiple images, structured output, and streaming. See [demos/vision.py](demos/vision.py) for a multi-provider example.

## Built-in Tools

Pre-built tools for file, web, and task operations with security sandboxing.

```python
from innerloop import Loop, FS_TOOLS, SAFE_FS_TOOLS, WEB_TOOLS

loop = Loop(
    model="anthropic/claude-haiku-4-5",
    tools=FS_TOOLS,
    workdir="./my-project",  # Sandboxed - can't escape this directory
)
```

## Truncation

Give the LLM control over what data it needs while protecting your context window.

```python
read("log.txt", head=0, tail=100)     # Last 100 lines
read("main.py", head=50, tail=50)     # First 50 + last 50
grep("TODO", head=20, tail=0)         # First 20 matches
```

Safety cap at 50KB / 2000 lines prevents runaway outputs.

## Bash Security

Control what shell commands the model can run.

```python
from innerloop import bash

safe_bash = bash(
    use={"make": "Run builds", "git": "Version control"},
    deny=["rm -rf", "sudo"],
)

strict_bash = bash(allow=["make", "git", "uv"])
```

## Skills

Load domain-specific prompt templates on demand—compatible with Claude Code skills.

```python
from pathlib import Path
from innerloop import Loop

loop = Loop(
    model="anthropic/claude-sonnet-4",
    skills_paths=[Path("~/.claude/skills"), Path(".claude/skills")],
)

response = loop.run("Review the code in src/ for quality issues")
# LLM invokes the code-reviewer skill if relevant
```

## One-Shot Calls

For simple extractions without tool iteration, `call` skips the loop.

```python
from pydantic import BaseModel
from innerloop import call

class Contact(BaseModel):
    name: str
    email: str

result = call(
    prompt="Extract: John Smith, john@acme.com",
    model="openai/gpt-5-mini",
    response_format=Contact,
)
print(result.output)  # Contact(name="John Smith", email="john@acme.com")
```

## Documentation

**Getting Started**
- [Getting Started](docs/getting-started.md) — Installation and first steps
- [Agent Loop](docs/agent-loop.md) — How the loop executes tools
- [Custom Tools](docs/custom-tools.md) — Build tools with the `@tool` decorator
- [Structured Output](docs/structured-output.md) — Pydantic, msgspec, and JSON Schema
- [One-Shot Calls](docs/call.md) — Single LLM calls without looping
- [Recipes](docs/recipes.md) — Common patterns and examples

**Sessions & Observability**
- [Sessions](docs/sessions.md) — Multi-turn conversations
- [Session Logging](docs/session-logging.md) — JSONL format, analysis with jq/hl/visidata
- [Observability](docs/observability.md) — Runtime logging with OpenTelemetry/Logfire/Weave

**Reference**
- [Streaming](docs/streaming.md) — Event types and real-time output
- [Vision](docs/vision.md) — Image input for vision models
- [Providers](docs/providers.md) — Supported providers and configuration
- [Built-in Tools](docs/builtin-tools.md) — Filesystem, web, and todo tools
- [Skills](docs/skills.md) — Claude Code-compatible prompt templates
- [Bash Tool](docs/bash.md) — Security modes and command filtering
- [Truncation](docs/truncation.md) — Preventing context overflow
- [Configuration](docs/configuration.md) — All configuration options
- [Security](docs/security.md) — Sandboxing and safety

**Contributing**
- [Contributing](docs/contributing.md) — Development setup and guidelines
- [Testing](docs/testing.md) — Running and writing tests

**Essays**
- [Building an Agentic Loop](docs/essays/building-an-agentic-loop.md) — What is an agent loop and how to build one

**Examples**
- [demos/](demos/) — Runnable examples for every feature
- [demos/README.py](demos/README.py) — Tests all code examples from this README (keep in sync)

## License

MIT
