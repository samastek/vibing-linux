"""Base platform protocols for Vibing."""

import enum
import pathlib
from collections.abc import Callable
from typing import Protocol


class AppState(enum.Enum):
    """Application states shown in the system tray."""

    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class ClipboardProvider(Protocol):
    """Protocol for interacting with the system clipboard."""

    def copy(self, text: str, timeout: int = 5) -> None:
        """Copy text to the system clipboard."""
        ...

    def paste(self, paste_delay: float = 0.1, paste_timeout: int = 3) -> bool:
        """Simulate a paste action (like Ctrl+V) into the currently focused window."""
        ...


class HotkeyProvider(Protocol):
    """Protocol for listening to global hotkeys."""

    def __init__(
        self,
        key_name: str,
        device_path: str,
        on_press: Callable[[], None] | None = None,
        on_release: Callable[[], None] | None = None,
        cancel_key_name: str | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> None: ...

    def start(self) -> None:
        """Start listening for the hotkey in a background thread."""
        ...

    def stop(self) -> None:
        """Stop the listener and wait for the thread to finish."""
        ...


class TrayProvider(Protocol):
    """Protocol for system tray integration."""

    def __init__(self, on_quit: Callable[[], None], tray_config: dict) -> None: ...

    def set_state(self, state: str) -> None:
        """Update the visual state of the tray icon (e.g. RECORDING, DONE)."""
        ...

    def run(self) -> None:
        """Run the blocking tray icon loop."""
        ...

    def stop(self) -> None:
        """Stop the tray icon."""
        ...


class SystemIntegrationProvider(Protocol):
    """Protocol for system-level integration (paths, opening files)."""

    def get_config_dir(self, app_name: str) -> pathlib.Path:
        """Return the standard user config directory for the application."""
        ...

    def get_data_dir(self, app_name: str) -> pathlib.Path:
        """Return the standard user data directory for the application."""
        ...

    def open_file(self, target: pathlib.Path) -> None:
        """Open the target file or directory with the system default application."""
        ...

    def notify(self, title: str, message: str) -> None:
        """Show a system notification."""
        ...


class OverlayProvider(Protocol):
    """Protocol for the floating transcript/correction overlay."""

    def start(self) -> None:
        """Initialise and prepare the overlay window."""
        ...

    def stop(self) -> None:
        """Tear down the overlay."""
        ...

    def show_transcript(self, text: str) -> None:
        """Show the raw transcription text."""
        ...

    def show_result(self, corrected: str) -> None:
        """Transition to the corrected text and schedule auto-hide."""
        ...

    def hide(self) -> None:
        """Immediately hide the overlay (e.g. on cancel)."""
        ...


class PlatformFactory(Protocol):
    """Factory extending all platform-specific providers."""

    @property
    def clipboard(self) -> ClipboardProvider: ...

    def create_hotkey(
        self,
        key_name: str,
        device_path: str,
        on_press: Callable[[], None] | None = None,
        on_release: Callable[[], None] | None = None,
        cancel_key_name: str | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> HotkeyProvider: ...

    def create_tray(self, on_quit: Callable[[], None], tray_config: dict) -> TrayProvider: ...

    def create_overlay(self, overlay_config: dict) -> OverlayProvider | None: ...

    @property
    def system(self) -> SystemIntegrationProvider: ...
