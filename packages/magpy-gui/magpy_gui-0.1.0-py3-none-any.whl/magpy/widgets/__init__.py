"""Custom widgets for MagPy UI."""

from .waveform import WaveformWidget
from .spectrogram import SpectrogramWidget
from .selection_table import SelectionTableWidget
from .playback import PlaybackControls
from .properties_panel import PropertiesPanel

__all__ = [
    "WaveformWidget",
    "SpectrogramWidget",
    "SelectionTableWidget",
    "PlaybackControls",
    "PropertiesPanel",
]
