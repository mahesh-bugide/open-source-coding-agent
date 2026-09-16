# Enterprise AI Coding Agent

Self-hosted MVP alternative to Copilot/Cursor for enterprise teams.

A VS Code extension sends a developer task to a backend agent service. The agent inspects the repository, plans changes, edits files in a sandbox copy, runs tests, iterates on failures, and returns changed files + diff for review/apply/reject.

## 1) What this project is

- FastAPI-based API + agent orchestrator.
- Typed tool runtime for repository operations.
- SSE streaming of agent progress/events to VS Code.
- Mock model mode for local development without GPU.
- vLLM inference service scaffold for Qwen3-Coder on NVIDIA L40S.
- Terraform scaffold for AWS ECS/ALB/RDS/Redis/S3/GPU topology.

## 2) Architecture

High-level flow:

Developer -> VS Code Extension -> ALB -> API/Agent service -> Tooling + Sandbox + Model Gateway -> vLLM

Supporting services: PostgreSQL, Redis, S3, CloudWatch, Secrets Manager.

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

Terraform scaffold:

```bash
cd infrastructure/terraform
terraform init
terraform plan -var-file=environments/dev/terraform.tfvars
```

See [AWS.md](AWS.md) and [DEPLOYMENT.md](DEPLOYMENT.md).

For Launch Template based one-click EC2 deployments, see [scripts/aws/README.md](scripts/aws/README.md).

## 8) VS Code extension setup

- Build extension from [vscode-extension](vscode-extension)
- Press `F5` in extension project to launch Extension Development Host
- Configure settings:
  - `enterpriseAgent.apiBaseUrl` (default `http://localhost:8080`)
  - `enterpriseAgent.apiKey` (default `dev-local-key`)

## Project layout

- [services/api](services/api): FastAPI API + orchestrator + tools
- [services/agent](services/agent): Agent worker placeholder service container
- [services/mock-model](services/mock-model): Local mock OpenAI-compatible endpoint
- [vscode-extension](vscode-extension): VS Code extension MVP
- [inference](inference): vLLM service container and startup scripts
- [infrastructure/terraform](infrastructure/terraform): AWS IaC scaffold
- [examples/sample-repository](examples/sample-repository): Evaluation target repo
- [evaluation](evaluation): agent task evaluation runner
