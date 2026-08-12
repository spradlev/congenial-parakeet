#!/usr/bin/env bash
set -euo pipefail

echo "Build script: create a .venv, install py2app, build .app, and move to ~/Documents"
PY=${PY:-python3}

if [[ "$(uname)" != "Darwin" ]]; then
  echo "This script is intended to run on macOS (Darwin). Aborting."
  exit 1
fi

# Remove existing venv to ensure it's created with the selected python
rm -rf .venv

# Create venv
$PY -m venv .venv

# Use venv python explicitly for installs and build to avoid PATH/activation issues
VENV_PY=".venv/bin/python"

# Install build deps into the venv
"$VENV_PY" -m pip install --upgrade pip setuptools wheel py2app importlib_resources

# Clean previous builds
rm -rf build dist

# Build the app using the venv python
"$VENV_PY" setup.py py2app

# Move to Documents
mkdir -p "$HOME/Documents"
# Find any .app produced in dist and move it. Use a stable name RPS.app in Documents.
APP_PATH=$(ls -1 dist/*.app 2>/dev/null | head -n 1 || true)
if [[ -n "$APP_PATH" && -d "$APP_PATH" ]]; then
  mv -f "$APP_PATH" "$HOME/Documents/RPS.app"
  echo "Built app moved to: $HOME/Documents/RPS.app"
else
  echo "Build failed: no .app found in dist"
  exit 1
fi

# Optional: create a DMG (uncomment to enable)
# DMG_NAME="$HOME/Documents/RPS.dmg"
# hdiutil create -volname "RPS" -srcfolder "$HOME/Documents/RPS.app" -ov -format UDZO "$DMG_NAME"
# echo "DMG created at $DMG_NAME"

# Deactivate venv (best-effort)
deactivate || true

echo "Done. You can now double-click ~/Documents/RPS.app to run the game."
