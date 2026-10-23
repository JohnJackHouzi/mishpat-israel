import html
import os
import time

import abonnement

SITE = os.environ.get("MISHPAT_PUBLIC_URL", "https://mishpat.studjoow.com").rstrip("/")
MCP_URL = SITE + "/mcp"
OLB = "https://he.wikisource.org/wiki/%D7%95%D7%99%D7%A7%D7%99%D7%98%D7%A7%D7%A1%D7%98:%D7%A1%D7%A4%D7%A8_%D7%94%D7%97%D7%95%D7%A7%D7%99%D7%9D_%D7%94%D7%A4%D7%AA%D7%95%D7%97"
CC = "https://creativecommons.org/licenses/by-sa/4.0/"
REPO = os.environ.get("MISHPAT_REPO_URL", "https://github.com/JohnJackHouzi/mishpat-israel")
LIEN_ABONNEMENT = os.environ.get("MISHPAT_LIEN_ABONNEMENT", "").strip()

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
.prix-grille{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.offre{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:22px;display:flex;flex-direction:column;gap:8px}
.offre.mise{border-color:var(--accent);box-shadow:0 14px 34px -22px var(--accent)}
.offre h3{margin:0;font-size:15px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.offre .montant{font:400 40px/1 var(--serif);color:var(--fg)}.offre .montant small{font:14px var(--sans);color:var(--muted)}
.offre ul{margin:6px 0 10px;padding-inline-start:18px;color:var(--ink);font-size:14.5px}
.btn{display:inline-block;text-align:center;font:600 15px var(--sans);border-radius:10px;padding:11px 16px;text-decoration:none;border:1px solid var(--accent)}
.btn-1{background:var(--accent);color:#fff}.btn-2{background:transparent;color:var(--accent)}
.btn[aria-disabled=true]{opacity:.55;pointer-events:none}
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
        "pricing_h": "Pricing",
        "trial": ("Free trial", "%d requests per day on the public address, no sign-up."),
        "plans": {"particulier": "Personal", "pro": "Pro", "pro-an": "Pro yearly"},
        "per": {"month": "month", "year": "year"},
        "perks": {"particulier": ["%s requests per day", "All tools and sources", "Sign in from Claude or ChatGPT"],
                  "pro": ["%s requests per day", "Professional use, invoice to your company", "Priority e-mail support"],
                  "pro-an": ["%s requests per day", "Two months free", "Invoice to your company"]},
        "subscribe": "Subscribe", "soon": "Opening soon", "account": "Already subscribed? My account",
        "vat": "Prices in shekels include VAT. No commitment: cancel at any time.",
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
        "pricing_h": "מחירים",
        "trial": ("ניסיון חינם", "%d בקשות ביום בכתובת הציבורית, ללא הרשמה."),
        "plans": {"particulier": "פרטי", "pro": "Pro", "pro-an": "Pro שנתי"},
        "per": {"month": "חודש", "year": "שנה"},
        "perks": {"particulier": ["%s בקשות ביום", "כל הכלים והמקורות", "התחברות מתוך Claude או ChatGPT"],
                  "pro": ["%s בקשות ביום", "שימוש מקצועי, חשבונית על שם החברה", "תמיכה מועדפת בדוא״ל"],
                  "pro-an": ["%s בקשות ביום", "חודשיים חינם", "חשבונית על שם החברה"]},
        "subscribe": "להרשמה", "soon": "בקרוב", "account": "כבר מנויים? החשבון שלי",
        "vat": "המחירים בשקלים כוללים מע״מ. ללא התחייבות: ביטול בכל עת.",
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


def tarifs(lang):
    t = T[lang]
    cartes = ['<div class=offre><h3>%s</h3><div class=montant>0</div><p>%s</p></div>'
              % (html.escape(t["trial"][0]), html.escape(t["trial"][1] % abonnement.ESSAI_PAR_JOUR))]
    for k, o in abonnement.OFFRES.items():
        perks = "".join("<li>%s</li>" % html.escape(x % "{:,}".format(o["plafond"]) if "%s" in x else x) for x in t["perks"][k])
        bouton = ('<a class="btn btn-1" href="%s?offre=%s">%s</a>' % (LIEN_ABONNEMENT, k, t["subscribe"]) if LIEN_ABONNEMENT
                  else '<a class="btn btn-2" aria-disabled=true>%s</a>' % t["soon"])
        cartes.append('<div class="offre%s"><h3>%s</h3><div class=montant><bdi>%s</bdi> <small>/ %s</small></div><ul>%s</ul>%s</div>'
                      % (" mise" if k == "particulier" else "", html.escape(t["plans"][k]), html.escape(abonnement.montant(o)),
                         t["per"][o["intervalle"]], perks, bouton))
    return ('<div class=prix-grille>%s</div><p class=note>%s <a href="/compte">%s</a></p>'
            % ("".join(cartes), html.escape(t["vat"]), html.escape(t["account"])))


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
<section id=pricing><h2>{t['pricing_h']}</h2>{tarifs(lang)}</section>
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


# ---------------------------------------------------------------- abonnement, compte, pages légales

EDITEUR = ("John Houzi, trading as Studjoow, licensed dealer in Israel (Osek Murshe), "
           "Tax ID 337927834, 49 Abarbanel, Tel Aviv 6608912, Israel")
CONTACT = "hello@studjoow.com"

CSS_DOC = """
.doc{max-width:760px;padding:28px 0 40px}
.doc h1{font:400 clamp(40px,6vw,60px)/1.05 var(--serif);margin:0 0 18px}
.doc h2{font:400 28px/1.15 var(--serif);margin:36px 0 10px}
.doc h3{font:600 17px var(--sans);margin:22px 0 8px}
.doc p,.doc li{color:var(--ink)}
.maj{font:12.5px var(--mono);color:var(--muted)}
.carte{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:26px 24px;margin:20px 0;max-width:640px}
.carte h2{margin-top:0}
.coche{display:flex;gap:12px;align-items:flex-start;margin:14px 0;font-size:15px;color:var(--ink)}
.coche input{margin-top:4px;width:18px;height:18px;accent-color:var(--accent);flex:none}
.champ{width:100%;font:15px var(--mono);padding:12px 14px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--fg)}
.alerte{border-left:3px solid #bf000f;background:var(--paper);padding:12px 16px;border-radius:0 10px 10px 0;margin:14px 0}
.info{border-left:3px solid #00a06d;background:var(--paper);padding:12px 16px;border-radius:0 10px 10px 0;margin:14px 0}
.statut{font:600 12px var(--mono);letter-spacing:.1em;text-transform:uppercase;padding:4px 8px;border-radius:6px;border:1.5px solid currentColor}
.statut.actif{color:#00a06d}.statut.suspendu{color:#f99c00}.statut.revoque{color:#bf000f}
dl.fiche{display:grid;grid-template-columns:150px 1fr;gap:8px 16px;margin:18px 0;font-size:15px}
dl.fiche dt{color:var(--muted)}dl.fiche dd{margin:0}
.choix-offres{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 0}
.choix{font:500 13.5px var(--sans);text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:8px 14px;color:var(--ink);background:var(--paper)}
.choix.actif{border-color:var(--accent);color:var(--accent);font-weight:600}
form.ligne{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}form.ligne .champ{flex:1;min-width:200px}
.mini{font-size:13.5px;color:var(--muted)}
.url-perso{display:flex;gap:8px;flex-wrap:wrap;align-items:center;background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:12px}
.url-perso code{font:14px var(--mono);word-break:break-all;flex:1}
button.btn{cursor:pointer}
@media (max-width:480px){dl.fiche{grid-template-columns:1fr}}
"""


def nombre(n):
    return "{:,}".format(n)


def gabarit(titre, contenu, description="", indexer=True):
    e = html.escape
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titre)} · Mishpat by Studjoow</title><meta name="description" content="{e(description or titre)}">
<meta name="robots" content="{'index,follow' if indexer else 'noindex,nofollow'}"><meta name="theme-color" content="#040e30">
<link rel="icon" href="/favicon.ico"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<style>{FONTS}{CSS}{CSS_DOC}</style></head><body>
<header class=top><div class=wrap><a class=brand href="/"><img src="/static/icones/icone-192.png" alt="">Mishpat by Studjoow</a>
<span class=lang><a href="/compte">My account</a></span></div></header>
<main class="wrap doc">{contenu}</main>
<footer><div class=wrap><p>Published by Studjoow. <a href="https://studjoow.com">studjoow.com</a></p>
<p><a href="/terms">Terms</a> · <a href="/privacy">Privacy</a> · <a href="/legal">Legal notice</a> · <a href="/compte">My account</a></p>
<p>Legal information, not legal advice.</p></div></footer></body></html>"""


def page_ferme():
    return gabarit("Subscriptions opening soon", "<h1>Soon.</h1><p>Subscriptions open shortly. Meanwhile the free trial "
                   "remains available on the public address <code>%s/mcp</code>.</p>"
                   '<p><a class="btn btn-2" href="/">Back to home</a></p>' % SITE, indexer=False)


def _periode(o):
    return "month" if o["intervalle"] == "month" else "year"


def page_abonnement(erreur=None, offre="particulier"):
    o = abonnement.OFFRES.get(offre, abonnement.OFFRES["particulier"])
    alerte = '<p class="alerte">%s</p>' % html.escape(erreur) if erreur else ""
    pro = offre != "particulier"
    avantages = ("<li>%s requests per day per personal address (and at most 60 per minute)</li>" % nombre(o["plafond"])
                 + ("<li>Invoice in your company's name: company name and VAT number asked at payment</li>"
                    "<li>Priority e-mail support</li>" if pro else "")
                 + "<li>All tools and sources; legislation updated every night</li>"
                 + "<li>No commitment: cancel at any time from your account</li>")
    choix = "".join('<a class="choix%s" href="/abonnement?offre=%s">%s · %s / %s</a>'
                    % (" actif" if k == offre else "", k, x["nom"], abonnement.montant(x), _periode(x))
                    for k, x in abonnement.OFFRES.items())
    return gabarit("Subscribe", """<h1>Subscribe.</h1>
<p>Israeli legislation, section by section, in Claude, ChatGPT and any MCP-compatible assistant.</p>
<nav class="choix-offres" aria-label="Plans">%s</nav>
<div class="carte">
<p class="mini">%s plan</p>
<p class="offre" style="border:0;padding:0;background:none"><span class=montant><bdi>%s</bdi> <small>/ %s</small></span></p>
<ul>%s</ul>
%s
<form method="post" action="/abonnement?offre=%s">
<input type="hidden" name="offre" value="%s">
<label class="coche"><input type="checkbox" name="cgv" value="1" required><span>I accept the <a href="/terms" target="_blank">Terms of service</a> and have read the <a href="/privacy" target="_blank">Privacy policy</a>.</span></label>
<label class="coche"><input type="checkbox" name="execution" value="1" required><span>I want to use the service right away. If I cancel within 14 days, I am refunded minus the days already used.</span></label>
<p><button class="btn btn-1" type="submit">Pay <bdi>%s</bdi> and get my access</button></p>
<p class="mini">Secure payment by Stripe. Your card details never pass through our servers.</p>
</form>
</div>
<p class="mini">Already subscribed? <a href="/compte">Manage my subscription</a>. The code is open source: <a href="%s">self-hosting</a> is free.</p>
""" % (choix, html.escape(o["nom"]), abonnement.montant(o), _periode(o), avantages, alerte, offre, offre,
       abonnement.montant(o), REPO), "%s plan of the Mishpat by Studjoow MCP server." % o["nom"], indexer=False)


def _copier(url):
    e = html.escape(url)
    return ('<div class="url-perso"><code id="u">%s</code><button type="button" class="btn btn-1" '
            "onclick=\"navigator.clipboard.writeText(document.getElementById('u').textContent).then(()=>{this.textContent='Copied'})\">"
            "Copy</button></div>" % e)


INSTALLER = """<h2>Connect with your account</h2>
<ol><li><b>Claude</b>: Settings, Connectors, <b>Add custom connector</b>. Address: <code>%s/abonne/mcp</code>, then <b>Connect</b>: enter your e-mail and the code you receive.</li>
<li><b>ChatGPT</b>: Settings, Apps and connectors, <b>Create</b> a connector with the same address, OAuth authentication.</li>
<li><b>Without sign-in</b> (Claude Code, Cursor, older clients): paste your personal address shown above instead.</li></ol>
<p>If you were using the public trial address, replace it.</p>""" % SITE


def page_merci(url, message=None, email=None, envoye=False):
    if not url:
        return gabarit("Subscription", "<h1>Subscription.</h1><p class=\"info\">%s</p>"
                       '<p><a class="btn btn-1" href="/compte">My account</a></p>' % html.escape(message or ""), indexer=False)
    courriel = ("<p>A copy has just been sent to <b>%s</b>.</p>" % html.escape(email)) if envoye and email else \
        "<p>Copy it now: it will not be shown on this page again.</p>"
    return gabarit("Thank you", """<h1>Thank you.</h1>
<p>Your subscription is active. Simplest: add the connector <code>%s/abonne/mcp</code> and sign in with your e-mail (see below). For clients without sign-in, here is your personal address:</p>
%s
<p class="alerte"><b>Shown only once.</b> Keep it to yourself: it gives access to your subscription. If in doubt, regenerate it from <a href="/compte">your account</a>.</p>
%s
%s
<p class="mini">Manage or cancel at any time: <a href="/compte">My account</a>. Legal information, not legal advice.</p>
""" % (SITE, _copier(url), courriel, INSTALLER), indexer=False)


def page_compte(erreur=None, info=None):
    bloc = ('<p class="alerte">%s</p>' % html.escape(erreur)) if erreur else ('<p class="info">%s</p>' % html.escape(info) if info else "")
    return gabarit("My account", """<h1>My account.</h1>
%s
<div class="carte"><h2>I have my personal address</h2>
<p>Paste it to see the status of your subscription, manage it, cancel it or regenerate the address.</p>
<form class="ligne" method="post" action="/compte"><input class="champ" name="adresse" placeholder="%s/mcp/..." autocomplete="off" required><button class="btn btn-1" type="submit">Open</button></form></div>
<div class="carte"><h2>I lost my address</h2>
<p>Enter the e-mail used for payment: you will receive an access link valid for one hour.</p>
<form class="ligne" method="post" action="/compte/lien"><input class="champ" type="email" name="email" placeholder="you@example.com" autocomplete="email" required><button class="btn btn-2" type="submit">Get a link</button></form></div>
<p class="mini">Not subscribed yet? <a href="/abonnement">Subscribe from <bdi>%s</bdi> per month</a>.</p>
""" % (bloc, SITE, abonnement.montant(abonnement.OFFRES["particulier"])), indexer=False)


def _date(s):
    return "%s/%s/%s" % (s[8:10], s[5:7], s[:4]) if s else "unknown"


def page_gestion(row, url, nouvelle=False, info=None):
    import oauth
    e = html.escape
    o = abonnement.offre_de(row)
    libelles = {"actif": "Active", "suspendu": "Suspended (payment failed)", "revoque": "Ended"}
    fin = ("Cancellation scheduled on %s" if row["resiliation_prevue"] else "Next payment on %s") % _date(row["fin_periode"])
    if row["statut"] == "revoque":
        fin = "Ended on %s" % _date(row["maj_le"])
    email = row["email"] or ""
    if "@" in email:
        nom, dom = email.split("@", 1)
        email = nom[:2] + "•" * max(len(nom) - 2, 1) + "@" + dom
    cache = '<input type="hidden" name="adresse" value="%s">' % e(url)
    lignes = oauth.assistants_connectes(row["abonnement"])
    assistants = ("<ul>%s</ul>" % "".join("<li><b>%s</b> · connected on %s</li>" % (e(l["nom"]), _date(l["dernier"])) for l in lignes)
                  if lignes else '<p class="mini">No assistant connected with « Connect ». Add the connector %s/abonne/mcp in Claude or ChatGPT.</p>' % SITE)
    if info:
        assistants = '<p class="info">%s</p>' % e(info) + assistants
    adresse_html = (_copier(url) + '<p class="info">New address created: the old one no longer works. Replace it in your connectors.</p>') if nouvelle else \
        '<p class="mini">Personal address: <code>%s/mcp/%s…</code></p>' % (SITE, e(url.rsplit("/", 1)[1][:6]))
    return gabarit("My subscription", """<h1>My subscription.</h1>
<div class="carte">
<p><span class="statut %s">%s</span></p>
<dl class="fiche"><dt>Plan</dt><dd>%s · <bdi>%s</bdi> per %s · %s requests per day</dd><dt>E-mail</dt><dd>%s</dd><dt>Billing</dt><dd>%s</dd><dt>Subscriber since</dt><dd>%s</dd></dl>
%s
<form class="ligne" method="post" action="/compte/portail">%s<button class="btn btn-1" type="submit">Manage payment or cancel</button></form>
<form class="ligne" method="post" action="/compte/regenerer" onsubmit="return confirm('The current address will stop working. Continue?')">%s<button class="btn btn-2" type="submit">Regenerate my address</button></form>
<p class="mini">Payment, invoices and cancellation are handled on Stripe's secure portal.</p>
</div>
<div class="carte"><h2>Connected assistants</h2>%s
<form class="ligne" method="post" action="/compte/deconnecter">%s<button class="btn btn-2" type="submit">Disconnect all my assistants</button></form></div>
%s""" % (e(row["statut"]), libelles.get(row["statut"], row["statut"]), e(o["nom"]), e(abonnement.montant(o)), _periode(o),
         nombre(o["plafond"]), e(email), fin, _date(row["cree_le"]), adresse_html, cache, cache, assistants, cache,
         INSTALLER if nouvelle else ""), indexer=False)


def terms():
    ofs = abonnement.OFFRES
    return gabarit("Terms of service", """<h1>Terms of service.</h1>
<p class="maj">Effective 23 October 2026</p>
<h2>1. Provider</h2>
<p>These terms govern the subscription to « Mishpat by Studjoow », available at %(site)s, provided by %(editeur)s (« Studjoow »). Contact: <a href="mailto:%(contact)s">%(contact)s</a>.</p>
<h2>2. The service</h2>
<p>The service is an MCP (Model Context Protocol) server giving a compatible AI assistant read access to Israeli legislation as consolidated by the Open Law Book project of Hebrew Wikisource (CC BY-SA 4.0), and to legislative data of the Knesset. It provides <b>legal information, not legal advice</b>. Israel has no official consolidated text: the binding text is the publication in Reshumot, to which the service links. The consolidated text may lag behind recent amendments. Answers written by the AI assistant are the assistant's own. For a specific situation, consult an Israeli lawyer.</p>
<p>The software is open source (MIT licence): anyone may host it for free. The subscription pays for hosting, the indexed databases, their daily updates and maintenance.</p>
<h2>3. Free trial</h2>
<p>The public address %(site)s/mcp can be used without sign-up, up to %(essai)d tool calls per day and per IP address. This limit may change.</p>
<h2>4. Prices and payment</h2>
<p>Three plans: <b>Personal, %(p1)s per month</b>; <b>Pro, %(p2)s per month</b>; <b>Pro yearly, %(p3)s per year</b>. Prices in shekels include VAT. Payment is taken by card through Stripe at subscription and then at each renewal. Any price change is announced by e-mail at least 30 days before it applies; you may cancel before then.</p>
<h2>5. Access</h2>
<p>After payment you can connect your assistant by signing in with your e-mail, or use a personal address shown once and sent by e-mail. The personal address is strictly personal: do not share it. It can be regenerated at any time from <a href="/compte">My account</a>, the old one then stops working. Each subscription includes, per day, up to %(c1)s tool calls (Personal) or %(c2)s (Pro), and at most 60 requests per minute; beyond that, access resumes the next day. The Pro plans allow professional use, issue invoices in the company's name and include priority e-mail support. In case of clear abuse (resale, public sharing of the address, mass extraction), Studjoow may suspend access after informing the subscriber.</p>
<h2>6. Duration and cancellation</h2>
<p>The subscription is a continuing transaction with no commitment, renewed at each period. You may cancel at any time from <a href="/compte">My account</a> or by e-mail to <a href="mailto:%(contact)s">%(contact)s</a>. The cancellation takes effect within 3 business days and you will not be charged for any period after it (Consumer Protection Law, 5741-1981, section 13D). If you cancel through the Stripe portal, access continues until the end of the period already paid; if you prefer that it stops earlier, write to us and the unused part is refunded. If a payment fails, access is suspended until it is settled, then the subscription ends.</p>
<h2>7. Cancellation within 14 days</h2>
<p>As a distance transaction, you may cancel within 14 days of the subscription (Consumer Protection Law, section 14C). As you asked for the service to start immediately, you pay only for the days used and Studjoow refunds the rest within 14 days, by the same means of payment. No cancellation fee is charged. Rights granted to you by the mandatory law of your country of residence are not affected.</p>
<h2>8. Liability and availability</h2>
<p>Studjoow strives to keep the service available and the data current, without guarantee of continuous availability or completeness. The data come from public sources that Studjoow does not publish. Studjoow is not responsible for answers written by the AI assistant you use, nor for decisions taken on their basis. Nothing in these terms limits rights you have under the law.</p>
<h2>9. Personal data</h2>
<p>See the <a href="/privacy">Privacy policy</a>.</p>
<h2>10. Disputes and governing law</h2>
<p>These terms are governed by the law of the State of Israel, without prejudice to more protective mandatory provisions of the consumer's country of residence. In case of difficulty, write first to <a href="mailto:%(contact)s">%(contact)s</a>: we answer within 7 business days. The competent courts are those of Tel Aviv-Jaffa, subject to the consumer's right to sue in the courts of their place of residence.</p>
""" % {"site": SITE, "editeur": html.escape(EDITEUR), "contact": CONTACT, "essai": abonnement.ESSAI_PAR_JOUR,
       "p1": abonnement.montant(ofs["particulier"]), "p2": abonnement.montant(ofs["pro"]), "p3": abonnement.montant(ofs["pro-an"]),
       "c1": nombre(ofs["particulier"]["plafond"]), "c2": nombre(ofs["pro"]["plafond"])},
        "Terms of service of the Mishpat by Studjoow subscription.")


def legal():
    return gabarit("Legal notice", """<h1>Legal notice.</h1>
<h2>Publisher</h2>
<p>%s.<br>E-mail: <a href="mailto:%s">%s</a>.</p>
<h2>Hosting</h2>
<p>Hetzner Online GmbH, Industriestrasse 25, 91710 Gunzenhausen, Germany, <a href="https://www.hetzner.com">hetzner.com</a>.</p>
<h2>Data</h2>
<p>Consolidated texts: <a href="%s">ספר החוקים הפתוח</a> (Open Law Book), Hebrew Wikisource contributors, licence <a href="%s">CC BY-SA 4.0</a>; the texts are reformatted (plain text, split by section) and shared under the same licence. Legislative data: Knesset OData API. Official publications: Reshumot. This service is not endorsed by Wikisource, the Wikimedia Foundation, the Knesset or the Israeli government.</p>
<h2>Source code</h2>
<p>Open source, MIT licence: <a href="%s">%s</a>.</p>
<h2>Nature of the service</h2>
<p>Legal information, not legal advice. For a specific situation, consult an Israeli lawyer.</p>
""" % (html.escape(EDITEUR), CONTACT, CONTACT, OLB, CC, REPO, REPO), "Legal notice of Mishpat by Studjoow.")


def privacy():
    return gabarit("Privacy policy", """<h1>Privacy.</h1>
<p class="maj">Effective 23 October 2026</p>
<h2>Controller</h2>
<p>%s. Contact: <a href="mailto:%s">%s</a>.</p>
<h2>What we do not collect</h2>
<p>No cookies, trackers or analytics. The legal questions sent by your assistant to the tools are neither stored nor linked to your identity. Fonts are served from this server.</p>
<h2>Free trial</h2>
<p>To apply the limit of %d requests per day, we keep a non-reversible fingerprint of your IP address (HMAC SHA-256 with a secret salt) and a daily counter. These rows are deleted automatically after 2 days.</p>
<h2>Subscription</h2>
<ul><li>Data: e-mail address, Stripe customer and subscription identifiers, status and dates of the subscription, SHA-256 fingerprint of your personal address (never the address itself), time of your request for immediate access.</li>
<li>Assistant sign-in: name of the registered assistant (Claude, ChatGPT...), fingerprints of sign-in tokens (never the tokens themselves), kept 90 days at most; one-time sign-in code valid 10 minutes.</li>
<li>Purposes: providing the service, sending your access and account messages, proving your request for immediate start.</li>
<li>Retention: during the subscription, then 12 months after it ends, before automatic deletion. Payment records are kept by Stripe under its legal obligations.</li></ul>
<h2>Recipients and processors</h2>
<ul><li><b>Stripe</b> (payment): your card details are entered at Stripe and never pass through our servers.</li>
<li><b>Resend</b> (e-mail delivery), United States.</li>
<li><b>Hetzner Online GmbH</b> (hosting), Germany.</li></ul>
<p>Server logs record neither your IP address nor your personal address.</p>
<h2>Your rights</h2>
<p>You may access, correct or delete your data, and object to its use, by writing to <a href="mailto:%s">%s</a>. You may also contact the Israeli Privacy Protection Authority (<a href="https://www.gov.il/en/departments/the_privacy_protection_authority">gov.il</a>) or, in the European Union, your data protection authority.</p>
""" % (html.escape(EDITEUR), CONTACT, CONTACT, abonnement.ESSAI_PAR_JOUR, CONTACT, CONTACT), "Privacy policy of Mishpat by Studjoow.")


CSS_OAUTH = """
:root{--bg:#f2f3fb;--paper:#ffffff;--fg:#1b0b16;--ink:#3a3f4e;--muted:#7e8493;--line:#d8dbe4;--accent:#b1338a;--accent2:#e0539f;--soft:#eddaec;--deep:#040e30;--ko:#bf000f;--ok:#00a06d;
  --serif:'Instrument Serif',Georgia,serif;--sans:'Plus Jakarta Sans',system-ui,-apple-system,'Segoe UI',sans-serif;--mono:'Geist Mono',ui-monospace,Menlo,monospace}
*{box-sizing:border-box}html,body{height:100%}
body{margin:0;font:16px/1.6 var(--sans);color:var(--fg);background:var(--deep);
  background-image:radial-gradient(700px 420px at 12% 8%,rgba(177,51,138,.38),transparent 70%),radial-gradient(600px 400px at 95% 100%,rgba(224,83,159,.22),transparent 70%);
  display:flex;flex-direction:column;align-items:center;justify-content:center;padding:28px 16px}
.carte-auth{width:100%;max-width:440px;background:var(--paper);border-radius:24px;padding:34px 32px 26px;box-shadow:0 40px 90px -30px rgba(0,0,0,.6)}
.liaison{display:flex;align-items:center;justify-content:center;gap:12px;margin:0 0 22px}
.liaison img{width:56px;height:56px;border-radius:16px;display:block}
.liaison .assistant{width:56px;height:56px;border-radius:16px;background:var(--soft);color:var(--accent);display:flex;align-items:center;justify-content:center;
  font:400 28px var(--serif)}
.liaison .fil{display:flex;gap:5px}.liaison .fil i{width:6px;height:6px;border-radius:50%;background:var(--line)}
.liaison .fil i:nth-child(2){background:var(--accent2)}
h1{font:400 32px/1.08 var(--serif);text-align:center;margin:0 0 6px;letter-spacing:-.01em}
.sous{text-align:center;color:var(--muted);font-size:14.5px;margin:0 0 24px}
label.l{display:block;font:600 12px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
.champ{width:100%;font:16px var(--sans);padding:14px 16px;border:1.5px solid var(--line);border-radius:12px;background:#fff;color:var(--fg);outline:none;transition:border-color .15s}
.champ:focus{border-color:var(--accent)}
.cases{display:flex;gap:8px;justify-content:space-between}
.cases input{width:100%;max-width:52px;height:60px;text-align:center;font:600 26px var(--mono);border:1.5px solid var(--line);border-radius:12px;background:#fff;color:var(--fg);outline:none}
.cases input:focus{border-color:var(--accent);box-shadow:0 0 0 4px rgba(177,51,138,.12)}
.btn{display:block;width:100%;margin-top:16px;font:600 15.5px var(--sans);border:0;border-radius:12px;padding:15px 18px;cursor:pointer;background:var(--accent);color:#fff;
  box-shadow:0 12px 26px -14px var(--accent);transition:transform .15s}
.btn:hover{transform:translateY(-1px)}
.alerte{background:#fdecee;color:var(--ko);border-radius:10px;padding:10px 14px;font-size:14px;margin:0 0 16px}
.info{color:var(--ink);font-size:14.5px;margin:0 0 16px;text-align:center}
.liens{display:flex;justify-content:center;gap:18px;flex-wrap:wrap;margin-top:20px;font-size:13.5px}
.liens button{background:none;border:0;padding:0;font:inherit;color:var(--muted);text-decoration:underline;text-underline-offset:3px;cursor:pointer}
.liens button:hover{color:var(--accent)}
.garanties{display:flex;justify-content:center;gap:14px;flex-wrap:wrap;margin:22px 0 0;padding:16px 0 0;border-top:1px solid var(--line);font-size:12.5px;color:var(--muted)}
.garanties span::before{content:"§ ";color:var(--accent);font-family:var(--serif)}
.pied{margin-top:20px;font-size:12.5px;color:#8a90a3;text-align:center}.pied a{color:#c9cdd8}
@media (max-width:420px){.carte-auth{padding:28px 20px 22px}.cases{gap:6px}.cases input{height:54px;font-size:22px}}
"""


def _masquer(email):
    if "@" not in email:
        return email
    nom, dom = email.split("@", 1)
    return nom[:2] + "•" * max(len(nom) - 2, 2) + "@" + dom


def _page_auth(titre, contenu):
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s · Mishpat by Studjoow</title><meta name="robots" content="noindex,nofollow"><meta name="theme-color" content="#040e30">
<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<style>%s%s</style></head><body>%s
<p class="pied">Mishpat by Studjoow · <a href="/">mishpat.studjoow.com</a> · Legal information, not legal advice.</p></body></html>""" % (
        html.escape(titre), FONTS, CSS_OAUTH, contenu)


def page_oauth(nom_client, demande, etape="email", email="", erreur=None):
    e = html.escape
    alerte = '<p class="alerte">%s</p>' % e(erreur) if erreur else ""
    cache = '<input type="hidden" name="demande" value="%s">' % e(demande)
    initiale = e((nom_client or "A").strip()[:1].upper())

    def lien(action, texte, extra=""):
        return ('<form method="post" action="/oauth/authorize">%s<input type="hidden" name="action" value="%s">%s'
                '<button type="submit">%s</button></form>' % (cache, action, extra, texte))

    if etape == "code":
        sous = "Code sent to <b>%s</b> if it matches an active subscription." % e(_masquer(email))
        corps = """%s<form method="post" action="/oauth/authorize" id="f">%s<input type="hidden" name="action" value="code">
<input type="hidden" name="code" id="code">
<label class="l">6-digit code</label>
<div class="cases" id="cases">%s</div>
<button class="btn" type="submit">Connect</button></form>
<div class="liens">%s%s</div>
<script>
(function(){var c=[].slice.call(document.querySelectorAll('#cases input')),h=document.getElementById('code');
function maj(){h.value=c.map(function(i){return i.value}).join('')}
c.forEach(function(i,k){
 i.addEventListener('input',function(){var v=i.value.replace(/\\D/g,'');if(v.length>1){v.split('').forEach(function(d,j){if(c[k+j])c[k+j].value=d});(c[Math.min(k+v.length,5)]).focus()}else{i.value=v;if(v&&k<5)c[k+1].focus()}maj();if(h.value.length===6)document.getElementById('f').submit()});
 i.addEventListener('keydown',function(ev){if(ev.key==='Backspace'&&!i.value&&k>0){c[k-1].focus()}});
 i.addEventListener('paste',function(ev){var t=(ev.clipboardData||window.clipboardData).getData('text').replace(/\\D/g,'').slice(0,6);if(!t)return;ev.preventDefault();
  t.split('').forEach(function(d,j){if(c[j])c[j].value=d});maj();(c[t.length]||c[5]).focus();if(t.length===6)document.getElementById('f').submit()});
});c[0].focus();})();
</script>""" % (alerte, cache, "".join('<input inputmode="numeric" autocomplete="%s" maxlength="1" aria-label="Digit %d">'
                                       % ("one-time-code" if k == 0 else "off", k + 1) for k in range(6)),
                lien("email", "Send a new code", '<input type="hidden" name="email" value="%s">' % e(email)),
                lien("retour", "Change e-mail"))
    elif etape == "cle":
        sous = "Paste the personal address received after your payment."
        corps = """%s<form method="post" action="/oauth/authorize">%s<input type="hidden" name="action" value="cle">
<label class="l" for="a">Personal address</label>
<input class="champ" id="a" name="adresse" placeholder="%s/mcp/..." autocomplete="off" required autofocus>
<button class="btn" type="submit">Connect</button></form>
<div class="liens">%s</div>""" % (alerte, cache, SITE, lien("retour", "Get a code by e-mail instead"))
    else:
        sous = "Enter the e-mail of your subscription: you will receive a sign-in code."
        corps = """%s<form method="post" action="/oauth/authorize">%s<input type="hidden" name="action" value="email">
<label class="l" for="m">Your e-mail</label>
<input class="champ" id="m" type="email" name="email" value="%s" placeholder="you@example.com" autocomplete="email" required autofocus>
<button class="btn" type="submit">Get my code</button></form>
<div class="liens">%s</div>""" % (alerte, cache, e(email), lien("cle", "I have my personal address"))
    contenu = """<main class="carte-auth">
<div class="liaison"><img src="/static/icones/icone-192.png" alt="Mishpat by Studjoow"><span class="fil"><i></i><i></i><i></i></span><span class="assistant" aria-hidden="true">%s</span></div>
<h1>Connect %s</h1>
<p class="sous">%s</p>
%s
<div class="liens">%s</div>
<div class="garanties"><span>No password</span><span>Code valid 10 min</span><span>Disconnect from <a href="/compte" style="color:inherit">your account</a></span></div>
</main>""" % (initiale, e(nom_client), sous, corps, lien("refuser", "Cancel"))
    return _page_auth("Sign in", contenu)


def page_oauth_erreur(message):
    return _page_auth("Sign-in failed", """<main class="carte-auth">
<div class="liaison"><img src="/static/icones/icone-192.png" alt="Mishpat by Studjoow"></div>
<h1>Sign-in failed</h1><p class="alerte" style="margin-top:16px">%s</p>
<p class="info">Need help: <a href="mailto:%s">%s</a></p></main>""" % (html.escape(message), CONTACT, CONTACT))
