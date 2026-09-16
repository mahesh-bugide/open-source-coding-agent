from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_agent.db.models import (
    AgentRunRecord,
    MessageRecord,
    SessionRecord,
    ToolCallRecord,
    UsageRecord,
    User,
)


class PersistenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ensure_user(self, user_id: str) -> User:
        existing = await self._session.get(User, user_id)
        if existing:
            return existing
        user = User(id=user_id)
        self._session.add(user)
        await self._session.commit()
        return user

    async def create_session(self, session_id: str, user_id: str, workspace_path: str) -> SessionRecord:
        record = SessionRecord(
            id=session_id,
            user_id=user_id,
            workspace_path=workspace_path,
            status="active",
        )
        self._session.add(record)
        await self._session.commit()
        return record

    async def get_session(self, session_id: str) -> SessionRecord | None:
        stmt = select(SessionRecord).where(SessionRecord.id == session_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_message(self, session_id: str, user_id: str, role: str, content: str) -> MessageRecord:
        record = MessageRecord(session_id=session_id, user_id=user_id, role=role, content=content)
        self._session.add(record)
        await self._session.commit()
        return record

    async def create_agent_run(
        self,
        session_id: str,
        user_id: str,
        model: str,
        run_id: str | None = None,
    ) -> AgentRunRecord:
        record = AgentRunRecord(
            id=run_id or str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            model=model,
        )
        self._session.add(record)
        await self._session.commit()
        return record

    async def complete_agent_run(
        self,
        run_id: str,
        *,
        status: str,
        success: bool,
        tool_calls: int,
        input_tokens: int,
        output_tokens: int,
        error: str | None = None,
    ) -> None:
        record = await self._session.get(AgentRunRecord, run_id)
        if not record:
            return

        completed_at = datetime.now(UTC)
        duration_ms = int((completed_at - record.started_at).total_seconds() * 1000)

        record.completed_at = completed_at
        record.status = status
        record.success = success
        record.tool_calls = tool_calls
        record.input_tokens = input_tokens
        record.output_tokens = output_tokens
        record.duration_ms = duration_ms
        record.error = error
        await self._session.commit()

    async def add_tool_call(
        self,
        agent_run_id: str,
        session_id: str,
        user_id: str,
        tool: str,
        input_json: dict | None,
        output_json: dict | None,
        latency_ms: int,
        success: bool,
        error: str | None,
    ) -> ToolCallRecord:
        record = ToolCallRecord(
            agent_run_id=agent_run_id,
            session_id=session_id,
            user_id=user_id,
            tool=tool,
            input_json=input_json,
            output_json=output_json,
            latency_ms=latency_ms,
            success=success,
            error=error,
        )
        self._session.add(record)
        await self._session.commit()
        return record

    async def add_usage(
        self,
        agent_run_id: str,
        session_id: str,
        user_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        metadata_json: dict | None,
    ) -> UsageRecord:
        record = UsageRecord(
            agent_run_id=agent_run_id,
            session_id=session_id,
            user_id=user_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            metadata_json=metadata_json,
        )
        self._session.add(record)
        await self._session.commit()
        return record
