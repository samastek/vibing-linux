"""Abstract base class for ASR providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class ASRProvider(ABC):
    """Interface for automatic speech recognition backends.

    All ASR providers must implement ``load_model`` and ``transcribe``.
    """

    @abstractmethod
    def load_model(self) -> None:
        """Load the ASR model into memory.

        Called once during application startup. Heavy imports and model
        loading should happen here, not in ``__init__``.
        """

    @abstractmethod
    def transcribe(
        self,
        audio: np.ndarray,
        language: str | None = None,
        initial_prompt: str | None = None,
    ) -> str:
        """Transcribe audio samples to text.

        Args:
            audio: A 1-D float32 numpy array of audio samples.
            language: Optional BCP-47 language hint (e.g. ``"en"``).
            initial_prompt: Optional prompt to guide transcription.

        Returns:
            The transcribed text, or an empty string if no speech was detected.
        """

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """Whether the model has been loaded and is ready for transcription."""
