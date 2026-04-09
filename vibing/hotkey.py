import select
import threading

import evdev
from evdev import ecodes


def find_keyboards(device_path=None):
    if device_path and device_path != "auto":
        return [evdev.InputDevice(device_path)]

    keyboards = []
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
    def __init__(
        self, key_name="KEY_RIGHTALT", device_path="auto", on_press=None, on_release=None
    ):
        self.key_code = getattr(ecodes, key_name)
        self.device_path = device_path
        self.on_press = on_press
        self.on_release = on_release
        self._running = False
        self._thread = None

    def _listen(self):
        keyboards = find_keyboards(self.device_path)
        devices = {dev.fd: dev for dev in keyboards}
        print(
            f"Listening for {ecodes.KEY[self.key_code]} on: "
            + ", ".join(dev.name for dev in keyboards)
        )

        while self._running:
            r, _, _ = select.select(list(devices.values()), [], [], 0.5)
            for dev in r:
                try:
                    for event in dev.read():
                        if event.type == ecodes.EV_KEY and event.code == self.key_code:
                            if event.value == 1 and self.on_press:
                                self.on_press()
                            elif event.value == 0 and self.on_release:
                                self.on_release()
                except OSError:
                    if self._running:
                        print(f"Device disconnected: {dev.name}")
                    del devices[dev.fd]
                    if not devices:
                        print("All keyboard devices disconnected.")
                        return

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
