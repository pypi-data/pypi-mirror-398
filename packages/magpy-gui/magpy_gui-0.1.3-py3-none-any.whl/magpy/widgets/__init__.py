"""Custom widgets for MagPy UI."""

from .waveform import WaveformWidget
from .spectrogram import SpectrogramWidget, SelectionBounds
from .selection_table import SelectionTableWidget
from .playback import PlaybackControls
from .properties_panel import PropertiesPanel
from .navigation_bar import NavigationBar, ViewType
from .detection_dialog import (
    ModelSelectionDialog,
    DetectionProgressDialog,
    BatchDetectionDialog,
)
from .detection_results import DetectionResultsWidget, get_label_color, DETECTION_COLORS

__all__ = [
    "WaveformWidget",
    "SpectrogramWidget",
    "SelectionBounds",
    "SelectionTableWidget",
    "PlaybackControls",
    "PropertiesPanel",
    "NavigationBar",
    "ViewType",
    # Detection widgets
    "ModelSelectionDialog",
    "DetectionProgressDialog",
    "BatchDetectionDialog",
    "DetectionResultsWidget",
    "get_label_color",
    "DETECTION_COLORS",
]
