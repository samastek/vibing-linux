"""macOS platform factory implementation."""

from typing import Callable, Optional

from vibing.platform.base import (
    PlatformFactory,
    ClipboardProvider,
    HotkeyProvider,
    TrayProvider,
    SystemIntegrationProvider,
)
from vibing.platform.macos.clipboard import MacOSClipboard
from vibing.platform.macos.hotkey import MacOSHotkey
from vibing.platform.macos.tray import MacOSTray
from vibing.platform.macos.system import MacOSSystemIntegration


class MacOSPlatformFactory(PlatformFactory):
    """Factory for macOS specific implementations."""

    @property
    def clipboard(self) -> ClipboardProvider:
        return MacOSClipboard()

    def create_hotkey(
        self,
        key_name: str,
        device_path: str,
        on_press: Optional[Callable[[], None]] = None,
        on_release: Optional[Callable[[], None]] = None,
    ) -> HotkeyProvider:
        return MacOSHotkey(key_name, device_path, on_press, on_release)

    def create_tray(self, on_quit: Callable[[], None], tray_config: dict) -> TrayProvider:
        """Create a tray provider."""
        return MacOSTray(on_quit=on_quit, tray_config=tray_config)

    @property
    def system(self) -> SystemIntegrationProvider:
        """Return the system integration tools."""
        return MacOSSystemIntegration()