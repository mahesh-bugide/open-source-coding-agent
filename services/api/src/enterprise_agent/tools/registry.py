from __future__ import annotations

from pathlib import Path

from enterprise_agent.core.config import Settings
from enterprise_agent.sandbox.manager import create_sandbox_manager
from enterprise_agent.tools.base import ToolDefinition, ToolRunner
from enterprise_agent.tools.command_tools import CommandTools
from enterprise_agent.tools.file_tools import FileTools
from enterprise_agent.tools.git_tools import GitTools
from enterprise_agent.tools.schemas import (
    CreateFileInput,
    CreateFileOutput,
    DeleteFileInput,
    DeleteFileOutput,
    EditFileInput,
    EditFileOutput,
    GitDiffInput,
    GitDiffOutput,
    GitStatusInput,
    GitStatusOutput,
    ListFilesInput,
    ListFilesOutput,
    ReadFileInput,
    ReadFileOutput,
    RunCommandInput,
    RunCommandOutput,
    RunTestsInput,
    RunTestsOutput,
    SearchCodeInput,
    SearchCodeOutput,
)


class ToolRegistry:
    def __init__(self, workspace_root: Path, settings: Settings) -> None:
        file_tools = FileTools(workspace_root)
        sandbox = create_sandbox_manager(workspace_root, settings)
        command_tools = CommandTools(sandbox)
        git_tools = GitTools(workspace_root)

        self.runner = ToolRunner(
            {
                "list_files": ToolDefinition(
                    name="list_files",
                    input_model=ListFilesInput,
                    output_model=ListFilesOutput,
                    handler=file_tools.list_files,
                ),
                "search_code": ToolDefinition(
                    name="search_code",
                    input_model=SearchCodeInput,
                    output_model=SearchCodeOutput,
                    handler=file_tools.search_code,
                ),
                "read_file": ToolDefinition(
                    name="read_file",
                    input_model=ReadFileInput,
                    output_model=ReadFileOutput,
                    handler=file_tools.read_file,
                ),
                "create_file": ToolDefinition(
                    name="create_file",
                    input_model=CreateFileInput,
                    output_model=CreateFileOutput,
                    handler=file_tools.create_file,
                ),
                "edit_file": ToolDefinition(
                    name="edit_file",
                    input_model=EditFileInput,
                    output_model=EditFileOutput,
                    handler=file_tools.edit_file,
                ),
                "delete_file": ToolDefinition(
                    name="delete_file",
                    input_model=DeleteFileInput,
                    output_model=DeleteFileOutput,
                    handler=file_tools.delete_file,
                ),
                "run_command": ToolDefinition(
                    name="run_command",
                    input_model=RunCommandInput,
                    output_model=RunCommandOutput,
                    handler=command_tools.run_command,
                ),
                "run_tests": ToolDefinition(
                    name="run_tests",
                    input_model=RunTestsInput,
                    output_model=RunTestsOutput,
                    handler=command_tools.run_tests,
                ),
                "git_status": ToolDefinition(
                    name="git_status",
                    input_model=GitStatusInput,
                    output_model=GitStatusOutput,
                    handler=git_tools.git_status,
                ),
                "git_diff": ToolDefinition(
                    name="git_diff",
                    input_model=GitDiffInput,
                    output_model=GitDiffOutput,
                    handler=git_tools.git_diff,
                ),
            }
        )

    async def execute(self, tool_name: str, payload: dict) -> dict:
        return await self.runner.execute(tool_name, payload)
