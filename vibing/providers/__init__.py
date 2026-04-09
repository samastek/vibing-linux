"""Provider factories for ASR and LLM backends."""

from __future__ import annotations

from typing import Any

from vibing.providers.asr.base import ASRProvider
from vibing.providers.llm.base import LLMProvider


def create_asr_provider(config: dict[str, Any]) -> ASRProvider:
    """Create an ASR provider based on config."""
    asr_cfg = config["asr"]
    provider_name = asr_cfg.get("provider", "faster_whisper")

    if provider_name == "faster_whisper":
        from vibing.providers.asr.faster_whisper import FasterWhisperProvider

        return FasterWhisperProvider(
            model=asr_cfg["model"],
            device=asr_cfg["device"],
            compute_type=asr_cfg["compute_type"],
            beam_size=asr_cfg.get("beam_size", 5),
        )
    elif provider_name == "openai_whisper":
        from vibing.providers.asr.openai_whisper import OpenAIWhisperProvider

        return OpenAIWhisperProvider(
            api_key=asr_cfg.get("api_key") or "",
            api_base=asr_cfg.get("api_base", "https://api.openai.com/v1"),
            model=asr_cfg.get("model", "whisper-1"),
        )
    else:
        raise ValueError(
            f"Unknown ASR provider: {provider_name!r}. "
            f"Supported: 'faster_whisper', 'openai_whisper'"
        )


def create_llm_provider(config: dict[str, Any]) -> LLMProvider | None:
    """Create an LLM provider based on config, or None if disabled."""
    llm_cfg = config["llm"]
    provider_name = llm_cfg.get("provider", "llama_cpp")

    if provider_name == "none":
        return None

    system_prompt = llm_cfg.get("system_prompt") or LLMProvider.DEFAULT_SYSTEM_PROMPT

    if provider_name == "llama_cpp":
        from vibing.providers.llm.llama_cpp import LlamaCppProvider

        return LlamaCppProvider(
            model_path=llm_cfg["model_path"],
            n_gpu_layers=llm_cfg.get("n_gpu_layers", -1),
            n_ctx=llm_cfg.get("n_ctx", 0),
            system_prompt=system_prompt,
        )
    elif provider_name == "openai":
        from vibing.providers.llm.openai import OpenAIProvider

        return OpenAIProvider(
            api_key=llm_cfg.get("api_key") or "",
            api_base=llm_cfg.get("api_base", "https://api.openai.com/v1"),
            model=llm_cfg.get("model", "gpt-4o-mini"),
            system_prompt=system_prompt,
        )
    elif provider_name == "anthropic":
        from vibing.providers.llm.anthropic import AnthropicProvider

        return AnthropicProvider(
            api_key=llm_cfg.get("api_key") or "",
            api_base=llm_cfg.get("api_base", "https://api.anthropic.com"),
            model=llm_cfg.get("model", "claude-sonnet-4-20250514"),
            system_prompt=system_prompt,
        )
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider_name!r}. "
            f"Supported: 'llama_cpp', 'openai', 'anthropic', 'none'"
        )
