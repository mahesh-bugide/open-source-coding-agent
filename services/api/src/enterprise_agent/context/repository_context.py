from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from enterprise_agent.context.symbols import SymbolExtractor
from enterprise_agent.tools.file_tools import FileTools
from enterprise_agent.tools.schemas import ListFilesInput, ReadFileInput, SearchCodeInput


@dataclass(slots=True)
class ContextFile:
    path: str
    content: str
    symbols: list[str]


@dataclass(slots=True)
class RepositoryContext:
    file_tree: list[str]
    search_hits: list[dict]
    files: list[ContextFile]


class RepositoryContextBuilder:
    def __init__(self, workspace_root: Path) -> None:
        self._workspace_root = workspace_root
        self._file_tools = FileTools(workspace_root)
        self._symbol_extractor = SymbolExtractor()

    def build(self, task: str, attachments: list[str] | None = None) -> RepositoryContext:
        tree = self._file_tools.list_files(ListFilesInput(max_depth=4)).files[:200]

        queries = self._queries_from_task(task)
        search_hits: list[dict] = []
        for query in queries:
            output = self._file_tools.search_code(SearchCodeInput(query=query, max_results=10))
            for match in output.matches:
                search_hits.append(match.model_dump())

        # Explicitly attached files (like an IDE's @file mention) always win and are
        # never dropped by the later file cap, regardless of search/keyword matching.
        attached_paths: list[str] = []
        for raw_path in attachments or []:
            normalized = raw_path.strip().lstrip("@").strip()
            if normalized and normalized not in attached_paths:
                attached_paths.append(normalized)

        unique_paths: list[str] = list(attached_paths)
        for hit in search_hits:
            path = hit["path"]
            if path not in unique_paths:
                unique_paths.append(path)

        for filename in self._filenames_from_task(task):
            for tree_path in tree:
                if tree_path.endswith(filename) and tree_path not in unique_paths:
                    unique_paths.append(tree_path)

        files: list[ContextFile] = []
        slot_limit = max(8, len(attached_paths))
        for path in unique_paths[:slot_limit]:
            try:
                read_output = self._file_tools.read_file(ReadFileInput(path=path, start_line=1, end_line=300))
            except Exception:
                continue
            symbols = self._symbol_extractor.extract(path, read_output.content)
            files.append(ContextFile(path=path, content=read_output.content, symbols=symbols))

        return RepositoryContext(file_tree=tree, search_hits=search_hits[:50], files=files)

    def _queries_from_task(self, task: str) -> list[str]:
        words = re.findall(r"[a-zA-Z_]{3,}", task.lower())
        unique: list[str] = []
        for word in words:
            if word not in unique:
                unique.append(word)
        return unique[:5] or [task[:40]]

    def _filenames_from_task(self, task: str) -> list[str]:
        candidates = re.findall(r"[\w./-]+\.[A-Za-z0-9]{1,10}\b", task)
        unique: list[str] = []
        for name in candidates:
            if name not in unique:
                unique.append(name)
        return unique

