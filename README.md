# Mishpat by Studjoow: Israeli law for AI assistants

An MCP server that connects AI assistants (Claude, ChatGPT, Cursor, VS Code...) to Israeli legislation: laws, Basic Laws, ordinances, regulations and orders, section by section, with their official publications in Reshumot and their legislative history from the Knesset.

**Endpoint:** `https://mishpat.studjoow.com/mcp` (streamable HTTP)

> שרת MCP שמחבר עוזרי בינה מלאכותית לחקיקה הישראלית: חוקים, חוקי־יסוד, פקודות, תקנות וצווים, סעיף אחר סעיף, עם הפרסומים ברשומות וההיסטוריה החקיקתית מהכנסת.

## Important

- Israel has **no official consolidated version** of its legislation. The text served here is the community consolidation of the Open Law Book (ספר החוקים הפתוח) of Hebrew Wikisource. It is unofficial and may lag behind a recent amendment.
- The binding text is the publication in **Reshumot** (רשומות). Every answer links to the official PDFs.
- Versions at a past date are not provided: Wikisource revision dates are editing dates, not dates of entry into force.
- Case law is not covered.
- Legal information, not legal advice.

## Tools

| Tool | What it does |
|---|---|
| `read_section` | Text of one section, its part, amendment years and the Reshumot PDFs of those amendments |
| `search_law` | Full-text search in Hebrew (prefixes ה/ו/ב/ל/מ/ש/כ handled), primary laws first |
| `find_law` | Find a text by title (Hebrew, or common English names) |
| `read_law` | Table of contents and list of Reshumot publications |
| `law_history` | Reshumot publications + Knesset record: status, dates, amending laws, former names |
| `verify_references` | Checks that law and section exist (and are not repealed) and that quotes appear word for word |
| `database_status` | Counts and dates of the data |

## Data

| Source | Content | Licence | Update |
|---|---|---|---|
| [ספר החוקים הפתוח](https://he.wikisource.org/wiki/ויקיטקסט:ספר_החוקים_הפתוח), Hebrew Wikisource (MediaWiki API, every page using `{{ח:התחלה}}`) | ~6,200 texts, consolidated, split by section, with the list of Reshumot publications | CC BY-SA 4.0 | nightly, incremental (revision ids) |
| Knesset OData API (`KNS_IsraelLaw`, `KNS_LawBinding`, `KNS_Bill`, `KNS_DocumentBill`...) | status, publication dates, amending laws, PDFs | Israeli open government data | weekly |
| Fallback: [ZeAlenu/knesset-data](https://huggingface.co/datasets/ZeAlenu/knesset-data) | mirror of the same API | ODC-BY | used when the official API is unreachable |

The Knesset API and `fs.knesset.gov.il` only answer from Israeli IP addresses. Outside Israel the mirror is used and its date is shown by `database_status` and `law_history`.

Texts derived from Wikisource are shared under CC BY-SA 4.0 with attribution to the Hebrew Wikisource contributors. This project is not endorsed by Wikisource, the Wikimedia Foundation, the Knesset or the Israeli government.

## Run locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r server/requirements.txt
.venv/bin/python scripts/build_laws.py        # ~15 min the first time, then incremental
.venv/bin/python scripts/fetch_knesset.py     # official API from Israel, mirror elsewhere
.venv/bin/python scripts/search.py article "חוק הגנת הפרטיות" 7
HOST=127.0.0.1 PORT=8000 .venv/bin/python server/server.py
```

Data goes to `~/droit-israel-data` (override with `MISHPAT_DATA`), never into Git.

## Docker

```bash
docker build -t mishpat .
docker run -p 8000:8000 -v mishpat-data:/data mishpat
```

On first start with an empty volume the container builds the databases (about 15 minutes), then updates them every night at 03:30 UTC (Knesset on Sundays). `MISHPAT_AUTO_UPDATE=0` disables it.

| Variable | Default | |
|---|---|---|
| `MISHPAT_PUBLIC_URL` | `https://mishpat.studjoow.com` | public address |
| `MISHPAT_ALLOWED_HOSTS` | empty | DNS rebinding protection, e.g. `mishpat.studjoow.com` |
| `MISHPAT_RATE_PER_MIN` | 60 | requests per minute and per IP on `/mcp` |
| `MISHPAT_CONCURRENCY` | 2 | simultaneous queries |
| `MISHPAT_TRUSTED_PROXIES` | 1 | proxies in front (X-Forwarded-For) |

## Licence

Code: MIT. Data: see above.

Published by [Studjoow](https://studjoow.com). French and EU law: [droit.studjoow.com](https://droit.studjoow.com).
