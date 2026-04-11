"""Interactive configuration for Vibing Linux.

Walks the user through ASR and LLM provider setup via ``questionary``
prompts, then writes the result to the config file.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import questionary
from huggingface_hub import hf_hub_download

from vibing.config import CONFIG_DIR, load_config, save_config
from vibing.setup import DEFAULT_GGUF_FILE, DEFAULT_GGUF_REPO, MODEL_DIR

logger = logging.getLogger("vibing.configure")

# ── Known local GGUF models ─────────────────────────────────────────────

_GGUF_MODELS = {
    "Gemma 4 E2B Instruct (Q4_K_M, ~3 GB)": {
        "repo": DEFAULT_GGUF_REPO,
        "file": DEFAULT_GGUF_FILE,
    },
}


# ── ASR configuration ───────────────────────────────────────────────────


def _configure_asr(current: dict) -> dict:
    """Ask ASR-related questions and return updated asr config section."""
    asr_cfg = dict(current)

    provider = questionary.select(
        "ASR provider (speech-to-text engine):",
        choices=[
            questionary.Choice("Local — Faster Whisper", value="faster_whisper"),
            questionary.Choice("Remote — OpenAI Whisper API", value="openai_whisper"),
        ],
        default=(
            "faster_whisper" if asr_cfg.get("provider") == "faster_whisper" else "openai_whisper"
        ),
    ).ask()

    if provider is None:
        raise KeyboardInterrupt

    asr_cfg["provider"] = provider

    if provider == "faster_whisper":
        model = questionary.text(
            "Whisper model name:",
            default=asr_cfg.get("model", "large-v3-turbo"),
        ).ask()
        if model is None:
            raise KeyboardInterrupt
        asr_cfg["model"] = model

        device = questionary.select(
            "Compute device:",
            choices=["cuda", "cpu"],
            default=asr_cfg.get("device", "cuda"),
        ).ask()
        if device is None:
            raise KeyboardInterrupt
        asr_cfg["device"] = device

        compute_type = questionary.select(
            "Compute type:",
            choices=["float16", "int8", "float32"],
            default=asr_cfg.get("compute_type", "float16"),
        ).ask()
        if compute_type is None:
            raise KeyboardInterrupt
        asr_cfg["compute_type"] = compute_type

        language = questionary.text(
            "Language code (BCP-47, e.g. en, fr, de):",
            default=asr_cfg.get("language", "en"),
        ).ask()
        if language is None:
            raise KeyboardInterrupt
        asr_cfg["language"] = language

    else:  # openai_whisper
        api_key = questionary.password(
            "OpenAI API key (leave blank to use OPENAI_API_KEY env var):",
            default="",
        ).ask()
        if api_key is None:
            raise KeyboardInterrupt
        asr_cfg["api_key"] = api_key

        api_base = questionary.text(
            "API base URL:",
            default=asr_cfg.get("api_base", "https://api.openai.com/v1"),
        ).ask()
        if api_base is None:
            raise KeyboardInterrupt
        asr_cfg["api_base"] = api_base

    return asr_cfg


# ── LLM configuration ───────────────────────────────────────────────────


def _ensure_model_available(model_path: str, repo: str, filename: str) -> None:
    """Check if a GGUF model exists locally; download if missing."""
    path = Path(model_path)
    if path.exists():
        print(f"  ✓ Model already available: {path}")
        return

    print()
    print(f"  Model not found at: {path}")
    print(f"  → Downloading {repo}/{filename} ...")
    print("    This is a one-time download (~2 GB). Please wait...")
    print()

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    try:
        hf_hub_download(
            repo_id=repo,
            filename=filename,
            local_dir=str(MODEL_DIR),
        )
        print(f"  ✓ Model downloaded to: {path}")
    except Exception as exc:
        print(f"  ✗ Download failed: {exc}")
        print()
        print("  You can download it manually with:")
        print(f"    huggingface-cli download {repo} {filename} --local-dir {MODEL_DIR}")
        print()
        if not _is_hf_cli_available():
            print("  Note: huggingface-cli is not on your PATH.")
            print("  Install it with:  pip install huggingface_hub")
            print()


def _is_hf_cli_available() -> bool:
    """Check if the huggingface-cli command is available on PATH."""
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if (Path(directory) / "huggingface-cli").is_file():
            return True
    return False


def _configure_llm(current: dict) -> dict:
    """Ask LLM-related questions and return updated llm config section."""
    llm_cfg = dict(current)

    current_provider = llm_cfg.get("provider", "llama_cpp")
    provider = questionary.select(
        "LLM provider (text correction engine):",
        choices=[
            questionary.Choice("Local — llama.cpp (GGUF model)", value="llama_cpp"),
            questionary.Choice("Remote — OpenAI API", value="openai"),
            questionary.Choice("Remote — Anthropic API", value="anthropic"),
            questionary.Choice("None — disable LLM correction", value="none"),
        ],
        default=current_provider,
    ).ask()

    if provider is None:
        raise KeyboardInterrupt

    llm_cfg["provider"] = provider

    if provider == "llama_cpp":
        _configure_llm_local(llm_cfg)
    elif provider == "openai":
        _configure_llm_openai(llm_cfg)
    elif provider == "anthropic":
        _configure_llm_anthropic(llm_cfg)
    # "none" requires no further questions

    return llm_cfg


def _configure_llm_local(llm_cfg: dict) -> None:
    """Configure local llama.cpp provider in-place."""
    model_choices = [questionary.Choice(name, value=name) for name in _GGUF_MODELS]
    model_choices.append(questionary.Choice("Custom model path", value="__custom__"))

    model_selection = questionary.select(
        "Local LLM model:",
        choices=model_choices,
    ).ask()

    if model_selection is None:
        raise KeyboardInterrupt

    if model_selection == "__custom__":
        model_path = questionary.path(
            "Path to GGUF model file:",
            default=llm_cfg.get("model_path", ""),
        ).ask()
        if model_path is None:
            raise KeyboardInterrupt
        llm_cfg["model_path"] = str(Path(model_path).expanduser())
    else:
        info = _GGUF_MODELS[model_selection]
        model_path = str(MODEL_DIR / info["file"])
        llm_cfg["model_path"] = model_path
        _ensure_model_available(model_path, info["repo"], info["file"])

    n_gpu_layers = questionary.text(
        "GPU layers (-1 = all layers on GPU, 0 = CPU only):",
        default=str(llm_cfg.get("n_gpu_layers", -1)),
    ).ask()
    if n_gpu_layers is None:
        raise KeyboardInterrupt
    llm_cfg["n_gpu_layers"] = int(n_gpu_layers)

    n_ctx = questionary.text(
        "Context window size:",
        default=str(llm_cfg.get("n_ctx", 0)),
    ).ask()
    if n_ctx is None:
        raise KeyboardInterrupt
    llm_cfg["n_ctx"] = int(n_ctx)


def _configure_llm_openai(llm_cfg: dict) -> None:
    """Configure OpenAI LLM provider in-place."""
    api_key = questionary.password(
        "OpenAI API key (leave blank to use OPENAI_API_KEY env var):",
        default="",
    ).ask()
    if api_key is None:
        raise KeyboardInterrupt
    llm_cfg["api_key"] = api_key

    model = questionary.text(
        "Model name:",
        default=llm_cfg.get("model", "") or "gpt-4o-mini",
    ).ask()
    if model is None:
        raise KeyboardInterrupt
    llm_cfg["model"] = model

    api_base = questionary.text(
        "API base URL:",
        default=llm_cfg.get("api_base", "") or "https://api.openai.com/v1",
    ).ask()
    if api_base is None:
        raise KeyboardInterrupt
    llm_cfg["api_base"] = api_base


def _configure_llm_anthropic(llm_cfg: dict) -> None:
    """Configure Anthropic LLM provider in-place."""
    api_key = questionary.password(
        "Anthropic API key (leave blank to use ANTHROPIC_API_KEY env var):",
        default="",
    ).ask()
    if api_key is None:
        raise KeyboardInterrupt
    llm_cfg["api_key"] = api_key

    model = questionary.text(
        "Model name:",
        default=llm_cfg.get("model", "") or "claude-sonnet-4-20250514",
    ).ask()
    if model is None:
        raise KeyboardInterrupt
    llm_cfg["model"] = model

    api_base = questionary.text(
        "API base URL:",
        default=llm_cfg.get("api_base", "") or "https://api.anthropic.com",
    ).ask()
    if api_base is None:
        raise KeyboardInterrupt
    llm_cfg["api_base"] = api_base


# ── Common settings ─────────────────────────────────────────────────────


def _configure_common(config: dict) -> None:
    """Ask common settings and update config in-place."""
    auto_paste = questionary.confirm(
        "Auto-paste transcribed text to the focused window?",
        default=config.get("auto_paste", True),
    ).ask()
    if auto_paste is None:
        raise KeyboardInterrupt
    config["auto_paste"] = auto_paste

    current_level = config.get("logging", {}).get("level", "INFO")
    log_level = questionary.select(
        "Log level:",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=current_level,
    ).ask()
    if log_level is None:
        raise KeyboardInterrupt
    config.setdefault("logging", {})["level"] = log_level


# ── Main entry point ────────────────────────────────────────────────────


def run_configure() -> None:
    """Run the interactive configuration wizard."""
    print()
    print("═══ Vibing Linux — Configuration ═══")
    print()

    # Ensure config dir exists and load current settings
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = load_config()

    try:
        # ASR configuration
        print("── Speech Recognition (ASR) ──")
        print()
        config["asr"] = _configure_asr(config["asr"])
        print()

        # LLM configuration
        print("── Text Correction (LLM) ──")
        print()
        config["llm"] = _configure_llm(config["llm"])
        print()

        # Common settings
        print("── General Settings ──")
        print()
        _configure_common(config)
        print()

    except KeyboardInterrupt:
        print()
        print("Configuration cancelled.")
        return

    # Save
    path = save_config(config)
    print()
    print(f"✓ Configuration saved to: {path}")
    print()
