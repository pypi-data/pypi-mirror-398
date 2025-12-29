"""Kryten Playlist Service - Automated playlist management for CyTube."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("kryten-playlist")
except PackageNotFoundError:
    __version__ = "0.0.0"
