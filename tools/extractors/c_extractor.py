from __future__ import annotations

from tools.extractors.base import BaseExtractor
from tools.models import ApiNode


class CExtractor(BaseExtractor):
    def build_tree(self, source: str, file_path: str, module_name: str) -> ApiNode:
        return ApiNode(
            node_type="module",
            name=module_name,
            qualname=module_name,
            lineno=1,
            end_lineno=max(1, len(source.splitlines())),
            file_path=file_path,
            language="c",
            docstring="Поддержка языка C пока не реализована.",
        )