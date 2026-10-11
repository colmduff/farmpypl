"""farmpypl: Income and organic-conversion calculator for an Irish dairy farm."""

from importlib.metadata import PackageNotFoundError, version
from farmpypl.core import FarmManager
from farmpypl.db import refresh_prices

__all__ = ["FarmManager", "refresh_prices"]

try:
    __version__ = version("farmpypl")
except PackageNotFoundError:  # running from source without installing
    __version__ = "unknown"
