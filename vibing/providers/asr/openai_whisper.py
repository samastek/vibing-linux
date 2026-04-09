"""OpenAI Whisper API ASR provider (hosted inference)."""

from __future__ import annotations

import io
import logging
import os
import wave

import numpy as np

from vibing.providers.asr.base import ASRProvider

logger = logging.getLogger("vibing.asr.openai_whisper")


class OpenAIWhisperProvider(ASRProvider):
    """ASR backend using the OpenAI Whisper API.

    Sends audio to the ``/audio/transcriptions`` endpoint. Requires an
    API key set via config or the ``OPENAI_API_KEY`` environment variable.
    """

    def __init__(
        self,
        api_key: str = "",
        api_base: str = "https://api.openai.com/v1",
        model: str = "whisper-1",
    ) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._api_base = api_base.rstrip("/")
        self._model = model
        self._loaded = False

    def load_model(self) -> None:
        if not self._api_key:
            raise ValueError(
                "OpenAI API key required for Whisper API. "
                "Set asr.api_key in config or OPENAI_API_KEY env var."
            )
        import httpx  # noqa: F401 — verify dependency is available

        self._loaded = True
        logger.info("OpenAI Whisper API provider ready (model: %s).", self._model)

    def transcribe(
        self,
        audio: np.ndarray,
        language: str | None = None,
        initial_prompt: str | None = None,
    ) -> str:
        if not self.is_loaded:
            raise RuntimeError("Provider not initialized. Call load_model() first.")

        if isinstance(audio, np.ndarray) and audio.size == 0:
            return ""

        import httpx

        wav_buffer = self._audio_to_wav(audio)

        data: dict = {"model": self._model}
        if language:
            data["language"] = language
        if initial_prompt:
            data["prompt"] = initial_prompt

        response = httpx.post(
            f"{self._api_base}/audio/transcriptions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            files={"file": ("audio.wav", wav_buffer, "audio/wav")},
            data=data,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json().get("text", "").strip()

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @staticmethod
    def _audio_to_wav(audio: np.ndarray, sample_rate: int = 16000) -> bytes:
        """Convert a float32 numpy array to WAV bytes."""
        pcm = (audio * 32767).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm.tobytes())
        return buf.getvalue()
