#!/bin/sh
set -eu
umask 077
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ ! -x .venv/bin/python ]; then
  echo "Run sh Setup.command first."
  exit 1
fi
exec .venv/bin/python main.py "$@"
