from __future__ import annotations

import argparse
import os
import subprocess
from datetime import date
from pathlib import Path
from typing import Iterator, List, Optional

from tools.extractors.c_extractor import CExtractor
from tools.extractors.python_extractor import PythonExtractor
from tools.language_detection import detect_language
from tools.mode_selector import choose_mode
from tools.models import ModuleDocModel
from tools.render_llm_context import render_llm_context_document
from tools.render_spec_md import render_spec_document
from tools.llm_enricher import enrich_with_llm
from tools.diff_engine import diff_with_snapshot, save_snapshot
from tools.git_diff import get_changed_qualnames, update_commit_in_fodt
from tools.fodt_registry import (
    save_fodt_hash, check_fodt_changed, backup_fodt,
    find_user_changed_sections, merge_section_with_llm,
    extract_function_sections,
)


SUPPORTED_SOURCE_EXTENSIONS = {".py", ".c", ".h"}


def format_ru_date() -> str:
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря",
    ]
    d = date.today()
    return "{} {} {}".format(d.day, months[d.month - 1], d.year)


def get_git_commit_hash() -> str:
    """Возвращает короткий хэш текущего git коммита или пустую строку."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def choose_extractor(language: str):
    if language == "python":
        return PythonExtractor()
    if language == "c":
        return CExtractor()
    return None


def iter_source_files(source_root: Path) -> Iterator[Path]:
    for path in source_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SOURCE_EXTENSIONS:
            if not should_skip(path):
                yield path


def should_skip(path: Path) -> bool:
    skip_parts = {".git", ".venv", "venv", "__pycache__", "node_modules", "docs"}
    return any(part in skip_parts for part in path.parts)


def module_name_from_path(source_root: Path, file_path: Path) -> str:
    relative = file_path.relative_to(source_root)
    return ".".join(relative.with_suffix("").parts)


def make_output_path(output_root: Path, module_name: str, mode: str) -> Path:
    stem = module_name.replace(".", "_")
    if mode == "llm_context":
        return output_root / "llm_{}.md".format(stem)
    return output_root / "spec_{}.md".format(stem)


def _auto_short_description(
    component_name: str,
    component_type: str,
    root_docstring: str,
) -> str:
    if root_docstring:
        first = root_docstring.strip().splitlines()[0].strip()
        if first and len(first) <= 200:
            return first

    templates = {
        "APPLICATION": "Приложение для автоматической обработки данных.",
        "MODULE":      "Программный модуль.",
        "COMPONENT":   "Программный компонент.",
        "LIBRARY":     "Программная библиотека.",
        "SERVICE":     "Программный сервис.",
    }
    ctype = (component_type or "MODULE").upper()
    return templates.get(ctype, "Программный компонент.")


def build_doc_model(
    file_path: Path,
    source_root: Path,
    version: str,
    status: str,
    espd_code: str,
    cid: str,
    marketplace_url: str,
    short_description: str,
    component_use_category: str,
    component_type: str,
    tags: str,
    authors: List[str],
    organizations: List[str],
    links: str,
    component_name: str = "",
    commit: str = "",
) -> Optional[ModuleDocModel]:
    source = file_path.read_text(encoding="utf-8")
    language = detect_language(str(file_path), source)

    extractor = choose_extractor(language)
    if extractor is None:
        return None

    module_name     = module_name_from_path(source_root, file_path)
    normalized_path = str(file_path).replace("\\", "/")

    tree = extractor.build_tree(
        source=source,
        file_path=normalized_path,
        module_name=module_name,
    )

    effective_name = (
        component_name.strip()
        or _name_from_docstring(tree)
        or module_name
    )

    effective_desc = short_description.strip() or _auto_short_description(
        effective_name,
        component_type,
        (tree.docstring or "").strip(),
    )

    return ModuleDocModel(
        component_name=effective_name,
        source_path=normalized_path,
        language=language,
        version=version,
        status=status,
        date=format_ru_date(),
        root=tree,
        espd_code=espd_code,
        cid=cid,
        marketplace_url=marketplace_url,
        short_description=effective_desc,
        component_use_category=component_use_category,
        component_type=component_type,
        tags=tags,
        authors=authors,
        organizations=organizations,
        links=links,
        commit=commit,
    )


def _name_from_docstring(tree) -> str:
    doc = (tree.docstring or "").strip()
    if not doc:
        return ""
    first_line = doc.splitlines()[0].strip()
    if len(first_line) <= 80 and not first_line.endswith("."):
        return first_line
    return ""




def _get_last_pipeline_fodt(fodt_path: str) -> str:
    """
    Возвращает содержимое fodt из последнего запуска пайплайна.
    Если есть .bak — читаем его (он был сохранён до ручных правок).
    Иначе читаем текущий файл.
    """
    bak_path = fodt_path + ".bak"
    if Path(bak_path).exists():
        return Path(bak_path).read_text(encoding="utf-8")
    return Path(fodt_path).read_text(encoding="utf-8")

def process_file(
    file_path: Path,
    source_root: Path,
    template_path: Path,
    output_root: Path,
    version: str,
    status: str,
    mode: str,
    espd_code: str,
    cid: str,
    marketplace_url: str,
    short_description: str,
    component_use_category: str,
    component_type: str,
    tags: str,
    authors: List[str],
    organizations: List[str],
    links: str,
    enrich: bool = False,
    api_key: str = "",
    component_name: str = "",
    fodt_template: str = "",
    commit: str = "",
) -> Optional[Path]:
    doc_model = build_doc_model(
        file_path=file_path,
        source_root=source_root,
        version=version,
        status=status,
        espd_code=espd_code,
        cid=cid,
        marketplace_url=marketplace_url,
        short_description=short_description,
        component_use_category=component_use_category,
        component_type=component_type,
        tags=tags,
        authors=authors,
        organizations=organizations,
        links=links,
        component_name=component_name,
        commit=commit,
    )

    if doc_model is None:
        return None

    selected_mode = choose_mode(mode)

    if selected_mode == "auto":
        selected_mode = "clean"
        if api_key or os.environ.get("OPENROUTER_API_KEY", ""):
            enrich = True

    diff_result, is_first_run = diff_with_snapshot(doc_model)
    if diff_result.has_changes() or is_first_run:
        print("[DIFF] {}".format(diff_result.summary()))
    else:
        print("[DIFF] Изменений не обнаружено.")

    # --- Режим update: патчим только изменившиеся секции ---
    output_path = make_output_path(output_root, doc_model.component_name, selected_mode)
    if selected_mode == "update":
        fodt_out = output_root / f"spec_{doc_model.component_name}.fodt"
        changed_qualnames, needs_update = get_changed_qualnames(
            fodt_path=str(fodt_out),
            source_file=str(file_path),
            root=doc_model.root,
            current_commit=commit,
        )
        if not needs_update and fodt_out.exists():
            print("[UPDATE] Изменений нет — fodt актуален")
            return fodt_out.with_suffix(".md")

        # Обогащаем только изменившиеся сущности через LLM
        if changed_qualnames and (enrich or os.environ.get("OPENROUTER_API_KEY")):
            print(f"[UPDATE] Обогащаем {len(changed_qualnames)} изменившихся сущностей...")
            doc_model = enrich_with_llm(
                doc_model,
                api_key=api_key or None,
                verbose=True,
                target_qualnames=changed_qualnames,
            )

        # Пересобираем md (нужен для актуального data)
        rendered = render_spec_document(doc_model, str(template_path))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")

        if fodt_out.exists():
            # Проверяем ручные изменения пользователя
            user_changed = check_fodt_changed(str(fodt_out))
            user_changed_sections = []

            if user_changed:
                print("[UPDATE] Пользователь изменил fodt вручную — сохраняем резервную копию")
                backup_fodt(str(fodt_out))

                # Читаем текущую (изменённую) версию fodt
                current_fodt = fodt_out.read_text(encoding="utf-8")

                # Генерируем версию пайплайна (ещё не записываем)
                from tools.fodt_filler import parse_markdown, update_fodt_sections
                md_text = output_path.read_text(encoding="utf-8")
                data = parse_markdown(md_text)

                # Применяем изменения пайплайна во временную копию
                import tempfile, shutil
                tmp_fodt = fodt_out.with_suffix(".tmp.fodt")
                shutil.copy(str(fodt_out), str(tmp_fodt))
                update_fodt_sections(str(tmp_fodt), data, changed_qualnames)

                pipeline_fodt = tmp_fodt.read_text(encoding="utf-8")

                # Находим пересечение: секции которые изменил пользователь
                # И которые также меняет пайплайн
                user_edited = find_user_changed_sections(
                    _get_last_pipeline_fodt(str(fodt_out)),
                    current_fodt,
                )
                pipeline_changes = {fn["name"] for fn in data.get("functions", [])
                                    if fn.get("qualname") in changed_qualnames
                                    or fn.get("name") in {q.split(".")[-1] for q in changed_qualnames}}

                overlap = set(user_edited) & pipeline_changes

                if overlap:
                    print(f"[UPDATE] Пересечение правок в секциях: {', '.join(overlap)}")
                    # Для каждой пересекающейся секции — merge через LLM
                    user_secs = extract_function_sections(current_fodt)
                    pipe_secs = extract_function_sections(pipeline_fodt)

                    for fn_name in overlap:
                        if fn_name in user_secs and fn_name in pipe_secs:
                            merged = merge_section_with_llm(
                                fn_name,
                                user_secs[fn_name],
                                pipe_secs[fn_name],
                                api_key=api_key or None,
                            )
                            # Применяем merged текст как новое описание функции
                            for fn in data.get("functions", []):
                                if fn["name"] == fn_name:
                                    fn["description"] = merged
                                    break
                else:
                    print("[UPDATE] Пересечений нет — пользовательские правки сохранятся")

                tmp_fodt.unlink(missing_ok=True)

            else:
                from tools.fodt_filler import parse_markdown, update_fodt_sections
                md_text = output_path.read_text(encoding="utf-8")
                data = parse_markdown(md_text)

            if not user_changed:
                update_fodt_sections(str(fodt_out), data, changed_qualnames)
            update_commit_in_fodt(str(fodt_out), commit)
            save_fodt_hash(str(fodt_out), commit)
            print(f"[UPDATE] fodt обновлён: {fodt_out}")
        else:
            # fodt ещё не существует — создаём с нуля
            print("[UPDATE] fodt не найден — создаём с нуля")
            if fodt_template:
                from tools.fodt_filler import parse_markdown, fill_template
                md_text = output_path.read_text(encoding="utf-8")
                tmpl_text = Path(fodt_template).read_text(encoding="utf-8")
                data = parse_markdown(md_text)
                filled = fill_template(tmpl_text, data)
                fodt_out.write_text(filled, encoding="utf-8")
                print(f"[FODT] Создан: {fodt_out}")

        save_snapshot(doc_model)
        return output_path

    if enrich and selected_mode != "llm_context":
        llm_targets = diff_result.needs_llm_entities()
        if llm_targets:
            print("[LLM] Обогащаем {} сущностей через OpenRouter...".format(len(llm_targets)))
            doc_model = enrich_with_llm(
                doc_model,
                api_key=api_key or None,
                verbose=True,
                target_qualnames={n.qualname for n in llm_targets},
            )
        else:
            print("[LLM] LLM не требуется — нет новых или сложных изменений.")
            from tools.llm_enricher import enrich_idl_with_llm
            doc_model = enrich_idl_with_llm(
                doc_model,
                api_key=api_key or None,
                verbose=True,
            )

    if selected_mode == "llm_context":
        rendered = render_llm_context_document(doc_model)
    else:
        rendered = render_spec_document(doc_model, str(template_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

    if selected_mode != "llm_context":
        save_snapshot(doc_model)

    # --- Генерация .fodt если передан шаблон ---
    if fodt_template and selected_mode != "llm_context":
        fodt_path = Path(fodt_template)
        if not fodt_path.exists():
            print("[FODT] Шаблон не найден: {}".format(fodt_template))
        else:
            try:
                from tools.fodt_filler import parse_markdown, fill_template
                md_text = output_path.read_text(encoding="utf-8")
                template_text = fodt_path.read_text(encoding="utf-8")
                data = parse_markdown(md_text)
                filled = fill_template(template_text, data)
                fodt_out = output_path.with_suffix(".fodt")
                fodt_out.write_text(filled, encoding="utf-8")
                save_fodt_hash(str(fodt_out), commit)
                print("[FODT] Сохранён: {}".format(fodt_out))
            except Exception as e:
                print("[FODT] Ошибка: {}".format(e))

    return output_path


def parse_list_arg(value: str) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Markdown specifications from source code."
    )

    parser.add_argument("--source-root",   default="work")
    parser.add_argument("--template",      default="templates/spec_component_ru.md")
    parser.add_argument("--output-root",   default="docs")
    parser.add_argument("--version",       default="0.1")
    parser.add_argument("--status",        default="черновик")
    parser.add_argument(
        "--mode", default="clean",
        choices=["clean", "update", "llm_context", "auto"],
    )
    parser.add_argument("--component-name", default="")
    parser.add_argument("--espd-code",      default="")
    parser.add_argument("--cid",            default="")
    parser.add_argument("--marketplace-url", default="")
    parser.add_argument("--short-description", default="")
    parser.add_argument("--component-use-category", default="")
    parser.add_argument("--component-type", default="MODULE")
    parser.add_argument("--tags",           default="")
    parser.add_argument("--authors",        default="")
    parser.add_argument("--organizations",  default="")
    parser.add_argument("--links",          default="")
    parser.add_argument("--enrich",         action="store_true")
    parser.add_argument("--api-key",        default="")
    parser.add_argument(
        "--fodt",
        default="",
        metavar="TEMPLATE.fodt",
        help="Путь к .fodt шаблону. Если указан — генерирует .fodt рядом с .md",
    )

    args = parser.parse_args()

    source_root   = Path(args.source_root)
    template_path = Path(args.template)
    output_root   = Path(args.output_root)

    if not source_root.exists():
        raise FileNotFoundError("Source root not found: {}".format(source_root))

    if args.mode == "clean" and not template_path.exists():
        raise FileNotFoundError("Template not found: {}".format(template_path))

    authors       = parse_list_arg(args.authors)
    organizations = parse_list_arg(args.organizations)

    # Автоматически получаем хэш текущего коммита
    commit = get_git_commit_hash()
    if commit:
        print("[GIT] Текущий коммит: {}".format(commit))

    generated = []

    for file_path in iter_source_files(source_root):
        result = process_file(
            file_path=file_path,
            source_root=source_root,
            template_path=template_path,
            output_root=output_root,
            version=args.version,
            status=args.status,
            mode=args.mode,
            espd_code=args.espd_code,
            cid=args.cid,
            marketplace_url=args.marketplace_url,
            short_description=args.short_description,
            component_use_category=args.component_use_category,
            component_type=args.component_type,
            tags=args.tags,
            authors=authors,
            organizations=organizations,
            links=args.links,
            enrich=args.enrich,
            api_key=args.api_key,
            component_name=args.component_name,
            fodt_template=args.fodt,
            commit=commit,
        )
        if result is not None:
            generated.append(result)

    print("Generated files:")
    for path in generated:
        print("  -", path)


if __name__ == "__main__":
    main()