from pathlib import Path

import pytest

from enterprise_agent.tools.file_tools import FileTools
from enterprise_agent.tools.schemas import CreateFileInput, ListFilesInput, ReadFileInput, SearchCodeInput


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir(parents=True)
    (tmp_path / "src" / "sample.py").write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    return tmp_path


def test_list_files_returns_workspace_relative_paths(workspace: Path) -> None:
    tools = FileTools(workspace)
    output = tools.list_files(ListFilesInput(path=".", max_depth=5))
    assert "src/sample.py" in output.files


def test_read_file_respects_line_window(workspace: Path) -> None:
    tools = FileTools(workspace)
    output = tools.read_file(ReadFileInput(path="src/sample.py", start_line=1, end_line=1))
    assert output.content.strip() == "def hello():"


def test_search_code_finds_match(workspace: Path) -> None:
    tools = FileTools(workspace)
    output = tools.search_code(SearchCodeInput(query="hello"))
    assert output.matches
    assert output.matches[0].path == "src/sample.py"


def test_create_file_blocks_path_traversal(workspace: Path) -> None:
    tools = FileTools(workspace)
    with pytest.raises(ValueError):
        tools.create_file(CreateFileInput(path="../escape.txt", content="bad"))
