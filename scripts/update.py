"""Mises à jour : lois (Wikisource, incrémental) chaque nuit, Knesset chaque semaine.

--service : boucle infinie pour le conteneur (premier passage au démarrage si une base manque).
"""
import argparse
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import KNESSET_DB, LAWS_DB  # noqa: E402

HERE = Path(__file__).resolve().parent
HEURE = 3


def lancer(script):
    print("[maj] %s : %s" % (dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), script), flush=True)
    r = subprocess.run([sys.executable, "-I", str(HERE / script)])
    if r.returncode:
        print("[maj] échec de %s (code %d)" % (script, r.returncode), flush=True)


def passe(knesset):
    lancer("build_laws.py")
    if knesset:
        lancer("fetch_knesset.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--service", action="store_true")
    ap.add_argument("--knesset", action="store_true")
    a = ap.parse_args()
    if not a.service:
        return passe(a.knesset or not KNESSET_DB.exists())
    if not LAWS_DB.exists() or not KNESSET_DB.exists():
        passe(not KNESSET_DB.exists())
    while True:
        now = dt.datetime.now(dt.timezone.utc)
        nxt = now.replace(hour=HEURE, minute=30, second=0, microsecond=0)
        if nxt <= now:
            nxt += dt.timedelta(days=1)
        time.sleep((nxt - now).total_seconds())
        passe(nxt.weekday() == 6)


if __name__ == "__main__":
    main()
