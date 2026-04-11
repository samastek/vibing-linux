"""Linux system integration provider."""

import logging
import pathlib
import subprocess

import xdg.BaseDirectory

logger = logging.getLogger("vibing.platform.linux.system")


class LinuxSystemIntegration:
    """Linux specific handling of paths and files using XDG specification."""

    def get_config_dir(self, app_name: str) -> pathlib.Path:
        """Return ~/.config/<app_name>."""
        return pathlib.Path(xdg.BaseDirectory.save_config_path(app_name))

    def get_data_dir(self, app_name: str) -> pathlib.Path:
        """Return ~/.local/share/<app_name>."""
        return pathlib.Path(xdg.BaseDirectory.save_data_path(app_name))

    def open_file(self, target: pathlib.Path) -> None:
        """Open the target file using xdg-open."""
        try:
            subprocess.Popen(["xdg-open", str(target)])
        except OSError as e:
            logger.error(f"Failed to open {target}: {e}")

    def notify(self, title: str, message: str) -> None:
        """Show a system notification using notify-send."""
        try:
            subprocess.run(["notify-send", title, message], check=False)
        except OSError as e:
            logger.error("Failed to send notification: %s", e)
