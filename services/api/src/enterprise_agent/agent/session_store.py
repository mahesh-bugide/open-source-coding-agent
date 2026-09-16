from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from enterprise_agent.agent.orchestrator import AgentRunResult
from enterprise_agent.core.config import Settings


@dataclass(slots=True)
class SessionRuntime:
    session_id: str
    workspace_path: Path
    active_run_id: str | None = None
    active_task: asyncio.Task[None] | None = None
    cancel_callback: Callable[[], None] | None = None
    latest_result: AgentRunResult | None = None


@dataclass(slots=True)
class SessionStore:
    sessions: dict[str, SessionRuntime] = field(default_factory=dict)


class SessionService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._store = SessionStore()

    def create_runtime(self, session_id: str, workspace_path: Path) -> SessionRuntime:
        runtime = SessionRuntime(session_id=session_id, workspace_path=workspace_path)
        self._store.sessions[session_id] = runtime
        return runtime

    def get_runtime(self, session_id: str) -> SessionRuntime | None:
        return self._store.sessions.get(session_id)
