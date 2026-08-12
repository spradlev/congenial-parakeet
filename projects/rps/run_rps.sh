#!/bin/bash
# Simple launcher for the RPS Tk app. Intended for use as the "Script" in a Platypus app.
# Looks for a python.org python first, falls back to python3 in PATH.

set -e
PY_CANDIDATES=("/usr/local/bin/python3" "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3" "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3" "python3")
PY=""
for p in "${PY_CANDIDATES[@]}"; do
  if [ -x "$p" ]; then
    PY="$p"
    break
  fi
  if command -v "$p" >/dev/null 2>&1; then
    PY="$(command -v "$p")"
    break
  fi
done

if [ -z "$PY" ]; then
  echo "No usable python3 found. Install python.org Python or ensure python3 is in PATH." >&2
  exit 1
fi

# Run the GUI from the script directory so relative paths work
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# If the project has a .venv, prefer it
if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
  PY="$SCRIPT_DIR/.venv/bin/python"
fi

exec "$PY" "$SCRIPT_DIR/rps_gui.py" "$@"
