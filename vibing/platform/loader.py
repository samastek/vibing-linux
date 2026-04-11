"""Dynamic platform plugin loader for Vibing."""

import importlib.metadata
import logging
import sys

from vibing.platform.base import PlatformFactory

logger = logging.getLogger("vibing.platform")


def get_platform_factory() -> PlatformFactory:
    """Load the platform factory specified by sys.platform via entry points."""
    group = "vibing.platforms"
    try:
        # Python 3.10+
        entry_points = importlib.metadata.entry_points(group=group)
    except TypeError:
        # Python 3.8/3.9
        entry_points = importlib.metadata.entry_points().get(group, [])

    for ep in entry_points:
        if ep.name == sys.platform:
            logger.info("Loading platform plugin for '%s'", ep.name)
            return ep.load()()  # Instantiate the factory

    raise RuntimeError(
        f"No platform plugin found for '{sys.platform}'. "
        f"Ensure your system is supported (e.g. check pyproject.toml)."
    )
