import os
import time
from pathlib import Path

from fastapi.testclient import TestClient


def _create_sample_repo(root: Path) -> None:
    (root / "src" / "auth").mkdir(parents=True)
    (root / "tests").mkdir(parents=True)
    (root / "src" / "auth" / "service.py").write_text(
        "DEFAULT_TIMEOUT_SECONDS = 0\n\n"
        "def issue_session_token(user_id: str, timeout_seconds: int = 0) -> tuple[str, int]:\n"
        "    token = f'token-{user_id}'\n"
        "    return token, 0\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_auth_service.py").write_text(
        "from src.auth.service import issue_session_token\n\n"
        "def test_issue_session_token_has_default_timeout():\n"
        "    _token, ttl = issue_session_token('alice')\n"
        "    assert ttl == 0\n",
        encoding="utf-8",
    )


def test_session_run_and_cancel(tmp_path: Path) -> None:
    db_path = tmp_path / "session-test.db"
    repo_path = tmp_path / "workspace"
    _create_sample_repo(repo_path)

    os.environ["POSTGRES_DSN"] = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    os.environ["REQUIRE_API_KEY"] = "true"
    os.environ["DEV_API_KEY"] = "dev-local-key"
    os.environ["MODEL_MODE"] = "mock"
    os.environ["MAX_AGENT_ITERATIONS"] = "2"
    os.environ["MAX_AGENT_SECONDS"] = "120"

    from enterprise_agent.core.config import get_settings

    get_settings.cache_clear()

    from enterprise_agent.main import app

    headers = {"x-api-key": "dev-local-key"}

    with TestClient(app) as client:
        session_response = client.post(
            "/v1/sessions",
            json={"workspace_path": str(repo_path)},
            headers=headers,
        )
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]

        run_response = client.post(
            f"/v1/sessions/{session_id}/messages",
            json={"message": "Fix the authentication timeout bug and update the tests."},
            headers=headers,
        )
        assert run_response.status_code == 200

        cancel_response = client.post(f"/v1/sessions/{session_id}/cancel", headers=headers)
        assert cancel_response.status_code == 200

        # Give background run wrapper a short interval for cleanup.
        time.sleep(0.5)

    get_settings.cache_clear()
