"""Integration test for the full processing pipeline with mock providers."""

from __future__ import annotations

import copy
from unittest.mock import MagicMock

import numpy as np

from vibing.app import VibingApp
from vibing.config import DEFAULTS


class TestPipeline:
    """Test the record → transcribe → correct → clipboard pipeline."""

    def _make_app(self, config, asr, llm=None):
        mock_factory = MagicMock()
        # Default: direct type succeeds so clipboard.copy is not called
        mock_factory.clipboard.type_text.return_value = True
        return VibingApp(config, factory=mock_factory, asr=asr, llm=llm)

    def test_full_pipeline_direct_type(self, mock_asr, mock_llm):
        """With auto_paste + direct_type, text is typed directly."""
        config = copy.deepcopy(DEFAULTS)
        config["auto_paste"] = True
        config["clipboard"]["direct_type"] = True
        app = self._make_app(config, mock_asr, mock_llm)

        audio = np.random.randn(16000).astype("float32")
        app._process(audio)

        app.factory.clipboard.type_text.assert_called_once_with(
            "corrected text", timeout=5
        )
        app.factory.clipboard.copy.assert_not_called()

    def test_full_pipeline_fallback_to_copy_paste(self, mock_asr, mock_llm):
        """When type_text fails, fall back to clipboard copy + paste."""
        config = copy.deepcopy(DEFAULTS)
        config["auto_paste"] = True
        config["clipboard"]["direct_type"] = True
        mock_factory = MagicMock()
        mock_factory.clipboard.type_text.return_value = False
        mock_factory.clipboard.paste.return_value = True
        app = VibingApp(config, factory=mock_factory, asr=mock_asr, llm=mock_llm)

        audio = np.random.randn(16000).astype("float32")
        app._process(audio)

        app.factory.clipboard.copy.assert_called_once_with("corrected text", timeout=5)
        app.factory.clipboard.paste.assert_called_once()

    def test_pipeline_without_llm(self, mock_asr):
        """Without LLM, raw transcription is used."""
        config = copy.deepcopy(DEFAULTS)
        config["auto_paste"] = True
        config["clipboard"]["direct_type"] = True
        app = self._make_app(config, mock_asr)

        audio = np.random.randn(16000).astype("float32")
        app._process(audio)

        app.factory.clipboard.type_text.assert_called_once_with(
            "hello world", timeout=5
        )

    def test_pipeline_clipboard_only(self, mock_asr, mock_llm):
        """When auto_paste is False, only copy() is called."""
        config = copy.deepcopy(DEFAULTS)
        config["auto_paste"] = False
        app = self._make_app(config, mock_asr, mock_llm)

        audio = np.random.randn(16000).astype("float32")
        app._process(audio)

        app.factory.clipboard.copy.assert_called_once_with("corrected text", timeout=5)
        app.factory.clipboard.type_text.assert_not_called()
        app.factory.clipboard.paste.assert_not_called()

    def test_pipeline_empty_transcription(self, mock_asr, mock_llm):
        """Empty transcription results in no clipboard or type activity."""
        config = copy.deepcopy(DEFAULTS)
        mock_asr._transcribe_result = ""
        app = self._make_app(config, mock_asr, mock_llm)

        audio = np.random.randn(16000).astype("float32")
        app._process(audio)

        app.factory.clipboard.copy.assert_not_called()
        app.factory.clipboard.type_text.assert_not_called()
