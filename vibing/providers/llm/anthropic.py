"""Anthropic LLM provider (hosted inference)."""

from __future__ import annotations

import logging
import os

import httpx

from vibing.providers.llm.base import LLMProvider

logger = logging.getLogger("vibing.llm.anthropic")


class AnthropicProvider(LLMProvider):
    """LLM backend using the Anthropic Messages API."""

    def __init__(
        self,
        api_key: str = "",
        api_base: str = "https://api.anthropic.com",
        model: str = "claude-sonnet-4-20250514",
        system_prompt: str = LLMProvider.DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._api_base = api_base.rstrip("/")
        self._model = model
        self._system_prompt = system_prompt
        self._loaded = False

    def load_model(self) -> None:
        if not self._api_key:
            raise ValueError(
                "Anthropic API key required. "
                "Set llm.api_key in config or ANTHROPIC_API_KEY env var."
            )

        self._loaded = True
        logger.info("Anthropic provider ready (model: %s).", self._model)

    def correct(self, text: str, temperature: float = 0.3) -> str:
        if not text.strip():
            return text
        if not self.is_loaded:
            raise RuntimeError("Provider not initialized. Call load_model() first.")

        response = httpx.post(
            f"{self._api_base}/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "system": self._system_prompt,
                "messages": [{"role": "user", "content": self.USER_MESSAGE_PREFIX + text}],
                "temperature": temperature,
                "max_tokens": max(len(text.split()) * 3, 256),
            },
            timeout=30.0,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Anthropic API error: {exc.response.status_code} {exc.response.text}"
            ) from None
        content = response.json().get("content", [])
        corrected = content[0]["text"].strip() if content else ""
        return corrected if corrected else text

    @property
    def is_loaded(self) -> bool:
        return self._loaded
