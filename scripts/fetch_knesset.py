"""Construit knesset.sqlite : lois d'Israël, lois modificatrices, dates et PDF officiels de רשומות.

Source officielle : API OData de la Knesset (https://knesset.gov.il/OdataV4/ParliamentInfo/), qui
n'est joignable que depuis une adresse israélienne. Sinon, repli sur le miroir public
ZeAlenu/knesset-data (Hugging Face, même schéma, ODC-BY), plus ancien : la date de chaque source
est enregistrée dans meta et affichée par les outils.
"""
import argparse
import datetime as dt
import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, KNESSET_DB, USER_AGENT, connect, title_key  # noqa: E402

TABLES = ["KNS_IsraelLaw", "KNS_IsraelLawName", "KNS_IsraelLawBinding", "KNS_LawBinding", "KNS_Bill",
          "KNS_DocumentBill", "KNS_DocumentIsraelLaw", "KNS_Status"]
ODATA = "https://knesset.gov.il/OdataV4/ParliamentInfo/"
MIRROR = "https://huggingface.co/datasets/ZeAlenu/knesset-data"


def get(url, tries=4):
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                if "maintenance-page" in r.geturl():
                    raise PermissionError("Knesset : accès refusé hors d'Israël (%s)" % r.geturl())
                return r.read()
        except PermissionError:
            raise
        except OSError as exc:
            if n == tries - 1:
                raise
            print("  réessai (%s)" % exc, file=sys.stderr)
            time.sleep(3 * (n + 1))


def official(table):
    url, rows = ODATA + table + "?$top=1000", []
    while url:
        d = json.loads(get(url))
        rows += d.get("value", [])
        url = d.get("@odata.nextLink")
    return rows


def mirror(table):
    tree = json.loads(get("https://huggingface.co/api/datasets/ZeAlenu/knesset-data/tree/main/data/" + table))
    cache = DATA / "knesset-miroir"
    cache.mkdir(exist_ok=True)

    def one(f):
        local = cache / ("%s.%s" % (Path(f["path"]).name, (f.get("oid") or "")[:12]))
        if not local.exists():
            local.write_bytes(get(MIRROR + "/resolve/main/" + urllib.parse.quote(f["path"])))
        return local.read_bytes().decode()

    files = sorted((x for x in tree if x["path"].endswith(".jsonl")), key=lambda x: x["path"])
    with ThreadPoolExecutor(8) as ex:
        texts = list(ex.map(one, files))
    return [json.loads(line) for t in texts for line in t.splitlines() if line.strip()]


def mirror_date():
    try:
        return json.loads(get("https://huggingface.co/api/datasets/ZeAlenu/knesset-data")).get("lastModified", "")[:10]
    except OSError:
        return ""


def store(con, table, rows):
    cols = ["Id"] if not rows else []
    for r in rows:
        for k in r:
            if k not in cols and not k.startswith("@"):
                cols.append(k)
    con.execute('DROP TABLE IF EXISTS "%s"' % table)
    con.execute('CREATE TABLE "%s" (%s)' % (table, ", ".join('"%s"' % c for c in cols)))
    con.executemany('INSERT INTO "%s" VALUES (%s)' % (table, ",".join("?" * len(cols))),
                    [[r.get(c) if not isinstance(r.get(c), (dict, list)) else json.dumps(r.get(c)) for c in cols]
                     for r in rows])


INDEXES = """
CREATE INDEX IF NOT EXISTS il_id ON KNS_IsraelLaw(Id);
CREATE INDEX IF NOT EXISTS lb_il ON KNS_LawBinding(IsraelLawID);
CREATE INDEX IF NOT EXISTS lb_law ON KNS_LawBinding(LawID);
CREATE INDEX IF NOT EXISTS bill_id ON KNS_Bill(Id);
CREATE INDEX IF NOT EXISTS docbill_bill ON KNS_DocumentBill(BillID);
CREATE INDEX IF NOT EXISTS ilb_il ON KNS_IsraelLawBinding(IsraelLawID);
CREATE INDEX IF NOT EXISTS ilb_rep ON KNS_IsraelLawBinding(IsraelLawReplacedID);
CREATE INDEX IF NOT EXISTS iln_il ON KNS_IsraelLawName(IsraelLawID);
CREATE TABLE IF NOT EXISTS law_keys (tkey TEXT, israel_law_id INTEGER);
CREATE INDEX IF NOT EXISTS lk_tkey ON law_keys(tkey);
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["auto", "officielle", "miroir"], default="auto")
    a = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = KNESSET_DB.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = connect(tmp, readonly=False)
    source = a.source
    if source == "auto":
        try:
            get(ODATA + "KNS_Status?$top=1")
            source = "officielle"
        except (PermissionError, OSError) as exc:
            print("API officielle injoignable (%s) : miroir Hugging Face" % exc)
            source = "miroir"
    for t in TABLES:
        rows = official(t) if source == "officielle" else mirror(t)
        store(con, t, rows)
        con.commit()
        print("  %s : %d lignes" % (t, len(rows)), flush=True)
    con.executescript(INDEXES)
    con.execute("DELETE FROM law_keys")
    for r in con.execute("SELECT Id, Name FROM KNS_IsraelLaw").fetchall():
        con.execute("INSERT INTO law_keys VALUES (?,?)", (title_key(r[1] or ""), r[0]))
    for r in con.execute("SELECT IsraelLawID, Name FROM KNS_IsraelLawName").fetchall():
        con.execute("INSERT INTO law_keys VALUES (?,?)", (title_key(r[1] or ""), r[0]))
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    con.execute("INSERT OR REPLACE INTO meta VALUES ('knesset_source', ?)", (source,))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('knesset_fetched', ?)", (now,))
    last = con.execute("SELECT max(LastUpdatedDate) FROM KNS_IsraelLaw").fetchone()[0] or ""
    con.execute("INSERT OR REPLACE INTO meta VALUES ('knesset_data_until', ?)", (last[:10],))
    if source == "miroir":
        con.execute("INSERT OR REPLACE INTO meta VALUES ('knesset_mirror_date', ?)", (mirror_date(),))
    con.commit()
    con.close()
    tmp.replace(KNESSET_DB)
    for suffix in ("-wal", "-shm"):
        Path(str(tmp) + suffix).unlink(missing_ok=True)
    print("terminé : source %s, données jusqu'au %s" % (source, last[:10]))


if __name__ == "__main__":
    main()
