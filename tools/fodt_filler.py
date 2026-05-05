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
# _section
# ---------------------------------------------------------------------------

def _normalize_heading(line: str) -> str:
    return line.strip().lstrip('#').strip()


def _heading_number(line: str) -> str:
    stripped = _normalize_heading(line)
    m = re.match(r'^(\d+(?:\.\d+)*\.?)\s', stripped)
    return m.group(1) if m else ""


def _section(md: str, start: str, end: str) -> str:
    def norm(s):
        return s.rstrip('.')

    start_n = norm(start)
    end_n   = norm(end)
    lines = md.splitlines()
    collecting = False
    result = []

    for line in lines:
        if line != line.lstrip() and not line.startswith('#'):
            if collecting:
                result.append(line)
            continue
        heading_num = _heading_number(line)
        if not collecting:
            if line.startswith('#') and heading_num and norm(heading_num) == start_n:
                collecting = True
                continue
            continue
        if heading_num and norm(heading_num) == end_n:
            break
        if heading_num:
            if norm(heading_num).startswith(end_n):
                break
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
        "component_name": "", "espd": "", "cid": "", "marketplace_url": "", "commit": "",
        "short_description": "", "category": "", "component_type": "",
        "status": "", "date": "", "version": "", "tags": "",
        "authors": [], "organizations": [],
        "introduction": "", "notes": "", "links": "",
        "component_description": "", "idl_block": "", "interface_title": "",
        "functions": [], "error_codes": [], "appendix": [],
    }

    for line in md.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        parts = [p.strip() for p in s.strip("|").split("|")]
        if len(parts) < 2:
            continue
        key, val = parts[0], clean(parts[1])
        if   "ЕСПД"                    in key: data["espd"]              = val
        elif "Имя компонента"          in key: data["component_name"]    = val
        elif "Краткое описание"        in key: data["short_description"]  = val
        elif "Component Use Category"  in key: data["category"]           = val
        elif "Component Type"          in key: data["component_type"]     = val
        elif "CID"                     in key: data["cid"]                = val
        elif "Marketplace URL"         in key: data["marketplace_url"]    = val
        elif "Статус"                  in key: data["status"]             = val
        elif "Дата изменения"          in key: data["date"]               = val
        elif "Версия"                  in key: data["version"]            = val
        elif "Теги"                    in key: data["tags"]               = val
        elif "Коммит"                  in key: data["commit"]             = val

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

    data["introduction"] = _section(md, "1.1.", "1.2.")
    data["notes"]        = _section(md, "1.2.", "1.3.")
    data["links"]        = _section(md, "1.3.", "2.")

    m = re.search(
        r'^#{1,3}\s+2\.\s+Компонент.*?\n(.*?)(?=^#{1,3}\s+2\.1\.|^#{1,3}\s+3\.)',
        md, re.MULTILINE | re.DOTALL
    )
    if m:
        data["component_description"] = clean(m.group(1))

    m = re.search(r'```(?:idl|cpp|c\+\+)?\n(.*?)```', md, re.DOTALL)
    if m:
        raw = m.group(1)
        cut = raw.find("};\n")
        if cut == -1:
            cut = raw.find("};")
        data["idl_block"] = (raw[:cut + 3] if cut != -1 else raw).rstrip()

    m = re.search(r'2\.1\.\s+(I\w+)\s+IDL', md)
    data["interface_title"] = m.group(1) if m else "I" + data["component_name"]

    data["functions"]   = _parse_functions(md)
    data["error_codes"] = _parse_errors(md)
    data["appendix"]    = _parse_appendix(md)

    return data


# ---------------------------------------------------------------------------
# Парсеры подсекций
# ---------------------------------------------------------------------------

def _parse_functions(md: str) -> list:
    fns = []
    blocks = re.split(r'(?=#{4,5}\s+2\.3\.)', md)
    for block in blocks:
        if not re.match(r'#{4,5}\s+2\.3\.', block):
            continue
        hm = re.match(r'#{4,5}\s+2\.3\.\S*\s+(Метод|Функция|Класс)\s+`(\w+)`', block)
        if not hm:
            continue
        fn = {"kind": hm.group(1), "name": hm.group(2), "is_class": hm.group(1) == "Класс"}

        def _f(label, b=block):
            m = re.search(r'\*\*' + re.escape(label) + r':\*\*\s*(.+?)(?=\n\s*\*\*|\Z)', b, re.DOTALL)
            return clean(m.group(1)) if m else ""

        fn["qualname"]    = _f("Полное имя").strip("`")
        fn["signature"]   = _f("Сигнатура").strip("`")
        fn["location"]    = _f("Расположение").strip("`")
        fn["description"] = _f("Назначение")
        fn["logic"]       = _f("Логика работы")
        fn["returns"]     = _f("Возвращаемое значение").strip("`")
        fn["params"]      = _parse_params(block)
        fn["exceptions"]  = re.findall(r'- `(\w+)` — (.+)', block)
        m = re.search(r'\*\*Пример использования:\*\*.*?```python\n(.*?)```', block, re.DOTALL)
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
                params.append({"name": parts[0], "type": parts[1], "default": parts[2], "kind": parts[3]})
    return params


def _parse_errors(md: str) -> list:
    codes = []
    m = re.search(r'^#{1,3}\s+3\.\s+Код.*?\n(.*?)(?=^#{1,3}\s+Приложение|\Z)', md, re.MULTILINE | re.DOTALL)
    if not m:
        return codes
    for line in m.group(1).splitlines():
        if not line.startswith("|"):
            continue
        if "Код ошибки" in line or "---" in line:
            continue
        parts = [clean(p) for p in line.strip("|").split("|")]
        if len(parts) >= 3 and parts[0]:
            codes.append({"code": parts[0], "value": parts[1], "description": parts[2]})
    return codes


def _parse_appendix(md: str) -> list:
    items = []
    m = re.search(r'^#{1,3}\s+Приложение\s+А.*?\n(.*?)(?=\Z)', md, re.MULTILINE | re.DOTALL)
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
    if fn.get("qualname"):    xml += odf_p("Полное имя: "    + fn["qualname"])
    if fn.get("location"):    xml += odf_p("Расположение: "  + fn["location"])
    if fn.get("description"): xml += odf_p(fn["description"])
    if fn.get("logic"):       xml += odf_p("Логика работы: " + fn["logic"])
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
            dflt = f", по умолчанию: {p['default']}" if p['default'] not in ("обязательный", "") else ""
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
    sfx = ["2", "3", "4", "5", "6", "7", "8"]
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
    lines = [f'Классов: {len(classes)}, функций верхнего уровня: {len(funcs)}, методов: {len(methods)}']
    if classes:
        lines += ['', 'Классы:'] + [f'  • {c["name"]} — {c.get("location", "")}' for c in classes]
    if funcs:
        lines += ['', 'Функции верхнего уровня:'] + [f'  • {f.get("signature") or f["name"]}' for f in funcs]
    if methods:
        lines += ['', 'Методы:'] + [f'  • {m.get("signature") or m["name"]}' for m in methods]
    for line in lines:
        xml += f'   <text:p text:style-name="P44">{escape(line)}</text:p>\n'
    xml += '   <text:p text:style-name="P38"/>\n'
    return xml


# ---------------------------------------------------------------------------
# fill_template
# ---------------------------------------------------------------------------

def _replace_once(xml: str, old: str, new: str, label: str) -> str:
    if old not in xml:
        print(f"[WARN] Якорь не найден: {label!r} (первые 80 символов: {old[:80]!r})")
        return xml
    return xml.replace(old, new, 1)


def _is_empty(val) -> bool:
    """Проверяет что значение пустое или является заглушкой."""
    if not val:
        return True
    return str(val).strip() in ("", "—", "-", "N/A", "n/a", "\u2014")


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

    # --- Marketplace ID — убираем placeholder, ставим тире ---
    # Шаблон: {<text:span text:style-name="T7">указан на карточке компонента в формате</text:span> uuid4}
    # Ищем через regex т.к. точная строка с кириллицей может отличаться
    r = re.sub(
        r'\{<text:span text:style-name="T7">[^<]*</text:span>[^}]*uuid4\}',
        '\u2014',
        r, count=1
    )

    # --- Marketplace URL --- 
    marketplace_url_val = data.get("marketplace_url") or ""
    if _is_empty(marketplace_url_val):
        marketplace_url_val = "\u2014"
    r = _replace_once(r,
        '<text:span text:style-name="T12">https://ip-office.com/product/n/a</text:span>',
        f'<text:span text:style-name="T12">{escape(marketplace_url_val)}</text:span>',
        "Marketplace URL")

    # --- Short Description ---
    r = _replace_once(r,
        '<text:span text:style-name="T7">n/a</text:span>',
        f'<text:span text:style-name="T7">{escape(data["short_description"] or "—")}</text:span>',
        "Short Description T7")

    # --- Category ---
    r = _replace_once(r,
        '<text:span text:style-name="T8">n/a</text:span>',
        f'<text:span text:style-name="T8">{escape(data["category"] or "—")}</text:span>',
        "Category T8")

    # --- Type ---
    r = _replace_once(r,
        '<text:span text:style-name="T10">COMPONENT</text:span>',
        f'<text:span text:style-name="T10">{escape(data.get("component_type") or "COMPONENT")}</text:span>',
        "Type T10")

    # --- Tags ---
    r = _replace_once(r,
        '<text:span text:style-name="T16">n/a</text:span>',
        f'<text:span text:style-name="T16">{escape(data["tags"] or "—")}</text:span>',
        "Tags T16")

    # --- Status ---
    r = _replace_once(r,
        'Status:</text:span> Draft',
        'Status:</text:span> ' + escape(data["status"] or "черновик"),
        "Status")

    # --- Version ---
    r = _replace_once(r,
        '<text:span text:style-name="T5">Version:</text:span> 1.0',
        f'<text:span text:style-name="T5">Version:</text:span> {escape(data["version"] or "0.1")}',
        "Version")

    # --- Commit — вставляем новую строку после Version ---
    if data.get("commit") and data["commit"] not in ("—", "-", ""):
        # Находим строку с Version в документе и вставляем Commit после неё
        ver_val = escape(data["version"] or "0.1")
        ver_anchor = f'<text:span text:style-name="T5">Version:</text:span> {ver_val}'
        ver_end = r.find('</text:p>', r.find(ver_anchor)) if ver_anchor in r else -1
        if ver_end != -1:
            commit_xml = (
                '\n   <text:p text:style-name="P11">'
                '<text:span text:style-name="T5">Commit:</text:span> '
                + escape(data["commit"]) +
                '</text:p>'
            )
            r = r[:ver_end + len('</text:p>')] + commit_xml + r[ver_end + len('</text:p>'):]
            print(f'[INFO] Commit {data["commit"]} вставлен в документ')

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
    r = re.sub(r'2\.1\. I\w+ IDL', f'2.1. {data["interface_title"]} IDL', r)

    # --- IDL блок ---
    # Если нет CID — это не ECO-компонент с зарегистрированным интерфейсом
    # IDL заменяем на N/A
    cid_empty = _is_empty(data.get("cid", ""))

    if cid_empty:
        idl_section_marker = f'2.1. {data["interface_title"]} IDL'
        idl_section_pos = r.find(idl_section_marker)
        if idl_section_pos != -1:
            first_code_p = r.find('<text:p text:style-name="code_5f_cpp">', idl_section_pos)
            next_list = r.find('<text:list text:continue-numbering="true"', first_code_p) if first_code_p != -1 else -1
            if first_code_p != -1 and next_list != -1:
                r = r[:first_code_p] + '<text:p text:style-name="P40">N/A</text:p>\n' + r[next_list:]
                print("[INFO] IDL заменён на N/A (нет CID)")
            else:
                print("[WARN] IDL блок не найден для замены на N/A")
        else:
            print("[WARN] Секция 2.1 не найдена для замены IDL на N/A")

    elif data["idl_block"]:
        # Есть CID и IDL от LLM — вставляем
        idl_section_marker = f'2.1. {data["interface_title"]} IDL'
        idl_section_pos = r.find(idl_section_marker)
        if idl_section_pos == -1:
            print("[WARN] Секция 2.1 не найдена для вставки IDL")
        else:
            first_code_p = r.find('<text:p text:style-name="code_5f_cpp">', idl_section_pos)
            next_list = r.find('<text:list text:continue-numbering="true"', first_code_p) if first_code_p != -1 else -1
            if first_code_p != -1 and next_list != -1:
                last_code_end = first_code_p
                pos = first_code_p
                while True:
                    p = r.find('<text:p text:style-name="code_5f_cpp">', pos)
                    if p == -1 or p >= next_list:
                        break
                    end = r.find('</text:p>', p) + len('</text:p>')
                    last_code_end = end
                    pos = end
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

    # --- Секция 2.2 состав интерфейса ---
    if data["functions"]:
        summary_xml = odf_interface_summary(data["functions"])
        fn_anchor = '<text:bookmark-start text:name="__RefHeading___Toc72881_228845717"/>'
        fn_pos = r.find(fn_anchor)
        if fn_pos != -1:
            list_start = r.rfind('<text:list text:continue-numbering', 0, fn_pos)
            r = r[:list_start] + summary_xml + r[list_start:]
        else:
            p40_after_idl = r.find('<text:p text:style-name="P40"/>', r.find('2.1. ' + data.get("interface_title", "") + ' IDL'))
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


# ---------------------------------------------------------------------------
# fill_fodt  —  точка входа
# ---------------------------------------------------------------------------

def fill_fodt(md_path: str, tmpl_path: str, out_path: str) -> None:
    md   = Path(md_path).read_text(encoding="utf-8")
    tmpl = Path(tmpl_path).read_text(encoding="utf-8")
    data = parse_markdown(md)
    result = fill_template(tmpl, data)
    Path(out_path).write_text(result, encoding="utf-8")
    print(f"[FODT] Сохранён: {out_path}")