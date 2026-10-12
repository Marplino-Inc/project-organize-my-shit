#!/bin/sh
set -eu
umask 077
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if ! command -v uv >/dev/null 2>&1; then
  echo "Install uv using your employer-approved method, then rerun this setup."
  echo "https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi
uv sync --locked --no-dev --python 3.12
printf '\nSetup complete. Run: sh Start.command\n'
