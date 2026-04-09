"""Configuration management for Vibing Linux.

Loads user settings from ``~/.config/vibing-linux/config.yaml``, merges
them with built-in defaults, and exposes validated configuration dicts.
"""

from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any

import yaml
from xdg.BaseDirectory import xdg_config_home, xdg_data_home

logger = logging.getLogger("vibing.config")

# ── XDG paths ────────────────────────────────────────────────────────────

CONFIG_DIR = Path(xdg_config_home) / "vibing-linux"
DATA_DIR = Path(xdg_data_home) / "vibing-linux"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
LOG_FILE = DATA_DIR / "vibing.log"

# ── Defaults ─────────────────────────────────────────────────────────────

DEFAULTS: dict[str, Any] = {
    "hotkey": {
        "key": "KEY_RIGHTALT",
        "device": "auto",
    },
    "asr": {
        "provider": "faster_whisper",
        "model": "large-v3-turbo",
        "device": "cuda",
        "compute_type": "float16",
        "language": "en",
        "initial_prompt": "",
        "beam_size": 5,
        # Hosted ASR settings (used when provider is "openai_whisper")
        "api_key": "",
        "api_base": "https://api.openai.com/v1",
    },
    "llm": {
        "provider": "llama_cpp",
        "model_path": str(DATA_DIR / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf"),
        "n_gpu_layers": -1,
        "n_ctx": 2048,
        "temperature": 0.3,
        "system_prompt": "",  # empty = use built-in default
        # Hosted LLM settings (used when provider is "openai" or "anthropic")
        "model": "",
        "api_key": "",
        "api_base": "",
    },
    "audio": {
        "sample_rate": 16000,
        "channels": 1,
        "min_duration": 0.3,
    },
    "clipboard": {
        "paste_delay": 0.1,
        "copy_timeout": 5,
        "paste_timeout": 3,
    },
    "tray": {
        "icon_size": 64,
        "colors": {
            "idle": [120, 120, 120],
            "recording": [220, 40, 40],
            "processing": [240, 160, 30],
            "done": [40, 180, 40],
            "error": [180, 40, 40],
        },
    },
    "auto_paste": True,
    "sound_feedback": True,
    "logging": {
        "level": "INFO",
    },
}

# ── Valid provider names (for validation) ────────────────────────────────

_VALID_ASR_PROVIDERS = {"faster_whisper", "openai_whisper"}
_VALID_LLM_PROVIDERS = {"llama_cpp", "openai", "anthropic", "none"}


# ── Helpers ──────────────────────────────────────────────────────────────

def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base*, returning a new dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _validate(config: dict) -> None:
    """Validate a merged config dict. Raises ``ValueError`` on problems."""
    asr_provider = config.get("asr", {}).get("provider", "faster_whisper")
    if asr_provider not in _VALID_ASR_PROVIDERS:
        raise ValueError(
            f"Invalid asr.provider: {asr_provider!r}. "
            f"Must be one of {_VALID_ASR_PROVIDERS}"
        )

    llm_provider = config.get("llm", {}).get("provider", "llama_cpp")
    if llm_provider not in _VALID_LLM_PROVIDERS:
        raise ValueError(
            f"Invalid llm.provider: {llm_provider!r}. "
            f"Must be one of {_VALID_LLM_PROVIDERS}"
        )

    sample_rate = config.get("audio", {}).get("sample_rate", 16000)
    if not isinstance(sample_rate, int) or sample_rate <= 0:
        raise ValueError(f"audio.sample_rate must be a positive integer, got {sample_rate!r}")


# ── Public API ───────────────────────────────────────────────────────────

def load_config() -> dict[str, Any]:
    """Load configuration from disk, merged with defaults.

    Returns a deep copy so callers cannot mutate the defaults.
    """
    config = copy.deepcopy(DEFAULTS)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            user_config = yaml.safe_load(f) or {}
        config = _deep_merge(config, user_config)

    _validate(config)
    return config


def save_default_config() -> Path:
    """Write the default config file if it does not exist.

    Returns the path to the config file.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(DEFAULTS, f, default_flow_style=False, sort_keys=False)
        logger.info("Default config written to %s", CONFIG_FILE)
    return CONFIG_FILE


def save_config(config: dict[str, Any]) -> Path:
    """Write the given config dict to the config file.

    Creates the config directory if it does not exist.
    Returns the path to the config file.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _validate(config)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    logger.info("Config saved to %s", CONFIG_FILE)
    return CONFIG_FILE
