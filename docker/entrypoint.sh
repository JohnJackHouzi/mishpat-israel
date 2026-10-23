#!/bin/sh
set -e
mkdir -p "$MISHPAT_DATA"
if [ "${MISHPAT_AUTO_UPDATE:-1}" = "1" ]; then
  python -I scripts/update.py --service &
fi
exec python server/server.py
