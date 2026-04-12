"""macOS system integration provider."""

import logging
import pathlib
import subprocess

from vibing.platform.base import SystemIntegrationProvider

logger = logging.getLogger("vibing.platform.macos.system")


class MacOSSystemIntegration(SystemIntegrationProvider):
    """macOS implementation for system integration tasks.

    Provides macOS-specific paths (e.g., ~/Library/Application Support)
    and uses the 'open' command to launch files.
    """

    def get_config_dir(self, app_name: str) -> pathlib.Path:
        """Return ~/Library/Application Support/<app_name>."""
        return pathlib.Path.home() / "Library" / "Application Support" / app_name

    def get_data_dir(self, app_name: str) -> pathlib.Path:
        """Return ~/Library/Application Support/<app_name> on macOS.
        (Usually data and config live in the same place in App Support).
        """
        return pathlib.Path.home() / "Library" / "Application Support" / app_name

    def open_file(self, target: pathlib.Path) -> None:
        """Open the target file or directory with the macOS 'open' command."""
        try:
            logger.debug("Opening %s via 'open'", target)
            subprocess.run(["open", str(target)], check=True)
        except Exception as e:
            logger.error("Failed to open %s: %s", target, e)

    def notify(self, title: str, message: str) -> None:
        """Show a system notification using macOS osascript."""
        try:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], check=False)
        except Exception as e:
            logger.error("Failed to send notification: %s", e)

    def open_accessibility_settings(self) -> None:
        """Open System Settings to the Accessibility privacy page."""
        try:
            subprocess.run(
                ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"],
                check=False,
            )
        except Exception as e:
            logger.error("Failed to open Accessibility settings: %s", e)
