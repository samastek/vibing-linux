"""Tests for vibing.tray."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from vibing.tray import AppState, SystemTray, _make_icon


class TestAppState:
    def test_all_states_exist(self):
        assert AppState.IDLE.value == "idle"
        assert AppState.RECORDING.value == "recording"
        assert AppState.PROCESSING.value == "processing"
        assert AppState.DONE.value == "done"
        assert AppState.ERROR.value == "error"


class TestMakeIcon:
    def test_default_size(self):
        img = _make_icon((255, 0, 0))
        assert img.size == (64, 64)

    def test_custom_size(self):
        img = _make_icon((0, 255, 0), size=128)
        assert img.size == (128, 128)

    def test_rgba_mode(self):
        img = _make_icon((0, 0, 255))
        assert img.mode == "RGBA"


class TestSystemTray:
    @patch("vibing.tray.pystray.Icon")
    def test_set_state(self, mock_icon_cls):
        mock_icon = MagicMock()
        mock_icon_cls.return_value = mock_icon

        tray = SystemTray()
        tray.set_state(AppState.RECORDING)
        assert mock_icon.title == "Vibing Linux - Recording..."

    @patch("vibing.tray.pystray.Icon")
    def test_custom_colors(self, mock_icon_cls):
        mock_icon = MagicMock()
        mock_icon_cls.return_value = mock_icon

        tray = SystemTray(
            tray_config={"colors": {"idle": [255, 255, 255]}}
        )
        # Should not raise; custom color is applied
        tray.set_state(AppState.IDLE)

    @patch("vibing.tray.pystray.Icon")
    def test_quit_callback(self, mock_icon_cls):
        mock_icon = MagicMock()
        mock_icon_cls.return_value = mock_icon
        quit_fn = MagicMock()

        tray = SystemTray(on_quit=quit_fn)
        tray._quit(mock_icon, None)

        quit_fn.assert_called_once()
        mock_icon.stop.assert_called_once()
