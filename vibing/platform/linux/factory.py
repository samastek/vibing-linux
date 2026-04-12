"""Linux platform factory implementation."""

from collections.abc import Callable

from vibing.platform.base import (
    ClipboardProvider,
    HotkeyProvider,
    OverlayProvider,
    PlatformFactory,
    SystemIntegrationProvider,
    TrayProvider,
)
from vibing.platform.linux.clipboard import LinuxClipboard
from vibing.platform.linux.hotkey import HotkeyListener
from vibing.platform.linux.system import LinuxSystemIntegration
from vibing.platform.linux.tray import SystemTray
from vibing.platform.overlay import TkOverlay


class LinuxPlatformFactory(PlatformFactory):
    """Factory for Linux specific implementations."""

    @property
    def clipboard(self) -> ClipboardProvider:
        return LinuxClipboard()

    def create_hotkey(
        self,
        key_name: str,
        device_path: str,
        on_press: Callable[[], None] | None = None,
        on_release: Callable[[], None] | None = None,
        cancel_key_name: str | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> HotkeyProvider:
        return HotkeyListener(
            key_name, device_path, on_press, on_release, cancel_key_name, on_cancel
        )

    def create_tray(self, on_quit: Callable[[], None], tray_config: dict) -> TrayProvider:
        """Create a tray provider."""
        return SystemTray(on_quit=on_quit, tray_config=tray_config)

    def create_overlay(self, overlay_config: dict) -> OverlayProvider | None:
        """Create the tkinter-based overlay (requires python3-tk)."""
        return TkOverlay(overlay_config)

    @property
    def system(self) -> SystemIntegrationProvider:
        """Return the system integration tools."""
        return LinuxSystemIntegration()
