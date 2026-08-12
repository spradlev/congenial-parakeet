#!/usr/bin/env bash
set -euo pipefail

echo "Build script: create a .venv, install py2app, build .app, and move to ~/Documents"
PY=python3

if [[ "$(uname)" != "Darwin" ]]; then
  echo "This script is intended to run on macOS (Darwin). Aborting."
  exit 1
fi

# Create venv
$PY -m venv .venv
# Activate
# shellcheck disable=SC1091
source .venv/bin/activate

# Install build deps
pip install --upgrade pip setuptools wheel py2app

# Clean previous builds
rm -rf build dist

# Build the app
python3 setup.py py2app

# Move to Documents
mkdir -p "$HOME/Documents"
APP_NAME="rps_gui.app"
if [[ -d "dist/$APP_NAME" ]]; then
  mv -f "dist/$APP_NAME" "$HOME/Documents/RPS.app"
  echo "Built app moved to: $HOME/Documents/RPS.app"
else
  echo "Build failed: dist/$APP_NAME not found"
  exit 1
fi

# Optional: create a DMG (uncomment to enable)
# DMG_NAME="$HOME/Documents/RPS.dmg"
# hdiutil create -volname "RPS" -srcfolder "$HOME/Documents/RPS.app" -ov -format UDZO "$DMG_NAME"
# echo "DMG created at $DMG_NAME"

# Deactivate venv (best-effort)
deactivate || true

echo "Done. You can now double-click ~/Documents/RPS.app to run the game."
