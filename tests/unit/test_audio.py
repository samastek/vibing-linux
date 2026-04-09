"""Tests for vibing.audio."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from vibing.audio import AudioRecorder


class TestAudioRecorder:
    def test_init_defaults(self):
        rec = AudioRecorder()
        assert rec.sample_rate == 16000
        assert rec.channels == 1
        assert not rec.is_recording

    def test_init_custom(self):
        rec = AudioRecorder(sample_rate=44100, channels=2)
        assert rec.sample_rate == 44100
        assert rec.channels == 2

    @patch("vibing.audio.sd.InputStream")
    def test_start_stop_empty(self, mock_stream_cls):
        mock_stream = MagicMock()
        mock_stream_cls.return_value = mock_stream

        rec = AudioRecorder()
        rec.start()
        mock_stream.start.assert_called_once()

        audio = rec.stop()
        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()
        assert isinstance(audio, np.ndarray)
        assert audio.size == 0

    @patch("vibing.audio.sd.InputStream")
    def test_start_stop_with_data(self, mock_stream_cls):
        mock_stream = MagicMock()
        mock_stream_cls.return_value = mock_stream

        rec = AudioRecorder()
        rec.start()

        # Simulate audio callback
        chunk = np.ones((160, 1), dtype="float32")
        rec._callback(chunk, 160, None, None)
        rec._callback(chunk, 160, None, None)

        audio = rec.stop()
        assert audio.shape == (320,)

    def test_stop_without_start(self):
        rec = AudioRecorder()
        audio = rec.stop()
        assert audio.size == 0

    @patch("vibing.audio.sd.InputStream")
    def test_context_manager(self, mock_stream_cls):
        mock_stream = MagicMock()
        mock_stream_cls.return_value = mock_stream

        with AudioRecorder() as rec:
            rec.start()

        mock_stream.stop.assert_called()
        mock_stream.close.assert_called()
