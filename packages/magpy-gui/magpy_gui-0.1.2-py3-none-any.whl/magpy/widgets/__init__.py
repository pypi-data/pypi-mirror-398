"""Custom widgets for MagPy UI."""

from .waveform import WaveformWidget
from .spectrogram import SpectrogramWidget, SelectionBounds
from .selection_table import SelectionTableWidget
from .playback import PlaybackControls
from .properties_panel import PropertiesPanel
from .navigation_bar import NavigationBar, ViewType

__all__ = [
    "WaveformWidget",
    "SpectrogramWidget",
    "SelectionBounds",
    "SelectionTableWidget",
    "PlaybackControls",
    "PropertiesPanel",
    "NavigationBar",
    "ViewType",
]
