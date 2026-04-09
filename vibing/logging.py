"""Logging configuration for Vibing Linux."""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys

from vibing.config import LOG_FILE


def setup_logging(level: str | None = None) -> logging.Logger:
    """Configure and return the application logger.

    The log level is resolved in order:
      1. ``level`` argument
      2. ``VIBING_LOG_LEVEL`` environment variable
      3. ``"INFO"`` default

    Logs are written to both stderr and a rotating log file at
    ``~/.local/share/vibing-linux/vibing.log``.

    Args:
        level: Optional log level name (DEBUG, INFO, WARNING, ERROR).

    Returns:
        The configured ``vibing`` logger.
    """
    log_level = (level or os.environ.get("VIBING_LOG_LEVEL", "INFO")).upper()

    logger = logging.getLogger("vibing")
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level, logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
