"""
Properties panel widget for displaying audio file and selection properties.

Shows metadata about the currently loaded audio file and selected region.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QGroupBox,
    QScrollArea,
)

from ..core.audio import AudioFile, AudioMetadata
from ..core.selection import Selection


class PropertiesPanel(QWidget):
    """
    Panel displaying audio file and selection properties.

    Shows file metadata (duration, sample rate, channels, bit depth, format)
    and selection details when a region is selected.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._audio: Optional[AudioFile] = None
        self._selection: Optional[Selection] = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # File properties group
        self._file_group = QGroupBox("File Properties")
        file_layout = QFormLayout(self._file_group)
        file_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        file_layout.setSpacing(6)

        self._filename_label = QLabel("-")
        self._filename_label.setWordWrap(True)
        file_layout.addRow("Filename:", self._filename_label)

        self._path_label = QLabel("-")
        self._path_label.setWordWrap(True)
        self._path_label.setStyleSheet("color: #808080; font-size: 11px;")
        file_layout.addRow("Path:", self._path_label)

        self._duration_label = QLabel("-")
        file_layout.addRow("Duration:", self._duration_label)

        self._sample_rate_label = QLabel("-")
        file_layout.addRow("Sample Rate:", self._sample_rate_label)

        self._channels_label = QLabel("-")
        file_layout.addRow("Channels:", self._channels_label)

        self._bit_depth_label = QLabel("-")
        file_layout.addRow("Bit Depth:", self._bit_depth_label)

        self._format_label = QLabel("-")
        file_layout.addRow("Format:", self._format_label)

        self._file_size_label = QLabel("-")
        file_layout.addRow("File Size:", self._file_size_label)

        content_layout.addWidget(self._file_group)

        # Selection properties group
        self._selection_group = QGroupBox("Selection Properties")
        selection_layout = QFormLayout(self._selection_group)
        selection_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        selection_layout.setSpacing(6)

        self._sel_start_label = QLabel("-")
        selection_layout.addRow("Start Time:", self._sel_start_label)

        self._sel_end_label = QLabel("-")
        selection_layout.addRow("End Time:", self._sel_end_label)

        self._sel_duration_label = QLabel("-")
        selection_layout.addRow("Duration:", self._sel_duration_label)

        self._sel_low_freq_label = QLabel("-")
        selection_layout.addRow("Low Freq:", self._sel_low_freq_label)

        self._sel_high_freq_label = QLabel("-")
        selection_layout.addRow("High Freq:", self._sel_high_freq_label)

        self._sel_bandwidth_label = QLabel("-")
        selection_layout.addRow("Bandwidth:", self._sel_bandwidth_label)

        self._sel_channel_label = QLabel("-")
        selection_layout.addRow("Channel:", self._sel_channel_label)

        content_layout.addWidget(self._selection_group)

        # Add stretch at end
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Apply styling
        self._apply_style()

    def _apply_style(self):
        """Apply panel styling."""
        self.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: #d4d4d4;
            }
            QLabel {
                color: #d4d4d4;
            }
            """
        )

    def set_audio(self, audio: Optional[AudioFile]):
        """
        Set the audio file to display properties for.

        Args:
            audio: AudioFile instance or None to clear.
        """
        self._audio = audio
        self._update_file_properties()

    def set_selection(self, selection: Optional[Selection]):
        """
        Set the selection to display properties for.

        Args:
            selection: Selection instance or None to clear.
        """
        self._selection = selection
        self._update_selection_properties()

    def _update_file_properties(self):
        """Update file properties display."""
        if self._audio is None or self._audio.filepath is None:
            self._filename_label.setText("-")
            self._path_label.setText("-")
            self._duration_label.setText("-")
            self._sample_rate_label.setText("-")
            self._channels_label.setText("-")
            self._bit_depth_label.setText("-")
            self._format_label.setText("-")
            self._file_size_label.setText("-")
            return

        filepath = self._audio.filepath

        # Filename
        self._filename_label.setText(filepath.name)

        # Path (parent directory)
        self._path_label.setText(str(filepath.parent))

        # Duration
        duration = self._audio.duration
        self._duration_label.setText(self._format_duration(duration))

        # Sample rate
        self._sample_rate_label.setText(f"{self._audio.sample_rate:,} Hz")

        # Channels
        channels = self._audio.num_channels
        channel_str = "Mono" if channels == 1 else "Stereo" if channels == 2 else f"{channels} channels"
        self._channels_label.setText(channel_str)

        # Bit depth
        metadata = self._audio.metadata
        if metadata and metadata.bit_depth:
            self._bit_depth_label.setText(f"{metadata.bit_depth}-bit")
        else:
            self._bit_depth_label.setText("-")

        # Format
        if metadata:
            self._format_label.setText(f"{metadata.format} ({metadata.subtype})")
        else:
            self._format_label.setText(filepath.suffix.upper().lstrip("."))

        # File size
        try:
            size_bytes = os.path.getsize(filepath)
            self._file_size_label.setText(self._format_file_size(size_bytes))
        except OSError:
            self._file_size_label.setText("-")

    def _update_selection_properties(self):
        """Update selection properties display."""
        if self._selection is None:
            self._sel_start_label.setText("-")
            self._sel_end_label.setText("-")
            self._sel_duration_label.setText("-")
            self._sel_low_freq_label.setText("-")
            self._sel_high_freq_label.setText("-")
            self._sel_bandwidth_label.setText("-")
            self._sel_channel_label.setText("-")
            return

        sel = self._selection

        # Time properties
        self._sel_start_label.setText(f"{sel.begin_time:.4f} s")
        self._sel_end_label.setText(f"{sel.end_time:.4f} s")
        self._sel_duration_label.setText(f"{sel.duration:.4f} s ({sel.duration * 1000:.1f} ms)")

        # Frequency properties
        if sel.low_freq is not None:
            self._sel_low_freq_label.setText(f"{sel.low_freq:.1f} Hz")
        else:
            self._sel_low_freq_label.setText("-")

        if sel.high_freq is not None:
            self._sel_high_freq_label.setText(f"{sel.high_freq:.1f} Hz")
        else:
            self._sel_high_freq_label.setText("-")

        if sel.bandwidth is not None:
            self._sel_bandwidth_label.setText(f"{sel.bandwidth:.1f} Hz")
        else:
            self._sel_bandwidth_label.setText("-")

        # Channel
        self._sel_channel_label.setText(str(sel.channel))

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration as HH:MM:SS.mmm or MM:SS.mmm."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60

        if hours > 0:
            return f"{hours:d}:{minutes:02d}:{secs:06.3f}"
        return f"{minutes:d}:{secs:06.3f}"

    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable form."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def clear(self):
        """Clear all displayed properties."""
        self._audio = None
        self._selection = None
        self._update_file_properties()
        self._update_selection_properties()
