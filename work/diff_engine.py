from __future__ import annotations

"""
tools/diff_engine.py

Сравнивает два дерева ApiNode (старое и новое) и возвращает список EntityDiff —
по одному на каждую изменившуюся или новую сущность.

Логика принятия решения needs_llm:
  - added          → True  (новая сущность, нужно полное описание)
  - removed        → False (просто убрать блок из документа)
  - signature_changed → False (факты из AST, LLM не нужен)
  - docstring_changed → False (разработчик уже написал текст)
  - body_changed + is_complex=True  → True  (логика могла измениться)
  - body_changed + is_complex=False → False (простая функция, не стоит токенов)
  - unchanged      → False
"""

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tools.models import ApiNode, ModuleDocModel


# ---------------------------------------------------------------------------
# Структура результата diff
# ---------------------------------------------------------------------------

@dataclass
class EntityDiff:
    qualname: str
    node_type: str               # function | method | class
    change_type: str             # added | removed | signature_changed |
                                 # docstring_changed | body_changed | unchanged
    is_complex: bool             # на основе analyze_complexity
    needs_llm: bool              # итоговое решение
    old_node: Optional[ApiNode] = None
    new_node: Optional[ApiNode] = None


@dataclass
class DiffResult:
    added:     List[EntityDiff] = field(default_factory=list)
    removed:   List[EntityDiff] = field(default_factory=list)
    changed:   List[EntityDiff] = field(default_factory=list)
    unchanged: List[EntityDiff] = field(default_factory=list)

    def needs_llm_entities(self) -> List[ApiNode]:
        """Возвращает ApiNode для которых нужен вызов LLM."""
        result = []
        for d in self.added + self.changed:
            if d.needs_llm and d.new_node is not None:
                result.append(d.new_node)
        return result

    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = [
            "Добавлено:  {}".format(len(self.added)),
            "Удалено:    {}".format(len(self.removed)),
            "Изменено:   {}".format(len(self.changed)),
            "Без изменений: {}".format(len(self.unchanged)),
            "Требуют LLM: {}".format(
                len([d for d in self.added + self.changed if d.needs_llm])
            ),
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Основная функция сравнения
# ---------------------------------------------------------------------------

def compute_diff(old_root: ApiNode, new_root: ApiNode) -> DiffResult:
    """
    Сравнивает два дерева ApiNode.
    Возвращает DiffResult со списками изменений.
    """
    old_map = _flatten_tree(old_root)
    new_map = _flatten_tree(new_root)

    result = DiffResult()

    all_qualnames = set(old_map) | set(new_map)

    for qualname in sorted(all_qualnames):
        old_node = old_map.get(qualname)
        new_node = new_map.get(qualname)

        if old_node is None and new_node is not None:
            # Новая сущность
            complexity = _is_complex(new_node)
            result.added.append(EntityDiff(
                qualname=qualname,
                node_type=new_node.node_type,
                change_type="added",
                is_complex=complexity,
                needs_llm=True,
                old_node=None,
                new_node=new_node,
            ))

        elif old_node is not None and new_node is None:
            # Удалённая сущность
            result.removed.append(EntityDiff(
                qualname=qualname,
                node_type=old_node.node_type,
                change_type="removed",
                is_complex=False,
                needs_llm=False,
                old_node=old_node,
                new_node=None,
            ))

        else:
            # Сущность существует в обоих деревьях — определяем тип изменения
            change_type = _detect_change_type(old_node, new_node)

            if change_type == "unchanged":
                result.unchanged.append(EntityDiff(
                    qualname=qualname,
                    node_type=new_node.node_type,
                    change_type="unchanged",
                    is_complex=False,
                    needs_llm=False,
                    old_node=old_node,
                    new_node=new_node,
                ))
            else:
                complexity = _is_complex(new_node)
                needs_llm  = _decide_needs_llm(change_type, complexity)
                result.changed.append(EntityDiff(
                    qualname=qualname,
                    node_type=new_node.node_type,
                    change_type=change_type,
                    is_complex=complexity,
                    needs_llm=needs_llm,
                    old_node=old_node,
                    new_node=new_node,
                ))

    return result


# ---------------------------------------------------------------------------
# Снапшоты — сохранение и загрузка дерева между запусками
# ---------------------------------------------------------------------------

def save_snapshot(doc: ModuleDocModel, snapshot_dir: str = "snapshots") -> Path:
    """
    Сохраняет дерево ApiNode в JSON-снапшот.
    Файл: snapshots/<module_name>.json
    """
    snap_path = Path(snapshot_dir)
    snap_path.mkdir(exist_ok=True)

    file_name = doc.component_name.replace(".", "_") + ".json"
    out_path  = snap_path / file_name

    data = _node_to_dict(doc.root)
    out_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_path


def load_snapshot(module_name: str, snapshot_dir: str = "snapshots") -> Optional[ApiNode]:
    """
    Загружает снапшот для модуля.
    Возвращает None если снапшот не найден.
    """
    file_name = module_name.replace(".", "_") + ".json"
    snap_path = Path(snapshot_dir) / file_name

    if not snap_path.exists():
        return None

    data = json.loads(snap_path.read_text(encoding="utf-8"))
    return _dict_to_node(data)


def diff_with_snapshot(
    doc: ModuleDocModel,
    snapshot_dir: str = "snapshots",
) -> Tuple[DiffResult, bool]:
    """
    Сравнивает текущее дерево со снапшотом.
    Возвращает (DiffResult, is_first_run).
    is_first_run=True если снапшот не найден (первый запуск).
    """
    old_root = load_snapshot(doc.component_name, snapshot_dir)

    if old_root is None:
        # Первый запуск — всё считается "added"
        result = DiffResult()
        for node in _flatten_tree(doc.root).values():
            complexity = _is_complex(node)
            result.added.append(EntityDiff(
                qualname=node.qualname,
                node_type=node.node_type,
                change_type="added",
                is_complex=complexity,
                needs_llm=True,
                old_node=None,
                new_node=node,
            ))
        return result, True

    return compute_diff(old_root, doc.root), False


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _flatten_tree(root: ApiNode) -> Dict[str, ApiNode]:
    """Разворачивает дерево в плоский словарь qualname → ApiNode."""
    result: Dict[str, ApiNode] = {}
    stack = [root]
    while stack:
        node = stack.pop()
        if node.node_type in ("function", "method", "class"):
            result[node.qualname] = node
        stack.extend(node.children)
    return result


def _detect_change_type(old: ApiNode, new: ApiNode) -> str:
    """
    Определяет тип изменения между двумя версиями одной сущности.
    Приоритет: signature > docstring > body > unchanged
    """
    # Сравниваем сигнатуры
    if _signature_changed(old, new):
        return "signature_changed"

    # Сравниваем декораторы (входят в сигнатуру интерфейса)
    if sorted(old.decorators) != sorted(new.decorators):
        return "signature_changed"

    # Сравниваем исключения
    old_exc = sorted(e.name for e in old.exceptions)
    new_exc = sorted(e.name for e in new.exceptions)
    if old_exc != new_exc:
        return "signature_changed"

    # docstring намеренно не сравниваем —
    # в снапшоте он всегда None, а в новом дереве может быть любым.
    # Изменение docstring отслеживается только если оба не None.
    old_doc = old.docstring
    new_doc = new.docstring
    if old_doc is not None and new_doc is not None and old_doc.strip() != new_doc.strip():
        return "docstring_changed"

    # Сравниваем расположение (изменилось тело — строки сдвинулись)
    old_span = (old.end_lineno or 0) - (old.lineno or 0)
    new_span = (new.end_lineno or 0) - (new.lineno or 0)
    if old_span != new_span:
        return "body_changed"

    return "unchanged"


def _signature_changed(old: ApiNode, new: ApiNode) -> bool:
    """Сравнивает сигнатуры двух узлов."""
    if old.signature is None and new.signature is None:
        return False
    if old.signature is None or new.signature is None:
        return True

    # Сравниваем return
    if old.signature.return_annotation != new.signature.return_annotation:
        return True

    # Сравниваем is_async
    if old.signature.is_async != new.signature.is_async:
        return True

    # Сравниваем параметры
    old_params = [
        (p.name, p.kind, p.annotation, p.default)
        for p in old.signature.parameters
    ]
    new_params = [
        (p.name, p.kind, p.annotation, p.default)
        for p in new.signature.parameters
    ]
    return old_params != new_params


def _is_complex(node: ApiNode) -> bool:
    """
    Оценивает сложность функции/метода.
    Использует те же критерии что и analyze_complexity в render_llm_context.
    """
    if node.node_type == "class":
        return False

    if node.signature and node.signature.is_async:
        return True

    if len(node.exceptions) >= 2:
        return True

    # Пробуем прочитать исходник и проанализировать AST
    try:
        source = Path(node.file_path).read_text(encoding="utf-8")
        lines  = source.splitlines()
        start  = (node.lineno or 1) - 1
        end    = node.end_lineno or len(lines)
        snippet = "\n".join(lines[start:end])
        tree   = ast.parse(snippet)
    except Exception:
        return False

    if_count     = sum(1 for n in ast.walk(tree) if isinstance(n, ast.If))
    loop_count   = sum(1 for n in ast.walk(tree)
                       if isinstance(n, (ast.For, ast.AsyncFor, ast.While)))
    return_count = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Return))
    line_span    = end - start

    return (
        if_count     >= 1   # любое ветвление
        or loop_count  >= 1  # любой цикл
        or return_count > 1  # несколько точек выхода
        or line_span   > 10  # функция длиннее 10 строк
    )


def _decide_needs_llm(change_type: str, is_complex: bool) -> bool:
    """
    Итоговое решение: нужен ли LLM для данного изменения.
    """
    if change_type == "added":
        return True
    if change_type in ("signature_changed", "docstring_changed"):
        return False
    if change_type == "body_changed":
        return is_complex
    return False


# ---------------------------------------------------------------------------
# Сериализация ApiNode → dict → ApiNode (для снапшотов)
# ---------------------------------------------------------------------------

def _node_to_dict(node: ApiNode) -> dict:
    sig = None
    if node.signature:
        sig = {
            "name": node.signature.name,
            "return_annotation": node.signature.return_annotation,
            "is_async": node.signature.is_async,
            "parameters": [
                {
                    "name":       p.name,
                    "kind":       p.kind,
                    "annotation": p.annotation,
                    "default":    p.default,
                }
                for p in node.signature.parameters
            ],
        }
    return {
        "node_type":   node.node_type,
        "name":        node.name,
        "qualname":    node.qualname,
        "lineno":      node.lineno,
        "end_lineno":  node.end_lineno,
        "file_path":   node.file_path,
        "language":    node.language,
        "signature":   sig,
        "docstring":   None,  # не сохраняем docstring — он не участвует в diff
        "decorators":  node.decorators,
        "exceptions":  [{"name": e.name, "details": e.details} for e in node.exceptions],
        "children":    [_node_to_dict(c) for c in node.children],
    }


def _dict_to_node(d: dict) -> ApiNode:
    from tools.models import ExceptionInfo, ParameterInfo, SignatureInfo

    sig = None
    if d.get("signature"):
        s = d["signature"]
        sig = SignatureInfo(
            name=s["name"],
            return_annotation=s.get("return_annotation"),
            is_async=s.get("is_async", False),
            parameters=[
                ParameterInfo(
                    name=p["name"],
                    kind=p["kind"],
                    annotation=p.get("annotation"),
                    default=p.get("default"),
                )
                for p in s.get("parameters", [])
            ],
        )

    return ApiNode(
        node_type=d["node_type"],
        name=d["name"],
        qualname=d["qualname"],
        lineno=d["lineno"],
        end_lineno=d["end_lineno"],
        file_path=d["file_path"],
        language=d.get("language", "python"),
        signature=sig,
        docstring=d.get("docstring"),
        decorators=d.get("decorators", []),
        exceptions=[
            ExceptionInfo(name=e["name"], details=e.get("details"))
            for e in d.get("exceptions", [])
        ],
        children=[_dict_to_node(c) for c in d.get("children", [])],
    )# test change
