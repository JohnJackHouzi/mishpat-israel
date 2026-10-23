"""Interrogation des bases : article, recherche, loi, historique, verifier, etat."""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ATTRIBUTION, KNESSET_DB, LAWS_DB, connect, key, norm, title_key, wiki_url  # noqa: E402

DISCLAIMER = ("Unofficial consolidated text (community-maintained, may lag behind amendments). Binding version: "
              "רשומות (Reshumot) publications linked in this answer. Legal information, not legal advice.")

ALIASES = {
    "privacy protection law": "חוק הגנת הפרטיות", "protection of privacy law": "חוק הגנת הפרטיות",
    "privacy law": "חוק הגנת הפרטיות", "consumer protection law": "חוק הגנת הצרכן",
    "electronic signature law": "חוק חתימה אלקטרונית", "computers law": "חוק המחשבים",
    "contracts law": "חוק החוזים (חלק כללי)", "contracts law (general part)": "חוק החוזים (חלק כללי)",
    "standard contracts law": "חוק החוזים האחידים", "sale law": "חוק המכר",
    "companies law": "חוק החברות", "copyright law": "חוק זכות יוצרים", "patents law": "חוק הפטנטים",
    "trademarks ordinance": "פקודת סימני מסחר", "penal law": "חוק העונשין",
    "income tax ordinance": "פקודת מס הכנסה", "value added tax law": "חוק מס ערך מוסף",
    "vat law": "חוק מס ערך מוסף", "freedom of information law": "חוק חופש המידע",
    "anti-spam law": "חוק התקשורת (בזק ושידורים)", "communications law": "חוק התקשורת (בזק ושידורים)",
    "equal employment opportunities law": "חוק שוויון ההזדמנויות בעבודה",
    "minimum wage law": "חוק שכר מינימום", "annual leave law": "חוק חופשה שנתית",
    "severance pay law": "חוק פיצויי פיטורים", "hours of work and rest law": "חוק שעות עבודה ומנוחה",
    "equal rights for persons with disabilities law": "חוק שוויון זכויות לאנשים עם מוגבלות",
    "prohibition on money laundering law": "חוק איסור הלבנת הון", "securities law": "חוק ניירות ערך",
    "restrictive trade practices law": "חוק התחרות הכלכלית", "economic competition law": "חוק התחרות הכלכלית",
    "torts ordinance": "פקודת הנזיקין", "civil wrongs ordinance": "פקודת הנזיקין",
    "unjust enrichment law": "חוק עשיית עושר ולא במשפט", "land law": "חוק המקרקעין",
    "basic law: human dignity and liberty": "חוק-יסוד: כבוד האדם וחירותו",
    "basic law: freedom of occupation": "חוק-יסוד: חופש העיסוק", "basic law: the knesset": "חוק-יסוד: הכנסת",
    "prohibition of defamation law": "חוק איסור לשון הרע", "defamation law": "חוק איסור לשון הרע",
    "credit data law": "חוק נתוני אשראי", "payment services law": "חוק שירותי תשלום",
    "interpretation law": "חוק הפרשנות", "evidence ordinance": "פקודת הראיות",
    "national insurance law": "חוק הביטוח הלאומי", "planning and building law": "חוק התכנון והבניה",
    "insolvency and economic rehabilitation law": "חוק חדלות פירעון ושיקום כלכלי",
    "data security regulations": "תקנות הגנת הפרטיות (אבטחת מידע)",
    "privacy protection (data security) regulations": "תקנות הגנת הפרטיות (אבטחת מידע)",
}

PREFIXES = ["", "ה", "ו", "ב", "ל", "מ", "ש", "כ", "וה", "וב", "ול", "ומ", "וש", "שה", "שב", "של", "מה", "בה",
            "לה", "כש", "וכ", "שמ"]


# ---------------------------------------------------------------- outils

def laws_db():
    if not LAWS_DB.exists():
        sys.exit("Base des lois absente : lancer scripts/build_laws.py")
    return connect(LAWS_DB)


def knesset_db():
    return connect(KNESSET_DB) if KNESSET_DB.exists() else None


def meta(con, k):
    try:
        r = con.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
    except Exception:
        return ""
    return r[0] if r else ""


KIND_RANK = {"basic_law": 0, "law": 0, "ordinance": 1, "regulations": 2, "order": 3, "rules": 3}


def resolve(con, q, n=5):
    """Renvoie (meilleure loi, autres candidates)."""
    q0 = q.strip()
    if not q0:
        return None, []
    q1 = ALIASES.get(q0.lower().strip(" ."), q0)
    nq = norm(q1)
    if q1.isdigit():
        rows = con.execute("SELECT * FROM laws WHERE knesset_id=? OR id=? ORDER BY knesset_id=? DESC",
                           (int(q1), int(q1), int(q1))).fetchall()
        if rows:
            return rows[0], rows[1:n]
    rows = con.execute("SELECT * FROM laws WHERE title=? OR full_title=?", (q1, q1)).fetchall()
    if not rows:
        rows = [r for r in con.execute("SELECT * FROM laws WHERE tkey=?", (title_key(nq),))]
    if rows:
        rows.sort(key=lambda r: (KIND_RANK.get(r["kind"], 5), len(r["title"])))
        return rows[0], rows[1:n]
    words = [w for w in re.findall(r"[\w֐-׿]+", nq) if len(w) > 1 and not w.isdigit()]
    if not words:
        return None, []
    match = " AND ".join('"%s"*' % w for w in words)
    try:
        ids = [r[0] for r in con.execute("SELECT rowid FROM titles_fts WHERE titles_fts MATCH ? ORDER BY rank LIMIT 40",
                                         (match,))]
    except Exception:
        ids = []
    if not ids:
        return None, []
    rows = con.execute("SELECT * FROM laws WHERE id IN (%s)" % ",".join("?" * len(ids)), ids).fetchall()
    tk = title_key(nq)
    rows.sort(key=lambda r: (not r["tkey"].startswith(tk), KIND_RANK.get(r["kind"], 5), len(r["title"])))
    return rows[0], rows[1:n]


def not_found(q, others):
    out = ["LAW NOT FOUND: %s" % q,
           "Use the Hebrew title (e.g. חוק הגנת הפרטיות, תקנות הגנת הפרטיות (אבטחת מידע)) or search_law_titles."]
    if others:
        out.append("Close titles: " + " ; ".join(r["title"] for r in others))
    return "\n".join(out)


HEB_YEAR = re.compile(r"(ה?ת[א-ת]{1,3}\"[א-ת])")


def pub_rows(con, law_id):
    rows, year, series = [], "", ""
    for r in con.execute("SELECT * FROM pubs WHERE law_id=? ORDER BY ord", (law_id,)):
        c = norm(r["citation"])
        m = HEB_YEAR.search(c)
        if m:
            year = m.group(1).lstrip("ה") if len(m.group(1)) > 4 else m.group(1)
        s = re.match(r"^([א-ת]+\"[א-ת])\s", c)
        if s:
            series = s.group(1)
        rows.append({"citation": r["citation"], "name": r["name"], "url": r["url"], "year": year, "series": series})
    return rows


def years_in(text):
    return {y.lstrip("ה") if len(y) > 4 else y for y in HEB_YEAR.findall(norm(text))}


def find_section(con, law_id, num):
    k = key(num)
    rows = con.execute("SELECT * FROM sections WHERE law_id=? AND (akey=? OR nkey=?) ORDER BY akey=? DESC, "
                       "anchor LIKE 'סעיף %' DESC, ord", (law_id, k, k, k)).fetchall()
    if rows:
        return rows[0]
    m = re.match(r"^(תוספת|schedule)\s*(.*)$", norm(num), re.I)
    if m:
        rows = con.execute("SELECT * FROM sections WHERE law_id=? AND (path LIKE ? OR anchor LIKE ?) ORDER BY ord",
                           (law_id, "%תוספת%", "תוספת%")).fetchall()
        return rows[0] if rows else None
    return None


def is_repealed(text):
    return bool(re.fullmatch(r"\(?(בוטל|בוטלה|בוטלו|נמחק|נמחקה)\)?\.?;?", norm(text)))


def law_header(law):
    return "%s\nWikisource: %s (revision %s, %s)%s" % (
        law["full_title"] or law["title"], wiki_url(law["title"]), law["revid"], (law["rev_ts"] or "")[:10],
        "\nKnesset law ID (IsraelLawID): %s" % law["knesset_id"] if law["knesset_id"] else "")


# ---------------------------------------------------------------- commandes

def cmd_article(a):
    con = laws_db()
    law, others = resolve(con, a.loi)
    if not law:
        return not_found(a.loi, others)
    s = find_section(con, law["id"], a.numero)
    if not s:
        nums = [r[0] for r in con.execute("SELECT num FROM sections WHERE law_id=? AND num!='' AND anchor LIKE 'סעיף %' "
                                          "ORDER BY ord", (law["id"],))]
        return "SECTION NOT FOUND: %s, section %s\nSections in this text: %s\n%s" % (
            law["title"], a.numero, ", ".join(nums[:400]) or "(none numbered)", wiki_url(law["title"]))
    out = [law_header(law), ""]
    if s["path"]:
        out.append("Part: " + s["path"])
    label = s["anchor"] or ("סעיף " + s["num"] if s["num"] else "")
    out.append("%s%s" % (label, " - " + s["title"] if s["title"] else ""))
    if s["amend"]:
        out.append("Amendment note (Wikisource): " + s["amend"])
    if is_repealed(s["text"]):
        out.append("STATUS: REPEALED (בוטל). Do not cite as current law.")
    out += ["", s["text"] or "(empty)", ""]
    out.append("Link: " + wiki_url(law["title"], s["anchor"]))
    pubs = pub_rows(con, law["id"])
    yrs = years_in(s["amend"])
    rel = [p for p in pubs if p["year"] in yrs] if yrs else []
    if rel:
        out.append("Official publications for the amendment years of this section (Reshumot PDF):")
        out += ["- %s, %s: %s" % (p["citation"], p["name"], p["url"] or "(no link)") for p in rel]
    if pubs:
        out.append("Original publication: %s, %s: %s" % (pubs[0]["citation"], pubs[0]["name"], pubs[0]["url"]))
    out += ["", DISCLAIMER, ATTRIBUTION]
    if others and a.loi.strip() != law["title"]:
        out.append("Other texts with a close title: " + " ; ".join(r["title"] for r in others[:4]))
    return "\n".join(out)


def fts_query(q):
    tokens = re.findall(r'"[^"]+"|\(|\)|\S+', norm(q).replace("״", '"'))
    out = []
    for t in tokens:
        if t in ("AND", "OR", "NOT", "(", ")") or t.startswith('"'):
            out.append(t)
        elif t.endswith("*"):
            out.append('"%s"*' % t[:-1].replace('"', ""))
        else:
            w = re.sub(r"[^\w֐-׿\-']", "", t).replace('"', "")
            if not w:
                continue
            if re.search(r"[א-ת]", w) and len(w) >= 2:
                out.append("(" + " OR ".join('"%s"' % (p + w) for p in PREFIXES) + ")")
            else:
                out.append('"%s"' % w)
    res = []
    for t in out:
        if res and res[-1] not in ("AND", "OR", "NOT", "(") and t not in ("AND", "OR", "NOT", ")"):
            res.append("AND")
        res.append(t)
    return " ".join(res)


KINDS = {"law": ("law", "basic_law"), "basic_law": ("basic_law",), "ordinance": ("ordinance",),
         "regulations": ("regulations",), "order": ("order",), "rules": ("rules",)}


def cmd_recherche(a):
    con = laws_db()
    q = fts_query(a.q)
    if not q:
        return "Empty query."
    where, args = ["sections_fts MATCH ?"], [q]
    if a.loi:
        law, others = resolve(con, a.loi)
        if not law:
            return not_found(a.loi, others)
        where.append("s.law_id=?")
        args.append(law["id"])
    if a.type in KINDS:
        where.append("l.kind IN (%s)" % ",".join("?" * len(KINDS[a.type])))
        args += list(KINDS[a.type])
    sql = ("SELECT s.*, l.title AS law_title, l.kind, snippet(sections_fts, 2, '[', ']', ' … ', 28) AS snip, "
           "bm25(sections_fts, 4.0, 2.0, 1.0) AS score FROM sections_fts JOIN sections s ON s.id=sections_fts.rowid "
           "JOIN laws l ON l.id=s.law_id WHERE %s ORDER BY score + (CASE WHEN l.kind IN ('law','basic_law') THEN -2 "
           "ELSE 0 END) LIMIT ?" % " AND ".join(where))
    try:
        rows = con.execute(sql, args + [a.limit]).fetchall()
    except Exception as exc:
        return "Invalid query (%s). Syntax: words, \"exact phrase\", AND, OR, NOT, prefix*." % exc
    if not rows:
        return "No result for: %s (search in Hebrew; Hebrew prefixes ה/ו/ב/ל/מ/ש/כ are handled automatically)." % a.q
    out = ["%d result(s) for: %s" % (len(rows), a.q), ""]
    for i, r in enumerate(rows, 1):
        label = r["anchor"] or ("סעיף " + r["num"] if r["num"] else "(untitled block)")
        out.append("%d. %s | %s%s" % (i, r["law_title"], label, " - " + r["title"] if r["title"] else ""))
        out.append("   " + r["snip"].replace("\n", " "))
        out.append("   " + wiki_url(r["law_title"], r["anchor"]))
    out += ["", "Read the full section with read_section before relying on it. " + ATTRIBUTION]
    return "\n".join(out)


def cmd_titres(a):
    con = laws_db()
    best, others = resolve(con, a.q, n=a.limit)
    if not best:
        return "No title matches: %s" % a.q
    out = []
    for r in [best] + list(others):
        out.append("- %s [%s, %d sections] %s%s" % (r["full_title"] or r["title"], r["kind"], r["n_sections"],
                                                     wiki_url(r["title"]),
                                                     " (Knesset ID %s)" % r["knesset_id"] if r["knesset_id"] else ""))
    return "\n".join(out)


def cmd_loi(a):
    con = laws_db()
    law, others = resolve(con, a.loi)
    if not law:
        return not_found(a.loi, others)
    out = [law_header(law), "Type: %s ; sections: %d" % (law["kind"], law["n_sections"]), ""]
    if law["preamble"]:
        out += ["Preamble / notes:", law["preamble"][:3000], ""]
    pubs = pub_rows(con, law["id"])
    if pubs:
        out.append("Publications in Reshumot (original + amendments), as listed on Wikisource:")
        out += ["- %s, %s: %s" % (p["citation"], p["name"], p["url"] or "(no link)") for p in pubs]
        out.append("")
    out.append("Table of contents:")
    last = None
    for s in con.execute("SELECT num, anchor, title, path, amend FROM sections WHERE law_id=? ORDER BY ord", (law["id"],)):
        if s["path"] != last and s["path"]:
            out.append("## " + s["path"])
            last = s["path"]
        label = s["anchor"] or s["num"]
        if label or s["title"]:
            out.append("  %s%s%s" % (label, " - " + s["title"] if s["title"] else "",
                                     " [%s]" % s["amend"] if s["amend"] else ""))
    out += ["", DISCLAIMER, ATTRIBUTION]
    if others:
        out.append("Other texts with a close title: " + " ; ".join(r["title"] for r in others[:4]))
    text = "\n".join(out)
    return text if len(text) < a.max_chars else text[:a.max_chars] + "\n[... truncated: read sections individually ...]"


def knesset_law_id(con_l, con_k, q):
    law, _ = resolve(con_l, q) if con_l else (None, [])
    if law and law["knesset_id"]:
        return law, law["knesset_id"]
    if q.strip().isdigit():
        return law, int(q)
    r = con_k.execute("SELECT israel_law_id FROM law_keys WHERE tkey=? LIMIT 1", (title_key(q),)).fetchone()
    return law, (r[0] if r else None)


def pdf_url(path):
    scheme, _, rest = (path or "").replace("\\", "/").partition("://")
    return scheme + "://" + re.sub(r"/{2,}", "/", rest) if rest else scheme


def fmt_date(s):
    return (s or "")[:10]


def cmd_historique(a):
    con_l = laws_db()
    con_k = knesset_db()
    law, others = resolve(con_l, a.loi)
    out = []
    if law:
        out.append(law_header(law))
        pubs = pub_rows(con_l, law["id"])
        if pubs:
            out += ["", "A. Publications in Reshumot listed on Wikisource (%d):" % len(pubs)]
            out += ["- %s, %s: %s" % (p["citation"], p["name"], p["url"] or "(no link)") for p in pubs]
    if con_k is None:
        out.append("\nKnesset database not installed.")
    else:
        _, kid = knesset_law_id(con_l, con_k, a.loi)
        il = con_k.execute("SELECT * FROM KNS_IsraelLaw WHERE Id=?", (kid,)).fetchone() if kid else None
        src = meta(con_k, "knesset_source")
        until = meta(con_k, "knesset_data_until")
        out.append("\nB. Knesset database (KNS_IsraelLaw %s), source: %s, data up to %s%s" % (
            kid or "?", "official Knesset OData API" if src == "officielle" else "public mirror of the Knesset OData API",
            until, "" if src == "officielle" else " (amendments after this date are missing here; see A)"))
        if il:
            out.append("Name: %s" % il["Name"])
            out.append("Status: %s ; basic law: %s ; first publication: %s ; latest publication: %s%s%s" % (
                il["LawValidityDesc"], "yes" if il["IsBasicLaw"] else "no", fmt_date(il["PublicationDate"]),
                fmt_date(il["LatestPublicationDate"]),
                " ; in force from " + fmt_date(il["ValidityStartDate"]) if il["ValidityStartDate"] else "",
                " until %s" % fmt_date(il["ValidityFinishDate"]) if il["ValidityFinishDate"] else ""))
            names = [r[0] for r in con_k.execute("SELECT Name FROM KNS_IsraelLawName WHERE IsraelLawID=? AND Name!=?",
                                                 (kid, il["Name"]))]
            if names:
                out.append("Former names: " + " ; ".join(dict.fromkeys(names)))
            rows = con_k.execute(
                "SELECT b.Id, b.Name, b.PublicationDate, b.MagazineNumber, b.PageNumber, lb.AmendmentTypeDesc, "
                "lb.BindingTypeDesc FROM KNS_LawBinding lb JOIN KNS_Bill b ON b.Id=lb.LawID WHERE lb.IsraelLawID=? "
                "GROUP BY b.Id ORDER BY b.PublicationDate", (kid,)).fetchall()
            if rows:
                out.append("Amending laws recorded by the Knesset (%d):" % len(rows))
                for r in rows:
                    docs = [pdf_url(d[0]) for d in con_k.execute(
                        "SELECT FilePath FROM KNS_DocumentBill WHERE BillID=? AND GroupTypeDesc='חוק - פרסום ברשומות' "
                        "AND lower(FilePath) LIKE '%.pdf' ORDER BY Id", (r["Id"],))]
                    out.append("- %s | published %s | ספר החוקים %s, p. %s | %s%s" % (
                        r["Name"], fmt_date(r["PublicationDate"]) or "?", r["MagazineNumber"] or "?",
                        r["PageNumber"] or "?", r["AmendmentTypeDesc"] or r["BindingTypeDesc"] or "",
                        ("\n  PDF: " + " ; ".join(docs[:3])) if docs else ""))
            else:
                out.append("No amending law linked in the Knesset database (older amendments are often only in A).")
            rep = con_k.execute("SELECT i.Id, i.Name FROM KNS_IsraelLawBinding b JOIN KNS_IsraelLaw i ON "
                                "i.Id=b.IsraelLawID WHERE b.IsraelLawReplacedID=?", (kid,)).fetchall()
            if rep:
                out.append("Replaced by: " + " ; ".join("%s (%s)" % (r["Name"], r["Id"]) for r in rep))
        elif not law:
            return not_found(a.loi, others)
        else:
            out.append("No Knesset record linked to this text (regulations and orders are often absent).")
    out += ["", "Point-in-time versions: NOT provided. Wikisource revision dates are editing dates, not dates of "
            "entry into force, so an older revision cannot be trusted as the law at a given date. For the text at a "
            "past date, read the amendment PDFs above in order.", DISCLAIMER, ATTRIBUTION]
    return "\n".join(out)


REF = re.compile(r"^(?P<loi>.+?)[,\s]+(?:סעיף|סעיפים|section|sec\.?|s\.|§|art\.?|article)\s*(?P<num>[\w֐-׿\"'״׳()\- ]+?)\s*$", re.I)


def split_ref(ref):
    r = norm(ref)
    m = REF.match(r)
    if m:
        return m.group("loi").strip(" ,"), m.group("num").strip()
    m = re.match(r"^(?P<loi>.+?),\s*(?P<num>\d+[א-ת]*\d*)\s*$", r)
    if m:
        return m.group("loi"), m.group("num")
    return r, ""


def squash(s):
    return re.sub(r"\s+", " ", re.sub(r"[\"'.,;:()\-]", " ", norm(s))).strip().lower()


def cmd_verifier(a):
    con = laws_db()
    out = []
    quotes = a.quote or []
    for i, ref in enumerate(a.refs):
        loi, num = split_ref(ref)
        law, others = resolve(con, loi)
        if not law:
            out.append("NOT FOUND | %s | law not identified%s" % (ref, (": close titles " + " ; ".join(
                r["title"] for r in others[:3])) if others else ""))
            continue
        if not num:
            out.append("FOUND (law) | %s | %s | %s" % (ref, law["full_title"] or law["title"], wiki_url(law["title"])))
            target = "\n".join(r[0] for r in con.execute("SELECT text FROM sections WHERE law_id=?", (law["id"],)))
        else:
            s = find_section(con, law["id"], num)
            if not s:
                out.append("NOT FOUND | %s | %s has no section %s" % (ref, law["title"], num))
                continue
            repealed = is_repealed(s["text"])
            out.append("%s | %s | %s, %s%s | %s" % ("REPEALED" if repealed else "FOUND", ref,
                                                   law["full_title"] or law["title"], s["anchor"] or s["num"],
                                                   " - " + s["title"] if s["title"] else "",
                                                   wiki_url(law["title"], s["anchor"])))
            target = s["text"]
        if i < len(quotes) and quotes[i].strip():
            ok = squash(quotes[i]) in squash(target)
            out.append("  quote %s: \"%s\"" % ("PRESENT" if ok else "ABSENT", quotes[i][:200]))
    out.append("\nNOT FOUND, REPEALED or ABSENT lines must not be cited as current law. " + DISCLAIMER)
    return "\n".join(out)


def cmd_etat(a):
    import etat
    return etat.texte()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("article")
    p.add_argument("loi")
    p.add_argument("numero")
    p = sub.add_parser("recherche")
    p.add_argument("--q", required=True)
    p.add_argument("--loi", default="")
    p.add_argument("--type", default="")
    p.add_argument("--limit", type=int, default=10)
    p = sub.add_parser("titres")
    p.add_argument("q")
    p.add_argument("--limit", type=int, default=10)
    p = sub.add_parser("loi")
    p.add_argument("loi")
    p.add_argument("--max-chars", type=int, default=30000)
    p = sub.add_parser("historique")
    p.add_argument("loi")
    p = sub.add_parser("verifier")
    p.add_argument("refs", nargs="+")
    p.add_argument("--quote", action="append")
    sub.add_parser("etat")
    a = ap.parse_args()
    print({"article": cmd_article, "recherche": cmd_recherche, "titres": cmd_titres, "loi": cmd_loi,
           "historique": cmd_historique, "verifier": cmd_verifier, "etat": cmd_etat}[a.cmd](a))


if __name__ == "__main__":
    main()
