from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tools.models import ApiNode, ModuleDocModel
from tools.extractors.python_extractor import render_signature


def render_spec_document(doc: ModuleDocModel, template_path: str) -> str:
    template = Path(template_path).read_text(encoding="utf-8")
    context = {
        "{{COMPONENT_NAME}}":        doc.component_name,
        "{{HEADER_BLOCK}}":          render_header_block(doc),
        "{{TABLE_OF_CONTENTS}}":     render_toc(doc),
        "{{OVERVIEW_INTRO}}":        render_overview_intro(doc),
        "{{INTRODUCTION}}":          render_introduction(doc),
        "{{NOTES}}":                 render_notes(enriched=getattr(doc, "enriched", False)),
        "{{LINKS}}":                 render_links(doc),
        "{{COMPONENT_DESCRIPTION}}": render_component_description(doc),
        "{{INTERFACE_TITLE}}":       render_interface_title(doc.root),
        "{{IDL_BLOCK}}":             render_idl_block(doc),
        "{{INTERFACE_SUMMARY}}":     render_interface_summary(doc.root),
        "{{FUNCTIONS_SECTION}}":     render_detailed_interface(doc.root),
        "{{ERROR_CODES_INTRO}}":     render_error_codes_intro(doc.root),
        "{{ERROR_CODES_TABLE}}":     render_error_codes_table(doc.root),
        "{{APPENDIX_A}}":            render_appendix_a(doc.root),
    }
    result = template
    for key, value in context.items():
        result = result.replace(key, value)
    return result


def render_header_block(doc: ModuleDocModel) -> str:
    espd   = doc.espd_code or "RU.—.XXXXX-XX"
    cid    = doc.cid or "—"
    url    = doc.marketplace_url or "—"
    desc   = doc.short_description or "Описание не указано."
    cat    = doc.component_use_category or "—"
    ctype  = doc.component_type or "MODULE"
    tags   = doc.tags or "—"
    commit = getattr(doc, "commit", "") or "—"

    lines = [
        "| Поле | Значение |", "|---|---|",
        "| **ЕСПД** | `{}` |".format(espd),
        "| **Имя компонента** | `{}` |".format(doc.component_name),
        "| **Краткое описание** | {} |".format(desc),
        "| **Component Use Category** | {} |".format(cat),
        "| **Component Type** | {} |".format(ctype),
        "| **CID** | `{}` |".format(cid),
        "| **Marketplace URL** | {} |".format(url),
        "| **Статус** | {} |".format(doc.status),
        "| **Дата изменения** | {} |".format(doc.date),
        "| **Версия** | {} |".format(doc.version),
        "| **Коммит** | `{}` |".format(commit),
        "| **Теги** | {} |".format(tags),
        "| **Источник кода** | `{}` |".format(doc.source_path),
        "",
    ]
    if doc.authors:
        lines += ["| Авторы | Компания |", "|---|---|"]
        orgs = doc.organizations or []
        for i, author in enumerate(doc.authors):
            org = orgs[i] if i < len(orgs) else "ПИРФ"
            lines.append("| {} | {} |".format(author, org))
    else:
        lines += ["| Авторы | Компания |", "|---|---|",
                  "| _(не указаны, используйте --authors)_ | ПИРФ |"]
    return "\n".join(lines)


def render_toc(doc: ModuleDocModel) -> str:
    root = doc.root
    name = doc.component_name
    lines = [
        "1. Обзор", "   1.1. Введение", "   1.2. Примечание", "   1.3. Ссылки",
        "2. Компонент {}".format(name),
        "   2.1. {} IDL".format(render_interface_title(root)),
        "   2.2. Состав интерфейса",
        "   2.3. Подробное описание интерфейса",
    ]
    idx = 1
    for child in root.children:
        if child.node_type == "class" and not child.name.startswith("_"):
            lines.append("      2.3.{}. Класс {}".format(idx, child.name))
            public = [m for m in child.children
                      if m.node_type == "method"
                      and m.name != "__init__"
                      and not m.name.startswith("_")]
            for j, m in enumerate(public, start=1):
                lines.append("         2.3.{}.{}. Метод {}".format(idx, j, m.name))
            idx += 1
        elif child.node_type == "function" and not child.name.startswith("_"):
            lines.append("      2.3.{}. Функция {}".format(idx, child.name))
            idx += 1
    lines += ["3. Коды ошибок", "Приложение А. Примеры использования"]
    return "<pre>\n{}\n</pre>".format("\n".join(lines))


def render_overview_intro(doc: ModuleDocModel) -> str:
    return "Данный документ описывает требования к реализации компонента `{}`.".format(doc.component_name)


def render_introduction(doc: ModuleDocModel) -> str:
    return (
        "Настоящий документ содержит автоматически сформированное описание "
        "программного компонента `{}` на основе анализа исходного кода. "
        "Документ отражает состав интерфейса, обнаруженные классы, функции, методы, "
        "их сигнатуры, параметры, возвращаемые значения и исключения."
    ).format(doc.component_name)


def render_notes(enriched: bool = False) -> str:
    if enriched:
        return (
            "Документ сформирован автоматически. "
            "Структурные данные извлечены из исходного кода статическим анализом. "
            "Текстовые описания сгенерированы языковой моделью на основе сигнатур и docstring."
        )
    return "Документ сформирован автоматически на основе статического анализа исходного кода."


def render_links(doc: ModuleDocModel) -> str:
    lines = ["Данный параграф содержит ссылки на компонент и на другую полезную информацию:"]
    if doc.marketplace_url and doc.marketplace_url != "—":
        lines += ["", "Доступен по адресу: {}".format(doc.marketplace_url)]
    if doc.links:
        lines += ["", doc.links]
    if len(lines) == 1:
        lines += ["", "—"]
    return "\n".join(lines)


def render_component_description(doc: ModuleDocModel) -> str:
    module_doc = safe_text(doc.root.docstring, "")
    desc = doc.short_description or module_doc or _build_fallback_component_desc(doc)
    return desc


def _build_fallback_component_desc(doc: ModuleDocModel) -> str:
    root = doc.root
    classes   = len([c for c in root.children
                     if c.node_type == "class" and not c.name.startswith("_")])
    functions = len([c for c in root.children
                     if c.node_type == "function" and not c.name.startswith("_")])
    methods   = count_nodes(root, "method")
    parts = []
    if classes:
        parts.append("{} {}".format(classes, pluralize_ru(classes, "класс", "класса", "классов")))
    if functions:
        parts.append("{} {}".format(functions, pluralize_ru(functions,
            "функция верхнего уровня", "функции верхнего уровня", "функций верхнего уровня")))
    if methods:
        parts.append("{} {}".format(methods, pluralize_ru(methods, "метод", "метода", "методов")))
    if not parts:
        return "В анализируемом модуле не обнаружены документируемые элементы интерфейса."
    return ("Описание компонента в docstring модуля отсутствует. "
            "По результатам анализа исходного кода обнаружено: {}.").format(", ".join(parts))


def render_interface_title(root: ApiNode) -> str:
    classes = [c for c in root.children
               if c.node_type == "class" and not c.name.startswith("_")]
    if not classes:
        return "IModule"
    for cls in classes:
        pub = [m for m in cls.children
               if m.node_type == "method" and not m.name.startswith("_") and m.name != "__init__"]
        if pub:
            return "I{}".format(cls.name)
    return "I{}".format(classes[0].name)


def render_idl_block(doc: ModuleDocModel) -> str:
    enriched_idl = getattr(doc, "enriched_idl", None)
    if enriched_idl and enriched_idl.strip():
        return "```idl\n{}\n```".format(enriched_idl.strip())
    root = doc.root
    classes   = [c for c in root.children
                 if c.node_type == "class" and not c.name.startswith("_")]
    functions = [c for c in root.children
                 if c.node_type == "function" and not c.name.startswith("_")]
    lines: List[str] = []
    for cls in classes:
        pub_methods = [m for m in cls.children
                       if m.node_type == "method"
                       and not m.name.startswith("__")
                       and not m.name.startswith("_")]
        if not pub_methods:
            continue
        lines.append("interface I{} {{".format(cls.name))
        lines.append("")
        for method in pub_methods:
            lines.append("    {};".format(render_signature_safe(method)))
        lines.append("}")
        lines.append("")
    for fn in functions:
        lines.append("{};".format(render_signature_safe(fn)))
    if not lines:
        return "```\n# Интерфейсные сущности не обнаружены\n```"
    return "```\n{}\n```".format("\n".join(lines))


def render_interface_summary(root: ApiNode) -> str:
    classes   = [c for c in root.children
                 if c.node_type == "class" and not c.name.startswith("_")]
    functions = [c for c in root.children
                 if c.node_type == "function" and not c.name.startswith("_")]
    methods_count = sum(
        len([x for x in cls.children
             if x.node_type == "method" and not x.name.startswith("_")])
        for cls in classes)
    lines = [
        "**Общая сводка:**", "",
        "- {} {}".format(len(classes), pluralize_ru(len(classes), "класс", "класса", "классов")),
        "- {} {}".format(len(functions), pluralize_ru(len(functions),
            "функция верхнего уровня", "функции верхнего уровня", "функций верхнего уровня")),
        "- {} {}".format(methods_count, pluralize_ru(methods_count, "метод", "метода", "методов")),
        "",
    ]
    if classes:
        lines.append("**Классы:**")
        lines.append("")
        for cls in classes:
            pub = len([x for x in cls.children
                       if x.node_type == "method"
                       and not x.name.startswith("_")
                       and x.name != "__init__"])
            lines.append("- `{}` — строка `{}`, публичных методов: `{}`".format(
                cls.name, cls.lineno, pub))
        lines.append("")
    if functions:
        lines.append("**Функции верхнего уровня:**")
        lines.append("")
        for fn in functions:
            lines.append("- `{}` — строка `{}`".format(render_signature_safe(fn), fn.lineno))
        lines.append("")
    if not classes and not functions:
        lines.append("Интерфейсные элементы не обнаружены.")
    return "\n".join(lines).rstrip()


def render_detailed_interface(root: ApiNode) -> str:
    lines: List[str] = []
    index = 1
    for child in root.children:
        if child.node_type == "class" and not child.name.startswith("_"):
            lines.extend(render_class_block(child, index)); index += 1
        elif child.node_type == "function" and not child.name.startswith("_"):
            lines.extend(render_function_block(child, index)); index += 1
    if not lines:
        return "Автоматически извлекаемые элементы интерфейса не обнаружены."
    return "\n".join(lines).rstrip()


def _is_dataclass(node: ApiNode) -> bool:
    return "dataclass" in node.decorators


def render_class_block(node: ApiNode, index: int) -> List[str]:
    lines: List[str] = []
    lines += [
        "#### 2.3.{}. Класс `{}`".format(index, node.name), "",
        "**Полное имя:** `{}`".format(node.qualname), "",
        "**Расположение:** `{}`".format(format_location(node)), "",
        "**Назначение:** {}".format(get_description(node)), "",
    ]
    lines += render_logic_block(node)
    if node.decorators:
        lines += ["**Декораторы класса:** {}".format(
            ", ".join("`{}`".format(x) for x in node.decorators)), ""]

    public_methods = [
        c for c in node.children
        if c.node_type == "method"
        and c.name != "__init__"
        and not c.name.startswith("_")
    ]
    lines.append("**Количество публичных методов:** `{}` {}".format(
        len(public_methods), pluralize_ru(len(public_methods), "метод", "метода", "методов")))
    lines.append("")

    if not _is_dataclass(node):
        init_method = next(
            (c for c in node.children if c.node_type == "method" and c.name == "__init__"), None)
        if init_method:
            lines += ["**Конструктор:**", "", "```python", render_example(init_method), "```", ""]

    if public_methods:
        lines += ["**Список публичных методов:**", ""]
        for i, m in enumerate(public_methods, start=1):
            lines.append("- `2.3.{}.{}. {}`".format(index, i, render_signature_safe(m)))
        lines.append("")
        for i, m in enumerate(public_methods, start=1):
            lines.extend(render_method_block(m, index, i))
    else:
        lines += ["Публичные методы не обнаружены.", ""]
    return lines


def render_method_block(node: ApiNode, class_index: int, method_index: int) -> List[str]:
    lines: List[str] = []
    lines += [
        "##### 2.3.{}.{}. Метод `{}`".format(class_index, method_index, node.name), "",
        "**Полное имя:** `{}`".format(node.qualname), "",
        "**Сигнатура:** `{}`".format(render_signature_safe(node)), "",
        "**Расположение:** `{}`".format(format_location(node)), "",
        "**Назначение:** {}".format(get_description(node)), "",
    ]
    lines += render_logic_block(node)
    if node.decorators:
        lines += ["**Декораторы:** {}".format(
            ", ".join("`{}`".format(x) for x in node.decorators)), ""]
    lines += ["**Параметры:**", ""]
    lines.extend(render_parameters(node, hide_internal=True))
    lines += ["", "**Возвращаемое значение:** {}".format(render_return_value(node)), "",
              "**Исключения:**", ""]
    lines.extend(render_exceptions(node))
    lines += ["", "**Пример использования:**", "", "```python", render_example(node), "```", ""]
    return lines


def render_function_block(node: ApiNode, index: int) -> List[str]:
    lines: List[str] = []
    lines += [
        "#### 2.3.{}. Функция `{}`".format(index, node.name), "",
        "**Полное имя:** `{}`".format(node.qualname), "",
        "**Сигнатура:** `{}`".format(render_signature_safe(node)), "",
        "**Расположение:** `{}`".format(format_location(node)), "",
        "**Назначение:** {}".format(get_description(node)), "",
    ]
    lines += render_logic_block(node)
    if node.decorators:
        lines += ["**Декораторы:** {}".format(
            ", ".join("`{}`".format(x) for x in node.decorators)), ""]
    lines += ["**Параметры:**", ""]
    lines.extend(render_parameters(node, hide_internal=False))
    lines += ["", "**Возвращаемое значение:** {}".format(render_return_value(node)), "",
              "**Исключения:**", ""]
    lines.extend(render_exceptions(node))
    lines += ["", "**Пример использования:**", "", "```python", render_example(node), "```", ""]
    return lines


def render_logic_block(node: ApiNode) -> List[str]:
    logic = getattr(node, 'logic', None)
    if not logic:
        return []
    return ["**Логика работы:** {}".format(logic), ""]


def render_parameters(node: ApiNode, hide_internal: bool) -> List[str]:
    if node.signature is None or not node.signature.parameters:
        return ["отсутствуют"]
    visible = [p for p in node.signature.parameters
               if not (hide_internal and p.name in ("self", "cls"))]
    if not visible:
        return ["отсутствуют"]
    lines = ["| Параметр | Тип | По умолчанию | Вид |", "|---|---|---|---|"]
    for param in visible:
        annotation = "`{}`".format(param.annotation) if param.annotation else "не указан"
        default    = "`{}`".format(param.default)    if param.default    else "обязательный"
        lines.append("| `{}` | {} | {} | {} |".format(
            param.name, annotation, default, map_param_kind(param.kind)))
    return lines


def render_return_value(node: ApiNode) -> str:
    if node.signature is None:
        return "не указано"
    if node.signature.return_annotation:
        return "`{}`".format(node.signature.return_annotation)
    return "не указано"


_EXCEPTION_HINTS = {
    "LookupError":         "запрошенный объект не найден",
    "ValueError":          "передано некорректное значение параметра",
    "TypeError":           "передан параметр недопустимого типа",
    "KeyError":            "ключ не найден в коллекции",
    "IndexError":          "индекс выходит за пределы допустимого диапазона",
    "AttributeError":      "объект не имеет указанного атрибута",
    "RuntimeError":        "ошибка выполнения операции",
    "NotImplementedError": "метод не реализован",
    "FileNotFoundError":   "указанный файл или путь не найден",
    "PermissionError":     "недостаточно прав для выполнения операции",
    "OSError":             "ошибка операционной системы",
    "IOError":             "ошибка ввода-вывода",
    "TimeoutError":        "превышено допустимое время ожидания",
    "ConnectionError":     "ошибка сетевого соединения",
    "StopIteration":       "итерация завершена",
    "OverflowError":       "результат выходит за пределы допустимого диапазона",
    "ZeroDivisionError":   "деление на ноль",
    "MemoryError":         "недостаточно памяти для выполнения операции",
    "RecursionError":      "превышена максимальная глубина рекурсии",
}


def render_exceptions(node: ApiNode) -> List[str]:
    if not node.exceptions:
        return ["- явные исключения не обнаружены"]
    lines = []
    for exc in node.exceptions:
        desc = exc.details if exc.details else _EXCEPTION_HINTS.get(exc.name, "исключение выброшено явно")
        lines.append("- `{}` — {}".format(exc.name, desc))
    return lines


def render_error_codes_intro(root: ApiNode) -> str:
    collected = collect_exception_sources(root)
    if not collected:
        return ("По результатам автоматического анализа явные пользовательские исключения "
                "в коде не обнаружены. Ниже приведены стандартные заглушки.")
    return ("По результатам автоматического анализа в коде обнаружены исключения, "
            "которые явно используются в операторах `raise`.\n\n"
            "Следующая таблица содержит коды ошибок:")


def render_error_codes_table(root: ApiNode) -> str:
    collected = collect_exception_sources(root)
    lines = ["| Код ошибки | Значение | Описание |", "|---|---|---|"]
    if not collected:
        lines += [
            "| `ERR_ECO_SUCCESES`          | `0x0000` | Выполнено успешно. Ошибок нет. |",
            "| `ERR_ECO_UNEXPECTED`        | `0xFFFF` | Непредвиденное условие. |",
            "| `ERR_ECO_POINTER`           | `0xFFEE` | Передано неправильное значение указателя. |",
            "| `ERR_ECO_NOINTERFACE`       | `0xFFED` | Такой интерфейс не поддерживается. |",
            "| `ERR_ECO_COMPONENT_NOTFOUND`| `0xFFE9` | Компонент не найден. |",
        ]
        return "\n".join(lines)
    lines += [
        "| `ERR_ECO_SUCCESES`   | `0x0000` | Выполнено успешно. Ошибок нет. |",
        "| `ERR_ECO_UNEXPECTED` | `0xFFFF` | Непредвиденное условие. |",
    ]
    for exc_name, owners in collected:
        hint = _EXCEPTION_HINTS.get(exc_name, "исключение выброшено явно")
        lines.append("| `{}` | — | {}. Обнаружено в: `{}`. |".format(
            exc_name, hint.capitalize(), ", ".join(owners)))
    return "\n".join(lines)


def render_appendix_a(root: ApiNode) -> str:
    examples: List[str] = []
    index = 1
    for child in root.children:
        if child.node_type == "class" and not child.name.startswith("_"):
            for method in child.children:
                if (method.node_type != "method"
                        or method.name == "__init__"
                        or method.name.startswith("_")):
                    continue
                examples += ["### А.{} `{}`".format(index, method.qualname), "",
                             "```python", render_example(method), "```", ""]
                index += 1
        elif child.node_type == "function" and not child.name.startswith("_"):
            examples += ["### А.{} `{}`".format(index, child.qualname), "",
                         "```python", render_example(child), "```", ""]
            index += 1
    if not examples:
        return "Примеры использования отсутствуют."
    return "\n".join(examples).rstrip()


def render_example(node: ApiNode) -> str:
    if node.signature is None:
        return "# пример недоступен"

    if node.node_type == "method" and node.name == "__init__":
        class_name = extract_class_name(node.qualname)
        init_args = []
        pre_lines = []
        for p in node.signature.parameters:
            if p.name in ("self", "cls"):
                continue
            val, pre = _param_value_and_pre(p.annotation, p.default, p.kind, p.name)
            pre_lines.extend(pre)
            init_args.append(val)
        result = "\n".join(pre_lines)
        if result:
            result += "\n"
        result += "obj = {}({})".format(class_name, ", ".join(init_args))
        return result

    positional_args: List[str] = []
    keyword_args: List[str] = []
    pre_lines: List[str] = []

    for p in node.signature.parameters:
        if node.node_type == "method" and p.name in ("self", "cls"):
            continue
        val, pre = _param_value_and_pre(p.annotation, p.default, p.kind, p.name)
        pre_lines.extend(pre)
        if p.kind == "keyword_only":
            keyword_args.append("{}={}".format(p.name, val))
        elif p.kind == "vararg":
            positional_args.extend(
                ["'tag1'", "'tag2'"] if (p.annotation and "str" in p.annotation.lower()) else ["1", "2"])
        elif p.kind == "kwarg":
            keyword_args.append("key='value'")
        else:
            positional_args.append(val)

    call_args = ", ".join(positional_args + keyword_args)
    pre = ("\n".join(pre_lines) + "\n") if pre_lines else ""

    if node.node_type == "method":
        class_name = extract_class_name(node.qualname)
        if "staticmethod" in node.decorators:
            return "{}result = {}.{}({})".format(pre, class_name, node.name, call_args)
        if "classmethod" in node.decorators:
            return "{}result = {}.{}()".format(pre, class_name, node.name)
        constructor_args = infer_constructor_args_from_method(node)
        return "{}obj = {}({})\nresult = obj.{}({})".format(
            pre, class_name, ", ".join(constructor_args), node.name, call_args)

    if node.signature.is_async:
        return "{}result = await {}({})".format(pre, node.name, call_args)
    return "{}result = {}({})".format(pre, node.name, call_args)


def _param_value_and_pre(
    annotation: Optional[str],
    default: Optional[str],
    kind: str,
    param_name: str,
) -> Tuple[str, List[str]]:
    if kind == "vararg":
        ann = annotation or ""
        return ("'tag1', 'tag2'" if "str" in ann.lower() else "1, 2"), []
    if kind == "kwarg":
        return "key='value'", []

    lower_name = param_name.lower()

    name_hints = {
        "endpoint":     "'http://example.com'",
        "path":         "'output.json'",
        "email":        "'user@example.com'",
        "name":         "'Alice'",
        "url":          "'http://example.com'",
        "host":         "'localhost'",
        "port":         "8080",
        "token":        "'secret-token'",
        "key":          "'key'",
        "timeout":      "30",
        "snapshot_dir": "'snapshots'",
        "module_name":  "'example_module'",
        "change_type":  "'added'",
        "is_complex":   "False",
    }
    if lower_name in name_hints:
        return name_hints[lower_name], []

    if default not in (None, ""):
        return default, []

    if annotation is None:
        return "None", []

    ann = annotation.lower()

    if "list" in ann:
        if "dict" in ann: return "[]", []
        if "int"  in ann: return "[1, 2, 3]", []
        if "str"  in ann: return "['a', 'b']", []
        return "[]", []
    if "dict"   in ann: return "{}", []
    if "set"    in ann: return "set()", []
    if "tuple"  in ann: return "()", []
    if "int"    in ann: return "1", []
    if "float"  in ann: return "1.0", []
    if "str"    in ann: return "'example'", []
    if "bool"   in ann: return "False", []
    if "bytes"  in ann: return "b''", []
    if "path"   in ann: return "Path('.')", []
    if "optional" in ann: return "None", []

    type_name = annotation.split("[")[0].strip()
    var_name = param_name
    pre_line = "# {}: создайте объект типа {}".format(var_name, type_name)
    return var_name, [pre_line]


def render_signature_safe(node: ApiNode) -> str:
    if node.signature is None:
        return node.name
    return render_signature(node.signature)


def format_location(node: ApiNode) -> str:
    if node.end_lineno and node.end_lineno != node.lineno:
        return "{}:{}-{}".format(node.file_path, node.lineno, node.end_lineno)
    return "{}:{}".format(node.file_path, node.lineno)


def get_description(node: ApiNode) -> str:
    text = safe_text(node.docstring, "")
    return text if text else build_fallback_description(node)


def build_fallback_description(node: ApiNode) -> str:
    name = node.name.lower()
    if node.node_type == "class":
        return "Класс `{}` выделен автоматически по структуре исходного кода.".format(node.name)
    prefixes = {
        "get_":       lambda s: "Возвращает значение, связанное с `{}`.".format(s),
        "set_":       lambda s: "Устанавливает значение, связанное с `{}`.".format(s),
        "is_":        lambda s: "Проверяет условие `{}` и возвращает логический результат.".format(s),
        "has_":       lambda s: "Проверяет наличие `{}`.".format(s),
        "create_":    lambda s: "Создаёт объект или данные, связанные с `{}`.".format(s),
        "build_":     lambda s: "Формирует результат, связанный с `{}`.".format(s),
        "process_":   lambda s: "Обрабатывает данные, связанные с `{}`.".format(s),
        "fetch_":     lambda s: "Получает данные, связанные с `{}`.".format(s),
        "load_":      lambda s: "Загружает данные, связанные с `{}`.".format(s),
        "save_":      lambda s: "Сохраняет данные, связанные с `{}`.".format(s),
        "validate_":  lambda s: "Проверяет корректность `{}`.".format(s),
        "merge_":     lambda s: "Объединяет данные, связанные с `{}`.".format(s),
        "normalize_": lambda s: "Нормализует данные `{}`.".format(s),
    }
    for prefix, fn in prefixes.items():
        if name.startswith(prefix):
            return fn(name[len(prefix):])
    if node.signature is not None and node.signature.return_annotation:
        return "Элемент `{}` выделен автоматически; возвращает `{}`.".format(
            node.name, node.signature.return_annotation)
    return "Элемент `{}` выделен автоматически по структуре исходного кода.".format(node.name)


def map_param_kind(kind: str) -> str:
    return {
        "positional_only":       "только позиционный",
        "positional_or_keyword": "позиционный или именованный",
        "vararg":                "произвольное число позиционных (*args)",
        "keyword_only":          "только именованный",
        "kwarg":                 "произвольный набор именованных (**kwargs)",
    }.get(kind, kind)


def extract_class_name(qualname: str) -> str:
    parts = qualname.split(".")
    return parts[-2] if len(parts) >= 2 else "ClassName"


def infer_constructor_args_from_method(node: ApiNode) -> List[str]:
    return ["[]"] if extract_class_name(node.qualname).endswith("Service") else []


def safe_text(value, fallback: str) -> str:
    if value is None:
        return fallback
    text = value.strip()
    return text if text else fallback


def count_nodes(root: ApiNode, node_type: str) -> int:
    count = 0
    stack = [root]
    while stack:
        node = stack.pop()
        if node.node_type == node_type:
            count += 1
        stack.extend(node.children)
    return count


def collect_exception_sources(root: ApiNode):
    mapping: Dict[str, List[str]] = {}
    stack = [root]
    while stack:
        node = stack.pop()
        if node.node_type in ("function", "method"):
            for exc in node.exceptions:
                owners = mapping.setdefault(exc.name, [])
                if node.qualname not in owners:
                    owners.append(node.qualname)
        stack.extend(node.children)
    return [(name, mapping[name]) for name in sorted(mapping)]


def pluralize_ru(number: int, one: str, two: str, five: str) -> str:
    n  = abs(number) % 100
    n1 = n % 10
    if 10 < n < 20: return five
    if 1 < n1 < 5:  return two
    if n1 == 1:     return one
    return five