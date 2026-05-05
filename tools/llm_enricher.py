from __future__ import annotations

"""
tools/llm_enricher.py
"""

import re
from typing import Dict, Optional, Tuple

from tools.models import ApiNode, ModuleDocModel
from tools.llm_client import call_llm
from tools.render_llm_context import render_llm_context_document


def enrich_with_llm(
    doc: ModuleDocModel,
    api_key: Optional[str] = None,
    verbose: bool = False,
    target_qualnames: Optional[set] = None,
) -> ModuleDocModel:
    prompt = render_llm_context_document(doc, target_qualnames=target_qualnames)

    if verbose:
        print("[LLM] Отправляем контекст ({} символов)...".format(len(prompt)))

    try:
        raw_response = call_llm(prompt, api_key=api_key)
    except Exception as e:
        print("[LLM] Предупреждение: не удалось получить ответ: {}".format(e))
        return doc

    if verbose:
        print("[LLM] Получен ответ ({} символов).".format(len(raw_response)))

    enriched = parse_llm_response(raw_response)

    if verbose:
        print("[LLM] Распознано сущностей: {}.".format(len(enriched)))
        for k in list(enriched.keys()):
            print("  - {}".format(k))

    apply_enrichment(doc.root, enriched)
    doc.enriched = True

    doc = enrich_idl_with_llm(doc, api_key=api_key, verbose=verbose)

    # Генерируем short_description и tags если они не заполнены
    doc = enrich_metadata_with_llm(doc, api_key=api_key, verbose=verbose)

    return doc


def enrich_metadata_with_llm(
    doc: ModuleDocModel,
    api_key: Optional[str] = None,
    verbose: bool = False,
) -> ModuleDocModel:
    """
    Генерирует short_description и tags через LLM если они не заполнены.
    """
    need_description = not getattr(doc, 'short_description', None)
    need_tags        = not getattr(doc, 'tags', None)

    if not need_description and not need_tags:
        return doc

    # Собираем контекст: имя модуля, описание из docstring, список публичных сущностей
    module_name = doc.root.name if doc.root else "unknown"
    entities = []
    stack = [doc.root]
    while stack:
        node = stack.pop()
        if node.node_type in ("function", "method", "class") and not node.name.startswith("_"):
            desc = node.docstring or ""
            entities.append(f"- {node.node_type} `{node.name}`: {desc[:120]}")
        stack.extend(node.children)

    entities_text = "\n".join(entities[:20])  # не больше 20 чтобы не раздувать промпт

    lines = [
        f"Модуль Python: `{module_name}`",
        f"Публичные сущности:",
        entities_text,
        "",
        "На основе этой информации сгенерируй строго в формате ниже:",
    ]

    if need_description:
        lines.append("SHORT_DESCRIPTION: <одно предложение, максимум 300 символов, на русском языке>")
    if need_tags:
        lines.append("TAGS: <3-7 тегов через запятую, на русском языке, например: diff, API, сравнение>")

    lines += [
        "",
        "Верни ТОЛЬКО строки SHORT_DESCRIPTION и/или TAGS без пояснений.",
    ]

    prompt = "\n".join(lines)

    if verbose:
        print("[LLM META] Запрашиваем метаданные ({} символов)...".format(len(prompt)))

    try:
        response = call_llm(prompt, api_key=api_key)
    except Exception as e:
        print("[LLM META] Предупреждение: не удалось получить метаданные: {}".format(e))
        return doc

    # Парсим ответ
    for line in response.splitlines():
        line = line.strip()
        if need_description and line.startswith("SHORT_DESCRIPTION:"):
            val = line[len("SHORT_DESCRIPTION:"):].strip()
            if val:
                doc.short_description = val[:300]
                if verbose:
                    print(f"[LLM META] short_description: {doc.short_description}")

        if need_tags and line.startswith("TAGS:"):
            val = line[len("TAGS:"):].strip()
            if val:
                doc.tags = val
                if verbose:
                    print(f"[LLM META] tags: {doc.tags}")

    return doc


def enrich_idl_with_llm(
    doc: ModuleDocModel,
    api_key: Optional[str] = None,
    verbose: bool = False,
) -> ModuleDocModel:
    classes = [c for c in doc.root.children if c.node_type == "class"]
    if not classes:
        return doc

    lines = [
        "Сгенерируй настоящий COM IDL (в стиле Microsoft MIDL) для следующих Python-интерфейсов.",
        "Правила:",
        "- Используй синтаксис: object, uuid(XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX), helpstring",
        "- Каждый метод возвращает HRESULT",
        "- Входные параметры: [in], выходные: [out, retval]",
        "- Типы: int → long, str → BSTR, bool → VARIANT_BOOL, float → double,",
        "  dict → struct с именем <ClassName>Data, list → SAFEARRAY",
        "- Конструктор (create_default/classmethod) → CoCreateInstance, не включай в интерфейс",
        "- Верни ТОЛЬКО IDL-код без пояснений и markdown-блоков",
        "",
    ]

    for cls in classes:
        public_methods = [
            m for m in cls.children
            if m.node_type == "method" and not m.name.startswith("__")
            and "classmethod" not in m.decorators
        ]
        if not public_methods:
            continue
        lines.append("// Класс: {}".format(cls.name))
        for method in public_methods:
            sig = _format_method_for_idl_prompt(method)
            lines.append("// {}".format(sig))
        lines.append("")

    prompt = "\n".join(lines)

    if verbose:
        print("[LLM IDL] Запрашиваем COM IDL ({} символов)...".format(len(prompt)))

    try:
        idl_response = call_llm(prompt, api_key=api_key)
    except Exception as e:
        print("[LLM IDL] Предупреждение: не удалось получить IDL: {}".format(e))
        return doc

    idl_clean = _strip_code_block(idl_response)

    if idl_clean.strip():
        doc.enriched_idl = idl_clean
        if verbose:
            print("[LLM IDL] COM IDL сгенерирован ({} символов).".format(len(idl_clean)))

    return doc


def _format_method_for_idl_prompt(method: ApiNode) -> str:
    if method.signature is None:
        return "def {}()".format(method.name)
    params = []
    for p in method.signature.parameters:
        if p.name in ("self", "cls"):
            continue
        ann = p.annotation or "any"
        params.append("{}: {}".format(p.name, ann))
    ret = method.signature.return_annotation or "None"
    return "def {}({}) -> {}".format(method.name, ", ".join(params), ret)


def _strip_code_block(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```(?:idl|cpp|c\+\+)?\s*\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n```\s*$', '', text)
    return text.strip()


def parse_llm_response(raw: str) -> Dict[str, Tuple[str, str]]:
    result: Dict[str, Tuple[str, str]] = {}
    normalized = re.sub(r'\n\s*---+\s*\n', '\n', raw)

    pattern = re.compile(
        r'###\s+Entity\s+`([^`]+)`\s*\n(.*?)(?=###\s+Entity\s+`|\Z)',
        re.DOTALL,
    )
    for match in pattern.finditer(normalized):
        qualname    = match.group(1).strip()
        description = match.group(2).strip()
        if qualname and description:
            result[qualname] = _extract_purpose_and_logic(description)

    if not result:
        pattern2 = re.compile(
            r'###\s+`([^`]+)`\s*\n(.*?)(?=###\s+`|\Z)',
            re.DOTALL,
        )
        for match in pattern2.finditer(normalized):
            qualname    = match.group(1).strip()
            description = match.group(2).strip()
            if qualname and description:
                result[qualname] = _extract_purpose_and_logic(description)

    return result


def _extract_purpose_and_logic(text: str) -> Tuple[str, str]:
    m_purpose = re.search(
        r'1\.\s*\*{0,2}Назначени[еяю][^:]*\*{0,2}[:\s]+(.+?)(?=\n\s*2\.|\Z)',
        text, re.DOTALL | re.IGNORECASE,
    )
    if m_purpose:
        purpose = m_purpose.group(1).strip()
        purpose = re.sub(r'\*+', '', purpose).strip()
        purpose = re.sub(r'\s+', ' ', purpose)
        if len(purpose) > 400:
            end = purpose.find('. ')
            if 0 < end < 400:
                purpose = purpose[:end + 1]
    else:
        purpose = ""
        for line in text.split('\n'):
            line = re.sub(r'\*+', '', line).strip()
            line = re.sub(r'^\d+\.\s*', '', line).strip()
            if line and not line.startswith('#') and len(line) > 15:
                purpose = line
                break
        if not purpose:
            purpose = text.strip()[:300]

    m_logic = re.search(
        r'2\.\s*\*{0,2}Логика\s+работы[^:]*\*{0,2}[:\s]+(.+?)(?=\n\s*3\.|\Z)',
        text, re.DOTALL | re.IGNORECASE,
    )
    if m_logic:
        logic = m_logic.group(1).strip()
        logic = re.sub(r'\*+', '', logic).strip()
        logic = re.sub(r'\s+', ' ', logic)
        if len(logic) > 800:
            logic = logic[:800].rsplit('. ', 1)[0] + '.'
    else:
        logic = ""

    return (purpose, logic)


def apply_enrichment(root: ApiNode, enriched: Dict[str, Tuple[str, str]]) -> None:
    stack = [root]
    while stack:
        node = stack.pop()
        if node.node_type in ("function", "method", "class"):
            data = enriched.get(node.qualname) or enriched.get(node.name)
            if data:
                purpose, logic = data
                if purpose:
                    node.docstring = purpose
                if logic and hasattr(node, 'logic'):
                    node.logic = logic
        stack.extend(node.children)