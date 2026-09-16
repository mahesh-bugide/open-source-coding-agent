# Enterprise AI Coding Agent API

FastAPI service containing the MVP agent orchestration runtime, typed tools, session APIs, and SSE event streaming.

## Run

```bash
pip install -e .[dev]
uvicorn enterprise_agent.main:app --reload --host 0.0.0.0 --port 8080
```

## Test

```bash
pytest
```
