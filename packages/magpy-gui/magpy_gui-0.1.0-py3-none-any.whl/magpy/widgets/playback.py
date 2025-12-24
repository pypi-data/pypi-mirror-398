"""
Playback controls widget for audio playback.

Provides play, pause, stop, and position seeking functionality.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
    QStyle,
    QComboBox,
)

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except (ImportError, OSError):
    sd = None
    SOUNDDEVICE_AVAILABLE = False

from ..core.audio import AudioFile


class PlaybackControls(QWidget):
    """
    Audio playback control widget.

    Features:
    - Play, pause, stop buttons
    - Position slider with seeking
    - Time display
    - Playback rate control
    - Loop mode
    """

    # Signals
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    position_changed = pyqtSignal(float)  # position in seconds
    _stream_finished = pyqtSignal()  # internal signal for thread-safe callback

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._audio: Optional[AudioFile] = None
        self._duration: float = 0.0
        self._position: float = 0.0
        self._is_playing: bool = False
        self._is_looping: bool = False
        self._playback_rate: float = 1.0

        # Playback stream
        self._stream: Optional[sd.OutputStream] = None
        self._playback_frame: int = 0

        # Timer for position updates
        self._update_timer = QTimer()
        self._update_timer.setInterval(50)  # 20 updates/second
        self._update_timer.timeout.connect(self._update_position)

        # Connect internal signal for thread-safe stream finished handling
        self._stream_finished.connect(self._handle_stream_finished)

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Play/Pause button
        self._play_btn = QPushButton()
        self._play_btn.setFixedSize(36, 36)
        self._play_btn.setToolTip("Play (Space)")
        self._update_play_button_icon()
        layout.addWidget(self._play_btn)

        # Stop button
        self._stop_btn = QPushButton()
        self._stop_btn.setFixedSize(36, 36)
        self._stop_btn.setToolTip("Stop")
        self._stop_btn.setText("■")
        layout.addWidget(self._stop_btn)

        layout.addSpacing(8)

        # Current time label
        self._time_label = QLabel("00:00.000")
        self._time_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        self._time_label.setMinimumWidth(80)
        layout.addWidget(self._time_label)

        # Position slider
        self._position_slider = QSlider(Qt.Orientation.Horizontal)
        self._position_slider.setRange(0, 1000)
        self._position_slider.setValue(0)
        self._position_slider.setStyleSheet(
            """
            QSlider::groove:horizontal {
                height: 6px;
                background-color: #3c3c3c;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #0e639c;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background-color: #1177bb;
            }
            QSlider::sub-page:horizontal {
                background-color: #0e639c;
                border-radius: 3px;
            }
            """
        )
        layout.addWidget(self._position_slider, stretch=1)

        # Duration label
        self._duration_label = QLabel("00:00.000")
        self._duration_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        self._duration_label.setMinimumWidth(80)
        layout.addWidget(self._duration_label)

        layout.addSpacing(8)

        # Loop button
        self._loop_btn = QPushButton("🔁")
        self._loop_btn.setFixedSize(36, 36)
        self._loop_btn.setCheckable(True)
        self._loop_btn.setToolTip("Loop")
        layout.addWidget(self._loop_btn)

        # Playback rate selector
        self._rate_combo = QComboBox()
        self._rate_combo.addItems(["0.25x", "0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self._rate_combo.setCurrentText("1.0x")
        self._rate_combo.setFixedWidth(70)
        self._rate_combo.setToolTip("Playback speed")
        layout.addWidget(self._rate_combo)

    def _setup_connections(self):
        """Set up signal connections."""
        self._play_btn.clicked.connect(self._toggle_playback)
        self._stop_btn.clicked.connect(self.stop)
        self._position_slider.sliderPressed.connect(self._on_slider_pressed)
        self._position_slider.sliderReleased.connect(self._on_slider_released)
        self._position_slider.valueChanged.connect(self._on_slider_changed)
        self._loop_btn.toggled.connect(self._on_loop_toggled)
        self._rate_combo.currentTextChanged.connect(self._on_rate_changed)

    def _update_play_button_icon(self):
        """Update play button icon based on state."""
        if self._is_playing:
            self._play_btn.setText("⏸")  # Pause icon
            self._play_btn.setToolTip("Pause (Space)")
        else:
            self._play_btn.setText("▶")  # Play icon
            self._play_btn.setToolTip("Play (Space)")

    def set_audio(self, audio: AudioFile):
        """Set the audio file for playback."""
        self._audio = audio
        self._duration = audio.duration
        self._position = 0.0
        self._playback_frame = 0
        self._update_display()

    def set_duration(self, duration: float):
        """Set the total duration."""
        self._duration = duration
        self._update_display()

    def _format_time(self, seconds: float) -> str:
        """Format time as MM:SS.mmm."""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes:02d}:{secs:06.3f}"

    def _update_display(self):
        """Update time display and slider."""
        self._time_label.setText(self._format_time(self._position))
        self._duration_label.setText(self._format_time(self._duration))

        if self._duration > 0:
            slider_value = int((self._position / self._duration) * 1000)
            self._position_slider.blockSignals(True)
            self._position_slider.setValue(slider_value)
            self._position_slider.blockSignals(False)

    def _toggle_playback(self):
        """Toggle between play and pause."""
        if self._is_playing:
            self.pause()
        else:
            self.play()

    def play(self):
        """Start playback."""
        if not SOUNDDEVICE_AVAILABLE or self._audio is None:
            return

        if self._is_playing:
            return

        self._is_playing = True
        self._update_play_button_icon()
        self.play_clicked.emit()

        # Start audio stream
        self._start_stream()
        self._update_timer.start()

    def pause(self):
        """Pause playback."""
        if not self._is_playing:
            return

        self._is_playing = False
        self._update_play_button_icon()
        self.pause_clicked.emit()

        # Stop stream but remember position
        self._stop_stream()
        self._update_timer.stop()

    def stop(self):
        """Stop playback and reset position."""
        self._is_playing = False
        self._position = 0.0
        self._playback_frame = 0
        self._update_play_button_icon()
        self._update_display()
        self.stop_clicked.emit()
        self.position_changed.emit(0.0)

        self._stop_stream()
        self._update_timer.stop()

    def _start_stream(self):
        """Start the audio output stream."""
        if self._audio is None:
            return

        sample_rate = int(self._audio.sample_rate * self._playback_rate)

        def callback(outdata, frames, time_info, status):
            """Audio callback for streaming playback."""
            if self._audio is None or self._audio.data is None:
                outdata.fill(0)
                return

            start = self._playback_frame
            end = start + frames

            if end >= len(self._audio.data):
                # End of audio
                remaining = len(self._audio.data) - start
                if remaining > 0:
                    outdata[:remaining] = self._audio.data[start:, :outdata.shape[1]]
                    outdata[remaining:] = 0
                else:
                    outdata.fill(0)

                if self._is_looping:
                    self._playback_frame = 0
                else:
                    # Signal to stop
                    raise sd.CallbackStop()
            else:
                outdata[:] = self._audio.data[start:end, :outdata.shape[1]]

            self._playback_frame = end

        try:
            self._stream = sd.OutputStream(
                samplerate=sample_rate,
                channels=min(2, self._audio.num_channels),
                callback=callback,
                finished_callback=self._on_stream_finished,
            )
            self._stream.start()
        except Exception as e:
            print(f"Failed to start audio stream: {e}")
            self._is_playing = False
            self._update_play_button_icon()

    def _stop_stream(self):
        """Stop the audio output stream."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _on_stream_finished(self):
        """Handle stream completion (called from audio thread)."""
        # Emit signal to handle in main thread
        self._stream_finished.emit()

    def _handle_stream_finished(self):
        """Handle stream completion in the main thread."""
        if not self._is_looping:
            self._is_playing = False
            self._update_play_button_icon()
            self._update_timer.stop()

    def _update_position(self):
        """Update position from playback frame."""
        if self._audio is not None and self._audio.sample_rate > 0:
            self._position = self._playback_frame / self._audio.sample_rate
            self._update_display()
            self.position_changed.emit(self._position)

    def _on_slider_pressed(self):
        """Handle slider press (pause updates during seeking)."""
        self._update_timer.stop()

    def _on_slider_released(self):
        """Handle slider release (seek to position)."""
        if self._duration > 0:
            self._position = (self._position_slider.value() / 1000) * self._duration
            if self._audio is not None:
                self._playback_frame = int(self._position * self._audio.sample_rate)
            self._update_display()
            self.position_changed.emit(self._position)

            # Restart stream if was playing
            if self._is_playing:
                self._stop_stream()
                self._start_stream()
                self._update_timer.start()

    def _on_slider_changed(self, value: int):
        """Handle slider value changes during drag."""
        if self._position_slider.isSliderDown() and self._duration > 0:
            pos = (value / 1000) * self._duration
            self._time_label.setText(self._format_time(pos))

    def _on_loop_toggled(self, checked: bool):
        """Handle loop button toggle."""
        self._is_looping = checked

    def _on_rate_changed(self, rate_text: str):
        """Handle playback rate change."""
        rate = float(rate_text.rstrip("x"))
        self._playback_rate = rate

        # Restart stream with new rate if playing
        if self._is_playing:
            self._stop_stream()
            self._start_stream()

    def seek_to(self, position: float):
        """Seek to a specific position in seconds."""
        self._position = max(0, min(position, self._duration))
        if self._audio is not None:
            self._playback_frame = int(self._position * self._audio.sample_rate)
        self._update_display()
        self.position_changed.emit(self._position)

        if self._is_playing:
            self._stop_stream()
            self._start_stream()
