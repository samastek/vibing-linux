"""llama.cpp LLM provider (local inference)."""

from __future__ import annotations

import logging
import os

from llama_cpp import Llama

from vibing.providers.llm.base import LLMProvider

logger = logging.getLogger("vibing.llm.llama_cpp")


class LlamaCppProvider(LLMProvider):
    """LLM backend using ``llama-cpp-python`` for local GGUF models.

    The heavy ``llama_cpp`` import and model loading are deferred to
    :meth:`load_model` so the application can start quickly.
    """

    def __init__(
        self,
        model_path: str,
        n_gpu_layers: int = -1,
        n_ctx: int = 0,
        system_prompt: str = LLMProvider.DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self._model_path = os.path.expanduser(model_path)
        self._n_gpu_layers = n_gpu_layers
        self._n_ctx = n_ctx
        self._system_prompt = system_prompt
        self._llm = None

    def load_model(self) -> None:
        if not os.path.isfile(self._model_path):
            raise FileNotFoundError(
                f"LLM model not found: {self._model_path}\n"
                "Download a GGUF model and set llm.model_path in config."
            )

        logger.info("Loading LLM: %s", self._model_path)
        self._llm = Llama(
            model_path=self._model_path,
            n_gpu_layers=self._n_gpu_layers,
            n_ctx=self._n_ctx,
            verbose=False,
        )
        logger.info("LLM loaded.")

    def correct(self, text: str, temperature: float = 0.3) -> str:
        if not text.strip():
            return text
        if not self.is_loaded:
            raise RuntimeError("LLM not loaded. Call load_model() first.")

        response = self._llm.create_chat_completion(
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": self.USER_MESSAGE_PREFIX + text},
            ],
            temperature=temperature,
            max_tokens=max(len(text.split()) * 3, 256),
        )
        corrected = response["choices"][0]["message"]["content"].strip()
        return corrected if corrected else text

    @property
    def is_loaded(self) -> bool:
        return self._llm is not None
