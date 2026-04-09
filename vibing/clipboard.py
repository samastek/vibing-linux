import os
import shutil
import subprocess
import time


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


def paste_from_clipboard():
    """Simulate Ctrl+V into the currently focused window."""
    time.sleep(0.1)
    server = os.environ.get("XDG_SESSION_TYPE", "x11").lower()
    try:
        if server == "wayland":
            if shutil.which("ydotool"):
                subprocess.run(
                    ["ydotool", "key", "ctrl+v"],
                    check=True, timeout=3,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            if shutil.which("wtype"):
                subprocess.run(
                    ["wtype", "-M", "ctrl", "-k", "v"],
                    check=True, timeout=3,
                )
                return True
        else:
            if shutil.which("xdotool"):
                subprocess.run(
                    ["xdotool", "key", "ctrl+v"],
                    check=True, timeout=3,
                )
                return True
        print("Warning: No paste tool found. Install ydotool, wtype, or xdotool.")
        return False
    except subprocess.TimeoutExpired:
        print("Warning: Paste command timed out.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Warning: Paste command failed: {e}")
        return False
