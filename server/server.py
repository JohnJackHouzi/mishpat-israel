import asyncio
import json
import logging
import os
import re
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
4. Answer in the language of the conversation (French, English, Hebrew...). For every section you rely on, present in this order:
   a) the exact Hebrew text, quoted word for word from read_section (the relevant subsection if the section is long), with its reference, e.g. חוק הגנת הפרטיות, התשמ"א-1981, סעיף 17ב1(א);
   b) a faithful translation into the language of the conversation, labelled as an unofficial translation (skip it if the conversation is in Hebrew);
   c) a plain-language explanation of what it means for the user's question, kept separate from the text and its translation.
5. End with a "Sources" block: one line per reference with the Wikisource link and the official Reshumot PDF given by the tools (original publication and the amendment that last changed the section).
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
import abonnement  # noqa: E402
import oauth  # noqa: E402

PROXIES = int(os.environ.get("MISHPAT_TRUSTED_PROXIES", "1"))
PUBLIC_PATHS = ("/health", "/ping", "/", "/he", "/favicon.ico", "/apple-touch-icon.png", "/robots.txt", "/sitemap.xml", "/llms.txt", "/favicon.svg")
MAX_CORPS = 1_000_000
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


async def json_brut(send, body):
    await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": body})


async def lire_corps(receive):
    morceaux, total = [], 0
    while True:
        msg = await receive()
        if msg["type"] != "http.request":
            return None
        morceaux.append(msg.get("body", b""))
        total += len(morceaux[-1])
        if total > MAX_CORPS:
            return None
        if not msg.get("more_body"):
            return b"".join(morceaux)


def rejouer(corps, receive):
    envoye = {"v": False}

    async def recv():
        if not envoye["v"]:
            envoye["v"] = True
            return {"type": "http.request", "body": corps, "more_body": False}
        return await receive()
    return recv


def appels_outils(corps):
    try:
        msgs = json.loads(corps)
    except ValueError:
        return []
    msgs = msgs if isinstance(msgs, list) else [msgs]
    return [m.get("id") for m in msgs if isinstance(m, dict) and m.get("method") == "tools/call"]


def message_essai():
    return ("Free trial limit reached: %d requests per day on the public address. "
            "To continue, subscribe for %s per month (%d requests per day), no commitment: %s/abonnement . "
            "The trial resets tomorrow (midnight UTC). Give this link to the user."
            % (abonnement.ESSAI_PAR_JOUR, abonnement.montant(abonnement.OFFRES["particulier"]), abonnement.PLAFOND_ABONNE, abonnement.SITE))


def message_plafond(plafond):
    return ("Daily subscription limit reached: %d requests per day per personal address (see the Terms). "
            "It resets tomorrow (midnight UTC). If the address may have been shared, regenerate it at %s/compte ."
            % (plafond, abonnement.SITE))


MESSAGES_STATUT = {
    "suspendu": "Subscription suspended: the last payment failed. Update the payment method at %s/compte .",
    "revoque": "Subscription ended: this personal address is no longer active. Subscribe again at %s/abonnement .",
}


class Garde:
    def __init__(self, app):
        self.app = app
        self.hits = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] in PUBLIC_PATHS or scope["path"].startswith("/static/"):
            return await self.app(scope, receive, send)
        abonne = None
        if scope["path"].rstrip("/") == "/abonne/mcp":
            entetes = dict(scope["headers"])
            abonne = oauth.abonne_par_jeton(entetes.get(b"authorization", b"").decode("latin-1"))
            if abonne is None:
                corps = json.dumps({"error": "invalid_token", "error_description": "Sign-in required: Mishpat by Studjoow subscription."}).encode()
                await send({"type": "http.response.start", "status": 401, "headers": [
                    (b"content-type", b"application/json"), (b"www-authenticate", oauth.entete_401().encode()),
                    (b"access-control-allow-origin", b"*"), (b"access-control-expose-headers", b"WWW-Authenticate")]})
                return await send({"type": "http.response.body", "body": corps})
            scope["path"], scope["raw_path"] = "/mcp", b"/mcp"
        elif scope["path"].startswith("/mcp/") and scope["path"].strip("/") != "mcp":
            abonne = abonnement.verifier_cle(scope["path"][5:].strip("/"))
            scope["path"], scope["raw_path"] = "/mcp", b"/mcp"
            if abonne is None:
                return await texte(send, 404, "Unknown personal address. Check the copied address or regenerate it at %s/compte ." % abonnement.SITE)
        ip = client_ip(scope)
        now, q = time.monotonic(), self.hits["k:" + abonne["abonnement"] if abonne else ip]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= RATE:
            return await texte(send, 429, "Too many requests, retry in a few seconds.", b"30")
        q.append(now)
        if len(self.hits) > 50000:
            for k in [k for k, v in self.hits.items() if not v or now - v[-1] > 60]:
                del self.hits[k]
        if scope["path"] == "/mcp" or scope["path"].startswith("/mcp/"):
            if not bases_pretes():
                return await texte(send, 503, "Database being installed, retry later.", b"600")
            limiter = abonne is not None or abonnement.actif()
            if limiter and scope["method"] == "POST":
                corps = await lire_corps(receive)
                if corps is None:
                    return await texte(send, 413, "Request too large.")
                ids = appels_outils(corps)
                if ids and abonne is not None and abonne["statut"] != "actif":
                    return await json_brut(send, abonnement.json_rpc_erreur(ids, MESSAGES_STATUT[abonne["statut"]] % abonnement.SITE))
                if ids and abonne is not None:
                    ok, _ = await asyncio.get_running_loop().run_in_executor(
                        None, abonnement.consommer_abonne, abonne["abonnement"], len(ids), abonnement.offre_de(abonne)["plafond"])
                    if not ok:
                        return await json_brut(send, abonnement.json_rpc_erreur(ids, message_plafond(abonnement.offre_de(abonne)["plafond"])))
                elif ids:
                    ok, _ = await asyncio.get_running_loop().run_in_executor(None, abonnement.consommer_essai, ip, len(ids))
                    if not ok:
                        return await json_brut(send, abonnement.json_rpc_erreur(ids, message_essai()))
                receive = rejouer(corps, receive)
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
    if abonnement.actif():
        page.LIEN_ABONNEMENT = "/abonnement"
    for chemin, fn in (("/terms", page.terms), ("/legal", page.legal), ("/privacy", page.privacy)):
        routes.append(Route(chemin, lambda r, fn=fn: HTMLResponse(fn(), headers=cache)))
    routes += routes_abonnement(page)
    for r in reversed(routes):
        app.router.routes.insert(0, r)
    return Garde(app)


def routes_abonnement(page):
    from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
    from starlette.routing import Route

    prive = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex", "Referrer-Policy": "no-referrer"}
    liens_envoyes = defaultdict(deque)

    def vue(contenu, status=200):
        return HTMLResponse(contenu, status_code=status, headers=prive)

    def ferme():
        return vue(page.page_ferme(), 503)

    async def formulaire(request):
        if not abonnement.actif():
            return ferme()
        offre = request.query_params.get("offre", "particulier")
        offre = offre if offre in abonnement.OFFRES else "particulier"
        if request.method == "GET":
            return vue(page.page_abonnement(offre=offre))
        f = await request.form()
        offre = f.get("offre") if f.get("offre") in abonnement.OFFRES else offre
        if f.get("cgv") != "1" or f.get("execution") != "1":
            return vue(page.page_abonnement("Tick both boxes to continue.", offre), 400)
        try:
            session = await abonnement.creer_session(abonnement.maintenant(), offre)
        except abonnement.ErreurStripe as exc:
            logging.getLogger("mishpat").error("Checkout : %s", exc)
            return vue(page.page_abonnement("Payment is temporarily unavailable, please retry in a moment.", offre), 502)
        return RedirectResponse(session["url"], status_code=303)

    async def merci(request):
        if not abonnement.actif():
            return ferme()
        sid = request.query_params.get("session_id", "")
        if not re.fullmatch(r"cs_(test|live)_[A-Za-z0-9]+", sid):
            return vue(page.page_merci(None, "Invalid confirmation link."), 400)
        try:
            s = await abonnement.stripe("GET", "/v1/checkout/sessions/" + sid, {"expand": ["subscription"]})
        except abonnement.ErreurStripe:
            return vue(page.page_merci(None, "Payment session not found."), 404)
        if (s.get("metadata") or {}).get("app") != abonnement.APP or s.get("status") != "complete" or not s.get("subscription"):
            return vue(page.page_merci(None, "The payment is not complete."), 402)
        row = abonnement.enregistrer_abonnement(s["subscription"], (s.get("customer_details") or {}).get("email"))
        envoye = await abonnement.envoyer_cle_si_besoin(row["abonnement"])
        if abonnement.marquer_affichee(row["abonnement"]):
            return vue(page.page_merci(abonnement.adresse(abonnement.cle_de(row["abonnement"], row["version"])), None, row["email"], envoye or row["email_envoye"]))
        return vue(page.page_merci(None, "Your personal address has already been shown on this page. Find it in the confirmation e-mail, or regenerate it from your account."))

    def ligne_depuis(f):
        return abonnement.verifier_cle(abonnement.extraire_cle(f.get("adresse", "")))

    async def compte(request):
        if not abonnement.actif():
            return ferme()
        if request.method == "GET":
            return vue(page.page_compte())
        row = ligne_depuis(await request.form())
        if not row:
            return vue(page.page_compte(erreur="Unknown personal address."), 404)
        return vue(page.page_gestion(row, abonnement.adresse(abonnement.cle_de(row["abonnement"], row["version"]))))

    async def acces(request):
        if not abonnement.actif():
            return ferme()
        aid = abonnement.lire_jeton(request.query_params.get("j", ""))
        row = aid and abonnement.db().execute("SELECT * FROM cles WHERE abonnement=?", (aid,)).fetchone()
        if not row:
            return vue(page.page_compte(erreur="Expired or invalid link: request a new one."), 400)
        return vue(page.page_gestion(row, abonnement.adresse(abonnement.cle_de(row["abonnement"], row["version"]))))

    async def portail(request):
        if not abonnement.actif():
            return ferme()
        row = ligne_depuis(await request.form())
        if not row:
            return vue(page.page_compte(erreur="Unknown personal address."), 404)
        try:
            p = await abonnement.creer_portail(row["client"])
        except abonnement.ErreurStripe as exc:
            logging.getLogger("mishpat").error("Portail : %s", exc)
            return vue(page.page_compte(erreur="Management portal temporarily unavailable."), 502)
        return RedirectResponse(p["url"], status_code=303)

    async def regenerer(request):
        if not abonnement.actif():
            return ferme()
        row = ligne_depuis(await request.form())
        if not row:
            return vue(page.page_compte(erreur="Unknown personal address."), 404)
        cle = abonnement.regenerer(row["abonnement"])
        row = abonnement.db().execute("SELECT * FROM cles WHERE abonnement=?", (row["abonnement"],)).fetchone()
        return vue(page.page_gestion(row, abonnement.adresse(cle), nouvelle=True))

    async def lien(request):
        if not abonnement.actif():
            return ferme()
        email = ((await request.form()).get("email") or "").strip()[:200]
        now, q = time.monotonic(), liens_envoyes[client_ip(request.scope)]
        while q and now - q[0] > 3600:
            q.popleft()
        if "@" in email and len(q) < 5:
            q.append(now)
            await abonnement.envoyer_lien_acces(email)
        return vue(page.page_compte(info="If a subscription matches this e-mail address, an access link valid for one hour has just been sent to it."))

    async def webhook(request):
        corps = await request.body()
        if not abonnement.signature_valide(corps, request.headers.get("stripe-signature", "")):
            return JSONResponse({"error": "invalid signature"}, status_code=400)
        ev = json.loads(corps)
        try:
            compte_rendu = await abonnement.traiter_evenement(ev)
        except Exception as exc:
            logging.getLogger("mishpat").exception("Webhook %s", ev.get("type"))
            return JSONResponse({"erreur": str(exc)[:200]}, status_code=500)
        return JSONResponse({"ok": True, "resultat": compte_rendu})

    def refus():
        return JSONResponse({"error": "unauthorized"}, status_code=401, headers=prive)

    async def admin_resume(request):
        if not abonnement.admin_autorise(request.headers.get("authorization", "")):
            return refus()
        data = await asyncio.get_running_loop().run_in_executor(None, abonnement.resume_admin)
        return JSONResponse(data, headers=prive)

    async def admin_regenerer(request):
        if not abonnement.admin_autorise(request.headers.get("authorization", "")):
            return refus()
        try:
            aid = (await request.json()).get("abonnement", "")
        except ValueError:
            aid = ""
        rep = await abonnement.regenerer_et_envoyer(aid) if aid else None
        if not rep:
            return JSONResponse({"error": "unknown subscription"}, status_code=404, headers=prive)
        return JSONResponse(rep, headers=prive)

    cors = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Authorization, Content-Type, mcp-protocol-version",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS"}

    def json_oauth(data, status=200):
        return JSONResponse(data, status_code=status, headers={**cors, "Cache-Control": "no-store", "Pragma": "no-cache"})

    async def meta_ressource(request):
        if request.method == "OPTIONS":
            return Response(status_code=204, headers=cors)
        return JSONResponse(oauth.meta_ressource(), headers={**cors, "Cache-Control": "public, max-age=3600"})

    async def meta_serveur(request):
        if request.method == "OPTIONS":
            return Response(status_code=204, headers=cors)
        return JSONResponse(oauth.meta_serveur(), headers={**cors, "Cache-Control": "public, max-age=3600"})

    async def oauth_register(request):
        if request.method == "OPTIONS":
            return Response(status_code=204, headers=cors)
        try:
            donnees = await request.json()
            rep = await asyncio.get_running_loop().run_in_executor(None, oauth.enregistrer_client, donnees)
        except (ValueError, AttributeError) as exc:
            return json_oauth({"error": "invalid_client_metadata", "error_description": str(exc)[:200]}, 400)
        return json_oauth(rep, 201)

    connexions = defaultdict(deque)

    def trop_de_codes(ip):
        now, q = time.monotonic(), connexions[ip]
        while q and now - q[0] > 3600:
            q.popleft()
        if len(q) >= 8:
            return True
        q.append(now)
        return False

    async def oauth_authorize(request):
        if request.method == "GET":
            try:
                did, nom = oauth.ouvrir_demande(dict(request.query_params))
            except oauth.ErreurOAuth as exc:
                return vue(page.page_oauth_erreur(exc.description), 400)
            return vue(page.page_oauth(nom, did))
        f = await request.form()
        did, action = f.get("demande", ""), f.get("action", "")
        d = oauth.demande(did)
        if not d:
            return vue(page.page_oauth_erreur("Request expired: start the connection again from your assistant."), 400)
        nom = (oauth.client(d["client_id"]) or {"nom": "Assistant"})["nom"]
        if action == "refuser":
            return RedirectResponse(oauth.refuser(did), status_code=302)
        if action == "email":
            email = (f.get("email") or "").strip()[:200]
            if "@" not in email:
                return vue(page.page_oauth(nom, did, erreur="Invalid e-mail address."), 400)
            if trop_de_codes(client_ip(request.scope)):
                return vue(page.page_oauth(nom, did, erreur="Too many code requests: try again in an hour."), 429)
            await oauth.envoyer_code_mail(did, email)
            return vue(page.page_oauth(nom, did, etape="code", email=email))
        if action == "code":
            row = oauth.verifier_code_mail(did, f.get("code", ""))
            url = oauth.accorder(did, row) if row else None
            if url:
                return RedirectResponse(url, status_code=302)
            d = oauth.demande(did)
            if not d or d["essais"] >= oauth.ESSAIS_MAX:
                return vue(page.page_oauth_erreur("Too many attempts: start the connection again from your assistant."), 400)
            return vue(page.page_oauth(nom, did, etape="code", email=d["email"] or "",
                                       erreur="Wrong or expired code (%d attempt(s) left)." % (oauth.ESSAIS_MAX - d["essais"])), 400)
        if action == "cle":
            row = abonnement.verifier_cle(abonnement.extraire_cle(f.get("adresse", "")))
            if row and row["statut"] == "actif":
                return RedirectResponse(oauth.accorder(did, row), status_code=302)
            return vue(page.page_oauth(nom, did, etape="cle", erreur="Unknown personal address or inactive subscription."), 400)
        return vue(page.page_oauth(nom, did, etape=action if action in ("cle",) else "email"))

    async def oauth_token(request):
        if request.method == "OPTIONS":
            return Response(status_code=204, headers=cors)
        form = dict(await request.form())
        basic = None
        entete = request.headers.get("authorization", "")
        if entete.lower().startswith("basic "):
            import base64
            from urllib.parse import unquote
            try:
                ident, _, secret = base64.b64decode(entete[6:]).decode().partition(":")
                basic = (unquote(ident), unquote(secret))
            except ValueError:
                return json_oauth({"error": "invalid_client"}, 401)
        try:
            rep = await asyncio.get_running_loop().run_in_executor(None, oauth.echanger, form, basic)
        except oauth.ErreurOAuth as exc:
            return json_oauth({"error": exc.code, "error_description": exc.description}, exc.statut)
        return json_oauth(rep)

    async def oauth_revoke(request):
        if request.method == "OPTIONS":
            return Response(status_code=204, headers=cors)
        oauth.revoquer_jeton((await request.form()).get("token", ""))
        return Response(status_code=200, headers=cors)

    async def deconnecter(request):
        if not abonnement.actif():
            return ferme()
        row = ligne_depuis(await request.form())
        if not row:
            return vue(page.page_compte(erreur="Unknown personal address."), 404)
        n = oauth.deconnecter_tout(row["abonnement"])
        return vue(page.page_gestion(row, abonnement.adresse(abonnement.cle_de(row["abonnement"], row["version"])),
                                     info="Assistants disconnected (%d token(s) deleted). Reconnect them whenever you like." % n))

    return [
        Route("/.well-known/oauth-protected-resource", meta_ressource, methods=["GET", "OPTIONS"]),
        Route("/.well-known/oauth-protected-resource/abonne/mcp", meta_ressource, methods=["GET", "OPTIONS"]),
        Route("/.well-known/oauth-authorization-server", meta_serveur, methods=["GET", "OPTIONS"]),
        Route("/.well-known/openid-configuration", meta_serveur, methods=["GET", "OPTIONS"]),
        Route("/oauth/register", oauth_register, methods=["POST", "OPTIONS"]),
        Route("/oauth/authorize", oauth_authorize, methods=["GET", "POST"]),
        Route("/oauth/token", oauth_token, methods=["POST", "OPTIONS"]),
        Route("/oauth/revoke", oauth_revoke, methods=["POST", "OPTIONS"]),
        Route("/compte/deconnecter", deconnecter, methods=["POST"]),
        Route("/admin/api/resume", admin_resume),
        Route("/admin/api/regenerer", admin_regenerer, methods=["POST"]),
        Route("/abonnement", formulaire, methods=["GET", "POST"]),
        Route("/merci", merci),
        Route("/compte", compte, methods=["GET", "POST"]),
        Route("/compte/acces", acces),
        Route("/compte/portail", portail, methods=["POST"]),
        Route("/compte/regenerer", regenerer, methods=["POST"]),
        Route("/compte/lien", lien, methods=["POST"]),
        Route("/stripe/webhook", webhook, methods=["POST"]),
    ]


app = build_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8000")),
                proxy_headers=False)
