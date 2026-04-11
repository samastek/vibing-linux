"""Clipboard operations for Linux (X11 and Wayland)."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time

logger = logging.getLogger("vibing.clipboard")


def _detect_session_type() -> str:
    """Return 'wayland' or 'x11' based on the current session."""
    return os.environ.get("XDG_SESSION_TYPE", "x11").lower()


class LinuxClipboard:
    """Linux implementation for clipboard operations."""

    def copy(self, text: str, timeout: int = 5) -> None:
        """Copy *text* to the system clipboard.

        Raises ``RuntimeError`` if no clipboard tool is available.
        """
        session = _detect_session_type()
        if session == "wayland" and shutil.which("wl-copy"):
            cmd = ["wl-copy"]
        elif shutil.which("xclip"):
            cmd = ["xclip", "-selection", "clipboard"]
        elif shutil.which("xsel"):
            cmd = ["xsel", "--clipboard", "--input"]
        else:
            raise RuntimeError("No clipboard tool found. Install xclip, xsel, or wl-clipboard.")
        subprocess.run(cmd, input=text.encode("utf-8"), check=True, timeout=timeout)

    def paste(
        self,
        paste_delay: float = 0.1,
        paste_timeout: int = 3,
    ) -> bool:
        """Simulate Ctrl+V into the currently focused window.

        Returns ``True`` if the paste was triggered successfully.
        """
        time.sleep(paste_delay)
        session = _detect_session_type()
        try:
            if session == "wayland":
                if shutil.which("ydotool"):
                    subprocess.run(
                        ["ydotool", "key", "ctrl+v"],
                        check=True,
                        timeout=paste_timeout,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True
                if shutil.which("wtype"):
                    subprocess.run(
                        ["wtype", "-M", "ctrl", "-k", "v"],
                        check=True,
                        timeout=paste_timeout,
                    )
                    return True
            else:
                if shutil.which("xdotool"):
                    subprocess.run(
                        ["xdotool", "key", "ctrl+v"],
                        check=True,
                        timeout=paste_timeout,
                    )
                    return True
            logger.warning("No paste tool found. Install ydotool, wtype, or xdotool.")
            return False
        except subprocess.TimeoutExpired:
            logger.warning("Paste command timed out.")
            return False
        except subprocess.CalledProcessError as e:
            logger.warning("Paste command failed: %s", e)
            return False
