"""macOS clipboard provider."""

import logging
import subprocess
import time

from vibing.platform.base import ClipboardProvider

logger = logging.getLogger("vibing.platform.macos.clipboard")


class MacOSClipboard(ClipboardProvider):
    """macOS implementation for clipboard operations.
    
    Uses pbcopy for copying to clipboard and AppleScript (osascript) 
    to simulate Cmd+V for pasting.
    """

    def copy(self, text: str, timeout: int = 5) -> None:
        """Copy text to the system clipboard using pbcopy."""
        try:
            logger.debug("Copying text to clipboard via pbcopy")
            process = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            process.communicate(input=text.encode("utf-8"), timeout=timeout)
            logger.debug("Successfully copied %d characters", len(text))
        except subprocess.TimeoutExpired:
            logger.error("pbcopy timed out after %s seconds", timeout)
            if process:
                process.kill()
        except Exception as e:
            logger.error("Failed to copy using pbcopy: %s", e)

    def paste(self, paste_delay: float = 0.1, paste_timeout: int = 3) -> bool:
        """Simulate a paste action (Cmd+V) using AppleScript."""
        logger.debug("Pasting from clipboard via osascript")

        time.sleep(paste_delay)

        script = 'tell application "System Events" to keystroke "v" using command down'
        try:
            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True,
                timeout=paste_timeout,
            )
            return True
        except subprocess.TimeoutExpired:
            logger.error("osascript timed out after %s seconds", paste_timeout)
        except Exception as e:
            logger.error("Failed to paste using osascript: %s", e)
        return False
