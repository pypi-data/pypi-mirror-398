"""BlizzardAPI v3 - Modern Python wrapper for the Blizzard API."""

__version__ = "3.0.0"

from .blizzard_api import BlizzardAPI
from .types import Locale, Region

__all__ = [
    "__version__",
    "BlizzardAPI",
    "Region",
    "Locale",
]
