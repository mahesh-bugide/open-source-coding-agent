from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from enterprise_agent.agent.orchestrator import AgentOrchestrator, AgentRunResult
from enterprise_agent.api.schemas import (
    ApplyChangesResponse,
    AskRequest,
    AskResponse,
    CancelSessionResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    HealthResponse,
    ReadyResponse,
    RejectChangesResponse,
    SendMessageRequest,
    SendMessageResponse,
    SessionResultResponse,
)
from enterprise_agent.context.repository_context import RepositoryContextBuilder
from enterprise_agent.core.auth import AuthContext, require_auth
from enterprise_agent.core.security import resolve_safe_path, resolve_workspace_root
from enterprise_agent.db.repository import PersistenceRepository
from enterprise_agent.model.client import create_model_gateway

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
async def ready(request: Request) -> ReadyResponse:
    database_ok = await request.app.state.database.ping()
    return ReadyResponse(status="ok" if database_ok else "degraded", database=database_ok)


@router.get("/metrics")
async def metrics(request: Request) -> dict:
    return request.app.state.metrics.snapshot()


@router.post("/v1/sessions", response_model=CreateSessionResponse)
async def create_session(
    payload: CreateSessionRequest,
    request: Request,
    auth: AuthContext = Depends(require_auth),
) -> CreateSessionResponse:
    settings = request.app.state.settings
    session_id = str(uuid.uuid4())

    try:
        workspace_root = resolve_workspace_root(payload.workspace_path, settings.allowed_workspace_root)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    runtime = request.app.state.session_service.create_runtime(session_id, workspace_root)
    runtime.workspace_path = workspace_root

    logger.info(
        "session_created",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "session_id": session_id,
            "user_id": auth.user_id,
            "workspace_path": str(workspace_root),
        },
    )

    async with request.app.state.database.session_factory() as db_session:
        repo = PersistenceRepository(db_session)
        await repo.ensure_user(auth.user_id)
        await repo.create_session(session_id, auth.user_id, str(workspace_root))

    await request.app.state.cache.set_json(
        f"session:{session_id}",
        {"status": "active", "user_id": auth.user_id},
        ttl_sec=60 * 60 * 8,
    )

    return CreateSessionResponse(session_id=session_id, status="created")


@router.post("/v1/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(
    session_id: str,
    payload: SendMessageRequest,
    request: Request,
    auth: AuthContext = Depends(require_auth),
) -> SendMessageResponse:
    runtime = request.app.state.session_service.get_runtime(session_id)
    if runtime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if runtime.active_task and not runtime.active_task.done():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session already has active run")

    run_id = str(uuid.uuid4())
    runtime.active_run_id = run_id
    tool_call_counter = {"count": 0}

    logger.info(
        "agent_run_requested",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "session_id": session_id,
            "user_id": auth.user_id,
            "agent_run_id": run_id,
            "model": request.app.state.settings.model_name,
        },
    )

    async def emit(event_type: str, body: dict) -> None:
        await request.app.state.event_bus.publish(session_id, event_type, body)

    async def record_tool_call(
        tool: str,
        input_payload: dict,
        output_payload: dict | None,
        success: bool,
        error: str | None,
        latency_ms: int,
    ) -> None:
        tool_call_counter["count"] += 1
        request.app.state.metrics.inc("tool_calls_total")
        request.app.state.metrics.add("tool_latency_ms_total", latency_ms)
        if not success:
            request.app.state.metrics.inc("tool_failures_total")

        async with request.app.state.database.session_factory() as db_session:
            repo = PersistenceRepository(db_session)
            await repo.add_tool_call(
                agent_run_id=run_id,
                session_id=session_id,
                user_id=auth.user_id,
                tool=tool,
                input_json=input_payload,
                output_json=output_payload,
                latency_ms=latency_ms,
                success=success,
                error=error,
            )

    orchestrator = AgentOrchestrator(
        settings=request.app.state.settings,
        session_id=session_id,
        run_id=run_id,
        source_workspace=runtime.workspace_path,
        emit_event=emit,
        record_tool_call=record_tool_call,
    )
    request.app.state.run_orchestrators[session_id] = orchestrator

    async with request.app.state.database.session_factory() as db_session:
        repo = PersistenceRepository(db_session)
        await repo.add_message(session_id, auth.user_id, "user", payload.message)
        await repo.create_agent_run(
            session_id,
            auth.user_id,
            request.app.state.settings.model_name,
            run_id=run_id,
        )

    async def run_wrapper() -> None:
        result: AgentRunResult | None = None
        error: str | None = None
        try:
            await request.app.state.cache.set_json(
                f"run:{run_id}",
                {"status": "running", "session_id": session_id},
                ttl_sec=60 * 60 * 8,
            )
            result = await orchestrator.run(payload.message)
            runtime.latest_result = result
        except Exception as exc:
            logger.exception("agent_run_failed", extra={"session_id": session_id, "run_id": run_id})
            error = str(exc)
        finally:
            async with request.app.state.database.session_factory() as db_session:
                repo = PersistenceRepository(db_session)
                if result is not None:
                    request.app.state.metrics.inc("agent_runs_total")
                    request.app.state.metrics.add("agent_duration_ms_total", result.duration_ms)
                    request.app.state.metrics.add("tokens_input_total", result.input_tokens)
                    request.app.state.metrics.add("tokens_output_total", result.output_tokens)
                    if result.success:
                        request.app.state.metrics.inc("agent_runs_success_total")
                    else:
                        request.app.state.metrics.inc("agent_runs_failure_total")

                    await repo.complete_agent_run(
                        run_id,
                        status=result.state.value,
                        success=result.success,
                        tool_calls=tool_call_counter["count"],
                        input_tokens=result.input_tokens,
                        output_tokens=result.output_tokens,
                        error=result.error,
                    )
                    await repo.add_usage(
                        agent_run_id=run_id,
                        session_id=session_id,
                        user_id=auth.user_id,
                        model=request.app.state.settings.model_name,
                        input_tokens=result.input_tokens,
                        output_tokens=result.output_tokens,
                        latency_ms=result.duration_ms,
                        metadata_json={
                            "iterations": result.iterations,
                            "tool_calls": tool_call_counter["count"],
                        },
                    )
                else:
                    request.app.state.metrics.inc("agent_runs_total")
                    request.app.state.metrics.inc("agent_runs_failure_total")
                    await repo.complete_agent_run(
                        run_id,
                        status="FAILED",
                        success=False,
                        tool_calls=0,
                        input_tokens=0,
                        output_tokens=0,
                        error=error,
                    )
                await request.app.state.cache.set_json(
                    f"run:{run_id}",
                    {
                        "status": (result.state.value if result else "FAILED"),
                        "session_id": session_id,
                    },
                    ttl_sec=60 * 60 * 8,
                )
            runtime.active_run_id = None

    task = asyncio.create_task(run_wrapper())
    runtime.active_task = task
    request.app.state.run_tasks[session_id] = task

    return SendMessageResponse(session_id=session_id, agent_run_id=run_id, status="running")


@router.post("/v1/sessions/{session_id}/ask", response_model=AskResponse)
async def ask_question(
    session_id: str,
    payload: AskRequest,
    request: Request,
    auth: AuthContext = Depends(require_auth),
) -> AskResponse:
    runtime = request.app.state.session_service.get_runtime(session_id)
    if runtime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    context_builder = RepositoryContextBuilder(runtime.workspace_path)
    context = context_builder.build(payload.question)

    model = create_model_gateway(request.app.state.settings)
    answer = await model.answer_question(payload.question, context)
    usage = model.last_usage()

    async with request.app.state.database.session_factory() as db_session:
        repo = PersistenceRepository(db_session)
        await repo.add_message(session_id, auth.user_id, "user", payload.question)
        await repo.add_message(session_id, auth.user_id, "assistant", answer)

    return AskResponse(
        session_id=session_id,
        question=payload.question,
        answer=answer,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        latency_ms=usage.latency_ms,
    )


@router.get("/v1/sessions/{session_id}/stream")
async def stream_session(
    session_id: str,
    request: Request,
    _: AuthContext = Depends(require_auth),
) -> StreamingResponse:
    runtime = request.app.state.session_service.get_runtime(session_id)
    if runtime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    queue = await request.app.state.event_bus.subscribe(session_id)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                    yield event.to_sse()
                except TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            await request.app.state.event_bus.unsubscribe(session_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/v1/sessions/{session_id}/cancel", response_model=CancelSessionResponse)
async def cancel_session(
    session_id: str,
    request: Request,
    _: AuthContext = Depends(require_auth),
) -> CancelSessionResponse:
    runtime = request.app.state.session_service.get_runtime(session_id)
    if runtime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    orchestrator = request.app.state.run_orchestrators.get(session_id)
    if orchestrator is None:
        return CancelSessionResponse(session_id=session_id, status="no_active_run")

    orchestrator.cancel()
    return CancelSessionResponse(session_id=session_id, status="cancelling")


@router.post("/v1/sessions/{session_id}/apply", response_model=ApplyChangesResponse)
async def apply_changes(
    session_id: str,
    request: Request,
    _: AuthContext = Depends(require_auth),
) -> ApplyChangesResponse:
    runtime = request.app.state.session_service.get_runtime(session_id)
    if runtime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    result = runtime.latest_result
    if result is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No run result available")

    sandbox_root = Path(result.sandbox_path)
    if not sandbox_root.exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sandbox workspace expired")

    applied: list[str] = []
    for relative in result.changed_files:
        source_file = sandbox_root / relative
        target_file = resolve_safe_path(runtime.workspace_path, relative)

        if source_file.exists() and source_file.is_file():
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(source_file.read_text(encoding="utf-8"), encoding="utf-8")
            applied.append(relative)
            continue

        if target_file.exists():
            target_file.unlink()
            applied.append(relative)

    return ApplyChangesResponse(session_id=session_id, applied_files=applied, status="applied")


@router.post("/v1/sessions/{session_id}/reject", response_model=RejectChangesResponse)
async def reject_changes(
    session_id: str,
    request: Request,
    _: AuthContext = Depends(require_auth),
) -> RejectChangesResponse:
    runtime = request.app.state.session_service.get_runtime(session_id)
    if runtime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    runtime.latest_result = None
    return RejectChangesResponse(session_id=session_id, status="rejected")


@router.get("/v1/sessions/{session_id}/result", response_model=SessionResultResponse)
async def get_result(
    session_id: str,
    request: Request,
    _: AuthContext = Depends(require_auth),
) -> SessionResultResponse:
    runtime = request.app.state.session_service.get_runtime(session_id)
    if runtime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    result = runtime.latest_result
    if result is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No run result available")

    return SessionResultResponse(
        session_id=session_id,
        status=result.state.value,
        success=result.success,
        changed_files=result.changed_files,
        diff=result.diff,
        iterations=result.iterations,
    )
