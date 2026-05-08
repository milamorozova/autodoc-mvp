from __future__ import annotations

"""
tools/fodt_registry.py

Реестр хэшей fodt файлов.
Отслеживает ручные изменения пользователя и помогает их сохранить
при обновлении документа пайплайном.
"""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


REGISTRY_PATH = "registry.json"


# ---------------------------------------------------------------------------
# Хэширование файла
# ---------------------------------------------------------------------------

def compute_file_hash(file_path: str) -> Optional[str]:
    """Возвращает MD5 хэш файла или None если файл не найден."""
    path = Path(file_path)
    if not path.exists():
        return None
    content = path.read_bytes()
    return hashlib.md5(content).hexdigest()


# ---------------------------------------------------------------------------
# Сохранение и чтение реестра
# ---------------------------------------------------------------------------

def save_fodt_hash(fodt_path: str, commit: str, registry_path: str = REGISTRY_PATH) -> None:
    """Сохраняет хэш fodt файла в реестр после запуска пайплайна."""
    file_hash = compute_file_hash(fodt_path)
    if not file_hash:
        print(f"[REGISTRY] Файл не найден: {fodt_path}")
        return

    registry = _load_registry(registry_path)
    key = Path(fodt_path).name
    registry[key] = {
        "hash":      file_hash,
        "commit":    commit,
        "timestamp": datetime.now().isoformat(),
        "path":      fodt_path,
    }
    _save_registry(registry, registry_path)
    print(f"[REGISTRY] Хэш сохранён для {key}: {file_hash[:8]}...")


def get_fodt_record(fodt_path: str, registry_path: str = REGISTRY_PATH) -> Optional[dict]:
    """Возвращает запись реестра для данного fodt или None."""
    registry = _load_registry(registry_path)
    key = Path(fodt_path).name
    return registry.get(key)


def check_fodt_changed(fodt_path: str, registry_path: str = REGISTRY_PATH) -> bool:
    """
    Проверяет изменился ли fodt файл с момента последнего запуска пайплайна.
    Возвращает True если файл изменился вручную.
    """
    record = get_fodt_record(fodt_path, registry_path)
    if not record:
        return False  # нет записи — считаем что не изменялся

    current_hash = compute_file_hash(fodt_path)
    if not current_hash:
        return False

    changed = current_hash != record["hash"]
    if changed:
        print(f"[REGISTRY] Обнаружены ручные изменения в {Path(fodt_path).name}")
    return changed


# ---------------------------------------------------------------------------
# Извлечение секций из fodt для сравнения
# ---------------------------------------------------------------------------

def extract_function_sections(fodt_content: str) -> Dict[str, str]:
    """
    Извлекает секции функций/методов/классов из fodt.
    Возвращает словарь: имя_функции → XML блок секции.
    """
    sections = {}

    # Ищем заголовки секций вида: 2.1.N. Функция/Метод/Класс <T29>name</T29>
    header_pattern = re.compile(
        r'<text:h[^>]*>2\.1\.(\d+)\. (?:Функция|Метод|Класс) '
        r'<text:span text:style-name="T29">([^<]+)</text:span></text:h>'
    )

    matches = list(header_pattern.finditer(fodt_content))

    for i, match in enumerate(matches):
        name = match.group(2)
        # Начало блока — list-тег перед заголовком
        block_start = fodt_content.rfind('<text:list text:continue-numbering="true"', 0, match.start())
        if block_start == -1:
            continue

        # Конец блока — начало следующего list-блока или секция 3
        if i + 1 < len(matches):
            next_block = fodt_content.rfind(
                '<text:list text:continue-numbering="true"',
                0, matches[i + 1].start()
            )
            block_end = next_block if next_block > block_start else matches[i + 1].start()
        else:
            # Последняя функция — ищем якорь секции 3
            section3 = fodt_content.find('__RefHeading___Toc72889_228845717')
            if section3 != -1:
                block_end = fodt_content.rfind('<text:list', 0, section3)
                if block_end <= block_start:
                    block_end = section3
            else:
                block_end = len(fodt_content)

        sections[name] = fodt_content[block_start:block_end]

    return sections


def find_user_changed_sections(
    old_fodt_content: str,
    new_fodt_content: str,
) -> List[str]:
    """
    Сравнивает два fodt и возвращает имена секций которые изменились.
    old_fodt_content — версия после последнего запуска пайплайна
    new_fodt_content — текущая версия (возможно с ручными правками)
    """
    old_sections = extract_function_sections(old_fodt_content)
    new_sections = extract_function_sections(new_fodt_content)

    changed = []
    for name in new_sections:
        if name in old_sections and old_sections[name] != new_sections[name]:
            changed.append(name)

    return changed


# ---------------------------------------------------------------------------
# Сохранение резервной копии
# ---------------------------------------------------------------------------

def backup_fodt(fodt_path: str) -> Optional[str]:
    """Сохраняет резервную копию fodt как .bak файл."""
    path = Path(fodt_path)
    if not path.exists():
        return None
    bak_path = str(path) + ".bak"
    path.read_bytes()
    Path(bak_path).write_bytes(path.read_bytes())
    print(f"[REGISTRY] Резервная копия сохранена: {bak_path}")
    return bak_path


# ---------------------------------------------------------------------------
# Слияние секций через LLM
# ---------------------------------------------------------------------------

def merge_section_with_llm(
    fn_name: str,
    user_section_xml: str,
    pipeline_section_xml: str,
    api_key: Optional[str] = None,
) -> str:
    """
    Использует LLM чтобы объединить пользовательские правки
    с обновлённым содержимым от пайплайна.

    Возвращает XML блок для вставки в fodt.
    """
    from tools.llm_client import call_llm

    # Извлекаем читаемый текст из XML для промпта
    user_text = _xml_to_plain(user_section_xml)
    pipeline_text = _xml_to_plain(pipeline_section_xml)

    prompt = "\n".join([
        f"Секция документации для функции `{fn_name}` была изменена двумя способами.",
        "",
        "1. Пользователь вручную отредактировал документ и получилась такая версия:",
        "```",
        user_text,
        "```",
        "",
        "2. Автоматический пайплайн сгенерировал обновлённую версию на основе нового кода:",
        "```",
        pipeline_text,
        "```",
        "",
        "Объедини эти две версии по следующим правилам:",
        "- Используй обновлённые технические данные из версии пайплайна (сигнатура, параметры, расположение)",
        "- Сохрани пользовательские улучшения текста если они не противоречат новому коду",
        "- Если пользователь улучшил описание назначения или логики — используй его версию",
        "- Если пайплайн обновил сигнатуру или параметры — используй версию пайплайна",
        "- Верни ТОЛЬКО итоговый текст секции без XML тегов и пояснений",
    ])

    try:
        merged_text = call_llm(prompt, api_key=api_key)
        print(f"[REGISTRY] Секция {fn_name} объединена через LLM")
        # Возвращаем текст — вызывающий код сам сформирует XML через odf_fn
        return merged_text.strip()
    except Exception as e:
        print(f"[REGISTRY] Ошибка LLM merge для {fn_name}: {e} — используем версию пайплайна")
        return pipeline_text


def _xml_to_plain(xml: str) -> str:
    """Убирает XML теги, оставляет только текст."""
    text = re.sub(r'<[^>]+>', ' ', xml)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _load_registry(registry_path: str) -> dict:
    path = Path(registry_path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_registry(registry: dict, registry_path: str) -> None:
    path = Path(registry_path)
    path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )