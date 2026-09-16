from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    pass


@dataclass(slots=True)
class ToolDefinition:
    name: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    handler: Callable[[BaseModel], BaseModel]


class ToolRunner:
    def __init__(self, tools: dict[str, ToolDefinition]) -> None:
        self._tools = tools

    async def execute(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ToolExecutionError(f"Unknown tool: {tool_name}")

        try:
            validated_input = tool.input_model.model_validate(payload)
        except ValidationError as exc:
            raise ToolExecutionError(f"Invalid input for tool {tool_name}: {exc}") from exc

        start = time.perf_counter()
        try:
            output_model = await asyncio.to_thread(tool.handler, validated_input)
            output_dict = output_model.model_dump()
            output_dict["latency_ms"] = int((time.perf_counter() - start) * 1000)
            logger.info(
                "tool_completed",
                extra={
                    "tool": tool_name,
                    "latency_ms": output_dict["latency_ms"],
                    "success": output_dict.get("success", True),
                },
            )
            return output_dict
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.exception(
                "tool_failed",
                extra={"tool": tool_name, "latency_ms": latency_ms, "error": str(exc)},
            )
            raise ToolExecutionError(str(exc)) from exc
