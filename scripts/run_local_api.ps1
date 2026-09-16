Param(
  [string]$WorkspaceRoot = ""
)

$env:APP_ENV = "development"
$env:POSTGRES_DSN = "sqlite+aiosqlite:///./local.db"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:MODEL_MODE = "mock"
$env:MODEL_BASE_URL = "http://localhost:8001/v1"
$env:MODEL_NAME = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
$env:DEV_API_KEY = "dev-local-key"
$env:REQUIRE_API_KEY = "true"
$env:SANDBOX_MODE = "local"

if ($WorkspaceRoot -ne "") {
  $env:ALLOWED_WORKSPACE_ROOT = $WorkspaceRoot
}

Set-Location "$PSScriptRoot\..\services\api"
python -m uvicorn enterprise_agent.main:app --host 0.0.0.0 --port 8080 --reload
