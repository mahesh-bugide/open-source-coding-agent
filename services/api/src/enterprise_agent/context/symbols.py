from __future__ import annotations

import re
from pathlib import Path

try:
    from tree_sitter import Language, Parser
except Exception:  # pragma: no cover
    Language = None
    Parser = None


class SymbolExtractor:
    def __init__(self) -> None:
        self._parsers: dict[str, Parser] = {}

    def extract(self, path: str, content: str) -> list[str]:
        suffix = Path(path).suffix.lower()

        parser = self._parsers.get(suffix)
        if parser and Parser is not None:
            symbols = self._extract_with_tree_sitter(parser, content)
            if symbols:
                return symbols

        return self._extract_with_regex(content)

    def _extract_with_tree_sitter(self, parser: Parser, content: str) -> list[str]:
        tree = parser.parse(content.encode("utf-8"))
        text = content
        names: list[str] = []

        def walk(node) -> None:
            if node.type in {
                "function_definition",
                "class_definition",
                "function_declaration",
                "class_declaration",
                "method_definition",
            }:
                for child in node.children:
                    if child.type in {"identifier", "name", "type_identifier", "property_identifier"}:
                        value = text[child.start_byte : child.end_byte].strip()
                        if value and value not in names:
                            names.append(value)
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        return names[:40]

    def _extract_with_regex(self, content: str) -> list[str]:
        symbols = re.findall(r"\b(?:def|class|function|const|let)\s+([A-Za-z_][A-Za-z0-9_]*)", content)
        deduped: list[str] = []
        for symbol in symbols:
            if symbol not in deduped:
                deduped.append(symbol)
        return deduped[:40]
