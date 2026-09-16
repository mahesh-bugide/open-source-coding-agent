from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from enterprise_agent.core.security import resolve_safe_path
from enterprise_agent.tools.schemas import (
    CreateFileInput,
    CreateFileOutput,
    DeleteFileInput,
    DeleteFileOutput,
    EditFileInput,
    EditFileOutput,
    ListFilesInput,
    ListFilesOutput,
    ReadFileInput,
    ReadFileOutput,
    SearchCodeInput,
    SearchCodeMatch,
    SearchCodeOutput,
)


class FileTools:
    def __init__(self, workspace_root: Path) -> None:
        self._workspace_root = workspace_root

    def list_files(self, payload: ListFilesInput) -> ListFilesOutput:
        root = resolve_safe_path(self._workspace_root, payload.path)
        files: list[str] = []
        truncated = False

        max_entries = 5000
        root_depth = len(root.parts)
        for current_root, dirnames, filenames in os.walk(root):
            current = Path(current_root)
            depth = len(current.parts) - root_depth
            if depth > payload.max_depth:
                dirnames[:] = []
                continue

            if not payload.include_hidden:
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                filenames = [f for f in filenames if not f.startswith(".")]

            for filename in filenames:
                path = current / filename
                files.append(path.relative_to(self._workspace_root).as_posix())
                if len(files) >= max_entries:
                    truncated = True
                    return ListFilesOutput(files=files, truncated=truncated)

        return ListFilesOutput(files=sorted(files), truncated=truncated)

    def search_code(self, payload: SearchCodeInput) -> SearchCodeOutput:
        rg_path = shutil.which("rg")
        if rg_path:
            return self._search_with_rg(rg_path, payload)
        return self._search_with_python(payload)

    def _search_with_rg(self, rg_path: str, payload: SearchCodeInput) -> SearchCodeOutput:
        command = [
            rg_path,
            "--line-number",
            "--no-heading",
            "--color=never",
            payload.query,
            ".",
        ]
        if payload.glob:
            command.extend(["--glob", payload.glob])

        completed = subprocess.run(
            command,
            cwd=self._workspace_root,
            shell=False,
            capture_output=True,
            text=True,
        )

        matches: list[SearchCodeMatch] = []
        if completed.returncode not in (0, 1):
            raise RuntimeError(f"ripgrep failed: {completed.stderr.strip()}")

        for line in completed.stdout.splitlines():
            parts = line.split(":", 2)
            if len(parts) != 3:
                continue
            path, line_number, code = parts
            matches.append(
                SearchCodeMatch(
                    path=Path(path).as_posix(),
                    line_number=int(line_number),
                    line=code,
                )
            )
            if len(matches) >= payload.max_results:
                break

        return SearchCodeOutput(matches=matches)

    def _search_with_python(self, payload: SearchCodeInput) -> SearchCodeOutput:
        matches: list[SearchCodeMatch] = []
        query_lower = payload.query.lower()

        for path in self._workspace_root.rglob("*"):
            if not path.is_file():
                continue
            if ".git" in path.parts:
                continue

            try:
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue

            for index, line in enumerate(lines, start=1):
                if query_lower in line.lower():
                    matches.append(
                        SearchCodeMatch(
                            path=path.relative_to(self._workspace_root).as_posix(),
                            line_number=index,
                            line=line,
                        )
                    )
                    if len(matches) >= payload.max_results:
                        return SearchCodeOutput(matches=matches)

        return SearchCodeOutput(matches=matches)

    def read_file(self, payload: ReadFileInput) -> ReadFileOutput:
        path = resolve_safe_path(self._workspace_root, payload.path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {payload.path}")

        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        total_lines = len(lines)
        start_index = max(payload.start_line - 1, 0)
        end_line = payload.end_line or total_lines
        end_index = min(end_line, total_lines)

        content = "\n".join(lines[start_index:end_index])
        return ReadFileOutput(
            path=path.relative_to(self._workspace_root).as_posix(),
            content=content,
            start_line=payload.start_line,
            end_line=end_index,
            total_lines=total_lines,
        )

    def create_file(self, payload: CreateFileInput) -> CreateFileOutput:
        path = resolve_safe_path(self._workspace_root, payload.path)
        if path.exists() and not payload.overwrite:
            raise FileExistsError(f"File already exists: {payload.path}")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload.content, encoding="utf-8")
        return CreateFileOutput(path=path.relative_to(self._workspace_root).as_posix(), created=True)

    def edit_file(self, payload: EditFileInput) -> EditFileOutput:
        path = resolve_safe_path(self._workspace_root, payload.path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {payload.path}")
        path.write_text(payload.new_content, encoding="utf-8")
        return EditFileOutput(path=path.relative_to(self._workspace_root).as_posix(), edited=True)

    def delete_file(self, payload: DeleteFileInput) -> DeleteFileOutput:
        path = resolve_safe_path(self._workspace_root, payload.path)
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {payload.path}")

        if path.is_dir():
            raise IsADirectoryError("delete_file only supports files in MVP")
        path.unlink()
        return DeleteFileOutput(path=path.relative_to(self._workspace_root).as_posix(), deleted=True)
