# Credits
This is code taken from the main assistant-ui repo. The assistant-stream library does not have its own documentation at the moment, and this is the gap this project tries to fill.

# assistant-stream

Typed streaming helpers for building assistant backends in Python.

This library focuses on one job: **turn an async "run" function into a structured stream of events** that can be encoded for different client transports (FastAPI/Starlette streaming responses, assistant-ui streams, or OpenAI-style SSE).

---

## Key features

- **Typed chunks** (`text-delta`, `tool-call-*`, `tool-result`, `update-state`, `source`, `data`, `error`)
- **FastAPI / Starlette friendly** response classes:
  - `DataStreamResponse` (assistant-ui newline protocol)
  - `AssistantTransportResponse` (SSE with JSON payloads)
  - `OpenAIStreamResponse` (minimal OpenAI-like chunk stream)
- **State syncing** via a convenient `controller.state` proxy that batches `update-state` operations
- **Tool call streaming** with incremental args and final results
- Optional **LangGraph** helpers (available when LangGraph/LangChain deps are installed)

---

## Installation

```bash
pip install assistant-stream
```

For local development:

```bash
pip install -e .
```

---

## Minimal usage (no web framework)

```python
from assistant_stream import create_run

async def run(controller):
    controller.append_text("Hello ")
    controller.append_text("world!")

stream = create_run(run)

async for chunk in stream:
    print(chunk)
```

---

## FastAPI example (assistant-ui Data Stream)

```python
from fastapi import FastAPI
from assistant_stream import create_run
from assistant_stream.serialization.data_stream import DataStreamResponse

app = FastAPI()

@app.get("/chat")
async def chat():
    async def run(controller):
        controller.append_text("Hello from FastAPI!")
    return DataStreamResponse(create_run(run))
```

---

## Tool call example

```python
import json
from assistant_stream import create_run

async def run(controller):
    tool = await controller.add_tool_call("search")
    tool.append_args_text(json.dumps({"q": "fastapi streaming"}))
    tool.set_response({"results": ["..."]})

stream = create_run(run)
```

---

## State syncing example

```python
from assistant_stream import create_run

async def run(controller):
    controller.state = {"draft": "", "messages": []}
    controller.state["draft"] += "Hello"
    controller.state["messages"].append({"role": "assistant", "content": "Hello"})

stream = create_run(run, state={})
```

---

## Documentation (Sphinx)

The repository includes modular Sphinx docs in `docs/`.

Build HTML docs:

```bash
cd docs
make html
# open docs/build/html/index.html
```

---

## Package layout

- `assistant_stream/create_run.py` – `create_run()` and `RunController`
- `assistant_stream/assistant_stream_chunk.py` – chunk types
- `assistant_stream/state_manager.py`, `assistant_stream/state_proxy.py` – state operations and proxy
- `assistant_stream/serialization/*` – response classes and encoders
- `assistant_stream/modules/*` – tool call + (optional) LangGraph helpers

---

## License

TBD
