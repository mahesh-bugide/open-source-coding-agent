from __future__ import annotations

import json
import re
import time
from typing import Any

import httpx

from enterprise_agent.context.repository_context import RepositoryContext
from enterprise_agent.core.config import Settings
from enterprise_agent.model.types import AgentPlan, FileEditProposal, ModelUsage


class ModelGateway:
    async def understand(self, task: str, context: RepositoryContext) -> str:
        raise NotImplementedError

    async def plan(self, task: str, context: RepositoryContext) -> AgentPlan:
        raise NotImplementedError

    async def propose_edits(
        self,
        task: str,
        context: RepositoryContext,
        iteration: int,
        failure_output: str | None,
    ) -> list[FileEditProposal]:
        raise NotImplementedError

    async def analyze_failure(self, task: str, test_output: str) -> str:
        raise NotImplementedError

    async def form_change_plan(self, task: str, context: RepositoryContext) -> str:
        raise NotImplementedError

    async def answer_question(self, question: str, context: RepositoryContext) -> str:
        raise NotImplementedError

    def last_usage(self) -> ModelUsage:
        raise NotImplementedError


class MockModelGateway(ModelGateway):
    def __init__(self) -> None:
        self._usage = ModelUsage()

    async def understand(self, task: str, context: RepositoryContext) -> str:
        self._usage.input_tokens += max(len(task) // 4, 1)
        self._usage.output_tokens += 30
        return f"Task intent understood: {task}. Relevant files found: {len(context.files)}"

    async def plan(self, task: str, context: RepositoryContext) -> AgentPlan:
        task_lower = task.lower()
        queries = [w for w in re.findall(r"[a-zA-Z_]{4,}", task_lower)][:4]
        if "auth" in task_lower or "authentication" in task_lower:
            queries.extend(["auth", "timeout", "login"])
        self._usage.input_tokens += max(len(task) // 4, 1)
        self._usage.output_tokens += 20
        return AgentPlan(search_queries=list(dict.fromkeys(queries))[:6], test_command="pytest -q")

    async def propose_edits(
        self,
        task: str,
        context: RepositoryContext,
        iteration: int,
        failure_output: str | None,
    ) -> list[FileEditProposal]:
        task_lower = task.lower()
        proposals: list[FileEditProposal] = []

        for item in context.files:
            if "auth" in task_lower and item.path.endswith("src/auth/service.py"):
                updated = item.content
                updated = updated.replace("DEFAULT_TIMEOUT_SECONDS = 0", "DEFAULT_TIMEOUT_SECONDS = 30")
                updated = updated.replace("timeout_seconds: int = 0", "timeout_seconds: int = 30")
                updated = updated.replace("return token, 0", "return token, timeout_seconds")
                if updated != item.content:
                    proposals.append(
                        FileEditProposal(
                            path=item.path,
                            new_content=updated,
                            reason="Fix authentication timeout default and return value",
                        )
                    )

            if (
                (iteration > 1 or failure_output)
                and "update the tests" in task_lower
                and item.path.endswith("tests/test_auth_service.py")
            ):
                updated = item.content
                if "assert ttl == 0" in updated:
                    updated = updated.replace("assert ttl == 0", "assert ttl == 30")
                if updated != item.content:
                    proposals.append(
                        FileEditProposal(
                            path=item.path,
                            new_content=updated,
                            reason="Align tests with timeout fix",
                        )
                    )

        if not proposals and failure_output:
            for item in context.files:
                if item.path.endswith("tests/test_auth_service.py") and "assert" in failure_output:
                    updated = item.content.replace("assert ttl == 0", "assert ttl == 30")
                    if updated != item.content:
                        proposals.append(
                            FileEditProposal(
                                path=item.path,
                                new_content=updated,
                                reason="Fix failing assertion based on test output",
                            )
                        )

        self._usage.input_tokens += 120
        self._usage.output_tokens += 160
        return proposals

    async def analyze_failure(self, task: str, test_output: str) -> str:
        self._usage.input_tokens += max(len(test_output) // 4, 1)
        self._usage.output_tokens += 40
        head = "\n".join(test_output.splitlines()[:20])
        return f"Test failure analysis for task '{task}': {head}"

    async def form_change_plan(self, task: str, context: RepositoryContext) -> str:
        self._usage.input_tokens += max(len(task) // 4, 1)
        self._usage.output_tokens += 25
        return f"Change plan for '{task}': edit {len(context.files)} candidate file(s) based on gathered context."

    async def answer_question(self, question: str, context: RepositoryContext) -> str:
        self._usage.input_tokens += max(len(question) // 4, 1)
        self._usage.output_tokens += 30
        return f"Mock answer for '{question}'. Relevant files found: {len(context.files)}"

    def last_usage(self) -> ModelUsage:
        return self._usage


class OpenAICompatModelGateway(ModelGateway):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._usage = ModelUsage()

    async def understand(self, task: str, context: RepositoryContext) -> str:
        prompt = (
            "Summarize the coding task in one short sentence. "
            f"Task: {task}. Candidate files: {[f.path for f in context.files][:8]}"
        )
        result = await self._chat(prompt)
        return result.strip()

    async def plan(self, task: str, context: RepositoryContext) -> AgentPlan:
        prompt = (
            "Return strict JSON with keys search_queries (array of <=6 strings) and test_command. "
            f"Task: {task}. File hints: {[f.path for f in context.files][:20]}"
        )
        result = await self._chat(prompt)
        parsed = self._extract_json(result)
        return AgentPlan.model_validate(parsed)

    async def propose_edits(
        self,
        task: str,
        context: RepositoryContext,
        iteration: int,
        failure_output: str | None,
    ) -> list[FileEditProposal]:
        snippets: list[dict[str, Any]] = []
        for item in context.files[:8]:
            snippets.append({"path": item.path, "content": item.content[:8000], "symbols": item.symbols})

        prompt = (
            "You are an automated coding agent. Return strict JSON with key edits containing "
            "[{path,new_content,reason}] for files that must be changed. "
            f"Task: {task}\nIteration: {iteration}\n"
            f"Failure: {failure_output or 'none'}\n"
            f"Files: {json.dumps(snippets)}"
        )
        result = await self._chat(prompt)
        parsed = self._extract_json(result)
        edits = parsed if isinstance(parsed, list) else parsed.get("edits", [])
        return [FileEditProposal.model_validate(edit) for edit in edits]

    async def analyze_failure(self, task: str, test_output: str) -> str:
        prompt = (
            "Analyze this failing test output and provide a concise diagnosis and fix hypothesis. "
            f"Task: {task}\nOutput:\n{test_output[:12000]}"
        )
        return (await self._chat(prompt)).strip()

    async def form_change_plan(self, task: str, context: RepositoryContext) -> str:
        file_paths = [item.path for item in context.files]
        prompt = (
            "Based on the task and the files already read below, describe in 2-4 concise sentences "
            "the concrete change plan you intend to make. Do not write code, just describe the approach.\n"
            f"Task: {task}\nFiles read: {file_paths}"
        )
        return (await self._chat(prompt)).strip()

    async def answer_question(self, question: str, context: RepositoryContext) -> str:
        snippets = [f"{item.path}:\n{item.content[:2000]}" for item in context.files[:6]]
        prompt = (
            "You are a helpful coding assistant. Answer the question clearly and concisely based on "
            "the repository context below. Do not propose file edits or run any tools; just answer.\n"
            f"Question: {question}\n"
            f"Relevant files:\n{chr(10).join(snippets) if snippets else 'none found'}"
        )
        return (await self._chat(prompt)).strip()

    def last_usage(self) -> ModelUsage:
        return self._usage

    async def _chat(self, prompt: str) -> str:
        headers = {}
        if self._settings.model_api_key:
            headers["Authorization"] = f"Bearer {self._settings.model_api_key}"

        body = {
            "model": self._settings.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise coding agent. Return exactly what was requested.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
            "stream": False,
        }

        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._settings.model_base_url}/chat/completions",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            payload = response.json()

        usage = payload.get("usage", {})
        self._usage = ModelUsage(
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

        return payload["choices"][0]["message"]["content"]

    def _extract_json(self, text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
            raise


def create_model_gateway(settings: Settings) -> ModelGateway:
    if settings.model_mode.lower() == "mock":
        return MockModelGateway()
    return OpenAICompatModelGateway(settings)
