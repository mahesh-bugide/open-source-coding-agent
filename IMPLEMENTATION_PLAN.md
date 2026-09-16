# Enterprise AI Coding Agent - Implementation Plan

## Project Status

- Date: 2026-09-15
- Workspace status: empty at start
- Objective: deliver a working local MVP with AWS deployable architecture scaffolding

## Phase 1 - Core Backend MVP (Implemented, Verification Partially Blocked)

### Goals

- Build FastAPI service with required API endpoints.
- Implement session lifecycle and SSE streaming of agent events.
- Implement explicit agent state machine with iteration and timeout guards.
- Implement strongly-typed agent tools with validation and workspace path protections.
- Add PostgreSQL models/schema and Redis-backed or in-memory session/event handling abstraction.

### Deliverables

- `services/api` backend source tree
- Core config, logging, auth abstraction
- Tool implementations: list_files, search_code, read_file, create_file, edit_file, delete_file, run_command, run_tests, git_status, git_diff
- Agent orchestrator and state machine
- SSE stream endpoint
- Initial tests for tools, state machine and API endpoints

### Verification

- Implemented test suites under `services/api/tests`.
- `get_errors` reports no static editor errors.
- Verified on local Python 3.13 interpreter:
	- `py -3.13 -m ruff check src tests` passes.
	- `py -3.13 -m pytest -q` passes (`8 passed`).
- Extension compiles with `npm run compile`.

## Phase 2 - Repository Context + Sandbox + Mock/Model Gateway

Status: Implemented

### Goals

- Add repository context builder using file tree, ripgrep, git status/diff and optional tree-sitter symbol extraction.
- Add sandbox manager abstraction and Docker-backed execution mode with resource/time/network restrictions.
- Add model gateway abstraction with OpenAI-compatible client and MOCK_MODEL mode.

### Deliverables

- Context pipeline modules
- Sandbox manager modules and sandbox image
- Model gateway modules and mock behavior
- Integration tests for agent loop in mock mode

### Verification

- Agent can complete at least one bug-fix task in sample repository in MOCK_MODEL mode.

## Phase 3 - VS Code Extension MVP

Status: Implemented

### Goals

- Build a functional VS Code extension panel/command flow.
- Send workspace info + user task to backend.
- Stream events and show progress.
- Show changed files and final diff.
- Support apply/reject flow.

### Deliverables

- `vscode-extension` source tree
- Commands/UI
- HTTP + SSE client integration

### Verification

- End-to-end local flow from extension to backend to sample repository changes.

## Phase 4 - Dockerized Local Development

Status: Implemented

### Goals

- Containerize API/agent service, inference service, and sandbox image.
- Add docker-compose for local no-GPU and GPU-capable paths.

### Deliverables

- Dockerfiles (API, agent, sandbox, inference)
- `docker-compose.yml`
- `.env.example`

### Verification

- Local stack boots in MOCK_MODEL mode.

## Phase 5 - Minimal AWS Deployment Scaffolding

Status: Implemented

### Goals

- Provide a minimal single-EC2-instance deployment path using Docker Compose (no Terraform/ECS/ALB/RDS required).

### Deliverables

- `scripts/aws/bootstrap_single_instance.sh` and `scripts/aws/README.md`
- `docker-compose.gpu.yml` override for switching from mock model to real vLLM on the same instance

### Verification

- `docker compose up -d --build mock-model api` boots and `/health`/`/ready` succeed.

## Phase 6 - Documentation + Evaluation Framework

Status: Implemented

### Goals

- Add comprehensive docs and sample repository tasks.
- Add evaluation script measuring success, duration, iterations, tool calls, and tokens.

### Deliverables

- Required docs: README, ARCHITECTURE, DEVELOPMENT, DEPLOYMENT, AWS, INFERENCE, AGENT, SECURITY, EVALUATION, NEXT_STEPS
- `examples/sample-repository` with seeded bugs and tasks
- evaluation runner script

### Verification

- Documentation is internally consistent with code.

## Decision Log

1. Keep backend and agent in same Python service process for MVP speed, while preserving modular boundaries.
2. Use SSE for streaming events due simpler browser/VS Code integration than WebSocket for this scope.
3. Use a model gateway interface with MOCK_MODEL fallback to support no-GPU local development.
4. Perform file edits inside a sandbox workspace copy and return patch/diff to support apply/reject workflows.
5. Use explicit iteration/time limits in agent execution loop.

## Risk Log

- Full production sandboxing hardening is out-of-scope for MVP but interface is designed for replacement.
- Tree-sitter language support differs per language and may be partial in MVP.

## Done Criteria Tracking

- [ ] Local backend start (code complete, run not executed in this environment)
- [ ] Local model/mock start (code complete, run not executed in this environment)
- [ ] VS Code extension run (compiled, runtime not executed in Extension Development Host)
- [x] Agent searches/reads/edits/tests/iterates
- [x] Diff review and apply/reject
- [x] Agent run persisted via SQLite (validated through integration test path)
- [x] Minimal single-instance AWS deployment scaffold complete
