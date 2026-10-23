import os
import re
import sqlite3
import unicodedata
from pathlib import Path

DATA = Path(os.environ.get("MISHPAT_DATA", Path.home() / "droit-israel-data"))
LAWS_DB = DATA / "laws.sqlite"
KNESSET_DB = DATA / "knesset.sqlite"

WIKI = "https://he.wikisource.org/wiki/"
API = "https://he.wikisource.org/w/api.php"
USER_AGENT = "mishpat-studjoow/1.0 (https://mishpat.studjoow.com; contact@studjoow.com)"
ATTRIBUTION = ("Consolidated text: Hebrew Wikisource, ספר החוקים הפתוח (Open Law Book), CC BY-SA 4.0, "
               "https://he.wikisource.org/wiki/ויקיטקסט:ספר_החוקים_הפתוח . Unofficial: the binding text is the "
               "publication in רשומות (Reshumot).")

NIQQUD = re.compile(r"[֑-ׇ]")
QUOTES = str.maketrans({"״": '"', "׳": "'", "“": '"', "”": '"', "„": '"', "‘": "'", "’": "'", "`": "'",
                        "־": "-", "–": "-", "—": "-", " ": " "})


def norm(s):
    s = unicodedata.normalize("NFC", s or "")
    return NIQQUD.sub("", s).translate(QUOTES).strip()


def key(s):
    """Clé de comparaison : sans niqqud, guillemets, tirets, espaces ni préfixe « סעיף »."""
    s = norm(s).lower()
    s = re.sub(r"^(סעיף|סעיפים|sec(tion)?\.?|§|art(icle)?\.?)\s*", "", s)
    return re.sub(r"[\s\"'\-().,]", "", s)


def title_key(s):
    s = norm(s)
    s = re.sub(r",?\s*(ה?תש[א-ת\"']*|ה?תר[א-ת\"']*)\s*-?\s*\d{4}\s*$", "", s)
    s = re.sub(r",?\s*\d{4}\s*$", "", s)
    s = re.sub(r"\s*\[[^\]]*\]\s*$", "", s)
    return re.sub(r"[\s\"'\-,.]", "", s)


def connect(path, readonly=True):
    if readonly:
        con = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=30)
    else:
        con = sqlite3.connect(path, timeout=60)
        con.execute("PRAGMA journal_mode=WAL")
    con.row_factory = sqlite3.Row
    return con


def wiki_url(title, anchor=""):
    u = WIKI + title.replace(" ", "_")
    return u + ("#" + anchor.replace(" ", "_") if anchor else "")


# ---------------------------------------------------------------- wikitext -> texte

def _split_args(body):
    args, depth, cur, i = [], 0, [], 0
    while i < len(body):
        two = body[i:i + 2]
        if two in ("{{", "[["):
            depth += 1
            cur.append(two)
            i += 2
            continue
        if two in ("}}", "]]") and depth:
            depth -= 1
            cur.append(two)
            i += 2
            continue
        if body[i] == "|" and depth == 0:
            args.append("".join(cur))
            cur = []
        else:
            cur.append(body[i])
        i += 1
    args.append("".join(cur))
    return args


def templates(text):
    """Découpe le texte en morceaux : str ou (nom, positionnels, nommés)."""
    out, i, n = [], 0, len(text)
    buf = []
    while i < n:
        if text.startswith("{{", i):
            depth, j = 0, i
            while j < n:
                if text.startswith("{{", j):
                    depth += 1
                    j += 2
                elif text.startswith("}}", j):
                    depth -= 1
                    j += 2
                    if depth == 0:
                        break
                else:
                    j += 1
            if depth:
                buf.append(text[i:])
                break
            if buf:
                out.append("".join(buf))
                buf = []
            parts = _split_args(text[i + 2:j - 2])
            name, pos, named = parts[0].strip(), [], {}
            for p in parts[1:]:
                m = re.match(r"^\s*([^=\[\]{}|]{1,20})=(.*)$", p, re.S)
                if m and not m.group(1).strip().isdigit():
                    named[m.group(1).strip()] = m.group(2)
                else:
                    pos.append(m.group(2) if m else p)
            out.append((name, pos, named))
            i = j
        else:
            buf.append(text[i])
            i += 1
    if buf:
        out.append("".join(buf))
    return out


def inline(text):
    """Rend un fragment en texte brut (liens, notes, gras, balises)."""
    res = []
    for t in templates(text):
        if isinstance(t, str):
            res.append(t)
            continue
        name, pos, named = t
        if name in ("ח:פנימי", "ח:חיצוני", "ח:קישור", "ח:פנימי-מקוצר"):
            res.append(inline(pos[1] if len(pos) > 1 and pos[1].strip() else (pos[0] if pos else "")))
        elif name in ("ח:הערה", "ח:הערה-מוסתרת", "ח:טבלה-הערה", "ח:מחוק", "ח:מודגש", "ח:נטוי", "ח:קו-תחתי", "ח:מוקטן"):
            res.append(inline(pos[0]) if pos else "")
        elif name.startswith("ח:"):
            continue
        elif name in ("ש", "שורה"):
            res.append("\n")
        elif pos:
            res.append(inline(pos[-1]))
    s = "".join(res)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", s)
    s = re.sub(r"'{2,5}", "", s)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"&nbsp;", " ", s)
    return re.sub(r"[ \t]+", " ", s).strip()


LEVELS = {"ח:ת": 0, "ח:תת": 1, "ח:תתת": 2, "ח:תתתת": 3, "ח:תתתתת": 4, "ח:תתתתתת": 5}


def parse(wikitext):
    """Analyse une page du ספר החוקים הפתוח.

    Renvoie dict : full_title, knesset_id, pubs [(citation, nom, url)], sections [dict num, anchor, title, amend, path, text].
    """
    law = {"full_title": "", "knesset_id": None, "pubs": [], "sections": [], "preamble": ""}
    heads = {}
    cur = None
    pre = []
    in_preamble = False

    def path():
        return " > ".join(heads[k] for k in sorted(heads) if heads[k])

    def open_section(num, title, amend, anchor):
        nonlocal cur
        cur = {"num": num, "anchor": anchor, "title": title, "amend": amend, "path": path(), "lines": []}
        law["sections"].append(cur)

    for raw in wikitext.splitlines():
        line = raw.strip()
        if not line or line.startswith("[[קטגוריה:") or line.startswith("__"):
            continue
        parts = templates(line)
        first = parts[0] if parts else ""
        if isinstance(first, str) and not first.strip() and len(parts) > 1:
            parts = parts[1:]
            first = parts[0]
        for t in parts:
            if isinstance(t, tuple):
                name, pos, named = t
                if name == "ח:מאגר" and pos and pos[0].strip().isdigit():
                    law["knesset_id"] = int(pos[0].strip())
                elif name == "ח:תיבה":
                    law["pubs"].append((inline(pos[0]) if pos else "", inline(pos[1]) if len(pos) > 1 else "",
                                        pos[2].strip().replace("{{=}}", "=").replace("&amp;", "&") if len(pos) > 2 else ""))
        if isinstance(first, tuple):
            name, pos, named = first
            rest = inline(line[len(_raw_template(line)):]) if line.startswith("{{") else ""
            if name == "ח:כותרת":
                law["full_title"] = inline(pos[0]) if pos else ""
                continue
            if name == "ח:פתיח-התחלה":
                in_preamble = True
                continue
            if name == "ח:סוגר":
                in_preamble = False
                continue
            if name in ("ח:התחלה", "ח:סוף", "ח:מפריד"):
                continue
            m = re.fullmatch(r"ח:קטע(\d)", name)
            if m:
                lvl = int(m.group(1))
                title = inline(pos[1]) if len(pos) > 1 else ""
                if title == "תוכן עניינים":
                    cur = None
                    continue
                for k in [k for k in heads if k >= lvl]:
                    del heads[k]
                heads[lvl] = title
                cur = None
                continue
            if name in ("ח:סעיף", "ח:סעיף*"):
                num = inline(pos[0]) if pos else ""
                title = inline(pos[1]) if len(pos) > 1 else ""
                amend = inline(pos[2]) if len(pos) > 2 else ""
                anchor = named.get("עוגן", "").strip() or ("סעיף " + num if num and name == "ח:סעיף" else "")
                if name == "ח:סעיף*" and not num and not anchor:
                    if cur is None or cur["lines"] or cur["title"]:
                        open_section("", "", "", "")
                    continue
                open_section(num, title, amend, anchor)
                if rest:
                    cur["lines"].append(rest)
                continue
            if name == "ח:חתימות":
                open_section("", "חתימות", "", "חתימות")
                cur["lines"].append(inline(pos[0]) if pos else "")
                continue
            if name in LEVELS:
                label = inline(pos[0]) if pos and "=" not in pos[0] else ""
                txt = ("  " * LEVELS[name]) + (label + " " if label else "") + rest
                if in_preamble:
                    pre.append(txt.strip())
                    continue
                if cur is None:
                    open_section("", "", "", "")
                cur["lines"].append(txt.rstrip())
                continue
        txt = inline(line)
        if line.startswith("<div") or line.startswith("</div") or line.startswith("{|") or line.startswith("|}"):
            txt = txt if not line.startswith("<div class=\"law-toc") else ""
        if not txt:
            continue
        if line.startswith("*"):
            txt = "• " + txt.lstrip("* ")
        if in_preamble:
            pre.append(txt)
        elif cur is not None:
            cur["lines"].append(txt)
        elif law["sections"] or heads:
            open_section("", "", "", "")
            cur["lines"].append(txt)
        else:
            pre.append(txt)
    law["preamble"] = "\n".join(p for p in pre if re.search(r"[א-תA-Za-z]{2}", p)).strip()
    for s in law["sections"]:
        s["text"] = "\n".join(l for l in s.pop("lines") if l.strip()).strip()
    law["sections"] = [s for s in law["sections"] if s["text"] or s["title"] or s["num"]]
    return law


def _raw_template(line):
    depth, j = 0, 0
    while j < len(line):
        if line.startswith("{{", j):
            depth += 1
            j += 2
        elif line.startswith("}}", j):
            depth -= 1
            j += 2
            if depth == 0:
                return line[:j]
        else:
            j += 1
    return line


def kind_of(title):
    t = norm(title)
    for prefix, kind in (("חוק-יסוד", "basic_law"), ("חוק יסוד", "basic_law"), ("חוק", "law"), ("פקודת", "ordinance"),
                         ("פקודה", "ordinance"), ("תקנות", "regulations"), ("תקנה", "regulations"), ("צו", "order"),
                         ("כללי", "rules"), ("כללים", "rules"), ("הוראות", "rules"), ("אכרזת", "proclamation"),
                         ("אכרזה", "proclamation"), ("הודעת", "notice"), ("הודעה", "notice"), ("החלטת", "decision"),
                         ("The ", "mandate"), ("דבר המלך", "mandate"), ("דבר-המלך", "mandate")):
        if t.startswith(prefix):
            return kind
    return "other"
