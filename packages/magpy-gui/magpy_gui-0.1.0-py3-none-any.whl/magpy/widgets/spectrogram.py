"""
Spectrogram visualization widget using pyqtgraph.

Provides interactive spectrogram display with multiple colormaps and selection support.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Tuple

import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout

import pyqtgraph as pg
from pyqtgraph import ColorMap

from ..core.spectrogram import SpectrogramResult


class SpectrogramColormap(Enum):
    """Available colormaps for spectrogram display."""

    VIRIDIS = "viridis"
    PLASMA = "plasma"
    MAGMA = "magma"
    INFERNO = "inferno"
    GRAYSCALE = "grayscale"
    COOL = "cool"
    HOT = "hot"
    CUBEHELIX = "cubehelix"


# Colormap definitions
COLORMAPS = {
    SpectrogramColormap.VIRIDIS: [
        (0.267004, 0.004874, 0.329415),
        (0.282327, 0.140926, 0.457517),
        (0.253935, 0.265254, 0.529983),
        (0.206756, 0.371758, 0.553117),
        (0.163625, 0.471133, 0.558148),
        (0.127568, 0.566949, 0.550556),
        (0.134692, 0.658636, 0.517649),
        (0.266941, 0.748751, 0.440573),
        (0.477504, 0.821444, 0.318195),
        (0.741388, 0.873449, 0.149561),
        (0.993248, 0.906157, 0.143936),
    ],
    SpectrogramColormap.PLASMA: [
        (0.050383, 0.029803, 0.527975),
        (0.254627, 0.013882, 0.615419),
        (0.417642, 0.000564, 0.658390),
        (0.562738, 0.051545, 0.641509),
        (0.692840, 0.165141, 0.564522),
        (0.798216, 0.280197, 0.469538),
        (0.881443, 0.392529, 0.383229),
        (0.949217, 0.517763, 0.295662),
        (0.988260, 0.652325, 0.211364),
        (0.988648, 0.809579, 0.145357),
        (0.940015, 0.975158, 0.131326),
    ],
    SpectrogramColormap.MAGMA: [
        (0.001462, 0.000466, 0.013866),
        (0.078815, 0.054184, 0.211667),
        (0.232077, 0.059889, 0.437695),
        (0.390384, 0.100379, 0.501864),
        (0.550287, 0.161158, 0.505719),
        (0.716387, 0.214982, 0.474625),
        (0.868793, 0.287728, 0.409303),
        (0.967671, 0.439703, 0.359630),
        (0.994738, 0.624350, 0.427397),
        (0.996898, 0.812403, 0.567105),
        (0.987053, 0.991438, 0.749504),
    ],
    SpectrogramColormap.INFERNO: [
        (0.001462, 0.000466, 0.013866),
        (0.087411, 0.044556, 0.224813),
        (0.258234, 0.038571, 0.406152),
        (0.416331, 0.090834, 0.432943),
        (0.578304, 0.148039, 0.404411),
        (0.735683, 0.215906, 0.330245),
        (0.865006, 0.316822, 0.226055),
        (0.954506, 0.468744, 0.099874),
        (0.987622, 0.645320, 0.039886),
        (0.964894, 0.843848, 0.273391),
        (0.988362, 0.998364, 0.644924),
    ],
    SpectrogramColormap.GRAYSCALE: [
        (0.0, 0.0, 0.0),
        (0.1, 0.1, 0.1),
        (0.2, 0.2, 0.2),
        (0.3, 0.3, 0.3),
        (0.4, 0.4, 0.4),
        (0.5, 0.5, 0.5),
        (0.6, 0.6, 0.6),
        (0.7, 0.7, 0.7),
        (0.8, 0.8, 0.8),
        (0.9, 0.9, 0.9),
        (1.0, 1.0, 1.0),
    ],
    SpectrogramColormap.COOL: [
        (0.0, 1.0, 1.0),
        (0.1, 0.9, 1.0),
        (0.2, 0.8, 1.0),
        (0.3, 0.7, 1.0),
        (0.4, 0.6, 1.0),
        (0.5, 0.5, 1.0),
        (0.6, 0.4, 1.0),
        (0.7, 0.3, 1.0),
        (0.8, 0.2, 1.0),
        (0.9, 0.1, 1.0),
        (1.0, 0.0, 1.0),
    ],
    SpectrogramColormap.HOT: [
        (0.0416, 0.0, 0.0),
        (0.3333, 0.0, 0.0),
        (0.6250, 0.0, 0.0),
        (0.9167, 0.0, 0.0),
        (1.0, 0.2083, 0.0),
        (1.0, 0.5000, 0.0),
        (1.0, 0.7917, 0.0),
        (1.0, 1.0, 0.0833),
        (1.0, 1.0, 0.3750),
        (1.0, 1.0, 0.6667),
        (1.0, 1.0, 1.0),
    ],
    SpectrogramColormap.CUBEHELIX: [
        (0.0, 0.0, 0.0),
        (0.107, 0.063, 0.165),
        (0.123, 0.171, 0.288),
        (0.094, 0.308, 0.312),
        (0.123, 0.434, 0.258),
        (0.273, 0.510, 0.196),
        (0.517, 0.534, 0.227),
        (0.763, 0.540, 0.396),
        (0.904, 0.583, 0.637),
        (0.929, 0.704, 0.864),
        (1.0, 1.0, 1.0),
    ],
}


def get_colormap(name: SpectrogramColormap) -> ColorMap:
    """Get a pyqtgraph ColorMap from the predefined colormaps."""
    colors = COLORMAPS.get(name, COLORMAPS[SpectrogramColormap.VIRIDIS])
    positions = np.linspace(0, 1, len(colors))
    colors_255 = [(int(r * 255), int(g * 255), int(b * 255)) for r, g, b in colors]
    return ColorMap(positions, colors_255)


class SpectrogramWidget(QWidget):
    """
    Interactive spectrogram visualization widget.

    Features:
    - Multiple colormap options
    - Time-frequency selection
    - Synchronized navigation
    - Brightness/contrast adjustment
    - Frequency range display
    - Auto-scroll to keep playhead visible
    - Click-to-seek
    """

    # Signals
    view_range_changed = pyqtSignal(float, float)  # start_time, end_time
    selection_created = pyqtSignal(float, float, float, float)  # start, end, low_freq, high_freq
    cursor_moved = pyqtSignal(float, float)  # time, frequency
    seek_requested = pyqtSignal(float)  # time position for seeking

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._spectrogram_result: Optional[SpectrogramResult] = None
        self._selections: List = []
        self._selection_items: List[pg.RectROI] = []
        self._colormap = SpectrogramColormap.VIRIDIS

        # Selection state
        self._is_selecting = False
        self._selection_start: Optional[Tuple[float, float]] = None

        # Display settings
        self._brightness = 0.0
        self._contrast = 1.0

        # Playback state
        self._auto_scroll = True
        self._is_playing = False
        self._playback_position: float = 0.0

        self._setup_ui()
        self._setup_interactions()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Configure pyqtgraph
        pg.setConfigOptions(antialias=True)

        # Create plot widget
        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setBackground("#1e1e1e")

        # Configure axes
        self._plot_widget.setLabel("bottom", "Time", units="s")
        self._plot_widget.setLabel("left", "Frequency", units="Hz")

        # Style axes
        axis_pen = pg.mkPen(color="#808080", width=1)
        for axis in ["left", "bottom"]:
            self._plot_widget.getAxis(axis).setPen(axis_pen)
            self._plot_widget.getAxis(axis).setTextPen(axis_pen)

        layout.addWidget(self._plot_widget)

        # Create image item for spectrogram
        self._image_item = pg.ImageItem()
        self._plot_widget.addItem(self._image_item)

        # Apply default colormap
        self._apply_colormap()

        # Playback position line
        self._playback_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color="#ff5722", width=2),
            movable=False,
        )
        self._playback_line.setVisible(False)
        self._plot_widget.addItem(self._playback_line)

        # Cursor crosshairs
        self._cursor_h = pg.InfiniteLine(
            angle=0,
            pen=pg.mkPen(color="#ffd54f", width=1, style=Qt.PenStyle.DashLine),
            movable=False,
        )
        self._cursor_v = pg.InfiniteLine(
            angle=90,
            pen=pg.mkPen(color="#ffd54f", width=1, style=Qt.PenStyle.DashLine),
            movable=False,
        )
        self._cursor_h.setVisible(False)
        self._cursor_v.setVisible(False)
        self._plot_widget.addItem(self._cursor_h)
        self._plot_widget.addItem(self._cursor_v)

        # Current selection ROI
        self._current_selection = pg.RectROI(
            [0, 0],
            [0, 0],
            pen=pg.mkPen(color="#4e9a06", width=2),
            movable=False,
            resizable=False,
        )
        self._current_selection.setVisible(False)
        self._plot_widget.addItem(self._current_selection)

        # Add colorbar
        self._colorbar = pg.ColorBarItem(
            values=(-80, 0),
            colorMap=get_colormap(self._colormap),
            label="Power (dB)",
        )
        self._colorbar.setImageItem(self._image_item)

    def _setup_interactions(self):
        """Set up mouse interactions."""
        self._plot_widget.sigRangeChanged.connect(self._on_range_changed)
        self._plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)
        self._plot_widget.scene().sigMouseClicked.connect(self._on_mouse_clicked)

    def _apply_colormap(self):
        """Apply the current colormap to the image."""
        cmap = get_colormap(self._colormap)
        lut = cmap.getLookupTable(nPts=256)
        self._image_item.setLookupTable(lut)

    def set_colormap(self, colormap: SpectrogramColormap):
        """Set the colormap for display."""
        self._colormap = colormap
        self._apply_colormap()

    def set_spectrogram(self, result: SpectrogramResult):
        """
        Set the spectrogram data to display.

        Args:
            result: SpectrogramResult from spectrogram computation.
        """
        self._spectrogram_result = result

        # Apply brightness/contrast adjustment
        data = result.spectrogram.copy()
        data = (data + self._brightness) * self._contrast

        # Set image data
        self._image_item.setImage(data.T)  # Transpose for correct orientation

        # Calculate transform for proper axis scaling
        # Image needs to be scaled to match time and frequency axes
        times = result.times
        freqs = result.frequencies

        if len(times) > 1 and len(freqs) > 1:
            time_scale = times[-1] / len(times)
            freq_scale = freqs[-1] / len(freqs)

            transform = pg.QtGui.QTransform()
            transform.scale(time_scale, freq_scale)
            self._image_item.setTransform(transform)

        # Set axis ranges
        self._plot_widget.setXRange(0, times[-1] if len(times) > 0 else 1, padding=0)
        self._plot_widget.setYRange(0, freqs[-1] if len(freqs) > 0 else 22050, padding=0)

    def set_view_range(self, start_time: float, end_time: float):
        """Set the visible time range."""
        self._plot_widget.setXRange(start_time, end_time, padding=0)

    def get_view_range(self) -> Tuple[float, float]:
        """Get the current visible time range."""
        view_range = self._plot_widget.viewRange()
        return view_range[0][0], view_range[0][1]

    def set_frequency_range(self, low_freq: float, high_freq: float):
        """Set the visible frequency range."""
        self._plot_widget.setYRange(low_freq, high_freq, padding=0)

    def set_playback_position(self, position: float):
        """Set the playback position indicator."""
        self._playback_position = position
        self._playback_line.setPos(position)
        self._playback_line.setVisible(True)

        # Auto-scroll to keep playhead visible
        if self._auto_scroll and self._is_playing and self._spectrogram_result:
            view_range = self._plot_widget.viewRange()[0]
            view_start, view_end = view_range[0], view_range[1]
            view_width = view_end - view_start
            duration = self._spectrogram_result.duration

            # Scroll if playhead is near the right edge (within 10% of view width)
            scroll_threshold = view_end - (view_width * 0.1)
            if position > scroll_threshold:
                # Scroll so playhead is at 20% from left
                new_start = position - (view_width * 0.2)
                new_end = new_start + view_width
                # Don't scroll past the end
                if new_end <= duration:
                    self._plot_widget.setXRange(new_start, new_end, padding=0)

    def clear_playback_position(self):
        """Hide the playback position indicator."""
        self._playback_line.setVisible(False)
        self._is_playing = False

    def set_playing(self, playing: bool):
        """Set the playing state for auto-scroll behavior."""
        self._is_playing = playing

    def set_auto_scroll(self, enabled: bool):
        """Enable or disable auto-scroll during playback."""
        self._auto_scroll = enabled

    def is_auto_scroll_enabled(self) -> bool:
        """Check if auto-scroll is enabled."""
        return self._auto_scroll

    def set_selections(self, selections: List):
        """
        Set the selections to display.

        Args:
            selections: List of Selection objects.
        """
        # Remove existing selection items
        for item in self._selection_items:
            self._plot_widget.removeItem(item)
        self._selection_items.clear()

        self._selections = selections

        # Add new selection rectangles
        for sel in selections:
            if sel.low_freq is not None and sel.high_freq is not None:
                rect = pg.RectROI(
                    [sel.begin_time, sel.low_freq],
                    [sel.duration, sel.bandwidth],
                    pen=pg.mkPen(color="#4e9a06", width=2),
                    movable=False,
                    resizable=False,
                )
                # Make it semi-transparent
                rect.setBrush(pg.mkBrush(color=(78, 154, 6, 50)))
                self._plot_widget.addItem(rect)
                self._selection_items.append(rect)

    def set_brightness(self, value: float):
        """Set brightness adjustment (-1 to 1)."""
        self._brightness = value * 40  # Scale to dB range
        if self._spectrogram_result:
            self.set_spectrogram(self._spectrogram_result)

    def set_contrast(self, value: float):
        """Set contrast adjustment (0.5 to 2.0)."""
        self._contrast = value
        if self._spectrogram_result:
            self.set_spectrogram(self._spectrogram_result)

    def zoom_in(self):
        """Zoom in on the center of the current view."""
        x_range = self._plot_widget.viewRange()[0]
        center = (x_range[0] + x_range[1]) / 2
        width = (x_range[1] - x_range[0]) / 2
        self._plot_widget.setXRange(center - width / 2, center + width / 2, padding=0)

    def zoom_out(self):
        """Zoom out from the center."""
        if self._spectrogram_result is None:
            return
        x_range = self._plot_widget.viewRange()[0]
        center = (x_range[0] + x_range[1]) / 2
        width = (x_range[1] - x_range[0]) * 2
        duration = self._spectrogram_result.duration
        new_start = max(0, center - width / 2)
        new_end = min(duration, center + width / 2)
        self._plot_widget.setXRange(new_start, new_end, padding=0)

    def zoom_fit(self):
        """Zoom to show all data."""
        if self._spectrogram_result:
            self._plot_widget.setXRange(0, self._spectrogram_result.duration, padding=0.02)
            max_freq = self._spectrogram_result.frequencies[-1]
            self._plot_widget.setYRange(0, max_freq, padding=0)

    def _on_range_changed(self):
        """Handle view range changes."""
        x_range = self._plot_widget.viewRange()[0]
        self.view_range_changed.emit(x_range[0], x_range[1])

    def _on_mouse_moved(self, pos):
        """Handle mouse movement."""
        if self._spectrogram_result is None:
            return

        mouse_point = self._plot_widget.plotItem.vb.mapSceneToView(pos)
        x, y = mouse_point.x(), mouse_point.y()

        max_time = self._spectrogram_result.duration
        max_freq = self._spectrogram_result.frequencies[-1]

        if 0 <= x <= max_time and 0 <= y <= max_freq:
            self._cursor_v.setPos(x)
            self._cursor_h.setPos(y)
            self._cursor_v.setVisible(True)
            self._cursor_h.setVisible(True)
            self.cursor_moved.emit(x, y)

            # Update selection during drag
            if self._is_selecting and self._selection_start is not None:
                start_x, start_y = self._selection_start
                width = abs(x - start_x)
                height = abs(y - start_y)
                pos_x = min(start_x, x)
                pos_y = min(start_y, y)
                self._current_selection.setPos([pos_x, pos_y])
                self._current_selection.setSize([width, height])
        else:
            self._cursor_v.setVisible(False)
            self._cursor_h.setVisible(False)

    def _on_mouse_clicked(self, event):
        """Handle mouse clicks for selection."""
        if self._spectrogram_result is None:
            return

        pos = event.scenePos()
        mouse_point = self._plot_widget.plotItem.vb.mapSceneToView(pos)
        x, y = mouse_point.x(), mouse_point.y()

        max_time = self._spectrogram_result.duration
        max_freq = self._spectrogram_result.frequencies[-1]

        if not (0 <= x <= max_time and 0 <= y <= max_freq):
            return

        modifiers = event.modifiers()

        if event.button() == Qt.MouseButton.LeftButton:
            if modifiers == Qt.KeyboardModifier.ShiftModifier:
                if not self._is_selecting:
                    # Start selection
                    self._selection_start = (x, y)
                    self._is_selecting = True
                    self._current_selection.setPos([x, y])
                    self._current_selection.setSize([0, 0])
                    self._current_selection.setVisible(True)
                else:
                    # Complete selection
                    start_x, start_y = self._selection_start
                    end_x, end_y = x, y

                    # Normalize coordinates
                    x1, x2 = min(start_x, end_x), max(start_x, end_x)
                    y1, y2 = min(start_y, end_y), max(start_y, end_y)

                    self._is_selecting = False
                    self._current_selection.setVisible(False)
                    self._selection_start = None

                    # Emit selection if large enough
                    if x2 - x1 > 0.001 and y2 - y1 > 10:  # Min 1ms, 10Hz
                        self.selection_created.emit(x1, x2, y1, y2)

            elif modifiers == Qt.KeyboardModifier.ControlModifier:
                # Ctrl+Click to seek to position
                self.seek_requested.emit(x)

    def export_image(self, filepath: str):
        """Export the current view as an image."""
        exporter = pg.exporters.ImageExporter(self._plot_widget.plotItem)
        exporter.export(filepath)
