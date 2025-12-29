"""
NVLib.component.visualrec
=========================

This module contains visual recognition components using MediaPipe and OpenCV.
Includes:

- FaceHandDetector (from FLRH.py): Detects faces and hands in video stream.
- HandTracker (from HandTracker.py): Tracks hands and landmarks with drawing utilities.

Usage:
    from NVLib.component.visualrec import FaceHandDetector, HandTracker
"""

from .FLRH import FaceHandDetector
from .HandTracker import HandTracker

__all__ = [
    "FaceHandDetector",
    "HandTracker",
]
