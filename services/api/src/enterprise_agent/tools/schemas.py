from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ToolBaseOutput(BaseModel):
    success: bool = True
    error: str | None = None
    latency_ms: int = 0


class ListFilesInput(BaseModel):
    path: str = "."
    max_depth: int = Field(default=4, ge=0, le=20)
    include_hidden: bool = False


class ListFilesOutput(ToolBaseOutput):
    files: list[str]
    truncated: bool = False


class SearchCodeInput(BaseModel):
    query: str = Field(min_length=1, max_length=512)
    glob: str | None = None
    max_results: int = Field(default=50, ge=1, le=500)


class SearchCodeMatch(BaseModel):
    path: str
    line_number: int
    line: str


class SearchCodeOutput(ToolBaseOutput):
    matches: list[SearchCodeMatch]


class ReadFileInput(BaseModel):
    path: str
    start_line: int = Field(default=1, ge=1)
    end_line: int | None = Field(default=None, ge=1)


class ReadFileOutput(ToolBaseOutput):
    path: str
    content: str
    start_line: int
    end_line: int
    total_lines: int


class CreateFileInput(BaseModel):
    path: str
    content: str
    overwrite: bool = False


class CreateFileOutput(ToolBaseOutput):
    path: str
    created: bool


class EditFileInput(BaseModel):
    path: str
    new_content: str


class EditFileOutput(ToolBaseOutput):
    path: str
    edited: bool


class DeleteFileInput(BaseModel):
    path: str


class DeleteFileOutput(ToolBaseOutput):
    path: str
    deleted: bool


class RunCommandInput(BaseModel):
    command: str = Field(min_length=1, max_length=4000)
    timeout_sec: int = Field(default=60, ge=1, le=1800)


class RunCommandOutput(ToolBaseOutput):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool


class RunTestsInput(BaseModel):
    command: str = Field(default="pytest -q", min_length=1, max_length=4000)
    timeout_sec: int = Field(default=120, ge=1, le=3600)


class RunTestsOutput(ToolBaseOutput):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool


class GitStatusInput(BaseModel):
    porcelain: bool = True


class GitStatusOutput(ToolBaseOutput):
    status: str


class GitDiffInput(BaseModel):
    pathspec: str | None = None

    @field_validator("pathspec")
    @classmethod
    def reject_absolute_pathspec(cls, value: str | None) -> str | None:
        if value and (value.startswith("/") or ":\\" in value):
            raise ValueError("pathspec must be workspace-relative")
        return value


class GitDiffOutput(ToolBaseOutput):
    diff: str
