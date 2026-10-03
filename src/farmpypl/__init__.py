"""farmpypl: Income and organic-conversion calculator for an Irish dairy farm."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("farmpypl")
except PackageNotFoundError:  # running from source without installing
    __version__ = "unknown"
