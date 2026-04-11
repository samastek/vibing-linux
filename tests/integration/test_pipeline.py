"""Integration test for the full processing pipeline with mock providers."""

from __future__ import annotations

import copy
from unittest.mock import MagicMock, patch

import numpy as np

from vibing.config import DEFAULTS


class TestPipeline:
    """Test the record → transcribe → correct → clipboard pipeline."""

    def test_full_pipeline(self, mock_asr, mock_llm):
        config = copy.deepcopy(DEFAULTS)

        with (
            patch("vibing.app.SystemTray") as MockTray,
            patch("vibing.app.HotkeyListener"),
            patch("vibing.app.copy_to_clipboard") as mock_copy,
            patch("vibing.app.paste_from_clipboard", return_value=True),
        ):
            MockTray.return_value = MagicMock()

            from vibing.app import VibingApp

            app = VibingApp(config, asr=mock_asr, llm=mock_llm)

            # Simulate 1 second of audio
            audio = np.random.randn(16000).astype("float32")
            app._process(audio)

            # Verify clipboard was called with the corrected text
            mock_copy.assert_called_once_with("corrected text", timeout=5)

    def test_pipeline_without_llm(self, mock_asr):
        config = copy.deepcopy(DEFAULTS)

        with (
            patch("vibing.app.SystemTray") as MockTray,
            patch("vibing.app.HotkeyListener"),
            patch("vibing.app.copy_to_clipboard") as mock_copy,
            patch("vibing.app.paste_from_clipboard", return_value=True),
        ):
            MockTray.return_value = MagicMock()

            from vibing.app import VibingApp

            app = VibingApp(config, asr=mock_asr, llm=None)

            audio = np.random.randn(16000).astype("float32")
            app._process(audio)

            # Without LLM, raw transcription goes to clipboard
            mock_copy.assert_called_once_with("hello world", timeout=5)

    def test_pipeline_empty_transcription(self, mock_asr, mock_llm):
        config = copy.deepcopy(DEFAULTS)
        mock_asr._transcribe_result = ""

        with (
            patch("vibing.app.SystemTray") as MockTray,
            patch("vibing.app.HotkeyListener"),
            patch("vibing.app.copy_to_clipboard") as mock_copy,
        ):
            MockTray.return_value = MagicMock()

            from vibing.app import VibingApp

            app = VibingApp(config, asr=mock_asr, llm=mock_llm)

            audio = np.random.randn(16000).astype("float32")
            app._process(audio)

            # Empty transcription = nothing copied
            mock_copy.assert_not_called()
