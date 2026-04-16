"""Tests for platform clipboard implementations."""

from __future__ import annotations

from subprocess import CalledProcessError, TimeoutExpired
from unittest.mock import patch

from vibing.platform.linux.clipboard import LinuxClipboard
from vibing.platform.macos.clipboard import MacOSClipboard


# ── LinuxClipboard.type_text ─────────────────────────────────────────────────


class TestLinuxClipboardTypeText:
    @patch("vibing.platform.linux.clipboard.subprocess.run")
    @patch("vibing.platform.linux.clipboard.shutil.which", return_value="/usr/bin/xdotool")
    @patch("vibing.platform.linux.clipboard._detect_session_type", return_value="x11")
    def test_x11_xdotool_success(self, _session, _which, mock_run):
        result = LinuxClipboard().type_text("hello world")
        assert result is True
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "xdotool"
        assert "hello world" in cmd

    @patch("vibing.platform.linux.clipboard.subprocess.run")
    @patch("vibing.platform.linux.clipboard.shutil.which", return_value="/usr/bin/wtype")
    @patch("vibing.platform.linux.clipboard._detect_session_type", return_value="wayland")
    def test_wayland_wtype_success(self, _session, _which, mock_run):
        result = LinuxClipboard().type_text("hello")
        assert result is True
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "wtype"
        assert "hello" in cmd

    @patch("vibing.platform.linux.clipboard.subprocess.run")
    @patch(
        "vibing.platform.linux.clipboard.shutil.which",
        side_effect=lambda t: "/usr/bin/ydotool" if t == "ydotool" else None,
    )
    @patch("vibing.platform.linux.clipboard._detect_session_type", return_value="wayland")
    def test_wayland_falls_back_to_ydotool(self, _session, _which, mock_run):
        result = LinuxClipboard().type_text("hello")
        assert result is True
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ydotool"
        assert "hello" in cmd

    @patch("vibing.platform.linux.clipboard.shutil.which", return_value=None)
    @patch("vibing.platform.linux.clipboard._detect_session_type", return_value="x11")
    def test_no_tool_returns_false(self, _session, _which):
        result = LinuxClipboard().type_text("hello")
        assert result is False

    @patch(
        "vibing.platform.linux.clipboard.subprocess.run",
        side_effect=CalledProcessError(1, "xdotool"),
    )
    @patch("vibing.platform.linux.clipboard.shutil.which", return_value="/usr/bin/xdotool")
    @patch("vibing.platform.linux.clipboard._detect_session_type", return_value="x11")
    def test_command_failure_returns_false(self, _session, _which, _run):
        result = LinuxClipboard().type_text("hello")
        assert result is False

    @patch(
        "vibing.platform.linux.clipboard.subprocess.run",
        side_effect=TimeoutExpired(cmd="xdotool", timeout=5),
    )
    @patch("vibing.platform.linux.clipboard.shutil.which", return_value="/usr/bin/xdotool")
    @patch("vibing.platform.linux.clipboard._detect_session_type", return_value="x11")
    def test_timeout_returns_false(self, _session, _which, _run):
        result = LinuxClipboard().type_text("hello")
        assert result is False


# ── MacOSClipboard.type_text ─────────────────────────────────────────────────


class TestMacOSClipboardTypeText:
    @patch("vibing.platform.macos.clipboard.subprocess.run")
    def test_success(self, mock_run):
        result = MacOSClipboard().type_text("hello world")
        assert result is True
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "osascript"
        assert "hello world" in cmd[2]

    @patch("vibing.platform.macos.clipboard.subprocess.run", side_effect=Exception("boom"))
    def test_failure_returns_false(self, _run):
        result = MacOSClipboard().type_text("hello")
        assert result is False

    @patch("vibing.platform.macos.clipboard.subprocess.run")
    def test_double_quotes_are_escaped(self, mock_run):
        MacOSClipboard().type_text('say "hi"')
        script = mock_run.call_args[0][0][2]
        assert '\\"hi\\"' in script

    @patch("vibing.platform.macos.clipboard.subprocess.run")
    def test_backslashes_are_escaped(self, mock_run):
        MacOSClipboard().type_text("C:\\Users\\test")
        script = mock_run.call_args[0][0][2]
        assert "C:\\\\Users\\\\test" in script

    @patch(
        "vibing.platform.macos.clipboard.subprocess.run",
        side_effect=TimeoutExpired(cmd="osascript", timeout=5),
    )
    def test_timeout_returns_false(self, _run):
        result = MacOSClipboard().type_text("hello")
        assert result is False
