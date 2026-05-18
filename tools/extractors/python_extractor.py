from __future__ import annotations

import ast
from typing import List, Optional

from tools.extractors.base import BaseExtractor
from tools.models import ApiNode, ExceptionInfo, ParameterInfo, SignatureInfo


import re as _re

def _strip_annotated(annotation: str) -> str:
    """Убирает Annotated[T, Doc(...)] оставляя только T."""
    if not annotation or not annotation.startswith("Annotated["):
        return annotation
    # Берём первый аргумент — всё до первой запятой на верхнем уровне скобок
    inner = annotation[len("Annotated["):]
    depth = 0
    for i, ch in enumerate(inner):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            return inner[:i].strip()
    return annotation


import re as _re

def _strip_annotated(annotation: str) -> str:
    """Убирает Annotated[T, Doc(...)] оставляя только T."""
    if not annotation or not annotation.startswith("Annotated["):
        return annotation
    # Берём первый аргумент — всё до первой запятой на верхнем уровне скобок
    inner = annotation[len("Annotated["):]
    depth = 0
    for i, ch in enumerate(inner):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            return inner[:i].strip()
    return annotation


# Словарь перевода стандартных маркеров в docstring
_DOCSTRING_TRANSLATIONS = {
    ".. deprecated::": "Устарело:",
    ".. deprecated ":  "Устарело:",
    "deprecated":      "Устарело",
    "Deprecated":      "Устарело",
    ".. note::":       "Примечание:",
    ".. note ":        "Примечание:",
    "Note:":           "Примечание:",
    "NOTE:":           "Примечание:",
    ".. warning::":    "Внимание:",
    ".. warning ":     "Внимание:",
    "Warning:":        "Внимание:",
    "WARNING:":        "Внимание:",
    ".. versionadded::":   "Добавлено в версии:",
    ".. versionchanged::": "Изменено в версии:",
    ".. seealso::":    "См. также:",
    "See also:":       "См. также:",
    "See Also:":       "См. также:",
    "Raises:":         "Исключения:",
    "Returns:":        "Возвращает:",
    "Parameters:":     "Параметры:",
    "Args:":           "Параметры:",
    "Example:":        "Пример:",
    "Examples:":       "Примеры:",
    "Todo:":           "TODO:",
}

def _normalize_docstring(text: str) -> str:
    """Переводит стандартные английские маркеры docstring на русский.
    Не трогает текст внутри URL (в скобках после markdown-ссылки).
    """
    if not text:
        return text
    import re
    # Разбиваем текст на части: URL и не-URL
    # Markdown ссылки вида [текст](url) — URL не трогаем
    parts = re.split(r'(\(https?://[^\)]+\))', text)
    result = []
    for i, part in enumerate(parts):
        if part.startswith('(http'):
            result.append(part)  # URL — не трогаем
        else:
            for eng, rus in _DOCSTRING_TRANSLATIONS.items():
                part = part.replace(eng, rus)
            result.append(part)
    return "".join(result).strip()


def _build_docstring(node) -> str:
    """Собирает docstring: берёт первый абзац стандартного docstring.
    Если docstring нет или он короткий — собирает Doc() из аннотаций параметров.
    """
    import ast as _ast
    base = _ast.get_docstring(node) or ""
    # Берём только первый абзац до ## Example, ## Parameters и т.д.
    if base:
        # Обрезаем по первому абзацу если после него идёт служебный маркер
        if "\n\n" in base:
            first_para = base[:base.index("\n\n")].strip()
            rest = base[base.index("\n\n"):].lstrip()
            markers = ["## Example", "## Parameters", "##", "Read more", "See also", "Note:", "Warning:"]
            if any(rest.startswith(m) for m in markers):
                base = first_para
        if base:
            return _normalize_docstring(base)
    # Если основного docstring нет — берём из Doc() аннотаций
    param_docs = _collect_param_docs(node)
    if param_docs:
        return _normalize_docstring(param_docs)
    return None


def _extract_doc_from_annotated(annotation_str: str) -> str:
    """Извлекает текст из Doc('...') внутри Annotated[T, Doc('...')]."""
    if not annotation_str or "Doc(" not in annotation_str:
        return ""
    import re
    # Ищем Doc('...') или Doc("...")
    m = re.search('Doc[(]([^)]{1,500})[)]', annotation_str)
    if m:
        return m.group(1).strip()
    return ""

def _collect_param_docs(node) -> str:
    """Собирает описания параметров из Annotated[T, Doc(...)] в одну строку."""
    import ast as _ast
    lines = []
    if not hasattr(node, "args"):
        return ""
    args = node.args
    all_args = args.posonlyargs + args.args + args.kwonlyargs
    if args.vararg:
        all_args.append(args.vararg)
    if args.kwarg:
        all_args.append(args.kwarg)
    for arg in all_args:
        if arg.annotation is None:
            continue
        ann_str = _ast.unparse(arg.annotation)
        doc = _extract_doc_from_annotated(ann_str)
        if doc and arg.arg not in ("self", "cls"):
            # Берём только первое предложение чтобы не раздувать
            first_sentence = doc.split(".")[0].strip()
            if first_sentence:
                lines.append(f"{arg.arg}: {first_sentence}")
    return "; ".join(lines)


class PythonExtractor(BaseExtractor):
    def build_tree(self, source: str, file_path: str, module_name: str) -> ApiNode:
        tree = ast.parse(source)

        root = ApiNode(
            node_type="module",
            name=module_name,
            qualname=module_name,
            lineno=1,
            end_lineno=max(1, len(source.splitlines())),
            file_path=file_path,
            language="python",
            docstring=_build_docstring(tree),
        )

        for node in tree.body:
            extracted = self._extract_node(
                node=node,
                parent_qualname=module_name,
                file_path=file_path,
                inside_class=False,
            )
            if extracted is not None:
                root.children.append(extracted)

        return root

    def _extract_node(
        self,
        node: ast.AST,
        parent_qualname: str,
        file_path: str,
        inside_class: bool,
    ) -> Optional[ApiNode]:
        if isinstance(node, ast.ClassDef):
            return self._extract_class(node, parent_qualname, file_path)

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return self._extract_function(node, parent_qualname, file_path, inside_class)

        return None

    def _extract_class(
        self,
        node: ast.ClassDef,
        parent_qualname: str,
        file_path: str,
    ) -> ApiNode:
        qualname = f"{parent_qualname}.{node.name}"

        class_node = ApiNode(
            node_type="class",
            name=node.name,
            qualname=qualname,
            lineno=node.lineno,
            end_lineno=getattr(node, "end_lineno", node.lineno),
            file_path=file_path,
            language="python",
            docstring=_build_docstring(node),
            decorators=self._collect_decorators(node.decorator_list),
        )

        for child in node.body:
            extracted = self._extract_node(
                node=child,
                parent_qualname=qualname,
                file_path=file_path,
                inside_class=True,
            )
            if extracted is not None:
                class_node.children.append(extracted)

        return class_node

    def _extract_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        parent_qualname: str,
        file_path: str,
        inside_class: bool,
    ) -> ApiNode:
        qualname = f"{parent_qualname}.{node.name}"

        return ApiNode(
            node_type="method" if inside_class else "function",
            name=node.name,
            qualname=qualname,
            lineno=node.lineno,
            end_lineno=getattr(node, "end_lineno", node.lineno),
            file_path=file_path,
            language="python",
            signature=self._build_signature(node),
            docstring=_build_docstring(node),
            decorators=self._collect_decorators(node.decorator_list),
            exceptions=self._collect_raises(node),
        )

    def _build_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> SignatureInfo:
        args = node.args
        parameters: List[ParameterInfo] = []

        regular_args = list(args.posonlyargs) + list(args.args)
        regular_defaults = [None] * (len(regular_args) - len(args.defaults)) + list(args.defaults)

        for arg, default in zip(args.posonlyargs, regular_defaults[: len(args.posonlyargs)]):
            parameters.append(
                ParameterInfo(
                    name=arg.arg,
                    kind="positional_only",
                    annotation=self._expr_to_str(arg.annotation),
                    default=self._expr_to_str(default),
                )
            )

        for arg, default in zip(args.args, regular_defaults[len(args.posonlyargs):]):
            parameters.append(
                ParameterInfo(
                    name=arg.arg,
                    kind="positional_or_keyword",
                    annotation=self._expr_to_str(arg.annotation),
                    default=self._expr_to_str(default),
                )
            )

        if args.vararg is not None:
            parameters.append(
                ParameterInfo(
                    name=args.vararg.arg,
                    kind="vararg",
                    annotation=self._expr_to_str(args.vararg.annotation),
                    default=None,
                )
            )

        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            parameters.append(
                ParameterInfo(
                    name=arg.arg,
                    kind="keyword_only",
                    annotation=self._expr_to_str(arg.annotation),
                    default=self._expr_to_str(default),
                )
            )

        if args.kwarg is not None:
            parameters.append(
                ParameterInfo(
                    name=args.kwarg.arg,
                    kind="kwarg",
                    annotation=self._expr_to_str(args.kwarg.annotation),
                    default=None,
                )
            )

        return SignatureInfo(
            name=node.name,
            parameters=parameters,
            return_annotation=self._expr_to_str(node.returns),
            is_async=isinstance(node, ast.AsyncFunctionDef),
        )

    def _collect_raises(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> List[ExceptionInfo]:
        exceptions: List[ExceptionInfo] = []

        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                exc_name = self._extract_exception_name(child.exc)
                if exc_name:
                    exceptions.append(ExceptionInfo(name=exc_name))
                else:
                    exceptions.append(ExceptionInfo(name="не удалось определить", details="MVP"))

        unique = []
        seen = set()
        for exc in exceptions:
            key = (exc.name, exc.details)
            if key not in seen:
                seen.add(key)
                unique.append(exc)

        return unique

    def _extract_exception_name(self, expr: Optional[ast.AST]) -> Optional[str]:
        if expr is None:
            return None

        if isinstance(expr, ast.Call):
            return self._expr_to_str(expr.func)

        return self._expr_to_str(expr)

    def _collect_decorators(self, decorators: List[ast.expr]) -> List[str]:
        result: List[str] = []
        for dec in decorators:
            text = self._expr_to_str(dec)
            if text:
                result.append(text)
        return result

    def _expr_to_str(self, expr: Optional[ast.AST]) -> Optional[str]:
        if expr is None:
            return None
        try:
            result = ast.unparse(expr)
            # Убираем Annotated[T, Doc('...')] -> T
            result = _strip_annotated(result)
            return result
        except Exception:
            return None


def render_signature(sig: SignatureInfo) -> str:
    parts: List[str] = []

    pos_only = [p for p in sig.parameters if p.kind == "positional_only"]
    pos_or_kw = [p for p in sig.parameters if p.kind == "positional_or_keyword"]
    vararg = next((p for p in sig.parameters if p.kind == "vararg"), None)
    kw_only = [p for p in sig.parameters if p.kind == "keyword_only"]
    kwarg = next((p for p in sig.parameters if p.kind == "kwarg"), None)

    def fmt_param(param: ParameterInfo) -> str:
        prefix = ""
        if param.kind == "vararg":
            prefix = "*"
        elif param.kind == "kwarg":
            prefix = "**"

        text = f"{prefix}{param.name}"
        if param.annotation:
            text += f": {param.annotation}"
        if param.default is not None:
            text += f" = {param.default}"
        return text

    for param in pos_only:
        parts.append(fmt_param(param))
    if pos_only:
        parts.append("/")

    for param in pos_or_kw:
        parts.append(fmt_param(param))

    if vararg:
        parts.append(fmt_param(vararg))
    elif kw_only:
        parts.append("*")

    for param in kw_only:
        parts.append(fmt_param(param))

    if kwarg:
        parts.append(fmt_param(kwarg))

    prefix = "async def" if sig.is_async else "def"
    result = f"{prefix} {sig.name}({', '.join(parts)})"
    if sig.return_annotation:
        result += f" -> {sig.return_annotation}"
    return result