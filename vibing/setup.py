"""First-run setup for Vibing Linux.

Handles model downloads, permission checks, and config creation
so users have a zero-configuration experience on first launch.
"""

from __future__ import annotations

import grp
import logging
import os
import sys
from pathlib import Path

import yaml

from vibing.config import CONFIG_FILE, DATA_DIR, save_default_config

logger = logging.getLogger("vibing.setup")

MODEL_DIR = DATA_DIR / "models"
DEFAULT_GGUF_REPO = "unsloth/gemma-4-E2B-it-GGUF"
DEFAULT_GGUF_FILE = "gemma-4-E2B-it-Q4_K_M.gguf"


def _check_input_group() -> bool:
    """Check if the current user is in the 'input' group for hotkey access."""
    try:
        input_gid = grp.getgrnam("input").gr_gid
        if input_gid not in os.getgroups():
            username = os.environ.get("USER", os.getlogin())
            logger.warning("")
            logger.warning("╔══════════════════════════════════════════════════════════╗")
            logger.warning("║  WARNING: Your user is not in the 'input' group.       ║")
            logger.warning("║  Global hotkeys will NOT work without this.            ║")
            logger.warning("╚══════════════════════════════════════════════════════════╝")
            logger.warning("")
            logger.warning("  Fix with:  sudo usermod -aG input %s", username)
            logger.warning("  Then log out and back in for it to take effect.")
            logger.warning("")
            return False
    except KeyError:
        pass
    return True


def _download_gguf_model() -> str | None:
    """Download the default GGUF model for LLM correction."""
    model_path = MODEL_DIR / DEFAULT_GGUF_FILE

    if model_path.exists():
        return str(model_path)

    logger.info("")
    logger.info("→ Downloading LLM model: %s/%s", DEFAULT_GGUF_REPO, DEFAULT_GGUF_FILE)
    logger.info("  This is a one-time download (~2 GB). Please wait...")
    logger.info("")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from huggingface_hub import hf_hub_download

        downloaded = hf_hub_download(
            repo_id=DEFAULT_GGUF_REPO,
            filename=DEFAULT_GGUF_FILE,
            local_dir=str(MODEL_DIR),
        )
        logger.info("  ✓ Model downloaded to: %s", downloaded)
        return str(model_path)

    except ImportError:
        logger.warning("  huggingface_hub not available. Skipping model download.")
        logger.warning("  Install it with:  pip install huggingface_hub")
        logger.warning(
            "  Then download:  huggingface-cli download %s %s --local-dir %s",
            DEFAULT_GGUF_REPO,
            DEFAULT_GGUF_FILE,
            MODEL_DIR,
        )
        return None

    except Exception as e:
        logger.warning("  Model download failed: %s", e)
        logger.warning(
            "  Download manually:  huggingface-cli download %s %s --local-dir %s",
            DEFAULT_GGUF_REPO,
            DEFAULT_GGUF_FILE,
            MODEL_DIR,
        )
        return None


def _needs_local_model(config_path: Path) -> bool:
    """Check if the current config uses a local LLM provider."""
    if not config_path.exists():
        return True  # first run defaults to llama_cpp

    with open(config_path) as f:
        cfg = yaml.safe_load(f) or {}
    provider = cfg.get("llm", {}).get("provider", "llama_cpp")
    return provider == "llama_cpp"


def run_first_time_setup() -> bool:
    """Run first-time setup if needed. Returns True if setup was performed."""
    is_first_run = not CONFIG_FILE.exists()

    if not is_first_run:
        if sys.platform != "darwin":
            _check_input_group()
        return False

    logger.info("")
    logger.info("═══ Vibing Linux — First-time setup ═══")
    logger.info("")

    save_default_config()
    if sys.platform != "darwin":
        _check_input_group()

    if _needs_local_model(CONFIG_FILE):
        logger.info("")
        logger.info("→ LLM model will be downloaded on first use.")
        logger.info("  Or set 'llm.model_path' in %s to a local GGUF file.", CONFIG_FILE)
        logger.info("")

    logger.info("")
    logger.info("═══ Setup complete! ═══")
    logger.info("  Config: %s", CONFIG_FILE)
    logger.info("  Models: %s", MODEL_DIR)
    logger.info("")

    return True
