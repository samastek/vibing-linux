import pystray
from PIL import Image, ImageDraw


def _make_icon(color):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill=color)
    return img


ICONS = {
    "idle": _make_icon((120, 120, 120)),
    "recording": _make_icon((220, 40, 40)),
    "processing": _make_icon((240, 160, 30)),
    "done": _make_icon((40, 180, 40)),
    "error": _make_icon((180, 40, 40)),
}

STATE_LABELS = {
    "idle": "Idle",
    "recording": "Recording...",
    "processing": "Processing...",
    "done": "Done",
    "error": "Error",
}


class SystemTray:
    def __init__(self, on_quit=None):
        self._on_quit = on_quit
        self._icon = pystray.Icon(
            "vibing-linux",
            ICONS["idle"],
            "Vibing Linux - Idle",
            menu=pystray.Menu(
                pystray.MenuItem("Quit", self._quit),
            ),
        )

    def set_state(self, state):
        self._icon.icon = ICONS.get(state, ICONS["idle"])
        self._icon.title = f"Vibing Linux - {STATE_LABELS.get(state, state)}"

    def _quit(self, icon, item):
        if self._on_quit:
            self._on_quit()
        icon.stop()

    def run(self):
        self._icon.run()

    def stop(self):
        self._icon.stop()
