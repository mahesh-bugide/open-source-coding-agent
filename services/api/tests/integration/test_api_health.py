import os
from pathlib import Path

from fastapi.testclient import TestClient


def test_health_and_ready_endpoints(tmp_path: Path) -> None:
    db_path = tmp_path / "api-test.db"
    os.environ["POSTGRES_DSN"] = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    os.environ["REQUIRE_API_KEY"] = "false"

    from enterprise_agent.core.config import get_settings

    get_settings.cache_clear()

    from enterprise_agent.main import app

    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        ready = client.get("/ready")
        assert ready.status_code == 200
        assert "status" in ready.json()

    get_settings.cache_clear()
