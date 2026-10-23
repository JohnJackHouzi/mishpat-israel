import asyncio
import json
import os
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import Icon

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
TIMEOUT = float(os.environ.get("MISHPAT_TIMEOUT", "30"))
MAX_CHARS = int(os.environ.get("MISHPAT_MAX_CHARS", "40000"))
RATE = int(os.environ.get("MISHPAT_RATE_PER_MIN", "60"))
CONCURRENT = asyncio.Semaphore(int(os.environ.get("MISHPAT_CONCURRENCY", "2")))
SITE = os.environ.get("MISHPAT_PUBLIC_URL", "https://mishpat.studjoow.com").rstrip("/")

INSTRUCTIONS = """Israeli legislation (חקיקה ישראלית): laws, Basic Laws, ordinances, regulations and orders, as consolidated by the Open Law Book project of Hebrew Wikisource (ספר החוקים הפתוח, CC BY-SA 4.0), plus the Knesset legislative database (laws, amending laws, publication dates, official Reshumot PDFs).

MANDATORY PROTOCOL
1. Never answer on Israeli law from memory: search first with these tools. Texts are in Hebrew: search with Hebrew terms (translate the user's question), cite in Hebrew and translate for the user when needed.
2. Read the full section (read_section) before relying on it, not only search snippets. Definitions sections (usually סעיף 1 or 3) often change the meaning.
3. Before citing, check every reference with verify_references. NOT FOUND, REPEALED or ABSENT lines must not be cited. Quotes are copied from the text read, never reconstructed.
4. Every legal statement is followed by its source, e.g. (חוק הגנת הפרטיות, התשמ"א-1981, סעיף 7).
5. End with a "Sources" block: one line per reference with the Wikisource link and, for the official text, the Reshumot PDF given by the tools.
6. The consolidated text is NOT official (no official consolidation exists in Israel) and may lag behind recent amendments: for anything recent or decisive, check law_history and the Reshumot PDF of the latest amendment, and say so.
7. Point-in-time versions are not available: say so if the facts are older than the latest amendment.
8. Case law is not covered. Legal information, not legal advice: recommend an Israeli lawyer (עורך דין) for a concrete case.
Limits: see database_status for dates of the data."""

_hosts = [h for h in os.environ.get("MISHPAT_ALLOWED_HOSTS", "").split(",") if h]
security = (
    TransportSecuritySettings(allowed_hosts=_hosts, allowed_origins=["*"])
    if _hosts
    else TransportSecuritySettings(enable_dns_rebinding_protection=False)
)

mcp = FastMCP(
    "mishpat-israel",
    instructions=INSTRUCTIONS,
    host=os.environ.get("HOST", "127.0.0.1"),
    port=int(os.environ.get("PORT", "8000")),
    stateless_http=True,
    json_response=True,
    transport_security=security,
    website_url=SITE,
    icons=[Icon(src=SITE + "/static/icones/icone-%d.png" % t, mimeType="image/png", sizes=["%dx%d" % (t, t)])
           for t in (192, 512)],
)


async def run(*args):
    async with CONCURRENT:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-I", str(SCRIPTS / "search.py"), *args,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            return "Timeout: narrow the query (law name, more precise Hebrew terms)."
    text = out.decode("utf-8", "replace")
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n[... truncated: narrow the search or read a single section ...]"
    return text


@mcp.tool()
async def read_section(law: str, section: str) -> str:
    """Read one section of an Israeli law or regulation (current consolidated text) | קריאת סעיף בחוק או בתקנות.
    law: Hebrew title, e.g. « חוק הגנת הפרטיות », « חוק הגנת הצרכן », « תקנות הגנת הפרטיות (אבטחת מידע) », a Knesset law ID (2000234) or a common English name (« Protection of Privacy Law »).
    section: « 7 », « 17ב1 », « 23מו », or a schedule item « תוספת 5 פרט 6 ».
    Returns the text, its place in the law, amendment years and links to the official Reshumot PDFs."""
    return await run("article", law, section)


@mcp.tool()
async def search_law(query: str, law: str = "", type: str = "", limit: int = 10) -> str:
    """Full-text search in Israeli legislation (Hebrew) | חיפוש טקסט מלא בחקיקה.
    query: Hebrew words; prefixes ה/ו/ב/ל/מ/ש/כ are matched automatically. Syntax: "exact phrase", AND, OR, NOT, prefix*.
    law: restrict to one law (Hebrew title). type: law, basic_law, ordinance, regulations, order, rules (default all; primary laws ranked first)."""
    return await run("recherche", "--q", query, "--loi", law, "--type", type, "--limit", str(min(max(limit, 1), 30)))


@mcp.tool()
async def find_law(name: str, limit: int = 10) -> str:
    """Find laws and regulations by title | איתור חוק או תקנות לפי שם.
    name: part of the Hebrew title (« הגנת הפרטיות », « חתימה אלקטרונית ») or a common English name. Returns titles, type, number of sections and links."""
    return await run("titres", name, "--limit", str(min(max(limit, 1), 30)))


@mcp.tool()
async def read_law(law: str) -> str:
    """Overview of a law: full title, table of contents (parts, sections, amendment years) and the list of its publications in Reshumot with official PDF links | מבנה החוק ורשימת פרסומים ברשומות."""
    return await run("loi", law)


@mcp.tool()
async def law_history(law: str) -> str:
    """Legislative history of a law | היסטוריה חקיקתית: Reshumot publications (original and each amendment, official PDFs) and the Knesset record (status in force or repealed, publication dates, amending laws, former names). States the date of the Knesset data. Point-in-time versions are not provided."""
    return await run("historique", law)


@mcp.tool()
async def verify_references(references: list[str], quotes: list[str] | None = None) -> str:
    """Check references before citing them | אימות הפניות לפני ציטוט.
    references: « חוק הגנת הפרטיות, סעיף 7 », « Protection of Privacy Law, section 17ב1 », « חוק חתימה אלקטרונית » (law only).
    quotes: excerpts that must appear word for word in the reference of the same rank. Any NOT FOUND, REPEALED or ABSENT line forbids the citation."""
    args = ["verifier", *references]
    for q in quotes or []:
        args += ["--quote", q]
    return await run(*args)


@mcp.tool()
async def database_status() -> str:
    """Counts and dates of the data (last Wikisource sync, date of the Knesset data, source used): cite it to state how current the answer is | מצב מאגר הנתונים."""
    return await run("etat")


sys.path.insert(0, str(SCRIPTS))
import etat as etat_bases  # noqa: E402

PROXIES = int(os.environ.get("MISHPAT_TRUSTED_PROXIES", "1"))
_pret = {"t": 0.0, "v": False}


def bases_pretes():
    if time.monotonic() - _pret["t"] > 30:
        _pret["v"] = etat_bases.etat(comptes=False)["pret"]
        _pret["t"] = time.monotonic()
    return _pret["v"]


def client_ip(scope):
    xff = dict(scope["headers"]).get(b"x-forwarded-for", b"").decode()
    hops = [h.strip() for h in xff.split(",") if h.strip()]
    if PROXIES and len(hops) >= PROXIES:
        return hops[-PROXIES]
    return (scope.get("client") or ("?",))[0]


async def texte(send, status, body, retry=None):
    headers = [(b"content-type", b"text/plain; charset=utf-8")]
    if retry:
        headers.append((b"retry-after", retry))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body.encode()})


class Garde:
    def __init__(self, app):
        self.app = app
        self.hits = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not (scope["path"] == "/mcp" or scope["path"].startswith("/mcp/")):
            return await self.app(scope, receive, send)
        ip = client_ip(scope)
        now, q = time.monotonic(), self.hits[ip]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= RATE:
            return await texte(send, 429, "Too many requests, retry in a few seconds.", b"30")
        q.append(now)
        if len(self.hits) > 50000:
            for k in [k for k, v in self.hits.items() if not v or now - v[-1] > 60]:
                del self.hits[k]
        if not bases_pretes():
            return await texte(send, 503, "Database being installed, retry later.", b"600")
        await self.app(scope, receive, send)


def build_app():
    import mimetypes

    import page
    from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
    from starlette.routing import Mount, Route
    from starlette.staticfiles import StaticFiles

    cache = {"Cache-Control": "public, max-age=600"}

    def health(request):
        e = etat_bases.etat(comptes=False)
        _pret.update(t=time.monotonic(), v=e["pret"])
        return Response(json.dumps(e, ensure_ascii=False), status_code=200 if e["pret"] else 503,
                        media_type="application/json")

    def accueil(lang):
        async def vue(request):
            body = await asyncio.get_running_loop().run_in_executor(None, page.render, etat_bases.etat, lang)
            return HTMLResponse(body, headers=cache)
        return vue

    async def llms(request):
        body = await asyncio.get_running_loop().run_in_executor(None, page.llms, etat_bases.etat)
        return PlainTextResponse(body, headers=cache)

    app = mcp.streamable_http_app()
    routes = [
        Route("/ping", lambda r: PlainTextResponse("ok")),
        Route("/health", health),
        Route("/", accueil("en")),
        Route("/he", accueil("he")),
        Route("/llms.txt", llms),
        Route("/robots.txt", lambda r: PlainTextResponse(page.robots(), headers=cache)),
        Route("/sitemap.xml", lambda r: Response(page.sitemap(), media_type="application/xml", headers=cache)),
        Route("/favicon.svg", lambda r: RedirectResponse("/static/icones/icone-192.png", status_code=301)),
    ]
    mimetypes.add_type("font/woff2", ".woff2")

    class StaticCache(StaticFiles):
        async def get_response(self, path, scope):
            resp = await super().get_response(path, scope)
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return resp

    routes.append(Mount("/static", app=StaticCache(directory=str(Path(__file__).resolve().parent / "static")),
                        name="static"))
    icones = Path(__file__).resolve().parent / "static" / "icones"
    for chemin, nom, type_mime in (("/favicon.ico", "favicon.ico", "image/x-icon"),
                                   ("/apple-touch-icon.png", "apple-touch-icon.png", "image/png")):
        contenu = (icones / nom).read_bytes() if (icones / nom).exists() else b""
        routes.append(Route(chemin, lambda r, c=contenu, t=type_mime: Response(
            c, media_type=t, headers={"Cache-Control": "public, max-age=86400"})))
    for r in reversed(routes):
        app.router.routes.insert(0, r)
    return Garde(app)


app = build_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8000")),
                proxy_headers=False)
