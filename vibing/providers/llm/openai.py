"""OpenAI-compatible LLM provider (hosted inference).

Works with the OpenAI API and any OpenAI-compatible endpoint
(Ollama, vLLM, LiteLLM, Together AI, etc.) by setting ``api_base``.
"""

from __future__ import annotations

import logging
import os

import httpx

from vibing.providers.llm.base import LLMProvider

logger = logging.getLogger("vibing.llm.openai")


class OpenAIProvider(LLMProvider):
    """LLM backend using the OpenAI chat completions API.

    Set ``api_base`` to use OpenAI-compatible endpoints like Ollama
    (``http://localhost:11434/v1``) or vLLM.
    """

    def __init__(
        self,
        api_key: str = "",
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        system_prompt: str = LLMProvider.DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._api_base = api_base.rstrip("/")
        self._model = model
        self._system_prompt = system_prompt
        self._loaded = False

    def load_model(self) -> None:
        if not self._api_key:
            raise ValueError(
                "OpenAI API key required. "
                "Set llm.api_key in config or OPENAI_API_KEY env var."
            )

        self._loaded = True
        logger.info(
            "OpenAI provider ready (model: %s, base: %s).",
            self._model, self._api_base,
        )

    def correct(self, text: str, temperature: float = 0.3) -> str:
        if not text.strip():
            return text
        if not self.is_loaded:
            raise RuntimeError("Provider not initialized. Call load_model() first.")

        response = httpx.post(
            f"{self._api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": self.USER_MESSAGE_PREFIX + text},
                ],
                "temperature": temperature,
                "max_tokens": max(len(text.split()) * 3, 256),
            },
            timeout=30.0,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"OpenAI API error: {exc.response.status_code} {exc.response.text}"
            ) from None
        corrected = (
            response.json()["choices"][0]["message"]["content"].strip()
        )
        return corrected if corrected else text

    @property
    def is_loaded(self) -> bool:
        return self._loaded
