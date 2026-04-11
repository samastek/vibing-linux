"""Linux platform factory implementation."""

from typing import Callable, Optional

from vibing.platform.base import (
    PlatformFactory,
    ClipboardProvider,
    HotkeyProvider,
    TrayProvider,
    SystemIntegrationProvider,
)
from vibing.platform.linux.clipboard import LinuxClipboard
from vibing.platform.linux.hotkey import HotkeyListener
from vibing.platform.linux.tray import SystemTray
from vibing.platform.linux.system import LinuxSystemIntegration


class LinuxPlatformFactory(PlatformFactory):
    """Factory for Linux specific implementations."""

    @property
    def clipboard(self) -> ClipboardProvider:
        return LinuxClipboard()

    def create_hotkey(
        self,
        key_name: str,
        device_path: str,
        on_press: Optional[Callable[[], None]] = None,
        on_release: Optional[Callable[[], None]] = None,
    ) -> HotkeyProvider:
        return HotkeyListener(key_name, device_path, on_press, on_release)

    def create_tray(self, on_quit: Callable[[], None], tray_config: dict) -> TrayProvider:
        """Create a tray provider."""
        return SystemTray(on_quit=on_quit, tray_config=tray_config)

    @property
    def system(self) -> SystemIntegrationProvider:
        """Return the system integration tools."""
        return LinuxSystemIntegration()
