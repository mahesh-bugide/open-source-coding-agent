from __future__ import annotations

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    workspace_path: str = Field(min_length=1)


class CreateSessionResponse(BaseModel):
    session_id: str
    status: str


class SendMessageRequest(BaseModel):
    message: str = Field(min_length=1)
    attachments: list[str] = Field(default_factory=list)


class SendMessageResponse(BaseModel):
    session_id: str
    agent_run_id: str
    status: str


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    attachments: list[str] = Field(default_factory=list)


class AskResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class CancelSessionResponse(BaseModel):
    session_id: str
    status: str


class ApplyChangesResponse(BaseModel):
    session_id: str
    applied_files: list[str]
    status: str


class RejectChangesResponse(BaseModel):
    session_id: str
    status: str


class SessionResultResponse(BaseModel):
    session_id: str
    status: str
    success: bool
    changed_files: list[str]
    diff: str
    iterations: int
    limitations: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    database: bool
