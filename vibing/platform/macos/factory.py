"""macOS platform factory implementation."""

from collections.abc import Callable

from vibing.platform.base import (
    ClipboardProvider,
    HotkeyProvider,
    PlatformFactory,
    SystemIntegrationProvider,
    TrayProvider,
)
from vibing.platform.macos.clipboard import MacOSClipboard
from vibing.platform.macos.hotkey import MacOSHotkey
from vibing.platform.macos.system import MacOSSystemIntegration
from vibing.platform.macos.tray import MacOSTray


class MacOSPlatformFactory(PlatformFactory):
    """Factory for macOS specific implementations."""

    @property
    def clipboard(self) -> ClipboardProvider:
        return MacOSClipboard()

    def create_hotkey(
        self,
        key_name: str,
        device_path: str,
        on_press: Callable[[], None] | None = None,
        on_release: Callable[[], None] | None = None,
        cancel_key_name: str | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> HotkeyProvider:
        return MacOSHotkey(key_name, device_path, on_press, on_release, cancel_key_name, on_cancel)

    def create_tray(self, on_quit: Callable[[], None], tray_config: dict) -> TrayProvider:
        """Create a tray provider."""
        return MacOSTray(on_quit=on_quit, tray_config=tray_config)

    @property
    def system(self) -> SystemIntegrationProvider:
        """Return the system integration tools."""
        return MacOSSystemIntegration()
