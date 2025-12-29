"""
Mac Cleaner - A safe and intelligent disk cleaning utility for macOS.

This package helps you reclaim disk space by identifying and cleaning:
- Temporary files
- System logs
- Browser caches
- Development caches (node_modules, Homebrew, Docker, etc.)
"""

__version__ = "1.1.0"
__author__ = "nmlemus"
__license__ = "MIT"

from .cleaner import main

__all__ = ["main"]
