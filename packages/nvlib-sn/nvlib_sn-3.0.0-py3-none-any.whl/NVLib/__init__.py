"""
NVLib: A Python Library that makes everything easy to code for Anyone and Everyone.

Requires Python 3.12.
"""

import sys

# Enforce Python 3.12
if sys.version_info[:2] != (3, 12):
    raise RuntimeError(
        "NVLib requires Python 3.12. "
        f"You are using Python {sys.version_info.major}.{sys.version_info.minor}."
    )

__version__ = "0.2.0"
__author__ = "Sai Neela"
__email__ = "saiathulithn@gmail.com"
__description__ = "A Python Library that makes everything easy to code for Anyone and Everyone"

from . import Components

__all__ = ['Components']
