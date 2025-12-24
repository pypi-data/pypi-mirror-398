"""
Waveform visualization widget using pyqtgraph.

Provides interactive waveform display with selection and navigation.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QColor, QPen, QBrush
from PyQt6.QtWidgets import QWidget, QVBoxLayout

import pyqtgraph as pg


class WaveformWidget(QWidget):
    """
    Interactive waveform visualization widget.

    Features:
    - Smooth zooming and panning
    - Selection creation and display
    - Synchronized view with other widgets
    - Playback position indicator
    - Auto-scroll to keep playhead visible
    - Click-to-seek on playhead
    """

    # Signals
    view_range_changed = pyqtSignal(float, float)  # start_time, end_time
    selection_created = pyqtSignal(float, float)  # start_time, end_time
    cursor_moved = pyqtSignal(float)  # time position
    seek_requested = pyqtSignal(float)  # time position for seeking

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._audio_data: Optional[np.ndarray] = None
        self._sample_rate: int = 44100
        self._duration: float = 0.0
        self._selections: List = []
        self._selection_items: List[pg.LinearRegionItem] = []

        # Selection state
        self._is_selecting = False
        self._selection_start: Optional[float] = None

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
        self._plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Configure axes
        self._plot_widget.setLabel("bottom", "Time", units="s")
        self._plot_widget.setLabel("left", "Amplitude")

        # Style axes
        axis_pen = pg.mkPen(color="#808080", width=1)
        for axis in ["left", "bottom"]:
            self._plot_widget.getAxis(axis).setPen(axis_pen)
            self._plot_widget.getAxis(axis).setTextPen(axis_pen)

        layout.addWidget(self._plot_widget)

        # Create waveform plot item
        self._waveform_curve = self._plot_widget.plot(
            [], [],
            pen=pg.mkPen(color="#4fc3f7", width=1),
        )

        # Playback position line
        self._playback_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color="#ff5722", width=2),
            movable=False,
        )
        self._playback_line.setVisible(False)
        self._plot_widget.addItem(self._playback_line)

        # Current selection region (while selecting)
        self._current_selection = pg.LinearRegionItem(
            brush=pg.mkBrush(color=(78, 154, 6, 80)),
            pen=pg.mkPen(color="#4e9a06", width=2),
        )
        self._current_selection.setVisible(False)
        self._plot_widget.addItem(self._current_selection)

        # Crosshair for cursor
        self._cursor_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color="#ffd54f", width=1, style=Qt.PenStyle.DashLine),
            movable=False,
        )
        self._cursor_line.setVisible(False)
        self._plot_widget.addItem(self._cursor_line)

    def _setup_interactions(self):
        """Set up mouse and keyboard interactions."""
        # Connect view range changes
        self._plot_widget.sigRangeChanged.connect(self._on_range_changed)

        # Mouse tracking for cursor
        self._plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)

        # Mouse click for selection
        self._plot_widget.scene().sigMouseClicked.connect(self._on_mouse_clicked)

    def set_audio(self, data: np.ndarray, sample_rate: int):
        """
        Set the audio data to display.

        Args:
            data: Audio samples (1D array).
            sample_rate: Sample rate in Hz.
        """
        self._audio_data = data
        self._sample_rate = sample_rate
        self._duration = len(data) / sample_rate

        # Downsample for display if needed
        display_data, display_times = self._prepare_display_data(data, sample_rate)

        self._waveform_curve.setData(display_times, display_data)

        # Set axis range
        self._plot_widget.setXRange(0, self._duration, padding=0)
        self._plot_widget.setYRange(-1.1, 1.1, padding=0)

    def _prepare_display_data(
        self, data: np.ndarray, sample_rate: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare audio data for efficient display.

        Downsamples long recordings for smooth rendering.
        """
        max_points = 50000  # Maximum points for smooth rendering

        if len(data) <= max_points:
            times = np.arange(len(data)) / sample_rate
            return data, times

        # Downsample using min/max envelope for accuracy
        factor = len(data) // (max_points // 2)
        num_chunks = len(data) // factor

        # Reshape and compute min/max for each chunk
        reshaped = data[: num_chunks * factor].reshape(-1, factor)
        mins = reshaped.min(axis=1)
        maxs = reshaped.max(axis=1)

        # Interleave min and max
        display_data = np.empty(num_chunks * 2, dtype=data.dtype)
        display_data[0::2] = mins
        display_data[1::2] = maxs

        # Generate time values
        chunk_duration = factor / sample_rate
        times = np.repeat(np.arange(num_chunks) * chunk_duration, 2)
        times[1::2] += chunk_duration / 2

        return display_data, times

    def set_view_range(self, start_time: float, end_time: float):
        """Set the visible time range."""
        self._plot_widget.setXRange(start_time, end_time, padding=0)

    def get_view_range(self) -> Tuple[float, float]:
        """Get the current visible time range."""
        view_range = self._plot_widget.viewRange()
        return view_range[0][0], view_range[0][1]

    def set_playback_position(self, position: float):
        """Set the playback position indicator."""
        self._playback_position = position
        self._playback_line.setPos(position)
        self._playback_line.setVisible(True)

        # Auto-scroll to keep playhead visible
        if self._auto_scroll and self._is_playing:
            view_range = self._plot_widget.viewRange()[0]
            view_start, view_end = view_range[0], view_range[1]
            view_width = view_end - view_start

            # Scroll if playhead is near the right edge (within 10% of view width)
            scroll_threshold = view_end - (view_width * 0.1)
            if position > scroll_threshold:
                # Scroll so playhead is at 20% from left
                new_start = position - (view_width * 0.2)
                new_end = new_start + view_width
                # Don't scroll past the end
                if new_end <= self._duration:
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

        # Add new selection items
        for sel in selections:
            region = pg.LinearRegionItem(
                values=[sel.begin_time, sel.end_time],
                brush=pg.mkBrush(color=(78, 154, 6, 50)),
                pen=pg.mkPen(color="#4e9a06", width=1),
                movable=False,
            )
            self._plot_widget.addItem(region)
            self._selection_items.append(region)

    def zoom_in(self):
        """Zoom in on the center of the current view."""
        x_range = self._plot_widget.viewRange()[0]
        center = (x_range[0] + x_range[1]) / 2
        width = (x_range[1] - x_range[0]) / 2
        self._plot_widget.setXRange(center - width / 2, center + width / 2, padding=0)

    def zoom_out(self):
        """Zoom out from the center of the current view."""
        x_range = self._plot_widget.viewRange()[0]
        center = (x_range[0] + x_range[1]) / 2
        width = (x_range[1] - x_range[0]) * 2
        new_start = max(0, center - width / 2)
        new_end = min(self._duration, center + width / 2)
        self._plot_widget.setXRange(new_start, new_end, padding=0)

    def zoom_fit(self):
        """Zoom to show all data."""
        self._plot_widget.setXRange(0, self._duration, padding=0.02)

    def _on_range_changed(self):
        """Handle view range changes."""
        x_range = self._plot_widget.viewRange()[0]
        self.view_range_changed.emit(x_range[0], x_range[1])

    def _on_mouse_moved(self, pos):
        """Handle mouse movement."""
        if self._audio_data is None:
            return

        # Convert scene position to plot coordinates
        mouse_point = self._plot_widget.plotItem.vb.mapSceneToView(pos)
        x = mouse_point.x()

        if 0 <= x <= self._duration:
            self._cursor_line.setPos(x)
            self._cursor_line.setVisible(True)
            self.cursor_moved.emit(x)

            # Update selection if actively selecting
            if self._is_selecting and self._selection_start is not None:
                start = min(self._selection_start, x)
                end = max(self._selection_start, x)
                self._current_selection.setRegion([start, end])
        else:
            self._cursor_line.setVisible(False)

    def _on_mouse_clicked(self, event):
        """Handle mouse clicks."""
        if self._audio_data is None:
            return

        # Get click position
        pos = event.scenePos()
        mouse_point = self._plot_widget.plotItem.vb.mapSceneToView(pos)
        x = mouse_point.x()

        if not (0 <= x <= self._duration):
            return

        modifiers = event.modifiers()

        if event.button() == Qt.MouseButton.LeftButton:
            if modifiers == Qt.KeyboardModifier.ShiftModifier:
                # Shift-click to start/end selection
                if not self._is_selecting:
                    self._selection_start = x
                    self._is_selecting = True
                    self._current_selection.setRegion([x, x])
                    self._current_selection.setVisible(True)
                else:
                    # Complete selection
                    end = x
                    start = min(self._selection_start, end)
                    end = max(self._selection_start, end)
                    self._is_selecting = False
                    self._current_selection.setVisible(False)
                    self._selection_start = None

                    if end - start > 0.001:  # Minimum 1ms selection
                        self.selection_created.emit(start, end)

            elif modifiers == Qt.KeyboardModifier.ControlModifier:
                # Ctrl+Click to seek to position
                self.seek_requested.emit(x)

    def export_image(self, filepath: str):
        """Export the current view as an image."""
        exporter = pg.exporters.ImageExporter(self._plot_widget.plotItem)
        exporter.export(filepath)
