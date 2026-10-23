import html
import os
import time

SITE = os.environ.get("MISHPAT_PUBLIC_URL", "https://mishpat.studjoow.com").rstrip("/")
MCP_URL = SITE + "/mcp"
OLB = "https://he.wikisource.org/wiki/%D7%95%D7%99%D7%A7%D7%99%D7%98%D7%A7%D7%A1%D7%98:%D7%A1%D7%A4%D7%A8_%D7%94%D7%97%D7%95%D7%A7%D7%99%D7%9D_%D7%94%D7%A4%D7%AA%D7%95%D7%97"
CC = "https://creativecommons.org/licenses/by-sa/4.0/"
REPO = os.environ.get("MISHPAT_REPO_URL", "https://github.com/JohnJackHouzi/mishpat-israel")

FONTS = """@font-face{font-family:'Instrument Serif';font-style:normal;font-weight:400;font-display:swap;src:url(/static/fonts/instrument-serif-normal-400.woff2) format('woff2')}
@font-face{font-family:'Plus Jakarta Sans';font-style:normal;font-weight:400 700;font-display:swap;src:url(/static/fonts/plus-jakarta-sans-normal-400-700.woff2) format('woff2')}
@font-face{font-family:'Geist Mono';font-style:normal;font-weight:400 500;font-display:swap;src:url(/static/fonts/geist-mono-normal-400.woff2) format('woff2')}"""

CSS = """
:root{--bg:#f2f3fb;--paper:#fff;--fg:#1b0b16;--ink:#3a3f4e;--muted:#7e8493;--line:#d8dbe4;--accent:#b1338a;--accent2:#e0539f;
--soft:#eddaec;--deep:#040e30;--warn:#fff4e5;--warnline:#f0c48a;
--serif:'Instrument Serif',Georgia,serif;--sans:'Plus Jakarta Sans','Noto Sans Hebrew','Arial Hebrew',system-ui,-apple-system,'Segoe UI',sans-serif;
--mono:'Geist Mono',ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root{--bg:#040e30;--paper:#0a1640;--fg:#f7f8fb;--ink:#c9cdd8;--muted:#8a90a3;--line:#1e2b5e;
--accent:#e0539f;--soft:#2a1640;--warn:#2a2410;--warnline:#6b5420}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 var(--sans)}
a{color:var(--accent)}
.wrap{max-width:960px;margin:0 auto;padding:0 16px}
header.top{background:var(--deep);color:#f7f8fb}
header.top .wrap{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-top:14px;padding-bottom:14px}
header.top a{color:#f7f8fb;text-decoration:none}
.brand{display:flex;align-items:center;gap:10px;font-weight:700}
.brand img{width:28px;height:28px;border-radius:6px}
.lang a{border:1px solid rgba(255,255,255,.3);border-radius:999px;padding:4px 12px;font-size:14px}
.hero{background:var(--deep);color:#f7f8fb;padding:48px 0 56px}
.hero h1{font:400 clamp(36px,6vw,60px)/1.05 var(--serif);margin:0 0 16px}
.hero h1 em{color:var(--accent2);font-style:italic}
.hero p{max-width:680px;color:#c9cdd8;font-size:18px;margin:0 0 24px}
.url{display:flex;flex-wrap:wrap;gap:8px;align-items:center;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.15);
border-radius:12px;padding:12px 14px;max-width:640px}
.url code{font:500 15px var(--mono);color:#fff;word-break:break-all;flex:1;direction:ltr;text-align:left}
.url button{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:8px 14px;font:600 14px var(--sans);cursor:pointer}
section{padding:40px 0;border-bottom:1px solid var(--line)}
h2{font:400 34px/1.1 var(--serif);margin:0 0 18px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
.card{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:18px}
.card h3{margin:0 0 6px;font-size:16px}.card p{margin:0;color:var(--ink);font-size:15px}
.card code{font:13px var(--mono);color:var(--accent)}
.warn{background:var(--warn);border:1px solid var(--warnline);border-radius:14px;padding:18px;color:var(--fg)}
.stats{display:flex;flex-wrap:wrap;gap:24px;margin-top:8px}
.stats div{min-width:140px}.stats b{display:block;font:400 34px var(--serif);color:var(--accent)}
.stats span{color:var(--muted);font-size:14px}
ol.steps{padding-inline-start:20px}ol.steps li{margin-bottom:8px}
footer{padding:28px 0 40px;color:var(--muted);font-size:14px}
footer p{margin:6px 0}
[dir=rtl] .url code{text-align:left}
"""

T = {
    "en": {
        "dir": "ltr", "title": "Mishpat by Studjoow: Israeli law for AI assistants",
        "desc": "MCP server connecting AI assistants to Israeli legislation: laws, regulations, Reshumot publications and Knesset legislative history, with sourced answers.",
        "other": ("עברית", "/he"),
        "h1": "Israeli law, <em>sourced</em>, inside your AI assistant.",
        "lead": "An MCP server that lets Claude, ChatGPT, Cursor and other assistants read Israeli laws and regulations section by section, search them, check references and trace every amendment back to its official publication in Reshumot.",
        "copy": "Copy",
        "connect_h": "Connect in one minute",
        "connect": [
            "<b>Claude</b> (claude.ai or desktop): Settings, Connectors, Add custom connector, paste the address above.",
            "<b>ChatGPT</b> (developer mode): Settings, Connectors, Create, paste the address, no authentication.",
            "<b>Cursor, VS Code, Claude Code</b>: add a remote MCP server of type streamable HTTP with this address.",
            "Ask in English, French or Hebrew: the assistant searches the Hebrew texts and cites the section and its source.",
        ],
        "what_h": "What it covers",
        "what": [
            ("Consolidated legislation", "About 6,000 laws, Basic Laws, ordinances, regulations and orders, section by section, from the Open Law Book of Hebrew Wikisource, synchronised every night."),
            ("Official publications", "For each text, the list of its publications in Reshumot (Sefer HaChukim, Kovetz HaTakanot), original and amendments, with links to the official PDFs."),
            ("Legislative history", "Knesset records: status in force or repealed, publication dates, amending laws, former names."),
            ("Reference checks", "Verifies that a law and section exist and that a quote appears word for word, before the assistant cites it."),
        ],
        "tools_h": "Tools",
        "tools": [
            ("read_section", "Text of one section, its part, amendment years and Reshumot PDFs."),
            ("search_law", "Full-text search in Hebrew, prefixes handled, primary laws first."),
            ("find_law", "Find a law or regulation by title."),
            ("read_law", "Table of contents and list of publications of a text."),
            ("law_history", "Amendments, dates, status and official PDFs."),
            ("verify_references", "Check references and quotes before citing."),
            ("database_status", "Dates and counts of the data."),
        ],
        "limits_h": "Read this before relying on it",
        "limits": [
            "Israel has no official consolidated version of its laws. The text served here is the community consolidation of the Open Law Book (Hebrew Wikisource): reliable and widely used, but unofficial, and it can lag behind a recent amendment.",
            "The binding text is the publication in Reshumot. Every answer links to the official PDFs: check them for anything recent or decisive.",
            "Versions at a past date are not provided. Case law is not covered yet.",
            "Legal information, not legal advice. For a specific situation, consult an Israeli lawyer.",
        ],
        "data_h": "Data",
        "texts": "texts", "sections": "sections", "sync": "last sync", "knesset": "Knesset data up to",
        "sources": "Sources and licences",
        "src": [
            'Consolidated texts: <a href="%s">ספר החוקים הפתוח</a>, Hebrew Wikisource contributors, licence <a href="%s">CC BY-SA 4.0</a>. The texts are reformatted (plain text, split by section); the reformatted texts are shared under the same licence.' % (OLB, CC),
            "Legislative history: Knesset OData API (Israeli open government data). When the API is not reachable, the public mirror ZeAlenu/knesset-data (ODC-BY) is used and its date is shown.",
            "Official publications: Reshumot, PDFs hosted by the Knesset (fs.knesset.gov.il) and other official sites. Some of these sites only answer from Israel.",
            "This service is independent: it is not endorsed by Wikisource, the Wikimedia Foundation, the Knesset or the Israeli government.",
        ],
        "pub": "Published by Studjoow.",
        "fr": 'French and EU law: <a href="https://droit.studjoow.com">droit.studjoow.com</a>',
    },
    "he": {
        "dir": "rtl", "title": "משפט by Studjoow: הדין הישראלי לעוזרי בינה מלאכותית",
        "desc": "שרת MCP שמחבר עוזרי בינה מלאכותית לחקיקה הישראלית: חוקים, תקנות, פרסומים ברשומות והיסטוריה חקיקתית מהכנסת, עם מקורות לכל תשובה.",
        "other": ("English", "/"),
        "h1": "הדין הישראלי, <em>עם מקורות</em>, בתוך עוזר הבינה המלאכותית שלכם.",
        "lead": "שרת MCP שמאפשר ל־Claude, ל־ChatGPT, ל־Cursor ולעוזרים אחרים לקרוא חוקים ותקנות סעיף אחר סעיף, לחפש בהם, לאמת הפניות ולהגיע מכל תיקון לפרסום הרשמי שלו ברשומות.",
        "copy": "העתקה",
        "connect_h": "התחברות בדקה",
        "connect": [
            "<b>Claude</b> (claude.ai או אפליקציית מחשב): הגדרות, מחברים, הוספת מחבר מותאם, הדבקת הכתובת שלמעלה.",
            "<b>ChatGPT</b> (מצב מפתחים): הגדרות, מחברים, יצירה, הדבקת הכתובת, ללא אימות.",
            "<b>Cursor, VS Code, Claude Code</b>: הוספת שרת MCP מרוחק מסוג streamable HTTP עם הכתובת הזו.",
            "אפשר לשאול בעברית, באנגלית או בצרפתית: העוזר מחפש בנוסח העברי ומצטט את הסעיף ואת מקורו.",
        ],
        "what_h": "מה כלול",
        "what": [
            ("חקיקה בנוסח משולב", "כ־6,000 חוקים, חוקי־יסוד, פקודות, תקנות וצווים, סעיף אחר סעיף, מתוך ספר החוקים הפתוח בוויקיטקסט, בסנכרון לילי."),
            ("פרסומים רשמיים", "לכל דבר חקיקה: רשימת הפרסומים ברשומות (ספר החוקים, קובץ התקנות), המקור והתיקונים, עם קישורים לקובצי ה־PDF הרשמיים."),
            ("היסטוריה חקיקתית", "נתוני הכנסת: תוקף או ביטול, תאריכי פרסום, חוקים מתקנים ושמות קודמים."),
            ("אימות הפניות", "בדיקה שהחוק והסעיף קיימים ושהציטוט מופיע מילה במילה, לפני שהעוזר מצטט."),
        ],
        "tools_h": "כלים",
        "tools": [
            ("read_section", "נוסח סעיף, מיקומו בחוק, שנות התיקון וקובצי רשומות."),
            ("search_law", "חיפוש טקסט מלא בעברית, כולל אותיות שימוש, חוקים ראשיים תחילה."),
            ("find_law", "איתור חוק או תקנות לפי שם."),
            ("read_law", "תוכן העניינים ורשימת הפרסומים של דבר חקיקה."),
            ("law_history", "תיקונים, תאריכים, תוקף וקובצי PDF רשמיים."),
            ("verify_references", "אימות הפניות וציטוטים לפני ציטוט."),
            ("database_status", "תאריכי הנתונים והיקפם."),
        ],
        "limits_h": "חשוב לקרוא לפני שמסתמכים",
        "limits": [
            "בישראל אין נוסח משולב רשמי של החקיקה. הנוסח המוצג כאן הוא הנוסח המשולב של ספר החוקים הפתוח בוויקיטקסט: מקור אמין ונפוץ, אך לא רשמי, וייתכן שאינו כולל תיקון חדש.",
            "הנוסח המחייב הוא הפרסום ברשומות. כל תשובה מקשרת לקובצי ה־PDF הרשמיים: יש לבדוק אותם בכל עניין חדש או מכריע.",
            "אין נוסחים היסטוריים לפי תאריך. פסיקה עדיין אינה כלולה.",
            "מידע משפטי בלבד ולא ייעוץ משפטי. במקרה קונקרטי יש לפנות לעורך דין.",
        ],
        "data_h": "נתונים",
        "texts": "דברי חקיקה", "sections": "סעיפים", "sync": "סנכרון אחרון", "knesset": "נתוני הכנסת עד",
        "sources": "מקורות ורישיונות",
        "src": [
            'נוסח משולב: <a href="%s">ספר החוקים הפתוח</a>, תורמי ויקיטקסט העברי, ברישיון <a href="%s">CC BY-SA 4.0</a>. הנוסח עובד (טקסט פשוט, חלוקה לסעיפים) ומופץ באותו רישיון.' % (OLB, CC),
            "היסטוריה חקיקתית: ממשק OData של הכנסת (מידע ממשלתי פתוח). כשהממשק אינו זמין, נעשה שימוש במראה הציבורית ZeAlenu/knesset-data (ODC-BY) ותאריכה מוצג.",
            "פרסומים רשמיים: רשומות, קבצים באתר הכנסת (fs.knesset.gov.il) ובאתרים רשמיים אחרים. חלק מהאתרים זמינים רק מישראל.",
            "השירות עצמאי ואינו מטעם ויקיטקסט, קרן ויקימדיה, הכנסת או ממשלת ישראל.",
        ],
        "pub": "בהוצאת Studjoow.",
        "fr": 'דין צרפתי ואירופי: <a href="https://droit.studjoow.com">droit.studjoow.com</a>',
    },
}

_cache = {}


def render(etat_fn, lang="en"):
    c = _cache.get(lang)
    if c and time.monotonic() - c[0] < 600:
        return c[1]
    t = T[lang]
    e = etat_fn()
    lo, kn = e.get("lois") or {}, e.get("knesset") or {}
    esc = html.escape
    li = lambda items: "".join("<li>%s</li>" % x for x in items)  # noqa: E731
    cards = lambda items: "".join("<div class=card><h3>%s</h3><p>%s</p></div>" % (esc(a), esc(b)) for a, b in items)  # noqa: E731
    tools = "".join("<div class=card><h3><code>%s</code></h3><p>%s</p></div>" % (esc(a), esc(b)) for a, b in t["tools"])
    stats = ""
    if "textes" in lo:
        stats = ("<div class=stats><div><b>%s</b><span>%s</span></div><div><b>%s</b><span>%s</span></div>"
                 "<div><b>%s</b><span>%s</span></div>%s</div>" % (
                     "{:,}".format(lo["textes"]), t["texts"], "{:,}".format(lo["sections"]), t["sections"],
                     esc(lo.get("synchro", "")[:10]), t["sync"],
                     "<div><b>%s</b><span>%s</span></div>" % (esc(kn.get("donnees_jusqu_au", "")), t["knesset"])
                     if kn.get("donnees_jusqu_au") else ""))
    jsonld = ('{"@context":"https://schema.org","@type":"WebApplication","name":"Mishpat by Studjoow","url":"%s",'
              '"applicationCategory":"DeveloperApplication","inLanguage":["he","en"],"publisher":{"@type":"Organization",'
              '"name":"Studjoow","url":"https://studjoow.com"},"isBasedOn":"%s"}' % (SITE, OLB))
    body = f"""<!doctype html><html lang="{lang}" dir="{t['dir']}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(t['title'])}</title><meta name="description" content="{esc(t['desc'])}">
<link rel="canonical" href="{SITE}{'/he' if lang == 'he' else '/'}">
<link rel="alternate" hreflang="en" href="{SITE}/"><link rel="alternate" hreflang="he" href="{SITE}/he">
<link rel="icon" href="/favicon.ico"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:title" content="{esc(t['title'])}"><meta property="og:description" content="{esc(t['desc'])}">
<meta name="theme-color" content="#040e30">
<script type="application/ld+json">{jsonld}</script>
<style>{FONTS}{CSS}</style></head><body>
<header class=top><div class=wrap><a class=brand href="{'/he' if lang == 'he' else '/'}"><img src="/static/icones/icone-192.png" alt="">Mishpat by Studjoow</a>
<span class=lang><a href="{t['other'][1]}" hreflang="{'he' if lang == 'en' else 'en'}">{t['other'][0]}</a></span></div></header>
<div class=hero><div class=wrap><h1>{t['h1']}</h1><p>{esc(t['lead'])}</p>
<div class=url><code id=u>{MCP_URL}</code><button type=button onclick="navigator.clipboard.writeText(document.getElementById('u').textContent);this.textContent='✓'">{t['copy']}</button></div></div></div>
<main class=wrap>
<section><h2>{t['connect_h']}</h2><ol class=steps>{li(t['connect'])}</ol></section>
<section><h2>{t['limits_h']}</h2><div class=warn><ul>{li(esc(x) for x in t['limits'])}</ul></div></section>
<section><h2>{t['what_h']}</h2><div class=grid>{cards(t['what'])}</div></section>
<section><h2>{t['tools_h']}</h2><div class=grid>{tools}</div></section>
<section><h2>{t['data_h']}</h2>{stats}</section>
<section><h2>{t['sources']}</h2><ul>{li(t['src'])}</ul></section>
</main>
<footer><div class=wrap><p>{t['pub']} <a href="https://studjoow.com">studjoow.com</a></p><p>{t['fr']}</p>
{f'<p><a href="{REPO}">{REPO.replace("https://", "")}</a></p>' if REPO else ''}</div></footer>
</body></html>"""
    _cache[lang] = (time.monotonic(), body)
    return body


def robots():
    return "User-agent: *\nAllow: /\nDisallow: /mcp\nSitemap: %s/sitemap.xml\n" % SITE


def sitemap():
    urls = "".join("<url><loc>%s%s</loc></url>" % (SITE, p) for p in ("/", "/he", "/llms.txt"))
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % urls


def llms(etat_fn):
    e = etat_fn()
    lo, kn = e.get("lois") or {}, e.get("knesset") or {}
    t = T["en"]
    out = ["# Mishpat by Studjoow", "", "> " + t["desc"], "",
           "MCP endpoint (streamable HTTP, no authentication): " + MCP_URL, "",
           "## Tools"] + ["- %s: %s" % x for x in t["tools"]] + ["", "## Limits"] + ["- " + x for x in t["limits"]]
    if "textes" in lo:
        out += ["", "## Data", "- %d texts, %d sections, last Wikisource sync %s" % (lo["textes"], lo["sections"], lo["synchro"])]
        if kn.get("donnees_jusqu_au"):
            out.append("- Knesset legislative data up to %s" % kn["donnees_jusqu_au"])
    out += ["", "## Sources", "- Open Law Book, Hebrew Wikisource, CC BY-SA 4.0: " + OLB,
            "- Knesset OData API; Reshumot official PDFs", "", "Published by Studjoow (https://studjoow.com)."]
    return "\n".join(out) + "\n"
