"""macOS hotkey provider."""

import logging
from typing import Callable, Optional

try:
    from pynput import keyboard
except ImportError:
    keyboard = None

from vibing.platform.base import HotkeyProvider

logger = logging.getLogger("vibing.platform.macos.hotkey")


class MacOSHotkey(HotkeyProvider):
    """macOS hotkey listener using pynput."""

    def __init__(
        self,
        key_name: str,
        device_path: str,
        on_press: Optional[Callable[[], None]] = None,
        on_release: Optional[Callable[[], None]] = None,
        cancel_key_name: Optional[str] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ) -> None:
        self.key_name = key_name
        self.device_path = device_path
        self.on_press = on_press
        self.on_release = on_release
        self.cancel_key_name = cancel_key_name
        self.on_cancel = on_cancel

        if keyboard is None:
            raise ImportError(
                "pynput is not installed. Hotkey support on macOS requires pynput."
            )

        self._listener: Optional["keyboard.GlobalHotKeys"] = None

    def start(self) -> None:
        if self._listener is not None:
            return

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
                if hasattr(self._listener, "canonical"):
                    hotkey.release(self._listener.canonical(key))
                # For push-to-talk release logic on a combination
                if not hotkey._state and self.on_release:
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
