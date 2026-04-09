#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="$HOME/.local/share/pipx/venvs/vibing-linux"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TORCH_VERSION="2.11.0"
CUDA_TAG="cu128"

echo "=== Vibing Linux Installer ==="

# 1. Install via pipx
echo "[1/4] Installing vibing-linux via pipx..."
pipx install "$SCRIPT_DIR" --force

# 2. Enable system site-packages (needed for PyGObject/gi)
echo "[2/4] Enabling system site-packages..."
sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' \
    "$VENV_DIR/pyvenv.cfg"

# 3. Install correct CUDA-enabled PyTorch (before nvidia libs to avoid conflicts)
INSTALLED_TORCH=$("$VENV_DIR/bin/python" -c "import torch; print(torch.__version__)" 2>/dev/null || echo "")
EXPECTED_TORCH="${TORCH_VERSION}+${CUDA_TAG}"
if [[ "$INSTALLED_TORCH" == "$EXPECTED_TORCH" ]]; then
    echo "[3/5] PyTorch $EXPECTED_TORCH already installed, skipping."
else
    echo "[3/5] Installing PyTorch ${TORCH_VERSION}+${CUDA_TAG}..."
    pipx runpip vibing-linux install \
        "torch==${TORCH_VERSION}+${CUDA_TAG}" \
        --extra-index-url "https://download.pytorch.org/whl/${CUDA_TAG}" \
        --force-reinstall --no-deps --quiet
fi

# 4. Reinstall nvidia CUDA runtime libs (torch --no-deps may have removed them)
echo "[4/5] Ensuring CUDA runtime libraries..."
pipx runpip vibing-linux install nvidia-cublas-cu12 nvidia-cudnn-cu12 --quiet

# 5. Verify
echo "[5/5] Verifying installation..."
vibing-linux --help

echo ""
echo "=== Installation complete ==="
echo ""
echo "Next steps:"
echo "  1. Download a GGUF model for text correction, e.g.:"
echo "     huggingface-cli download Qwen/Qwen2.5-3B-Instruct-GGUF qwen2.5-3b-instruct-q4_k_m.gguf \\"
echo "       --local-dir ~/.local/share/vibing-linux/models"
echo ""
echo "  2. Set the model path in ~/.config/vibing-linux/config.yaml:"
echo "     llm:"
echo "       model_path: ~/.local/share/vibing-linux/models/qwen2.5-3b-instruct-q4_k_m.gguf"
echo ""
echo "  3. Ensure your user is in the 'input' group (for global hotkeys):"
echo "     sudo usermod -aG input \$USER   # then log out and back in"
echo ""
echo "  4. Run:  vibing-linux"
#!/usr/bin/env bash
# ─── Vibing Linux — install / update script ────────────────────────────────
#
# Usage:
#   ./install.sh                 # install or update vibing
#   ./install.sh --cuda 12.8     # override CUDA version (default: auto-detect)
#   ./install.sh --cpu            # force CPU-only torch
#
# This script:
#   1. Installs vibing-linux via pipx
#   2. Enables system site-packages (for PyGObject / GTK3)
#   3. Replaces PyPI torch with the correct CUDA build for your driver
#   4. Injects evdev and bitsandbytes
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
echo "✓ Done!  Run:  vibing"
echo "  First-time:  vibing --check"
