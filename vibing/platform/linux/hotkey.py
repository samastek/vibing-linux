"""Global hotkey listener using evdev (Linux input devices)."""

from __future__ import annotations

import logging
import select
import threading
import time
from collections.abc import Callable

import evdev
from evdev import ecodes

logger = logging.getLogger("vibing.hotkey")


def find_keyboards(device_path: str | None = None) -> list[evdev.InputDevice]:
    """Detect keyboard input devices.

    If *device_path* is given (and is not ``"auto"``), uses that single
    device.  Otherwise auto-detects by looking for devices that report
    the A–Z key range.

    Raises ``RuntimeError`` if no keyboards are found.
    """
    if device_path and device_path != "auto":
        return [evdev.InputDevice(device_path)]

    keyboards: list[evdev.InputDevice] = []
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
            caps = dev.capabilities()
            if ecodes.EV_KEY in caps:
                keys = caps[ecodes.EV_KEY]
                if ecodes.KEY_A in keys and ecodes.KEY_Z in keys:
                    keyboards.append(dev)
        except (PermissionError, OSError):
            continue

    if not keyboards:
        raise RuntimeError(
            "No keyboard found. Ensure you are in the 'input' group:\n"
            "  sudo usermod -aG input $USER\n"
            "Then log out and back in."
        )
    return keyboards


class HotkeyListener:
    """Listens for a global hotkey press/release on evdev input devices."""

    def __init__(
        self,
        key_name: str = "KEY_RIGHTALT",
        device_path: str = "auto",
        on_press: Callable[[], None] | None = None,
        on_release: Callable[[], None] | None = None,
        cancel_key_name: str | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> None:
        self.key_code: int = getattr(ecodes, key_name)
        self.cancel_key_code: int | None = (
            getattr(ecodes, cancel_key_name) if cancel_key_name else None
        )
        self.device_path = device_path
        self.on_press = on_press
        self.on_release = on_release
        self.on_cancel = on_cancel
        self._running = False
        self._thread: threading.Thread | None = None

    _RECONNECT_INTERVAL = 2.0  # seconds to wait when no keyboards found at all
    _RESCAN_INTERVAL = 3.0  # seconds between periodic rescans for new/reconnected devices
    _RECONNECT_POLL_INTERVAL = 1.0  # faster rescan when a known device is disconnected

    def _listen(self) -> None:
        devices: dict[int, evdev.InputDevice] = {}
        last_rescan = 0.0  # forces an immediate scan on first iteration
        pending_reconnect: set[str] = set()  # names of devices waiting to reconnect

        while self._running:
            now = time.monotonic()

            rescan_interval = (
                self._RECONNECT_POLL_INTERVAL if pending_reconnect else self._RESCAN_INTERVAL
            )

            # ── Periodic rescan for new / reconnected devices ────────
            if now - last_rescan >= rescan_interval:
                last_rescan = now
                try:
                    keyboards = find_keyboards(self.device_path)
                except RuntimeError:
                    if not devices:
                        logger.warning(
                            "No keyboard found. Retrying in %.0fs...",
                            self._RECONNECT_INTERVAL,
                        )
                        deadline = time.monotonic() + self._RECONNECT_INTERVAL
                        while self._running and time.monotonic() < deadline:
                            time.sleep(0.2)
                    continue

                initial = not devices
                current_names = {dev.name for dev in devices.values()}
                for dev in keyboards:
                    if dev.name not in current_names:
                        devices[dev.fd] = dev
                        if dev.name in pending_reconnect:
                            logger.info("Device reconnected: %s", dev.name)
                            pending_reconnect.discard(dev.name)
                        elif not initial:
                            logger.info("New device connected: %s", dev.name)
                    else:
                        dev.close()  # already tracked; discard duplicate fd

                if initial and devices:
                    logger.info(
                        "Listening for %s on: %s",
                        ecodes.KEY[self.key_code],
                        ", ".join(dev.name for dev in devices.values()),
                    )

            if not devices:
                time.sleep(0.2)
                continue

            # ── Event loop ───────────────────────────────────────────
            r, _, _ = select.select(list(devices.values()), [], [], 0.5)
            for dev in r:
                try:
                    for event in dev.read():
                        if event.type != ecodes.EV_KEY:
                            continue
                        if event.code == self.key_code:
                            if event.value == 1 and self.on_press:
                                self.on_press()
                            elif event.value == 0 and self.on_release:
                                self.on_release()
                        elif (
                            self.cancel_key_code
                            and event.code == self.cancel_key_code
                            and event.value == 1
                            and self.on_cancel
                        ):
                            self.on_cancel()
                except OSError:
                    logger.warning("Device disconnected: %s", dev.name)
                    pending_reconnect.add(dev.name)
                    devices.pop(dev.fd, None)
                    last_rescan = 0.0  # trigger immediate rescan on next iteration

        for dev in devices.values():
            dev.close()

    def start(self) -> None:
        """Start listening for the hotkey in a background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the listener and wait for the thread to finish."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
