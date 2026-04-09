import os
import shutil
import subprocess


def _display_server():
    return os.environ.get("XDG_SESSION_TYPE", "x11").lower()


def copy_to_clipboard(text):
    server = _display_server()
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


def paste():
    server = _display_server()
    try:
        if server == "wayland" and shutil.which("wtype"):
            subprocess.run(
                ["wtype", "-M", "ctrl", "v", "-m", "ctrl"], check=True, timeout=2
            )
        elif shutil.which("xdotool"):
            subprocess.run(
                ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
                check=True,
                timeout=2,
            )
    except Exception as e:
        print(f"Auto-paste failed: {e}")
