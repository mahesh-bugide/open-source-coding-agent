# Enterprise AI Coding Agent

Self-hosted MVP alternative to Copilot/Cursor for enterprise teams.

A VS Code extension sends a developer task to a backend agent service. The agent inspects the repository, plans changes, edits files in a sandbox copy, runs tests, iterates on failures, and returns changed files + diff for review/apply/reject.

## 1) What this project is

- FastAPI-based API + agent orchestrator.
- Typed tool runtime for repository operations.
- SSE streaming of agent progress/events to VS Code.
- Mock model mode for local development without GPU.
- vLLM inference service for open-source coding models (runs on the same EC2 instance as the API by default).
- Minimal single-instance AWS deployment path (no Terraform, no ECS/ALB/RDS required).

## 2) Architecture

High-level flow:

Developer -> VS Code Extension -> API service (FastAPI) -> Tooling + Sandbox + Model Gateway -> vLLM

API persists to SQLite by default; cache falls back to in-memory automatically if Redis isn't present.

See [ARCHITECTURE.md](ARCHITECTURE.md).

## 3) Local setup

Prerequisites:

- Python 3.11+ preferred for backend runtime
- Node.js 20+ for extension build
- Docker for compose flow
- Git, ripgrep

API local setup:

```bash
cd services/api
pip install -e .[dev]
```

Extension setup:

```bash
cd vscode-extension
npm install
npm run compile
```

## 4) Running the agent

Start API and mock model:

```powershell
./scripts/run_mock_model.ps1
./scripts/run_local_api.ps1 -WorkspaceRoot "C:\Dev\AI\coding-agent"
```

Then open VS Code command palette and run:

- `AI Coding Agent: Open`

In UI, enter task example:

- `Fix the authentication timeout issue and update the tests.`

## 5) Running vLLM

See [INFERENCE.md](INFERENCE.md) and [inference/README.md](inference/README.md).

## 6) Running tests

Backend tests:

```bash
cd services/api
pytest -q
ruff check src tests
```

Sample repo tests:

```bash
cd examples/sample-repository
pip install -e .[dev]
pytest -q
```

## 7) Deploying to AWS

Minimal single-instance path (default):

```bash
bash scripts/aws/bootstrap_single_instance.sh
```

See [AWS.md](AWS.md), [DEPLOYMENT.md](DEPLOYMENT.md), and [scripts/aws/README.md](scripts/aws/README.md).

## 8) VS Code extension setup

- Build extension from [vscode-extension](vscode-extension)
- Press `F5` in extension project to launch Extension Development Host
- Configure settings:
  - `enterpriseAgent.apiBaseUrl` (default `http://localhost:8080`)
  - `enterpriseAgent.apiKey` (default `dev-local-key`)

## Project layout

- [services/api](services/api): FastAPI API + orchestrator + tools
- [services/mock-model](services/mock-model): Local mock OpenAI-compatible endpoint
- [vscode-extension](vscode-extension): VS Code extension MVP
- [inference](inference): vLLM service container and startup scripts
- [scripts/aws](scripts/aws): minimal single-instance AWS bootstrap
- [examples/sample-repository](examples/sample-repository): Evaluation target repo
- [evaluation](evaluation): agent task evaluation runner
