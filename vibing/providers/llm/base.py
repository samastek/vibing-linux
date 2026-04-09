"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Interface for LLM text-correction backends.

    All LLM providers must implement ``load_model`` and ``correct``.
    """

    DEFAULT_SYSTEM_PROMPT: str = (
        "You are a text correction assistant for transcribed speech. "
        "Your tasks:\n"
        "1. Resolve speaker self-corrections: when the speaker corrects "
        "themselves mid-speech (e.g. 'the meeting is at 3, no sorry, 4 PM' "
        "→ 'The meeting is at 4 PM'), keep only the final intended version.\n"
        "2. Remove false starts and restarts (e.g. 'I went to the... the store' "
        "→ 'I went to the store').\n"
        "3. Remove filler words and hesitations (uh, um, like, you know, so, "
        "I mean) when they add no meaning.\n"
        "4. Remove stuttered or repeated words.\n"
        "5. Fix grammar, punctuation, and capitalization.\n"
        "Preserve the speaker's meaning, tone, and intent. Do not add new "
        "content. Output only the corrected text, nothing else."
    )

    @abstractmethod
    def load_model(self) -> None:
        """Load the LLM model or establish an API connection.

        Called once during application startup. Heavy imports and model
        loading should happen here, not in ``__init__``.
        """

    @abstractmethod
    def correct(self, text: str, temperature: float = 0.3) -> str:
        """Correct transcribed text using the LLM.

        Args:
            text: Raw transcribed text to correct.
            temperature: Sampling temperature (lower = more deterministic).

        Returns:
            The corrected text, or the original text if correction fails.
        """

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """Whether the model/API is ready for inference."""
