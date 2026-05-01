from __future__ import annotations

from abc import ABC, abstractmethod
from tools.models import ApiNode


class BaseExtractor(ABC):
    @abstractmethod
    def build_tree(self, source: str, file_path: str, module_name: str) -> ApiNode:
        raise NotImplementedError