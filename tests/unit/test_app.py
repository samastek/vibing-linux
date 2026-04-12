"""Tests for vibing.app.VibingApp."""

from __future__ import annotations

import copy
from unittest.mock import MagicMock, patch

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
