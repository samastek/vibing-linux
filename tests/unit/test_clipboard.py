"""Tests for vibing.clipboard."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from vibing.clipboard import copy_to_clipboard, paste_from_clipboard


class TestCopyToClipboard:
    @patch("vibing.clipboard.subprocess.run")
    @patch("vibing.clipboard.shutil.which", return_value="/usr/bin/xclip")
    @patch("vibing.clipboard._detect_session_type", return_value="x11")
    def test_copy_xclip(self, mock_session, mock_which, mock_run):
        copy_to_clipboard("hello")
        mock_run.assert_called_once()
        args = mock_run.call_args
        assert args[0][0] == ["xclip", "-selection", "clipboard"]
        assert args[1]["input"] == b"hello"

    @patch("vibing.clipboard.subprocess.run")
    @patch("vibing.clipboard.shutil.which", return_value="/usr/bin/wl-copy")
    @patch("vibing.clipboard._detect_session_type", return_value="wayland")
    def test_copy_wayland(self, mock_session, mock_which, mock_run):
        copy_to_clipboard("hello")
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["wl-copy"]

    @patch("vibing.clipboard.shutil.which", return_value=None)
    @patch("vibing.clipboard._detect_session_type", return_value="x11")
    def test_copy_no_tool_raises(self, mock_session, mock_which):
        with pytest.raises(RuntimeError, match="No clipboard tool found"):
            copy_to_clipboard("hello")


class TestPasteFromClipboard:
    @patch("vibing.clipboard.subprocess.run")
    @patch("vibing.clipboard.shutil.which", return_value="/usr/bin/xdotool")
    @patch("vibing.clipboard._detect_session_type", return_value="x11")
    @patch("vibing.clipboard.time.sleep")
    def test_paste_x11(self, mock_sleep, mock_session, mock_which, mock_run):
        result = paste_from_clipboard(paste_delay=0.0)
        assert result is True
        mock_run.assert_called_once()

    @patch("vibing.clipboard.shutil.which", return_value=None)
    @patch("vibing.clipboard._detect_session_type", return_value="x11")
    @patch("vibing.clipboard.time.sleep")
    def test_paste_no_tool(self, mock_sleep, mock_session, mock_which):
        result = paste_from_clipboard(paste_delay=0.0)
        assert result is False
