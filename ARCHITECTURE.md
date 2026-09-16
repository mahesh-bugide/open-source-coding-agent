# Architecture

## Core components

- VS Code extension: captures user task and streams execution progress.
- API service (FastAPI): session management, streaming, cancellation, apply/reject.
- Agent orchestrator: explicit state machine and iterative execution loop.
- Tool runtime: typed, validated, logged repository and command tools.
- Repository context builder: bounded context via file tree + search + targeted reads.
- Model gateway: mock mode or OpenAI-compatible vLLM backend.
- Sandbox manager: local or Docker command execution with limits.
- Data layer: PostgreSQL persistence for sessions, runs, calls, usage.

## State machine

START -> UNDERSTAND -> PLAN -> SEARCH -> READ -> EDIT -> TEST

- PASS => COMPLETE
- FAIL => ANALYZE_FAILURE -> EDIT -> TEST

Stop conditions:

- complete
- tests pass
- max iterations reached
- timeout reached
- cancelled
- unrecoverable tool error

## Security boundaries

- vLLM kept private (no public ingress).
- Agent execution in sandbox copy of repository.
- Path traversal checks on file tools.
- Command timeout and resource controls.
- API key auth abstraction (OIDC extension point).

## Event protocol (SSE)

Events include:

- agent_started
- agent_message
- agent_thinking
- tool_started
- tool_completed
- file_changed
- test_started
- test_completed
- agent_completed
- agent_failed
