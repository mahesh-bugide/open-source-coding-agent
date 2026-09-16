from __future__ import annotations

from pydantic import BaseModel, Field


class AgentPlan(BaseModel):
    search_queries: list[str] = Field(default_factory=list)
    test_command: str = "pytest -q"


class FileEditProposal(BaseModel):
    path: str
    new_content: str
    reason: str


class ModelUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
