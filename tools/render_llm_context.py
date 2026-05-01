from pathlib import Path
from typing import List, Optional, Set

import ast

from tools.models import ApiNode, ModuleDocModel
from tools.extractors.python_extractor import render_signature
from tools.mode_selector import collect_llm_candidates


def render_llm_context_document(
    doc: ModuleDocModel,
    template_path: str = "",
    target_qualnames: Optional[Set[str]] = None,
) -> str:
    """
    target_qualnames: если задан — включаем в промпт только эти сущности.
    Если None — включаем все кандидаты (поведение как раньше).
    """
    lines: List[str] = []

    lines.append("# LLM Context")
    lines.append("")
    lines.append("## Global task")
    lines.append("")
    lines.append(
        "Сформируй улучшенные описания только для переданных ниже сущностей. "
        "Для каждой сущности нужно подготовить структурированное описание по схеме:"
    )
    lines.append("")
    lines.append("1. Назначение: одно предложение о том, зачем существует эта функция.")
    lines.append("2. Логика работы: 2-4 предложения о том, как именно она это делает — алгоритм, ключевые шаги, условия.")
    lines.append("")
    lines.append("Правила:")
    lines.append("- не выдумывай факты, которых нет в коде и доступном контексте;")
    lines.append("- опирайся на сигнатуру, docstring, исключения и исходный код;")
    lines.append("- если информации недостаточно, укажи это явно;")
    lines.append("- не переписывай код, а только описывай его.")
    lines.append("")

    lines.append("## Component")
    lines.append("")
    lines.append("- name: `{}`".format(doc.component_name))
    lines.append("- source_path: `{}`".format(doc.source_path))
    lines.append("- language: `{}`".format(doc.language))
    lines.append("- version: `{}`".format(doc.version))
    lines.append("- status: `{}`".format(doc.status))
    lines.append("- date: `{}`".format(doc.date))
    lines.append("")

    module_doc = (doc.root.docstring or "").strip()
    lines.append("## Module docstring")
    lines.append("")
    lines.append(module_doc if module_doc else "MISSING")
    lines.append("")

    candidates = collect_llm_candidates(doc.root)

    # Фильтруем по target_qualnames если задан
    if target_qualnames is not None:
        candidates = [c for c in candidates if c.qualname in target_qualnames]

    lines.append("## Entity count")
    lines.append("")
    lines.append("{}".format(len(candidates)))
    lines.append("")

    if not candidates:
        lines.append("## Entities")
        lines.append("")
        lines.append("No candidates found.")
        lines.append("")
        return "\n".join(lines)

    lines.append("## Entities")
    lines.append("")

    for node in candidates:
        lines.extend(render_node_context(node))

    return "\n".join(lines).rstrip() + "\n"


def render_node_context(node: ApiNode) -> List[str]:
    lines: List[str] = []

    reasons = infer_llm_reasons(node)
    complexity = analyze_complexity(node)

    lines.append("### Entity `{}`".format(node.qualname))
    lines.append("")
    lines.append("- type: `{}`".format(node.node_type))
    lines.append("- name: `{}`".format(node.name))
    lines.append("- qualname: `{}`".format(node.qualname))
    lines.append("- location: `{}`".format(format_location(node)))
    lines.append("- reason: `{}`".format(", ".join(reasons) if reasons else "general_enrichment"))
    lines.append("")

    lines.append("#### Signature")
    lines.append("")
    if node.signature is not None:
        lines.append("```python")
        lines.append(render_signature(node.signature))
        lines.append("```")
    else:
        lines.append("MISSING")
    lines.append("")

    lines.append("#### Description from code")
    lines.append("")
    doc = (node.docstring or "").strip()
    lines.append(doc if doc else "MISSING")
    lines.append("")

    lines.append("#### Decorators")
    lines.append("")
    if node.decorators:
        for dec in node.decorators:
            lines.append("- `{}`".format(dec))
    else:
        lines.append("- none")
    lines.append("")

    lines.append("#### Parameters")
    lines.append("")
    params = render_parameters(node)
    if params:
        lines.extend(params)
    else:
        lines.append("- none")
    lines.append("")

    lines.append("#### Return")
    lines.append("")
    if node.signature is not None and node.signature.return_annotation:
        lines.append("- `{}`".format(node.signature.return_annotation))
    else:
        lines.append("- MISSING")
    lines.append("")

    lines.append("#### Exceptions")
    lines.append("")
    if node.exceptions:
        for exc in node.exceptions:
            if exc.details:
                lines.append("- `{}` — {}".format(exc.name, exc.details))
            else:
                lines.append("- `{}`".format(exc.name))
    else:
        lines.append("- none")
    lines.append("")

    lines.append("#### Complexity")
    lines.append("")
    for item in complexity:
        lines.append("- {}".format(item))
    lines.append("")

    lines.append("#### Class / parent context")
    lines.append("")
    lines.append(infer_parent_context(node))
    lines.append("")

    lines.append("#### Source code")
    lines.append("")
    lines.append("```python")
    lines.append(extract_source_snippet(node))
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")

    return lines


def render_parameters(node: ApiNode) -> List[str]:
    if node.signature is None or not node.signature.parameters:
        return []

    result: List[str] = []

    for param in node.signature.parameters:
        if param.name in ("self", "cls"):
            continue

        annotation = param.annotation if param.annotation is not None else "MISSING"
        default = param.default if param.default is not None else "MISSING"

        result.append(
            "- `{}`: kind=`{}`, annotation=`{}`, default=`{}`".format(
                param.name,
                param.kind,
                annotation,
                default,
            )
        )

    return result


def infer_parent_context(node: ApiNode) -> str:
    parts = node.qualname.split(".")
    if len(parts) >= 3:
        class_name = parts[-2]
        return "Entity belongs to class `{}`.".format(class_name)
    return "Top-level function in module."


def infer_llm_reasons(node: ApiNode) -> List[str]:
    reasons: List[str] = []

    doc = (node.docstring or "").strip()
    if not doc:
        reasons.append("missing_docstring")
    elif len(doc) < 40:
        reasons.append("short_docstring")

    if node.exceptions:
        reasons.append("has_exceptions")

    if node.signature is not None:
        visible_params = [
            p for p in node.signature.parameters
            if p.name not in ("self", "cls")
        ]
        if len(visible_params) >= 3:
            reasons.append("multiple_parameters")
        if node.signature.is_async:
            reasons.append("async")

    complexity = collect_complexity_flags(node)
    if complexity["if_count"] > 0:
        reasons.append("branching")
    if complexity["loop_count"] > 0:
        reasons.append("loop")
    if complexity["await_count"] > 0:
        reasons.append("await")
    if complexity["raise_count"] > 0:
        reasons.append("raise")
    if complexity["return_count"] > 1:
        reasons.append("multiple_returns")

    if not reasons:
        reasons.append("general_enrichment")

    return deduplicate_preserve_order(reasons)


def analyze_complexity(node: ApiNode) -> List[str]:
    flags = collect_complexity_flags(node)

    result = [
        "if_count=`{}`".format(flags["if_count"]),
        "loop_count=`{}`".format(flags["loop_count"]),
        "await_count=`{}`".format(flags["await_count"]),
        "raise_count=`{}`".format(flags["raise_count"]),
        "return_count=`{}`".format(flags["return_count"]),
        "line_span=`{}`".format((node.end_lineno or node.lineno) - node.lineno + 1),
    ]

    if is_complex(flags, node):
        result.append("diagram_candidate=`yes`")
    else:
        result.append("diagram_candidate=`no`")

    return result


def collect_complexity_flags(node: ApiNode) -> dict:
    source = extract_source_snippet(node)
    try:
        parsed = ast.parse(source)
    except Exception:
        return {
            "if_count": 0,
            "loop_count": 0,
            "await_count": 0,
            "raise_count": 0,
            "return_count": 0,
        }

    if_count = 0
    loop_count = 0
    await_count = 0
    raise_count = 0
    return_count = 0

    for child in ast.walk(parsed):
        if isinstance(child, ast.If):
            if_count += 1
        elif isinstance(child, (ast.For, ast.AsyncFor, ast.While)):
            loop_count += 1
        elif isinstance(child, ast.Await):
            await_count += 1
        elif isinstance(child, ast.Raise):
            raise_count += 1
        elif isinstance(child, ast.Return):
            return_count += 1

    return {
        "if_count": if_count,
        "loop_count": loop_count,
        "await_count": await_count,
        "raise_count": raise_count,
        "return_count": return_count,
    }


def is_complex(flags: dict, node: ApiNode) -> bool:
    span = (node.end_lineno or node.lineno) - node.lineno + 1
    if span > 10:
        return True
    if flags["if_count"] > 1:
        return True
    if flags["loop_count"] > 0:
        return True
    if flags["raise_count"] > 0:
        return True
    if flags["await_count"] > 0:
        return True
    if flags["return_count"] > 1:
        return True
    return False


def format_location(node: ApiNode) -> str:
    if node.end_lineno and node.end_lineno != node.lineno:
        return "{}:{}-{}".format(node.file_path, node.lineno, node.end_lineno)
    return "{}:{}".format(node.file_path, node.lineno)


def extract_source_snippet(node: ApiNode) -> str:
    try:
        path = Path(node.file_path)
        if not path.exists():
            return "# source file not found"

        lines = path.read_text(encoding="utf-8").splitlines()

        start = max(node.lineno - 1, 0)
        end = node.end_lineno if node.end_lineno else node.lineno
        snippet = lines[start:end]

        if not snippet:
            return "# empty snippet"

        return "\n".join(snippet)
    except Exception as exc:
        return "# failed to extract source: {}".format(exc)


def deduplicate_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result