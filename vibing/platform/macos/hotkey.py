"""macOS hotkey provider."""

import ctypes
import ctypes.util
import logging
import subprocess
from collections.abc import Callable

try:
    from pynput import keyboard
except ImportError:
    keyboard = None

from vibing.platform.base import HotkeyProvider

logger = logging.getLogger("vibing.platform.macos.hotkey")

# Load the macOS Accessibility framework to check process trust status.
_ax_lib_path = ctypes.util.find_library("ApplicationServices")
_ax_lib = ctypes.cdll.LoadLibrary(_ax_lib_path) if _ax_lib_path else None

if _ax_lib is not None:
    _ax_lib.AXIsProcessTrusted.restype = ctypes.c_bool
    _ax_lib.AXIsProcessTrusted.argtypes = []


def _is_process_trusted() -> bool:
    """Return True if this process has macOS Accessibility API permission."""
    if _ax_lib is None:
        return True
    return bool(_ax_lib.AXIsProcessTrusted())


class MacOSHotkey(HotkeyProvider):
    """macOS hotkey listener using pynput."""

    def __init__(
        self,
        key_name: str,
        device_path: str,
        on_press: Callable[[], None] | None = None,
        on_release: Callable[[], None] | None = None,
        cancel_key_name: str | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> None:
        self.key_name = key_name
        self.device_path = device_path
        self.on_press = on_press
        self.on_release = on_release
        self.cancel_key_name = cancel_key_name
        self.on_cancel = on_cancel

        if keyboard is None:
            raise ImportError("pynput is not installed. Hotkey support on macOS requires pynput.")

        self._listener: keyboard.GlobalHotKeys | None = None

    def start(self) -> None:
        if self._listener is not None:
            return

        if not _is_process_trusted():
            logger.error("")
            logger.error("╔══════════════════════════════════════════════════════════════╗")
            logger.error("║  macOS Accessibility permission required for hotkeys        ║")
            logger.error("╠══════════════════════════════════════════════════════════════╣")
            logger.error("║  System Settings is opening — find this app/terminal in    ║")
            logger.error("║  the list, toggle the switch next to it, then restart.     ║")
            logger.error("╚══════════════════════════════════════════════════════════════╝")
            logger.error("")
            subprocess.run(
                ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"],
                check=False,
            )

        logger.info("Starting global hotkeys listener for %s", self.key_name)

        target_cancel_key = None
        if self.cancel_key_name:
            try:
                target_cancel_key = getattr(keyboard.Key, self.cancel_key_name.replace("Key.", ""))
            except AttributeError:
                target_cancel_key = keyboard.KeyCode.from_char(self.cancel_key_name)

        if "<" in self.key_name:
            hotkey = keyboard.HotKey(keyboard.HotKey.parse(self.key_name), self.on_press)

            def on_press(key):
                if target_cancel_key and key == target_cancel_key and self.on_cancel:
                    self.on_cancel()
                if hasattr(self._listener, "canonical"):
                    hotkey.press(self._listener.canonical(key))

            def on_release(key):
                was_engaged = not hotkey._state
                if hasattr(self._listener, "canonical"):
                    hotkey.release(self._listener.canonical(key))
                if was_engaged and self.on_release:
                    self.on_release()

            self._listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release,
            )
            self._listener.start()
        else:
            # Single key fallback
            try:
                target_key = getattr(keyboard.Key, self.key_name.replace("Key.", ""))
            except AttributeError:
                target_key = keyboard.KeyCode.from_char(self.key_name)

            def on_press(key):
                if key == target_key and self.on_press:
                    self.on_press()
                elif target_cancel_key and key == target_cancel_key and self.on_cancel:
                    self.on_cancel()

            def on_release(key):
                if key == target_key and self.on_release:
                    self.on_release()

            self._listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release,
            )
            self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener.join()
            self._listener = None
