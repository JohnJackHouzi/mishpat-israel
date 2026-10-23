"""Construit ou met à jour laws.sqlite depuis le ספר החוקים הפתוח (Wikisource hébreu, API MediaWiki).

Toutes les pages de l'espace principal qui incluent {{ח:התחלה}} sont des textes du projet.
Mise à jour incrémentale : seules les pages dont la révision a changé sont relues.
"""
import argparse
import datetime as dt
import json
import sys
import time
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, LAWS_DB, API, USER_AGENT, connect, kind_of, norm, parse, title_key

SCHEMA = """
CREATE TABLE IF NOT EXISTS laws (
  id INTEGER PRIMARY KEY, title TEXT NOT NULL, full_title TEXT, tkey TEXT, kind TEXT,
  revid INTEGER, rev_ts TEXT, knesset_id INTEGER, preamble TEXT, n_sections INTEGER, n_chars INTEGER,
  wikitext BLOB
);
CREATE INDEX IF NOT EXISTS laws_tkey ON laws(tkey);
CREATE INDEX IF NOT EXISTS laws_knesset ON laws(knesset_id);
CREATE TABLE IF NOT EXISTS sections (
  id INTEGER PRIMARY KEY, law_id INTEGER NOT NULL, ord INTEGER, num TEXT, nkey TEXT, anchor TEXT, akey TEXT,
  title TEXT, amend TEXT, path TEXT, text TEXT
);
CREATE INDEX IF NOT EXISTS sections_law ON sections(law_id, ord);
CREATE INDEX IF NOT EXISTS sections_key ON sections(law_id, nkey);
CREATE TABLE IF NOT EXISTS pubs (law_id INTEGER, ord INTEGER, citation TEXT, name TEXT, url TEXT);
CREATE INDEX IF NOT EXISTS pubs_law ON pubs(law_id);
CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(law_title, sec_title, text, tokenize='unicode61 remove_diacritics 2');
CREATE VIRTUAL TABLE IF NOT EXISTS titles_fts USING fts5(title, tokenize='unicode61 remove_diacritics 2');
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
"""


def api(params, tries=5):
    params = dict(params, format="json", formatversion="2", maxlag="5")
    url = API + "?" + urllib.parse.urlencode(params)
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r)
            if data.get("error", {}).get("code") == "maxlag":
                time.sleep(5 * (n + 1))
                continue
            if "error" in data:
                raise RuntimeError(data["error"])
            return data
        except (OSError, ValueError) as exc:
            if n == tries - 1:
                raise
            print("  réessai (%s)" % exc, file=sys.stderr)
            time.sleep(3 * (n + 1))
    raise RuntimeError("API indisponible")


def list_pages():
    pages, cont = {}, {}
    while True:
        d = api({"action": "query", "generator": "embeddedin", "geititle": "תבנית:ח:התחלה", "geinamespace": 0,
                 "geilimit": "max", "prop": "info", **cont})
        for p in d.get("query", {}).get("pages", []):
            pages[p["pageid"]] = (p["title"], p["lastrevid"])
        if "continue" not in d:
            return pages
        cont = d["continue"]


def fetch(pageids):
    out, cont = {}, {}
    ids = "|".join(str(i) for i in pageids)
    while True:
        d = api({"action": "query", "pageids": ids, "prop": "revisions", "rvprop": "ids|timestamp|content",
                 "rvslots": "main", **cont})
        for p in d.get("query", {}).get("pages", []):
            revs = p.get("revisions") or []
            if revs and "content" in revs[0].get("slots", {}).get("main", {}):
                r = revs[0]
                out[p["pageid"]] = (p["title"], r["revid"], r["timestamp"], r["slots"]["main"]["content"])
        if "continue" not in d:
            return out
        cont = d["continue"]


def store(con, pid, title, revid, ts, wikitext):
    law = parse(wikitext)
    delete(con, pid)
    full = law["full_title"] or title
    con.execute("INSERT INTO laws VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (pid, title, full, title_key(title), kind_of(title), revid, ts, law["knesset_id"], law["preamble"],
                 len(law["sections"]), sum(len(s["text"]) for s in law["sections"]),
                 zlib.compress(wikitext.encode(), 6)))
    con.execute("INSERT INTO titles_fts(rowid, title) VALUES (?,?)", (pid, norm(full) + " " + norm(title)))
    for i, (cit, name, url) in enumerate(law["pubs"]):
        con.execute("INSERT INTO pubs VALUES (?,?,?,?,?)", (pid, i, cit, name, url))
    from common import key
    for i, s in enumerate(law["sections"]):
        cur = con.execute("INSERT INTO sections(law_id, ord, num, nkey, anchor, akey, title, amend, path, text) "
                          "VALUES (?,?,?,?,?,?,?,?,?,?)",
                          (pid, i, s["num"], key(s["num"]), s["anchor"], key(s["anchor"]), s["title"], s["amend"],
                           s["path"], s["text"]))
        con.execute("INSERT INTO sections_fts(rowid, law_title, sec_title, text) VALUES (?,?,?,?)",
                    (cur.lastrowid, norm(full), norm(s["title"]), norm(s["text"])))


def delete(con, pid):
    ids = [r[0] for r in con.execute("SELECT id FROM sections WHERE law_id=?", (pid,))]
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        con.execute("DELETE FROM sections_fts WHERE rowid IN (%s)" % ",".join("?" * len(chunk)), chunk)
    con.execute("DELETE FROM sections WHERE law_id=?", (pid,))
    con.execute("DELETE FROM pubs WHERE law_id=?", (pid,))
    con.execute("DELETE FROM titles_fts WHERE rowid=?", (pid,))
    con.execute("DELETE FROM laws WHERE id=?", (pid,))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reparse", action="store_true", help="réanalyser le wikitext déjà stocké, sans réseau")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    con = connect(LAWS_DB, readonly=False)
    con.executescript(SCHEMA)

    if a.reparse:
        rows = con.execute("SELECT id, title, revid, rev_ts, wikitext FROM laws").fetchall()
        for r in rows:
            store(con, r["id"], r["title"], r["revid"], r["rev_ts"], zlib.decompress(r["wikitext"]).decode())
        con.commit()
        print("réanalysé : %d pages" % len(rows))
        return

    started = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    remote = list_pages()
    local = {r[0]: r[1] for r in con.execute("SELECT id, revid FROM laws")}
    todo = [pid for pid, (_, rev) in remote.items() if local.get(pid) != rev]
    gone = [pid for pid in local if pid not in remote]
    if a.limit:
        todo = todo[:a.limit]
    print("pages du projet : %d ; à lire : %d ; retirées : %d" % (len(remote), len(todo), len(gone)), flush=True)
    for pid in gone:
        delete(con, pid)
    for i in range(0, len(todo), 50):
        batch = fetch(todo[i:i + 50])
        for pid, (title, revid, ts, text) in batch.items():
            store(con, pid, title, revid, ts, text)
        con.commit()
        print("  %d/%d" % (min(i + 50, len(todo)), len(todo)), flush=True)
        time.sleep(0.5)
    con.execute("INSERT OR REPLACE INTO meta VALUES ('wikisource_sync', ?)", (started,))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('wikisource_pages', ?)", (str(len(remote)),))
    con.commit()
    if todo or gone:
        con.execute("INSERT INTO sections_fts(sections_fts) VALUES ('optimize')")
        con.commit()
    print("terminé : %d textes en base" % con.execute("SELECT count(*) FROM laws").fetchone()[0])


if __name__ == "__main__":
    main()
