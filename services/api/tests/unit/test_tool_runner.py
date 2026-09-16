import pytest

from enterprise_agent.tools.base import ToolDefinition, ToolExecutionError, ToolRunner
from enterprise_agent.tools.schemas import ListFilesInput, ListFilesOutput


class DummyTool:
    def list_files(self, payload: ListFilesInput) -> ListFilesOutput:
        return ListFilesOutput(files=[payload.path])


@pytest.mark.asyncio()
async def test_tool_runner_validates_input() -> None:
    tool = DummyTool()
    runner = ToolRunner(
        {
            "list_files": ToolDefinition(
                name="list_files",
                input_model=ListFilesInput,
                output_model=ListFilesOutput,
                handler=tool.list_files,
            )
        }
    )

    result = await runner.execute("list_files", {"path": "."})
    assert result["files"] == ["."]


@pytest.mark.asyncio()
async def test_tool_runner_rejects_invalid_input() -> None:
    tool = DummyTool()
    runner = ToolRunner(
        {
            "list_files": ToolDefinition(
                name="list_files",
                input_model=ListFilesInput,
                output_model=ListFilesOutput,
                handler=tool.list_files,
            )
        }
    )

    with pytest.raises(ToolExecutionError):
        await runner.execute("list_files", {"max_depth": -1})
