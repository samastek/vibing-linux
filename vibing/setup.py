"""First-run setup for Vibing Linux.

Handles model downloads, permission checks, and config creation
so users have a zero-configuration experience on first launch.
"""

import grp
import os
import sys
from pathlib import Path

from vibing.config import CONFIG_FILE, DATA_DIR, DEFAULTS, save_default_config


MODEL_DIR = DATA_DIR / "models"
DEFAULT_GGUF_REPO = "Qwen/Qwen2.5-3B-Instruct-GGUF"
DEFAULT_GGUF_FILE = "qwen2.5-3b-instruct-q4_k_m.gguf"


def _check_input_group():
    """Check if the current user is in the 'input' group for hotkey access."""
    try:
        input_gid = grp.getgrnam("input").gr_gid
        if input_gid not in os.getgroups():
            username = os.environ.get("USER", os.getlogin())
            print("")
            print("╔══════════════════════════════════════════════════════════╗")
            print("║  WARNING: Your user is not in the 'input' group.       ║")
            print("║  Global hotkeys will NOT work without this.            ║")
            print("╚══════════════════════════════════════════════════════════╝")
            print("")
            print(f"  Fix with:  sudo usermod -aG input {username}")
            print("  Then log out and back in for it to take effect.")
            print("")
            return False
    except KeyError:
        # 'input' group doesn't exist on this system
        pass
    return True


def _download_gguf_model():
    """Download the default GGUF model for LLM correction."""
    model_path = MODEL_DIR / DEFAULT_GGUF_FILE

    if model_path.exists():
        return str(model_path)

    print("")
    print(f"→ Downloading LLM model: {DEFAULT_GGUF_REPO}/{DEFAULT_GGUF_FILE}")
    print("  This is a one-time download (~2 GB). Please wait...")
    print("")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from huggingface_hub import hf_hub_download

        downloaded = hf_hub_download(
            repo_id=DEFAULT_GGUF_REPO,
            filename=DEFAULT_GGUF_FILE,
            local_dir=str(MODEL_DIR),
        )
        print(f"  ✓ Model downloaded to: {downloaded}")
        return str(model_path)

    except ImportError:
        print("  Warning: huggingface_hub not available. Skipping model download.")
        print(f"  You can install it manually:")
        print(f"    pip install huggingface_hub")
        print(f"  Then download the model:")
        print(f"    huggingface-cli download {DEFAULT_GGUF_REPO} {DEFAULT_GGUF_FILE} \\")
        print(f"      --local-dir {MODEL_DIR}")
        return None

    except Exception as e:
        print(f"  Warning: Model download failed: {e}")
        print(f"  You can download it manually later:")
        print(f"    huggingface-cli download {DEFAULT_GGUF_REPO} {DEFAULT_GGUF_FILE} \\")
        print(f"      --local-dir {MODEL_DIR}")
        return None


def run_first_time_setup():
    """Run first-time setup if needed. Returns True if setup was performed."""
    is_first_run = not CONFIG_FILE.exists()

    if not is_first_run:
        # Still check input group on every run
        _check_input_group()
        return False

    print("")
    print("═══ Vibing Linux — First-time setup ═══")
    print("")

    # 1. Create default config
    save_default_config()

    # 2. Check input group
    _check_input_group()

    # 3. Download GGUF model
    model_path = _download_gguf_model()

    # 4. Update config with downloaded model path if successful
    if model_path:
        import yaml

        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f) or {}

        if "llm" not in config:
            config["llm"] = {}
        config["llm"]["model_path"] = model_path

        with open(CONFIG_FILE, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print("")
    print("═══ Setup complete! ═══")
    print(f"  Config: {CONFIG_FILE}")
    print(f"  Models: {MODEL_DIR}")
    print("")

    return True
