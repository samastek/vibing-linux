import os
import shutil
import subprocess


def copy_to_clipboard(text):
    server = os.environ.get("XDG_SESSION_TYPE", "x11").lower()
    if server == "wayland" and shutil.which("wl-copy"):
        cmd = ["wl-copy"]
    elif shutil.which("xclip"):
        cmd = ["xclip", "-selection", "clipboard"]
    elif shutil.which("xsel"):
        cmd = ["xsel", "--clipboard", "--input"]
    else:
        raise RuntimeError(
            "No clipboard tool found. Install xclip, xsel, or wl-clipboard."
        )
    subprocess.run(cmd, input=text.encode("utf-8"), check=True, timeout=5)
