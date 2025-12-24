"""MagPy controllers - bridge between GUI and bioamla core."""

from .audio_controller import AudioController, AudioMetadata

__all__ = [
    "AudioController",
    "AudioMetadata",
]