"""Tests for vibing.app.VibingApp."""

from __future__ import annotations

import copy
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from vibing.app import VibingApp
from vibing.config import DEFAULTS


class TestVibingApp:
    @pytest.fixture
    def app(self, mock_asr, mock_llm, mock_overlay):
        config = copy.deepcopy(DEFAULTS)
        mock_factory = MagicMock()
        app = VibingApp(config, factory=mock_factory, asr=mock_asr, llm=mock_llm, overlay=mock_overlay)
        return app

    def test_init(self, app):
        assert app.asr is not None
        assert app.llm is not None
        assert not app._recording

    @patch("vibing.app.AudioRecorder")
    def test_on_press_starts_recording(self, mock_rec_cls, app):
        app._on_press()
        assert app._recording is True

    @patch("vibing.app.AudioRecorder")
    def test_on_press_ignores_double_press(self, mock_rec_cls, app):
        app._on_press()
        app._on_press()  # should be no-op

    def test_on_release_without_press_is_noop(self, app):
        app._on_release()
        # should not raise

    def test_shutdown(self, app):
        app.shutdown()
        app.hotkey.stop.assert_called_once()


class TestPipeline:
    """Tests for the _process() clipboard/type pipeline."""

    @pytest.fixture
    def audio(self):
        return np.zeros(16000, dtype="float32")

    @pytest.fixture
    def app(self, mock_asr, mock_overlay):
        config = copy.deepcopy(DEFAULTS)
        config["auto_paste"] = True
        config["clipboard"]["direct_type"] = True
        mock_factory = MagicMock()
        return VibingApp(config, factory=mock_factory, asr=mock_asr, llm=None, overlay=mock_overlay)

    def test_direct_type_success_skips_clipboard(self, app, audio):
        """When type_text succeeds, copy() must not be called."""
        app.factory.clipboard.type_text.return_value = True

        app._process(audio)

        app.factory.clipboard.type_text.assert_called_once()
        app.factory.clipboard.copy.assert_not_called()
        app.factory.clipboard.paste.assert_not_called()

    def test_direct_type_failure_falls_back_to_copy_paste(self, app, audio):
        """When type_text fails, fall back to copy() + paste()."""
        app.factory.clipboard.type_text.return_value = False
        app.factory.clipboard.paste.return_value = True

        app._process(audio)

        app.factory.clipboard.type_text.assert_called_once()
        app.factory.clipboard.copy.assert_called_once()
        app.factory.clipboard.paste.assert_called_once()

    def test_direct_type_disabled_uses_copy_paste(self, mock_asr, mock_overlay, audio):
        """When direct_type is False, type_text is never attempted."""
        config = copy.deepcopy(DEFAULTS)
        config["auto_paste"] = True
        config["clipboard"]["direct_type"] = False
        mock_factory = MagicMock()
        mock_factory.clipboard.paste.return_value = True
        app = VibingApp(config, factory=mock_factory, asr=mock_asr, llm=None, overlay=mock_overlay)

        app._process(audio)

        app.factory.clipboard.type_text.assert_not_called()
        app.factory.clipboard.copy.assert_called_once()
        app.factory.clipboard.paste.assert_called_once()

    def test_auto_paste_disabled_uses_clipboard_only(self, mock_asr, mock_overlay, audio):
        """When auto_paste is False, only copy() is called — no type or paste."""
        config = copy.deepcopy(DEFAULTS)
        config["auto_paste"] = False
        mock_factory = MagicMock()
        app = VibingApp(config, factory=mock_factory, asr=mock_asr, llm=None, overlay=mock_overlay)

        app._process(audio)

        app.factory.clipboard.type_text.assert_not_called()
        app.factory.clipboard.copy.assert_called_once()
        app.factory.clipboard.paste.assert_not_called()

