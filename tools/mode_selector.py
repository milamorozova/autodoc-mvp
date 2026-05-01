from typing import List

from tools.models import ApiNode


def choose_mode(mode: str) -> str:
    allowed = {"clean", "llm_context", "auto"}
    if mode not in allowed:
        return "clean"
    return mode


def collect_llm_candidates(root: ApiNode) -> List[ApiNode]:
    result: List[ApiNode] = []
    stack = [root]

    while stack:
        node = stack.pop()

        # Классы включаем если они публичные (не начинаются с _)
        if node.node_type == "class" and not node.name.startswith("_"):
            result.append(node)

        # Функции и методы включаем только публичные
        if node.node_type in ("function", "method") and not node.name.startswith("_"):
            result.append(node)

        stack.extend(node.children)

    return sorted(result, key=lambda x: x.qualname)


def should_use_llm_for_node(node: ApiNode) -> bool:
    return node.node_type in ("function", "method", "class") and not node.name.startswith("_")