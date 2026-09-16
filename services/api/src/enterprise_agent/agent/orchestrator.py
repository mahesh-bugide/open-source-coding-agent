from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from enterprise_agent.agent.state import AgentState
from enterprise_agent.context.repository_context import RepositoryContextBuilder
from enterprise_agent.core.config import Settings
from enterprise_agent.model.client import create_model_gateway
from enterprise_agent.model.types import AgentPlan, ModelUsage
from enterprise_agent.tools.base import ToolExecutionError
from enterprise_agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class AgentRunResult(BaseModel):
    session_id: str
    agent_run_id: str
    state: AgentState
    success: bool
    iterations: int
    changed_files: list[str]
    diff: str
    duration_ms: int
    input_tokens: int
    output_tokens: int
    error: str | None = None
    sandbox_path: str


@dataclass(slots=True)
class RunArtifact:
    run_id: str
    session_id: str
    source_workspace: Path
    sandbox_workspace: Path
    changed_files: list[str]
    diff: str


EventCallback = Callable[[str, dict], Awaitable[None]]
ToolRecordCallback = Callable[[str, dict, dict | None, bool, str | None, int], Awaitable[None]]


class AgentOrchestrator:
    def __init__(
        self,
        settings: Settings,
        session_id: str,
        run_id: str,
        source_workspace: Path,
        emit_event: EventCallback,
        record_tool_call: ToolRecordCallback,
    ) -> None:
        self._settings = settings
        self._session_id = session_id
        self._run_id = run_id
        self._source_workspace = source_workspace
        self._emit = emit_event
        self._record_tool_call = record_tool_call
        self._cancel_event = asyncio.Event()

    def cancel(self) -> None:
        self._cancel_event.set()

    async def run(self, task: str) -> AgentRunResult:
        start = time.perf_counter()
        state = AgentState.START
        iterations = 0
        failure_output: str | None = None
        plan = AgentPlan()
        model_usage = ModelUsage()
        edited_paths: list[str] = []

        sandbox_workspace = self._create_sandbox_workspace()
        tool_registry = ToolRegistry(sandbox_workspace, self._settings)
        context_builder = RepositoryContextBuilder(sandbox_workspace)
        model = create_model_gateway(self._settings)

        await self._emit("agent_started", {"task": task, "state": state.value})

        try:
            while True:
                if self._cancel_event.is_set():
                    state = AgentState.CANCELLED
                    await self._emit("agent_failed", {"reason": "cancelled"})
                    break

                elapsed = time.perf_counter() - start
                if elapsed > self._settings.max_agent_seconds:
                    state = AgentState.TIMEOUT
                    await self._emit("agent_failed", {"reason": "timeout"})
                    break

                if state == AgentState.START:
                    state = AgentState.UNDERSTAND
                    continue

                if state == AgentState.UNDERSTAND:
                    context = await asyncio.to_thread(context_builder.build, task)
                    summary = await model.understand(task, context)
                    await self._emit("agent_message", {"message": summary, "state": state.value})
                    state = AgentState.PLAN
                    continue

                if state == AgentState.PLAN:
                    context = await asyncio.to_thread(context_builder.build, task)
                    plan = await model.plan(task, context)
                    await self._emit(
                        "agent_thinking",
                        {
                            "state": state.value,
                            "search_queries": plan.search_queries,
                            "test_command": plan.test_command,
                        },
                    )
                    state = AgentState.SEARCH
                    continue

                if state == AgentState.SEARCH:
                    for query in plan.search_queries[:5]:
                        await self._emit("tool_started", {"tool": "search_code", "query": query})
                        output = await self._execute_tool(
                            tool_registry,
                            "search_code",
                            {"query": query, "max_results": 20},
                        )
                        await self._emit(
                            "tool_completed",
                            {"tool": "search_code", "query": query, "output": output},
                        )
                    state = AgentState.READ
                    continue

                if state == AgentState.READ:
                    context = await asyncio.to_thread(context_builder.build, task)
                    await self._emit(
                        "agent_message",
                        {
                            "message": f"Context prepared from {len(context.files)} relevant files",
                            "state": state.value,
                            "files": [item.path for item in context.files],
                        },
                    )
                    state = AgentState.EDIT
                    continue

                if state == AgentState.EDIT:
                    iterations += 1
                    if iterations > self._settings.max_agent_iterations:
                        state = AgentState.FAILED
                        await self._emit("agent_failed", {"reason": "max_iterations_reached"})
                        break

                    context = await asyncio.to_thread(context_builder.build, task)
                    edits = await model.propose_edits(task, context, iterations, failure_output)

                    if not edits:
                        state = AgentState.FAILED
                        await self._emit("agent_failed", {"reason": "model_returned_no_edits"})
                        break

                    for edit in edits:
                        await self._emit("tool_started", {"tool": "edit_file", "path": edit.path})
                        await self._execute_tool(
                            tool_registry,
                            "edit_file",
                            {"path": edit.path, "new_content": edit.new_content},
                        )
                        if edit.path not in edited_paths:
                            edited_paths.append(edit.path)
                        await self._emit(
                            "file_changed",
                            {"path": edit.path, "reason": edit.reason},
                        )
                    state = AgentState.TEST
                    continue

                if state == AgentState.TEST:
                    await self._emit("test_started", {"command": plan.test_command})
                    output = await self._execute_tool(
                        tool_registry,
                        "run_tests",
                        {"command": plan.test_command, "timeout_sec": 300},
                    )
                    await self._emit("test_completed", output)

                    if output["exit_code"] == 0:
                        state = AgentState.COMPLETE
                        break

                    failure_output = (output.get("stdout") or "") + "\n" + (output.get("stderr") or "")
                    state = AgentState.ANALYZE_FAILURE
                    continue

                if state == AgentState.ANALYZE_FAILURE:
                    analysis = await model.analyze_failure(task, failure_output or "")
                    await self._emit("agent_message", {"message": analysis, "state": state.value})
                    state = AgentState.EDIT
                    continue

                break

        except ToolExecutionError as exc:
            state = AgentState.FAILED
            await self._emit("agent_failed", {"reason": f"tool_error: {exc}"})
        except Exception as exc:
            state = AgentState.FAILED
            logger.exception("agent_run_unhandled_exception", extra={"session_id": self._session_id})
            await self._emit("agent_failed", {"reason": str(exc)})

        diff_text = ""
        changed_files = list(edited_paths)

        try:
            diff_output = await self._execute_tool(tool_registry, "git_diff", {})
            status_output = await self._execute_tool(tool_registry, "git_status", {"porcelain": True})
            parsed = self._parse_changed_files(status_output.get("status", ""))
            if parsed:
                changed_files = parsed
            diff_text = diff_output.get("diff", "")
        except Exception:
            # Non-git workspaces can still return file-level edits for review.
            diff_text = ""

        model_usage = model.last_usage()
        success = state == AgentState.COMPLETE

        await self._emit(
            "agent_completed" if success else "agent_failed",
            {
                "state": state.value,
                "success": success,
                "iterations": iterations,
                "changed_files": changed_files,
                "diff": diff_text,
                "input_tokens": model_usage.input_tokens,
                "output_tokens": model_usage.output_tokens,
            },
        )

        duration_ms = int((time.perf_counter() - start) * 1000)

        return AgentRunResult(
            session_id=self._session_id,
            agent_run_id=self._run_id,
            state=state,
            success=success,
            iterations=iterations,
            changed_files=changed_files,
            diff=diff_text,
            duration_ms=duration_ms,
            input_tokens=model_usage.input_tokens,
            output_tokens=model_usage.output_tokens,
            error=None if success else state.value,
            sandbox_path=str(sandbox_workspace),
        )

    async def _execute_tool(self, registry: ToolRegistry, tool: str, payload: dict) -> dict:
        start = time.perf_counter()
        try:
            output = await registry.execute(tool, payload)
            latency_ms = int((time.perf_counter() - start) * 1000)
            await self._record_tool_call(tool, payload, output, True, None, latency_ms)
            return output
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            await self._record_tool_call(tool, payload, None, False, str(exc), latency_ms)
            raise

    def _create_sandbox_workspace(self) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix=f"agent-run-{self._session_id}-{self._run_id}-"))
        destination = temp_dir / "workspace"
        shutil.copytree(self._source_workspace, destination, dirs_exist_ok=False)
        return destination

    def _parse_changed_files(self, status: str) -> list[str]:
        paths: list[str] = []
        for line in status.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split(maxsplit=1)
            if len(parts) == 2:
                paths.append(parts[1])
        return paths
