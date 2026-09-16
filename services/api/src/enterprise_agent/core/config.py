from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="enterprise-ai-coding-agent-api", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8080, alias="PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    require_api_key: bool = Field(default=True, alias="REQUIRE_API_KEY")
    dev_api_key: str = Field(default="dev-local-key", alias="DEV_API_KEY")

    postgres_dsn: str = Field(
        default="sqlite+aiosqlite:///./local.db",
        alias="POSTGRES_DSN",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    model_mode: str = Field(default="mock", alias="MODEL_MODE")
    model_base_url: str = Field(default="http://localhost:8001/v1", alias="MODEL_BASE_URL")
    model_api_key: str = Field(default="", alias="MODEL_API_KEY")
    model_name: str = Field(
        default="Qwen/Qwen2.5-Coder-1.5B-Instruct",
        alias="MODEL_NAME",
    )

    max_agent_iterations: int = Field(default=6, alias="MAX_AGENT_ITERATIONS")
    max_agent_seconds: int = Field(default=600, alias="MAX_AGENT_SECONDS")
    tool_default_timeout_seconds: int = Field(default=60, alias="TOOL_DEFAULT_TIMEOUT_SECONDS")

    sandbox_mode: str = Field(default="local", alias="SANDBOX_MODE")
    sandbox_image: str = Field(default="enterprise-agent-sandbox:latest", alias="SANDBOX_IMAGE")
    sandbox_cpu_limit: float = Field(default=1.0, alias="SANDBOX_CPU_LIMIT")
    sandbox_memory_limit_mb: int = Field(default=1024, alias="SANDBOX_MEMORY_LIMIT_MB")
    sandbox_pids_limit: int = Field(default=256, alias="SANDBOX_PIDS_LIMIT")
    sandbox_disk_limit_mb: int = Field(default=2048, alias="SANDBOX_DISK_LIMIT_MB")
    sandbox_network_disabled: bool = Field(default=True, alias="SANDBOX_NETWORK_DISABLED")

    allowed_workspace_root: Path | None = Field(default=None, alias="ALLOWED_WORKSPACE_ROOT")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
