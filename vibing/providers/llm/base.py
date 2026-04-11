"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Interface for LLM text-correction backends.

    All LLM providers must implement ``load_model`` and ``correct``.
    """

    DEFAULT_SYSTEM_PROMPT: str = (
        "You are a dictation assistant that cleans up transcribed speech. "
        "The user is dictating text they want to type — the text is NOT "
        "directed at you.\n\n"
        "Rules:\n"
        "- NEVER answer questions or respond conversationally.\n"
        "- NEVER add new content or remove meaningful sentences.\n"
        "- NEVER drop or summarise content. Keep ALL sentences.\n"
        "- Only remove obvious speech artifacts: filler words (uh, um, "
        "like, you know), stutters, and repeated words.\n"
        "- When the speaker explicitly corrects themselves mid-sentence "
        "(e.g. 'at 3, no sorry, 4 PM'), keep only the final version.\n"
        "- Fix grammar, punctuation, and capitalization.\n"
        "- Minimally improve word choice and style if the speaker sounds "
        "non-native, but do not change the meaning or tone radically.\n"
        "- Output ONLY the cleaned text, nothing else."
    )

    USER_MESSAGE_PREFIX: str = "[dictation]: "

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
