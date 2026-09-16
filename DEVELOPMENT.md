# Development

## Backend

```bash
cd services/api
pip install -e .[dev]
uvicorn enterprise_agent.main:app --reload --host 0.0.0.0 --port 8080
```

Environment variables are defined in [services/api/.env.example](services/api/.env.example).

## Extension

```bash
cd vscode-extension
npm install
npm run compile
```

Run extension host with `F5` in VS Code while the extension folder is open.

## Mock model

```bash
cd services/mock-model
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8001
```

## Docker local stack

```bash
docker compose up --build
```

GPU profile:

```bash
docker compose --profile gpu up --build
```

## Checks

```bash
cd services/api
pytest -q
ruff check src tests
```
