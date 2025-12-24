"""
This is the initialization module for the gold-dl package.

It provides the main entry point for the package (CLI)
and exposes the public API for programmatic usage.
"""

from .cli import app
from .services import DownloadService

__all__ = ["DownloadService"]