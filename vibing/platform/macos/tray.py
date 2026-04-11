"""System tray icon for Vibing (macOS)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import pystray
from PIL import Image, ImageDraw

from vibing.platform.base import AppState, TrayProvider
from vibing.platform.macos.system import MacOSSystemIntegration

logger = logging.getLogger("vibing.platform.macos.tray")

_STATE_LABELS: dict[AppState, str] = {
    AppState.IDLE: "Idle",
    AppState.RECORDING: "Recording...",
    AppState.PROCESSING: "Processing...",
    AppState.DONE: "Done",
    AppState.ERROR: "Error",
}

# Default RGB colours for each state.
_DEFAULT_COLORS: dict[str, tuple[int, int, int]] = {
    "idle": (120, 120, 120),
    "recording": (220, 40, 40),
    "processing": (240, 160, 30),
    "done": (40, 180, 40),
    "error": (180, 40, 40),
}


def _make_icon(color: tuple[int, int, int], size: int = 64) -> Image.Image:
    """Create a coloured circle icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = size // 8
    draw.ellipse([margin, margin, size - margin, size - margin], fill=color)
    return img


class MacOSTray(TrayProvider):
    """Manages the pystray system-tray icon and menu for macOS."""

    def __init__(
        self,
        on_quit: Callable[[], None] | None = None,
        tray_config: dict[str, Any] | None = None,
    ) -> None:
        cfg = tray_config or {}
        icon_size: int = cfg.get("icon_size", 64)
        color_overrides: dict[str, list[int]] = cfg.get("colors", {})

        self._icons: dict[AppState, Image.Image] = {}
        for state in AppState:
            rgb = color_overrides.get(state.value)
            color = tuple(rgb) if rgb and len(rgb) == 3 else _DEFAULT_COLORS[state.value]  # type: ignore[arg-type]
            self._icons[state] = _make_icon(color, size=icon_size)

        self._on_quit = on_quit

        menu = pystray.Menu(
            pystray.MenuItem("Show Logs", self._show_logs),
            pystray.MenuItem("Quit", self._quit),
        )

        self._icon = pystray.Icon(
            "vibing",
            self._icons[AppState.IDLE],
            "Vibing - Idle",
            menu=menu,
        )

    def set_state(self, state: AppState) -> None:
        """Update the tray icon and tooltip to reflect *state*."""
        self._icon.icon = self._icons.get(state, self._icons[AppState.IDLE])
        label = _STATE_LABELS.get(state, state.value)
        self._icon.title = f"Vibing - {label}"

    def _show_logs(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        system = MacOSSystemIntegration()
        log_file = system.get_data_dir("vibing-linux") / "vibing.log"
        if not log_file.exists():
            logger.warning("Log file does not exist yet: %s", log_file)
            return

        system.open_file(log_file)

    def _quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        if self._on_quit:
            self._on_quit()
        icon.stop()

    def run(self) -> None:
        """Start the tray icon (blocks until stopped)."""
        # pystray on macOS requires the event loop to run on the main thread
        self._icon.run()

    def stop(self) -> None:
        """Stop the tray icon."""
        self._icon.stop()
