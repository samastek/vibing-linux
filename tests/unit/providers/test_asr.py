"""Tests for ASR provider implementations."""

from __future__ import annotations

import numpy as np
import pytest

from vibing.providers.asr.base import ASRProvider
from vibing.providers.asr.faster_whisper import FasterWhisperProvider


class TestASRProviderContract:
    """Verify the ABC cannot be instantiated directly."""

    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            ASRProvider()


class TestFasterWhisperProvider:
    def test_init(self):
        provider = FasterWhisperProvider()
        assert not provider.is_loaded

    def test_transcribe_without_load_raises(self):
        provider = FasterWhisperProvider()
        with pytest.raises(RuntimeError, match="not loaded"):
            provider.transcribe(np.array([0.1, 0.2], dtype="float32"))

    def test_transcribe_empty_audio(self):
        provider = FasterWhisperProvider()
        # Empty audio should return "" even without loading
        provider._model = True  # bypass is_loaded check
        result = provider.transcribe(np.array([], dtype="float32"))
        assert result == ""


class TestOpenAIWhisperProvider:
    def test_load_model_no_key_raises(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from vibing.providers.asr.openai_whisper import OpenAIWhisperProvider

        provider = OpenAIWhisperProvider(api_key="")
        with pytest.raises(ValueError, match="API key required"):
            provider.load_model()
