import copy
import os
from pathlib import Path

import yaml

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "vibing-linux"
DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "vibing-linux"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULTS = {
    "hotkey": {
        "key": "KEY_RIGHTALT",
        "device": "auto",
    },
    "asr": {
        "model": "large-v3-turbo",
        "device": "cuda",
        "compute_type": "float16",
        "language": "en",
        "initial_prompt": "",
    },
    "llm": {
        "model_path": str(DATA_DIR / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf"),
        "n_gpu_layers": -1,
        "n_ctx": 2048,
        "temperature": 0.3,
    },
    "audio": {
        "sample_rate": 16000,
        "channels": 1,
    },
    "auto_paste": True,
    "sound_feedback": True,
}


def _deep_merge(base, override):
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config():
    config = copy.deepcopy(DEFAULTS)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            user_config = yaml.safe_load(f) or {}
        config = _deep_merge(config, user_config)
    return config


def save_default_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(DEFAULTS, f, default_flow_style=False, sort_keys=False)
        print(f"Default config written to {CONFIG_FILE}")
    return CONFIG_FILE
