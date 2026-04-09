"""Faster Whisper ASR provider (local inference)."""

from __future__ import annotations

import logging

import numpy as np
from faster_whisper import WhisperModel

from vibing.providers.asr.base import ASRProvider

logger = logging.getLogger("vibing.asr.faster_whisper")


class FasterWhisperProvider(ASRProvider):
    """ASR backend using the ``faster-whisper`` library.

    The heavy ``faster_whisper`` import and model loading are deferred to
    :meth:`load_model` so the application can start quickly.
    """

    def __init__(
        self,
        model: str = "large-v3-turbo",
        device: str = "cuda",
        compute_type: str = "float16",
        beam_size: int = 5,
    ) -> None:
        self._model_name = model
        self._device = device
        self._compute_type = compute_type
        self._beam_size = beam_size
        self._model = None

    def load_model(self) -> None:
        logger.info(
            "Loading ASR model: %s on %s (%s)",
            self._model_name, self._device, self._compute_type,
        )
        self._model = WhisperModel(
            self._model_name,
            device=self._device,
            compute_type=self._compute_type,
        )
        logger.info("ASR model loaded.")

    def transcribe(
        self,
        audio: np.ndarray,
        language: str | None = None,
        initial_prompt: str | None = None,
    ) -> str:
        if not self.is_loaded:
            raise RuntimeError("ASR model not loaded. Call load_model() first.")

        if isinstance(audio, np.ndarray) and audio.size == 0:
            return ""

        segments, _info = self._model.transcribe(
            audio,
            language=language,
            initial_prompt=initial_prompt or None,
            beam_size=self._beam_size,
            vad_filter=True,
        )
        text = " ".join(seg.text for seg in segments).strip()
        return text

    @property
    def is_loaded(self) -> bool:
        return self._model is not None
