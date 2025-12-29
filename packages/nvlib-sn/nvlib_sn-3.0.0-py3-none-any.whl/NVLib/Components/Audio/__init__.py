"""
NVLib.component.Audio
=====================

Audio-related utilities and components.

This submodule currently provides TextToSpeech functionality using edge_tts
and pygame for text-to-speech conversion and audio playback.

Modules:
- TextToSpeech: Implements async text-to-speech conversion and playback.
"""

from .TextToSpeech import say

__all__ = [
    "say",
]
