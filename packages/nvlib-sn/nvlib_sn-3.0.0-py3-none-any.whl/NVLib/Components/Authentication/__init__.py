"""
NVLib.component.Authentication
==============================

Authentication-related utilities and components.

Currently provides Firebase authentication integration through
the Auth class in FirebaseAuth module.
"""

from .FirebaseAuth import Auth

__all__ = [
    "Auth",
]
