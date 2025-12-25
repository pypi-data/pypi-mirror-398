"""Core package for the Python reimplementation of xindy."""

from importlib import metadata


try:
    __version__ = metadata.version("xindy")
except metadata.PackageNotFoundError:  # pragma: no cover - during local dev
    __version__ = "0.0.0"

__all__ = ["__version__"]
