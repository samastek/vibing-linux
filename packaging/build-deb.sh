#!/usr/bin/env bash
# ─── Build .deb package for Vibing Linux ────────────────────────────────────
#
# Usage:
#   ./build-deb.sh                  # build with version from pyproject.toml
#   ./build-deb.sh --version 0.2.0  # override version
#
# Prerequisites:
#   - nfpm (https://nfpm.goreleaser.com/install/)
#     Install: go install github.com/goreleaser/nfpm/v2/cmd/nfpm@latest
#          or: curl -sfL https://install.goreleaser.com/github.com/goreleaser/nfpm.sh | sh
#
# Output:
#   vibing-linux_<version>_amd64.deb  in the packaging/ directory
# ────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments
VERSION=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --version) VERSION="$2"; shift 2 ;;
        *)         echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Auto-detect version from pyproject.toml if not specified
if [[ -z "$VERSION" ]]; then
    VERSION=$(grep -oP '^version = "\K[^"]+' "$PROJECT_DIR/pyproject.toml" | head -1)
    if [[ -z "$VERSION" ]]; then
        echo "Error: Could not detect version from pyproject.toml"
        exit 1
    fi
fi

echo "═══ Building vibing-linux ${VERSION} .deb package ═══"

# Check nfpm is available
if ! command -v nfpm &>/dev/null; then
    echo "Error: nfpm is not installed."
    echo ""
    echo "Install it with one of:"
    echo "  go install github.com/goreleaser/nfpm/v2/cmd/nfpm@latest"
    echo "  curl -sfL https://install.goreleaser.com/github.com/goreleaser/nfpm.sh | sh"
    echo "  snap install nfpm"
    exit 1
fi

# Ensure scripts are executable
chmod +x "$SCRIPT_DIR/scripts/postinst"
chmod +x "$SCRIPT_DIR/scripts/prerm"
chmod +x "$SCRIPT_DIR/scripts/postrm"
chmod +x "$SCRIPT_DIR/bin/vibing-linux"

# Clean any previous build artifacts in the source tree
find "$PROJECT_DIR/vibing" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_DIR/vibing" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Build
cd "$SCRIPT_DIR"
export VERSION
nfpm pkg --packager deb --target "${SCRIPT_DIR}/vibing-linux_${VERSION}_amd64.deb"

echo ""
echo "═══ Build complete ═══"
echo "  Package: ${SCRIPT_DIR}/vibing-linux_${VERSION}_amd64.deb"
echo ""
echo "  Install with:"
echo "    sudo apt install ./vibing-linux_${VERSION}_amd64.deb"
echo ""
echo "  Inspect with:"
echo "    dpkg -I vibing-linux_${VERSION}_amd64.deb"
echo "    dpkg -c vibing-linux_${VERSION}_amd64.deb"
