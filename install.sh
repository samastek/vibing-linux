#!/usr/bin/env bash
# ─── Vibing Linux — install / update script (pipx fallback) ────────────────
#
# RECOMMENDED: Install via .deb package from GitHub Releases instead:
#   sudo apt install ./vibing-linux_*.deb
#
# This script is a fallback for users who prefer pipx or non-Debian systems.
#
# Usage:
#   ./install.sh                 # install or update vibing
#   ./install.sh --cuda 12.8     # override CUDA version (default: auto-detect)
#   ./install.sh --cpu           # force CPU-only torch
#
# Prerequisites:
#   - pipx (apt install pipx)
#   - python3-gi (apt install python3-gi gir1.2-ayatanaappindicator3-0.1)
#   - libportaudio2 (apt install libportaudio2)
#   - wl-clipboard or xclip (apt install wl-clipboard)
# ────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$HOME/.local/share/pipx/venvs/vibing-linux"
VENV_CFG="$VENV_DIR/pyvenv.cfg"

CUDA_VER=""
CPU_ONLY=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --cuda)  CUDA_VER="$2"; shift 2 ;;
        --cpu)   CPU_ONLY=true; shift ;;
        *)       echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "═══ Vibing Linux installer ═══"

# ── 1. pipx install ─────────────────────────────────────────────────────────
echo "→ Installing vibing-linux via pipx..."
pipx install "$SCRIPT_DIR" --force

# ── 2. Enable system site-packages (for gi / PyGObject) ─────────────────────
if [[ -f "$VENV_CFG" ]]; then
    sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' "$VENV_CFG"
    echo "→ Enabled system site-packages (PyGObject)"
fi

# ── 3. Install correct torch build ──────────────────────────────────────────
INSTALLED_TORCH=$("$VENV_DIR/bin/python" -c "import torch; print(torch.__version__)" 2>/dev/null || echo "")

if $CPU_ONLY; then
    if [[ "$INSTALLED_TORCH" == "2.11.0+cpu" ]]; then
        echo "→ PyTorch 2.11.0+cpu already installed, skipping."
    else
        echo "→ Installing CPU-only torch..."
        pipx runpip vibing-linux install "torch==2.11.0+cpu" \
            --extra-index-url https://download.pytorch.org/whl/cpu \
            --force-reinstall --no-deps
    fi
else
    # Auto-detect CUDA version from nvidia-smi if not specified
    if [[ -z "$CUDA_VER" ]]; then
        if command -v nvidia-smi &>/dev/null; then
            CUDA_VER=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1)
            # Map driver to max supported CUDA
            DRIVER_CUDA=$(nvidia-smi | grep -oP 'CUDA Version: \K[0-9]+\.[0-9]+' 2>/dev/null || true)
            if [[ -n "$DRIVER_CUDA" ]]; then
                MAJOR=$(echo "$DRIVER_CUDA" | cut -d. -f1)
                MINOR=$(echo "$DRIVER_CUDA" | cut -d. -f2)
                CUDA_VER="${MAJOR}.${MINOR}"
            fi
        fi
    fi

    if [[ -z "$CUDA_VER" ]]; then
        if [[ "$INSTALLED_TORCH" == "2.11.0+cpu" ]]; then
            echo "→ PyTorch 2.11.0+cpu already installed, skipping."
        else
            echo "→ No GPU detected, installing CPU-only torch..."
            pipx runpip vibing-linux install "torch==2.11.0+cpu" \
                --extra-index-url https://download.pytorch.org/whl/cpu \
                --force-reinstall --no-deps
        fi
    else
        # Map CUDA version to torch index name (e.g. 12.8 → cu128)
        CU_TAG="cu$(echo "$CUDA_VER" | tr -d '.')"
        EXPECTED_TORCH="2.11.0+${CU_TAG}"
        if [[ "$INSTALLED_TORCH" == "$EXPECTED_TORCH" ]]; then
            echo "→ PyTorch $EXPECTED_TORCH already installed, skipping."
        else
            echo "→ Detected CUDA $CUDA_VER — installing torch+${CU_TAG}..."
            pipx runpip vibing-linux install "torch==2.11.0+${CU_TAG}" \
                --extra-index-url "https://download.pytorch.org/whl/${CU_TAG}" \
                --force-reinstall
        fi
    fi
fi

# ── 4. Verify ────────────────────────────────────────────────────────────────
echo ""
echo "═══ Verifying installation ═══"
"$VENV_DIR/bin/python" -c "
import torch
cuda = torch.cuda.is_available()
print(f'  torch:  {torch.__version__}')
print(f'  CUDA:   {\"yes — \" + torch.cuda.get_device_name(0) if cuda else \"no (CPU mode)\"}')
"
echo ""
echo "✓ Done!  Run:  vibing-linux"
echo "  First launch will download AI models and set up config automatically."
