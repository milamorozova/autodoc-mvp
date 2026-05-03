from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean(text):
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text.strip()


def odf_p(text, style="P44"):
    return f'   <text:p text:style-name="{style}">{escape(clean(text))}</text:p>\n'


def odf_code(code):
    out = ""
    for line in code.splitlines():
        out += f'<text:p text:style-name="code_5f_cpp">{escape(line)}</text:p>\n'
    return out


# ---------------------------------------------------------------------------
# _section  —  надёжный парсер секций markdown
# ---------------------------------------------------------------------------

def _normalize_heading(line: str) -> str:
    """Возвращает текст заголовка без символов # и пробелов."""
    return line.strip().lstrip('#').strip()


def _heading_number(line: str) -> str:
    """
    Если строка — заголовок вида '## 1.2. Примечание',
    возвращает числовой префикс '1.2.' (без пробела после).
    Если не заголовок — пустая строка.
    """
    stripped = _normalize_heading(line)
    m = re.match(r'^(\d+(?:\.\d+)*\.?)\s', stripped)
    return m.group(1) if m else ""


def _section(md: str, start: str, end: str) -> str:
    """
    Извлекает текст между заголовком, начинающимся с `start`,
    и заголовком, начинающимся с `end`.

    Работает независимо от уровня # (один, два, три знака решётки)
    и от того, есть ли точка в конце номера (1.1 == 1.1.).
    """
    # нормализуем start/end: убираем trailing точку для сравнения
    def norm(s):
        return s.rstrip('.')

    start_n = norm(start)
    end_n   = norm(end)

    lines = md.splitlines()
    collecting = False
    result = []

    for line in lines:
        # Пропускаем строки с отступом — это оглавление, не заголовки секций
        if line != line.lstrip() and not line.startswith('#'):
            if collecting:
                result.append(line)
            continue

        heading_num = _heading_number(line)

        # Проверяем совпадение с start — только реальные заголовки с #
        if not collecting:
            if line.startswith('#') and heading_num and norm(heading_num) == start_n:
                collecting = True
                continue
            continue

        # Уже собираем — проверяем стоп-условие
        if heading_num and norm(heading_num) == end_n:
            break
        # Стоп на любом заголовке того же или более высокого уровня
        # (т.е. с таким же или более коротким числовым префиксом)
        if heading_num:
            # end_n может быть '1.2', start_n '1.1'
            # Если текущий заголовок начинается с end_n — стоп
            if norm(heading_num).startswith(end_n):
                break
            # Если уровень <= уровня start — тоже стоп
            start_depth = start_n.count('.')
            cur_depth   = norm(heading_num).count('.')
            if cur_depth <= start_depth and norm(heading_num) != start_n:
                break

        result.append(line)

    return '\n'.join(result).strip()


# ---------------------------------------------------------------------------
# parse_markdown
# ---------------------------------------------------------------------------

def parse_markdown(md: str) -> dict:
    data = {
        "component_name": "", "espd": "", "cid": "", "marketplace_url": "",
        "short_description": "", "category": "", "component_type": "",
        "status": "", "date": "", "version": "", "tags": "",
        "authors": [], "organizations": [],
        "introduction": "", "notes": "", "links": "",
        "component_description": "", "idl_block": "", "interface_title": "",
        "functions": [], "error_codes": [], "appendix": [],
    }

    # --- Таблица метаданных ---
    for line in md.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        parts = [p.strip() for p in s.strip("|").split("|")]
        if len(parts) < 2:
            continue
        key, val = parts[0], clean(parts[1])
        if "ЕСПД"                    in key: data["espd"]             = val
        elif "Имя компонента"        in key: data["component_name"]   = val
        elif "Краткое описание"      in key: data["short_description"] = val
        elif "Component Use Category" in key: data["category"]        = val
        elif "Component Type"        in key: data["component_type"]   = val
        elif "CID"                   in key: data["cid"]              = val
        elif "Marketplace URL"       in key: data["marketplace_url"]  = val
        elif "Статус"                in key: data["status"]           = val
        elif "Дата изменения"        in key: data["date"]             = val
        elif "Версия"                in key: data["version"]          = val
        elif "Теги"                  in key: data["tags"]             = val

    # --- Авторы ---
    in_authors = False
    for line in md.splitlines():
        if "| Авторы |" in line:
            in_authors = True
            continue
        if in_authors:
            if line.startswith("|---"):
                continue
            if not line.startswith("|"):
                in_authors = False
                continue
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 2 and parts[0] and not parts[0].startswith("_"):
                data["authors"].append(parts[0])
                data["organizations"].append(parts[1] if len(parts) > 1 else "")

    # --- Текстовые секции ---
    data["introduction"] = _section(md, "1.1.", "1.2.")
    data["notes"]        = _section(md, "1.2.", "1.3.")
    data["links"]        = _section(md, "1.3.", "2.")

    # --- Описание компонента (секция 2, до 2.1) ---
    m = re.search(
        r'^#{1,3}\s+2\.\s+Компонент.*?\n(.*?)(?=^#{1,3}\s+2\.1\.|^#{1,3}\s+3\.)',
        md, re.MULTILINE | re.DOTALL
    )
    if m:
        data["component_description"] = clean(m.group(1))

    # --- IDL блок ---
    # Берём содержимое первого ```idl/cpp/c++ блока и обрезаем по первому };
    m = re.search(r'```(?:idl|cpp|c\+\+)?\n(.*?)```', md, re.DOTALL)
    if m:
        raw = m.group(1)
        # Ищем закрывающий }; и берём только до него включительно
        cut = raw.find("};\n")
        if cut == -1:
            cut = raw.find("};")
        data["idl_block"] = (raw[:cut + 3] if cut != -1 else raw).rstrip()

    # --- Заголовок интерфейса ---
    m = re.search(r'2\.1\.\s+(I\w+)\s+IDL', md)
    data["interface_title"] = m.group(1) if m else "I" + data["component_name"]

    # --- Функции, ошибки, приложение ---
    data["functions"]   = _parse_functions(md)
    data["error_codes"] = _parse_errors(md)
    data["appendix"]    = _parse_appendix(md)

    return data


# ---------------------------------------------------------------------------
# Парсеры подсекций
# ---------------------------------------------------------------------------

def _parse_functions(md: str) -> list:
    fns = []
    # Разбиваем по заголовкам #### 2.3.x или ##### 2.3.x.y
    blocks = re.split(r'(?=#{4,5}\s+2\.3\.)', md)
    for block in blocks:
        if not re.match(r'#{4,5}\s+2\.3\.', block):
            continue
        hm = re.match(r'#{4,5}\s+2\.3\.\S*\s+(Метод|Функция|Класс)\s+`(\w+)`', block)
        if not hm:
            continue
        fn = {
            "kind":     hm.group(1),
            "name":     hm.group(2),
            "is_class": hm.group(1) == "Класс",
        }

        def _f(label, b=block):
            m = re.search(
                r'\*\*' + re.escape(label) + r':\*\*\s*(.+?)(?=\n\s*\*\*|\Z)',
                b, re.DOTALL
            )
            return clean(m.group(1)) if m else ""

        fn["qualname"]    = _f("Полное имя").strip("`")
        fn["signature"]   = _f("Сигнатура").strip("`")
        fn["location"]    = _f("Расположение").strip("`")
        fn["description"] = _f("Назначение")
        fn["logic"]       = _f("Логика работы")
        fn["returns"]     = _f("Возвращаемое значение").strip("`")
        fn["params"]      = _parse_params(block)
        fn["exceptions"]  = re.findall(r'- `(\w+)` — (.+)', block)
        m = re.search(r'\*\*Пример использования:\*\*.*?```python\n(.*?)```',
                      block, re.DOTALL)
        fn["example"] = m.group(1).strip() if m else ""
        fns.append(fn)
    return fns


def _parse_params(block: str) -> list:
    params, in_t = [], False
    for line in block.splitlines():
        if "| Параметр |" in line:
            in_t = True
            continue
        if in_t:
            if line.startswith("|---"):
                continue
            if not line.startswith("|"):
                break
            parts = [clean(p) for p in line.strip("|").split("|")]
            if len(parts) >= 4 and parts[0] and "отсутствуют" not in parts[0]:
                params.append({
                    "name":    parts[0],
                    "type":    parts[1],
                    "default": parts[2],
                    "kind":    parts[3],
                })
    return params


def _parse_errors(md: str) -> list:
    codes = []
    m = re.search(
        r'^#{1,3}\s+3\.\s+Код.*?\n(.*?)(?=^#{1,3}\s+Приложение|\Z)',
        md, re.MULTILINE | re.DOTALL
    )
    if not m:
        return codes
    for line in m.group(1).splitlines():
        if not line.startswith("|"):
            continue
        if "Код ошибки" in line or "---" in line:
            continue
        parts = [clean(p) for p in line.strip("|").split("|")]
        if len(parts) >= 3 and parts[0]:
            codes.append({
                "code":        parts[0],
                "value":       parts[1],
                "description": parts[2],
            })
    return codes


def _parse_appendix(md: str) -> list:
    items = []
    m = re.search(
        r'^#{1,3}\s+Приложение\s+А.*?\n(.*?)(?=\Z)',
        md, re.MULTILINE | re.DOTALL
    )
    if not m:
        return items
    for block in re.split(r'###\s+А\.\d+', m.group(1)):
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        name  = clean(lines[0]) if lines else ""
        cm    = re.search(r'```python\n(.*?)```', block, re.DOTALL)
        code  = cm.group(1).strip() if cm else ""
        if name:
            items.append({"name": name, "code": code})
    return items


# ---------------------------------------------------------------------------
# ODF генераторы
# ---------------------------------------------------------------------------

def odf_fn(fn: dict, idx: int) -> str:
    name = fn["name"]
    kind = fn.get("kind", "Функция")
    xml = (
        f'   <text:list text:continue-numbering="true" text:style-name="L1">\n'
        f'    <text:list-item>\n'
        f'     <text:list>\n'
        f'      <text:list-item>\n'
        f'       <text:list>\n'
        f'        <text:list-header>\n'
        f'         <text:h text:style-name="P42" text:outline-level="1">'
        f'2.1.{idx}. {escape(kind)} '
        f'<text:span text:style-name="T29">{escape(name)}</text:span>'
        f'</text:h>\n'
        f'        </text:list-header>\n'
        f'       </text:list>\n'
        f'      </text:list-item>\n'
        f'     </text:list>\n'
        f'    </text:list-item>\n'
        f'   </text:list>\n'
        f'   <text:p text:style-name="P43"/>\n'
    )

    if fn.get("qualname"):    xml += odf_p("Полное имя: "      + fn["qualname"])
    if fn.get("location"):    xml += odf_p("Расположение: "    + fn["location"])
    if fn.get("description"): xml += odf_p(fn["description"])
    if fn.get("logic"):       xml += odf_p("Логика работы: "   + fn["logic"])

    if fn.get("signature"):
        xml += (
            f'   <text:p text:style-name="P44">'
            f'<text:span text:style-name="T18">Сигнатура: </text:span>'
            f'<text:span text:style-name="T29">{escape(fn["signature"])}</text:span>'
            f'</text:p>\n'
        )

    if fn.get("params"):
        xml += odf_p("Параметры:")
        for p in fn["params"]:
            dflt = (f", по умолчанию: {p['default']}"
                    if p['default'] not in ("обязательный", "") else "")
            xml += odf_p("  • " + p['name'] + " (" + p['type'] + ")" + dflt + " — " + p['kind'])
    else:
        xml += odf_p("Параметры: отсутствуют")

    if fn.get("returns"):
        xml += odf_p("Возвращает: " + fn["returns"])

    if fn.get("exceptions"):
        xml += odf_p("Исключения:")
        for en, ed in fn["exceptions"]:
            xml += odf_p("  • " + en + " — " + ed)
    else:
        xml += odf_p("Исключения: явные исключения не обнаружены")

    if fn.get("example"):
        xml += odf_p("Пример использования:")
        xml += odf_code(fn["example"])

    xml += '   <text:p text:style-name="P43"/>\n'
    return xml


def odf_toc(fns: list) -> str:
    out = ""
    for i, fn in enumerate(fns, 1):
        out += (
            f'     <text:p text:style-name="P22">'
            f'2.1.{i}. {escape(fn.get("kind", "Функция"))} {escape(fn["name"])}'
            f'</text:p>\n'
        )
    return out


def odf_errors(codes: list) -> str:
    rows = ""
    sfx  = ["2", "3", "4", "5", "6", "7", "8"]
    for i, ec in enumerate(codes):
        s = sfx[min(i, len(sfx) - 1)]
        rows += (
            f'    <table:table-row table:style-name="Таблица3.1">\n'
            f'     <table:table-cell table:style-name="Таблица3.A{s}" office:value-type="string">\n'
            f'      <text:p text:style-name="P54">{escape(ec["code"])}</text:p>\n'
            f'     </table:table-cell>\n'
            f'     <table:table-cell table:style-name="Таблица3.B{s}" office:value-type="string">\n'
            f'      <text:p text:style-name="P54">{escape(ec["value"])}</text:p>\n'
            f'     </table:table-cell>\n'
            f'     <table:table-cell table:style-name="Таблица3.C{s}" office:value-type="string">\n'
            f'      <text:p text:style-name="P55">{escape(ec["description"])}</text:p>\n'
            f'     </table:table-cell>\n'
            f'    </table:table-row>\n'
        )
    return rows


def odf_appendix(items: list) -> str:
    out = ""
    for i, item in enumerate(items, 1):
        label = '\u0410.' + str(i) + '. ' + escape(item["name"])
        out += '   <text:p text:style-name="P57"><text:span text:style-name="T19">' + label + '</text:span></text:p>\n'
        if item["code"]:
            out += odf_code(item["code"])
        out += '   <text:p text:style-name="P57"/>\n'
    return out


def odf_interface_summary(fns: list) -> str:
    """Генерирует секцию 2.2 — состав интерфейса."""
    classes = [f for f in fns if f.get("is_class")]
    methods = [f for f in fns if f.get("kind") == "Метод"]
    funcs   = [f for f in fns if f.get("kind") == "Функция"]

    xml = (
        '   <text:list text:continue-numbering="true" text:style-name="L1">\n'
        '    <text:list-item>\n'
        '     <text:list>\n'
        '      <text:list-header>\n'
        '       <text:h text:style-name="P45" text:outline-level="1">2.2. Состав интерфейса</text:h>\n'
        '      </text:list-header>\n'
        '     </text:list>\n'
        '    </text:list-item>\n'
        '   </text:list>\n'
        '   <text:p text:style-name="P40"/>\n'
    )
    from xml.sax.saxutils import escape as _e
    lines = []
    lines.append(f'Классов: {len(classes)}, функций верхнего уровня: {len(funcs)}, методов: {len(methods)}')
    if classes:
        lines.append('')
        lines.append('Классы:')
        for c in classes:
            lines.append(f'  • {c["name"]} — {c.get("location", "")}')
    if funcs:
        lines.append('')
        lines.append('Функции верхнего уровня:')
        for f in funcs:
            sig = f.get("signature") or f["name"]
            lines.append(f'  • {sig}')
    if methods:
        lines.append('')
        lines.append('Методы:')
        for m in methods:
            sig = m.get("signature") or m["name"]
            lines.append(f'  • {sig}')

    for line in lines:
        xml += f'   <text:p text:style-name="P44">{_e(line)}</text:p>\n'

    xml += '   <text:p text:style-name="P38"/>\n'
    return xml


# ---------------------------------------------------------------------------
# fill_template  —  с проверкой каждой замены
# ---------------------------------------------------------------------------

def _replace_once(xml: str, old: str, new: str, label: str) -> str:
    """str.replace с предупреждением если якорь не найден."""
    if old not in xml:
        print(f"[WARN] Якорь не найден: {label!r} (первые 80 символов: {old[:80]!r})")
        return xml
    return xml.replace(old, new, 1)


def fill_template(tmpl: str, data: dict) -> str:
    r = tmpl
    name = data["component_name"]

    # --- Плейсхолдеры ---
    replacements = {
        "[!output PROJECT_NAME]":     name,
        "[!output FIX_PROJECT_NAME]": name,
        "[!output DOC_ESPD_RU]":      data["espd"]  or "RU.\u2014.XXXXX-XX",
        "[!output GUID_CID_TARGET]":  data["cid"]   or "\u2014",
        "[!output GUID_IID]":         data["cid"]   or "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
        "[!output DOC_DATE_TIME]":    data["date"]  or "\u2014",
        "[!output AUTHOR]":           data["authors"][0]       if data["authors"]       else "\u2014",
        "[!output COMPANY]":          data["organizations"][0] if data["organizations"] else "\u041f\u0418\u0420\u0424",
    }
    for ph, val in replacements.items():
        r = r.replace(escape(ph), escape(val)).replace(ph, escape(val))

    # --- Метаданные обложки ---
    r = _replace_once(r,
        '<text:span text:style-name="T7">n/a</text:span>',
        f'<text:span text:style-name="T7">{escape(data["short_description"] or "—")}</text:span>',
        "Short Description T7")

    r = _replace_once(r,
        '<text:span text:style-name="T8">n/a</text:span>',
        f'<text:span text:style-name="T8">{escape(data["category"] or "—")}</text:span>',
        "Category T8")

    r = _replace_once(r,
        '<text:span text:style-name="T10">COMPONENT</text:span>',
        f'<text:span text:style-name="T10">{escape(data.get("component_type") or "COMPONENT")}</text:span>',
        "Type T10")

    r = _replace_once(r,
        '<text:span text:style-name="T16">n/a</text:span>',
        f'<text:span text:style-name="T16">{escape(data["tags"] or "—")}</text:span>',
        "Tags T16")

    r = _replace_once(r,
        'Status:</text:span> Draft',
        'Status:</text:span> ' + escape(data["status"] or "черновик"),
        "Status")

    r = _replace_once(r,
        '<text:span text:style-name="T5">Version:</text:span> 1.0',
        f'<text:span text:style-name="T5">Version:</text:span> {escape(data["version"] or "0.1")}',
        "Version")

    # --- Введение (1.1) ---
    old_intro = (
        '<text:p text:style-name="P24">'
        '<text:span text:style-name="T19">Описание</text:span>'
        '<text:span text:style-name="T18">.</text:span>'
        '</text:p>'
    )
    if data["introduction"]:
        r = _replace_once(r, old_intro,
            f'<text:p text:style-name="P24">'
            f'<text:span text:style-name="T19">{escape(data["introduction"])}</text:span>'
            f'</text:p>',
            "Введение P24")
    else:
        print("[INFO] introduction пустой — секция 1.1 не заменена")

    # --- Примечание (1.2) ---
    # Удаляем шаблонный блок "Ключевые слова в документе" вместе с заменой P28
    keywords_block = (
        '\n   <text:list text:style-name="WWNum1">\n'
        '    <text:list-header>\n'
        '     <text:p text:style-name="P29">Ключевые слова в документе</text:p>\n'
        '    </text:list-header>\n'
        '   </text:list>'
    )
    if data["notes"]:
        new_p28 = f'<text:p text:style-name="P28">{escape(data["notes"])}</text:p>'
        old_p28_with_kw = '<text:p text:style-name="P28"/>' + keywords_block
        if old_p28_with_kw in r:
            r = r.replace(old_p28_with_kw, new_p28, 1)
        else:
            r = _replace_once(r, '<text:p text:style-name="P28"/>', new_p28, "Примечание P28")
    else:
        r = r.replace(keywords_block, '', 1)
        print("[INFO] notes пустой — секция 1.2 не заменена")

    # --- Описание компонента ---
    old_desc = (
        '<text:p text:style-name="P37">Компонент, имеет следующ'
        '<text:span text:style-name="T28">е</text:span>е описание:</text:p>\n'
        '   <text:p text:style-name="P36"/>\n'
        '   <text:p text:style-name="P36"/>'
    )
    if data["component_description"]:
        r = _replace_once(r, old_desc,
            f'<text:p text:style-name="P37">Компонент, имеет следующ'
            f'<text:span text:style-name="T28">е</text:span>е описание:</text:p>\n'
            f'   <text:p text:style-name="P36">{escape(data["component_description"])}</text:p>',
            "Описание компонента P37")

    # --- Заголовок 2.1 ---
    # Ищем любой вариант '2.1. I<что-угодно> IDL' и заменяем
    r = re.sub(r'2\.1\. I\w+ IDL', f'2.1. {data["interface_title"]} IDL', r)

    # --- IDL блок ---
    if data["idl_block"]:
        # Шаблон начинается с 'import "IEcoBase1.h"' — ищем первый code_5f_cpp параграф в IDL секции
        # Находим начало IDL блока по первому code_5f_cpp после заголовка 2.1
        idl_section_marker = f'2.1. {data["interface_title"]} IDL'
        idl_section_pos = r.find(idl_section_marker)
        if idl_section_pos == -1:
            print("[WARN] Секция 2.1 не найдена для вставки IDL")
        else:
            # Ищем первый параграф code_5f_cpp после заголовка 2.1
            first_code_p = r.find('<text:p text:style-name="code_5f_cpp">', idl_section_pos)
            # Ищем следующий list ПОСЛЕ first_code_p (не после маркера заголовка)
            next_list = r.find('<text:list text:continue-numbering="true"', first_code_p) if first_code_p != -1 else -1
            if first_code_p != -1 and next_list != -1:
                # Находим последний code_5f_cpp перед next_list
                last_code_end = first_code_p
                pos = first_code_p
                while True:
                    p = r.find('<text:p text:style-name="code_5f_cpp">', pos)
                    if p == -1 or p >= next_list:
                        break
                    end = r.find('</text:p>', p) + len('</text:p>')
                    last_code_end = end
                    pos = end
                # Также захватываем P41 параграфы (они тоже часть IDL блока)
                pos = first_code_p
                last_code_end_ext = last_code_end
                while True:
                    p41 = r.find('<text:p text:style-name="P41">', pos)
                    if p41 == -1 or p41 >= next_list:
                        break
                    end = r.find('</text:p>', p41) + len('</text:p>')
                    if end > last_code_end_ext:
                        last_code_end_ext = end
                    pos = end
                last_code_end = last_code_end_ext
                r = r[:first_code_p] + odf_code(data["idl_block"]) + r[last_code_end:]
                print(f"[INFO] IDL блок вставлен ({len(data['idl_block'])} символов)")
            else:
                print("[WARN] IDL блок не найден в шаблоне")

    # --- Секция 2.2 состав интерфейса — вставляем ПОСЛЕ IDL, ПЕРЕД функциями ---
    if data["functions"]:
        summary_xml = odf_interface_summary(data["functions"])
        # Ищем конец IDL блока — последний code_5f_cpp перед первой функцией 2.1.1
        # Вставляем 2.2 прямо перед блоком функций
        fn_anchor = '<text:bookmark-start text:name="__RefHeading___Toc72881_228845717"/>'
        fn_pos = r.find(fn_anchor)
        if fn_pos != -1:
            list_start = r.rfind('<text:list text:continue-numbering', 0, fn_pos)
            r = r[:list_start] + summary_xml + r[list_start:]
        else:
            # Fallback: вставляем перед P40 который идёт после IDL
            p40_after_idl = r.find('<text:p text:style-name="P40"/>', r.find('2.1. ' + data.get("interface_title","") + ' IDL'))
            if p40_after_idl != -1:
                r = r[:p40_after_idl] + summary_xml + r[p40_after_idl:]
            else:
                print("[WARN] Не найдено место для вставки секции 2.2")

    # --- Функции ---
    if data["functions"]:
        fn_xml = "".join(odf_fn(fn, i) for i, fn in enumerate(data["functions"], 1))
        old_fs = '<text:bookmark-start text:name="__RefHeading___Toc72881_228845717"/>2.1.1.'
        old_fe = (
            '<text:p text:style-name="P46">'
            '<text:span text:style-name="T19">Функция</text:span>'
            '<text:span text:style-name="T18">.</text:span></text:p>'
        )
        si = r.find(old_fs)
        ei = r.find(old_fe)
        if si != -1 and ei != -1:
            ls = r.rfind('<text:list text:continue-numbering', 0, si)
            r  = r[:ls] + fn_xml + r[ei + len(old_fe):]
        else:
            print("[WARN] Якорь блока функций не найден")

    # --- Оглавление ---
    ot1 = ('<text:p text:style-name="P22"><text:a xlink:type="simple" '
           'xlink:href="#__RefHeading___Toc72881_228845717"')
    ot2 = ('<text:p text:style-name="P22"><text:a xlink:type="simple" '
           'xlink:href="#__RefHeading___Toc72883_228845717"')
    si1 = r.find(ot1)
    si2 = r.find(ot2)
    if si1 != -1 and si2 != -1:
        end2 = r.find('</text:p>', si2) + len('</text:p>')
        r = r[:si1] + odf_toc(data["functions"]) + r[end2:]
    else:
        print("[WARN] Якоря оглавления не найдены")

    # --- Таблица ошибок ---
    if data["error_codes"]:
        or_ = (
            '    <table:table-row table:style-name="Таблица3.1">\n'
            '     <table:table-cell table:style-name="Таблица3.A2"'
        )
        ot  = '</table:table>'
        si  = r.find(or_)
        ei  = r.find(ot, si)
        if si != -1 and ei != -1:
            r = r[:si] + odf_errors(data["error_codes"]) + '   </table:table>' + r[ei + len(ot):]
        else:
            print("[WARN] Якорь таблицы ошибок не найден")

    # --- Приложение А ---
    if data["appendix"]:
        ah  = '<text:h text:style-name="P56"'
        p57 = '<text:p text:style-name="P57">'
        idx = r.find(ah)
        if idx != -1:
            pi = r.find(p57, idx)
            if pi != -1:
                r = r[:pi] + odf_appendix(data["appendix"]) + r[pi:]
            else:
                print("[WARN] P57 после P56 не найден")
        else:
            print("[WARN] Якорь приложения P56 не найден")

    return r