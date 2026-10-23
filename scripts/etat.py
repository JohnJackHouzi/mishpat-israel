import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import KNESSET_DB, LAWS_DB, connect  # noqa: E402


def _meta(con):
    try:
        return {r[0]: r[1] for r in con.execute("SELECT k, v FROM meta")}
    except Exception:
        return {}


def etat(comptes=True):
    e = {"pret": False, "lois": None, "knesset": None}
    if LAWS_DB.exists():
        try:
            con = connect(LAWS_DB)
            m = _meta(con)
            e["lois"] = {"synchro": m.get("wikisource_sync", ""), "pages_projet": m.get("wikisource_pages", "")}
            if comptes:
                e["lois"]["textes"] = con.execute("SELECT count(*) FROM laws").fetchone()[0]
                e["lois"]["sections"] = con.execute("SELECT count(*) FROM sections").fetchone()[0]
                e["lois"]["par_type"] = dict(con.execute("SELECT kind, count(*) FROM laws GROUP BY kind ORDER BY 2 DESC"))
            e["pret"] = bool(m.get("wikisource_sync"))
        except Exception as exc:
            e["lois"] = {"erreur": str(exc)[:200]}
    if KNESSET_DB.exists():
        try:
            con = connect(KNESSET_DB)
            m = _meta(con)
            e["knesset"] = {"source": m.get("knesset_source", ""), "telecharge": m.get("knesset_fetched", ""),
                            "donnees_jusqu_au": m.get("knesset_data_until", ""),
                            "miroir_du": m.get("knesset_mirror_date", "")}
            if comptes:
                e["knesset"]["lois"] = con.execute("SELECT count(*) FROM KNS_IsraelLaw").fetchone()[0]
                e["knesset"]["liens_modificatifs"] = con.execute("SELECT count(*) FROM KNS_LawBinding").fetchone()[0]
        except Exception as exc:
            e["knesset"] = {"erreur": str(exc)[:200]}
    return e


def texte():
    e = etat()
    out = []
    lo = e["lois"] or {}
    if "textes" in lo:
        out.append("Consolidated texts (Hebrew Wikisource, ספר החוקים הפתוח, CC BY-SA 4.0): %d texts, %d sections, "
                   "last sync %s." % (lo["textes"], lo["sections"], lo["synchro"] or "never"))
        out.append("By type: " + ", ".join("%s %d" % kv for kv in lo["par_type"].items()))
    else:
        out.append("Consolidated texts: not installed.")
    k = e["knesset"] or {}
    if "lois" in k:
        out.append("Knesset legislative database: %d laws, %d amendment links, data up to %s, source %s%s, "
                   "downloaded %s." % (k["lois"], k["liens_modificatifs"], k["donnees_jusqu_au"],
                                       "official OData API" if k["source"] == "officielle" else "public mirror",
                                       " dated %s" % k["miroir_du"] if k.get("miroir_du") else "", k["telecharge"]))
    else:
        out.append("Knesset legislative database: not installed.")
    out.append("Not covered: case law (court decisions), point-in-time versions, English translations. "
               "No consolidated text in Israel is official: the binding text is the Reshumot publication.")
    return "\n".join(out)


if __name__ == "__main__":
    print(texte())
