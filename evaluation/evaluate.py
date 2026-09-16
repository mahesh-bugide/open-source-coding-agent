from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any

import httpx


async def read_sse_until_done(client: httpx.AsyncClient, url: str, headers: dict[str, str]) -> dict[str, Any]:
    completed_payload: dict[str, Any] | None = None

    async with client.stream("GET", url, headers=headers, timeout=600.0) as response:
        response.raise_for_status()
        buffer = ""
        async for chunk in response.aiter_text():
            buffer += chunk
            frames = buffer.split("\n\n")
            buffer = frames.pop() or ""
            for frame in frames:
                if not frame.startswith("data:"):
                    continue
                payload = frame[5:].strip()
                if not payload:
                    continue
                event = json.loads(payload)
                event_type = event.get("type")
                if event_type in {"agent_completed", "agent_failed"}:
                    completed_payload = event
                    return completed_payload

    return completed_payload or {"type": "agent_failed", "payload": {"reason": "stream_closed"}}


async def run_task(
    client: httpx.AsyncClient,
    api_base_url: str,
    api_key: str,
    workspace_path: str,
    task: str,
) -> dict[str, Any]:
    headers = {"x-api-key": api_key, "content-type": "application/json"}

    session_response = await client.post(
        f"{api_base_url}/v1/sessions",
        headers=headers,
        json={"workspace_path": workspace_path},
    )
    session_response.raise_for_status()
    session_id = session_response.json()["session_id"]

    start = time.perf_counter()
    run_response = await client.post(
        f"{api_base_url}/v1/sessions/{session_id}/messages",
        headers=headers,
        json={"message": task},
    )
    run_response.raise_for_status()
    run_id = run_response.json()["agent_run_id"]

    completion_event = await read_sse_until_done(
        client,
        f"{api_base_url}/v1/sessions/{session_id}/stream",
        {"x-api-key": api_key},
    )

    duration_ms = int((time.perf_counter() - start) * 1000)
    payload = completion_event.get("payload", {})

    return {
        "session_id": session_id,
        "agent_run_id": run_id,
        "event_type": completion_event.get("type"),
        "success": bool(payload.get("success", False)),
        "iterations": int(payload.get("iterations", 0)),
        "changed_files": payload.get("changed_files", []),
        "input_tokens": int(payload.get("input_tokens", 0)),
        "output_tokens": int(payload.get("output_tokens", 0)),
        "duration_ms": duration_ms,
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base-url", default="http://localhost:8080")
    parser.add_argument("--api-key", default="dev-local-key")
    parser.add_argument("--tasks", default="evaluation/tasks.json")
    parser.add_argument("--workspace-root", default=".")
    args = parser.parse_args()

    tasks_path = Path(args.tasks)
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))

    results: list[dict[str, Any]] = []
    async with httpx.AsyncClient() as client:
        for item in tasks:
            workspace_path = str((Path(args.workspace_root) / item["workspace_path"]).resolve())
            result = await run_task(
                client,
                api_base_url=args.api_base_url,
                api_key=args.api_key,
                workspace_path=workspace_path,
                task=item["task"],
            )
            result["task_id"] = item["id"]
            results.append(result)

    success_count = sum(1 for item in results if item["success"])
    output = {
        "total": len(results),
        "success": success_count,
        "success_rate": (success_count / len(results)) if results else 0.0,
        "results": results,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
