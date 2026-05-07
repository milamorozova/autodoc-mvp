from __future__ import annotations

"""
tools/git_diff.py

Утилиты для получения изменений из git diff и определения
какие сущности AST были затронуты.
"""

import re
import subprocess
from pathlib import Path
from typing import List, Optional, Set, Tuple

from tools.models import ApiNode


# ---------------------------------------------------------------------------
# Чтение хэша коммита из существующего fodt
# ---------------------------------------------------------------------------

def get_commit_from_fodt(fodt_path: str) -> Optional[str]:
    """
    Читает хэш коммита из поля Commit в существующем fodt файле.
    Возвращает хэш или None если файл не найден или поле отсутствует.
    """
    path = Path(fodt_path)
    if not path.exists():
        return None

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[GIT] Не удалось прочитать fodt: {e}")
        return None

    # Ищем строку вида: <T5>Commit:</text:span> abc1234</text:p>
    m = re.search(
        r'<text:span text:style-name="T5">Commit:</text:span>\s*([a-f0-9]{6,40})',
        content
    )
    if m:
        return m.group(1).strip()

    print("[GIT] Поле Commit не найдено в fodt — возможно первый запуск")
    return None


# ---------------------------------------------------------------------------
# Получение git diff
# ---------------------------------------------------------------------------

def get_git_diff(old_commit: str, source_file: str) -> str:
    """
    Запускает git diff <old_commit> HEAD -- <source_file>
    Возвращает текст diff или пустую строку.
    """
    try:
        result = subprocess.run(
            ["git", "diff", old_commit, "HEAD", "--", source_file],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"[GIT] git diff завершился с ошибкой: {result.stderr.strip()}")
            return ""
    except Exception as e:
        print(f"[GIT] Не удалось выполнить git diff: {e}")
        return ""


# ---------------------------------------------------------------------------
# Парсинг diff — получение изменившихся номеров строк
# ---------------------------------------------------------------------------

def parse_changed_lines(diff_text: str) -> Set[int]:
    """
    Из текста git diff извлекает номера строк которые были добавлены
    или удалены в новой версии файла.

    Формат hunk header: @@ -old_start,old_count +new_start,new_count @@
    Нас интересуют строки новой версии (префикс +).
    """
    changed_lines: Set[int] = set()

    current_new_line = 0

    for line in diff_text.splitlines():
        # Hunk header: @@ -a,b +c,d @@
        hunk = re.match(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
        if hunk:
            current_new_line = int(hunk.group(1))
            continue

        if line.startswith('---') or line.startswith('+++'):
            continue

        if line.startswith('+'):
            changed_lines.add(current_new_line)
            current_new_line += 1
        elif line.startswith('-'):
            # удалённая строка — не увеличиваем счётчик новых строк
            # но помечаем окрестность как изменённую (берём current_new_line)
            changed_lines.add(current_new_line)
        else:
            # контекстная строка
            current_new_line += 1

    return changed_lines


# ---------------------------------------------------------------------------
# Определение изменившихся сущностей по номерам строк
# ---------------------------------------------------------------------------

def find_changed_nodes(root: ApiNode, changed_lines: Set[int]) -> List[ApiNode]:
    """
    Обходит дерево AST и возвращает узлы (функции, методы, классы)
    чьи строки пересекаются с изменёнными строками.
    """
    changed_nodes: List[ApiNode] = []
    stack = [root]

    while stack:
        node = stack.pop()
        if node.node_type in ("function", "method", "class"):
            # пропускаем приватные сущности
            if not node.name.startswith("_"):
                node_lines = set(range(node.lineno, (node.end_lineno or node.lineno) + 1))
                if node_lines & changed_lines:  # пересечение
                    changed_nodes.append(node)
        stack.extend(node.children)

    return changed_nodes


# ---------------------------------------------------------------------------
# Главная функция — всё вместе
# ---------------------------------------------------------------------------

def get_changed_qualnames(
    fodt_path: str,
    source_file: str,
    root: ApiNode,
    current_commit: str,
) -> Tuple[Set[str], bool]:
    """
    Определяет какие сущности изменились с момента последнего коммита в fodt.

    Возвращает:
        (set of qualnames, needs_update)
        needs_update=False если изменений нет или не удалось определить
    """
    # Читаем хэш из fodt
    old_commit = get_commit_from_fodt(fodt_path)

    if not old_commit:
        print("[GIT] Старый коммит не найден — пересборка с нуля")
        return set(), False

    if old_commit == current_commit:
        print("[GIT] Коммит не изменился — апдейт не нужен")
        return set(), False

    print(f"[GIT] Сравниваем {old_commit}..{current_commit} для {source_file}")

    # Получаем diff
    diff_text = get_git_diff(old_commit, source_file)

    if not diff_text.strip():
        print("[GIT] Diff пустой — изменений в исходном файле нет")
        return set(), False

    # Парсим изменившиеся строки
    changed_lines = parse_changed_lines(diff_text)
    print(f"[GIT] Изменилось строк: {len(changed_lines)}")

    # Находим затронутые узлы AST
    changed_nodes = find_changed_nodes(root, changed_lines)

    if not changed_nodes:
        print("[GIT] Изменения не затронули публичные сущности")
        return set(), False

    qualnames = {node.qualname for node in changed_nodes}
    print(f"[GIT] Затронутые сущности ({len(qualnames)}): {', '.join(sorted(qualnames))}")

    return qualnames, True


# ---------------------------------------------------------------------------
# Обновление поля Commit в существующем fodt
# ---------------------------------------------------------------------------

def update_commit_in_fodt(fodt_path: str, new_commit: str) -> bool:
    """
    Обновляет хэш коммита в существующем fodt файле.
    Возвращает True если успешно.
    """
    path = Path(fodt_path)
    if not path.exists():
        return False

    try:
        content = path.read_text(encoding="utf-8")
        new_content = re.sub(
            r'(<text:span text:style-name="T5">Commit:</text:span>\s*)[a-f0-9]{6,40}',
            r'\g<1>' + new_commit,
            content
        )
        if new_content == content:
            print(f"[GIT] Поле Commit не найдено в fodt для обновления")
            return False
        path.write_text(new_content, encoding="utf-8")
        print(f"[GIT] Commit обновлён: {new_commit}")
        return True
    except Exception as e:
        print(f"[GIT] Ошибка при обновлении Commit в fodt: {e}")
        return False