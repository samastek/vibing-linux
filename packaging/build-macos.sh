#!/usr/bin/env bash
# ─── Build .dmg package for Vibing (macOS) ──────────────────────────────────
#
# Usage:
#   ./build-macos.sh
#
# Prerequisites:
#   - pyinstaller installed in the current python environment
#   - macOS
#
# Output:
#   dist/Vibing.app
#   dist/Vibing.dmg
# ────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "═══ Building Vibing macOS Application ═══"

cd "$PROJECT_DIR"

if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found in current environment. Setting up a local build environment..."
    if [ ! -f ".venv/bin/activate" ]; then
        python3 -m venv .venv
    fi
    source .venv/bin/activate
    echo "Installing required dependencies..."
    pip install --upgrade pip
    pip install -e .
    pip install pyinstaller
fi

echo "[1/3] Cleaning previous builds..."
rm -rf build/ dist/Vibing.app dist/Vibing.dmg

echo "[2/3] Running PyInstaller..."
pyinstaller --noconfirm --clean Vibing.spec

echo "[3/3] Creating DMG image..."
hdiutil create -volname "Vibing" -srcfolder dist/Vibing.app -ov -format UDZO dist/Vibing.dmg

echo ""
echo "═══ Build complete ═══"
echo "  Application Bundle: $PROJECT_DIR/dist/Vibing.app"
echo "  Disk Image (DMG):   $PROJECT_DIR/dist/Vibing.dmg"
echo ""
echo "  You can now open the DMG file and drag Vibing.app to your Applications folder."