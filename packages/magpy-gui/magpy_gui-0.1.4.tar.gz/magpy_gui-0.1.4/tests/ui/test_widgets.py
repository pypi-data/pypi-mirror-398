"""Tests for UI widgets."""

import numpy as np
import pytest

# Skip all tests if PyQt6 is not available or no display
pytest.importorskip("PyQt6")


@pytest.fixture
def qapp():
    """Create a QApplication for testing."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def sample_audio():
    """Generate sample audio data for testing."""
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    data = np.sin(2 * np.pi * 440 * t)
    return data, sample_rate


class TestWaveformWidget:
    """Tests for WaveformWidget."""

    def test_create_widget(self, qapp):
        """Test creating a waveform widget."""
        from magpy.ui.widgets import WaveformWidget

        widget = WaveformWidget()
        assert widget is not None

    def test_set_audio(self, qapp, sample_audio):
        """Test setting audio data."""
        from magpy.ui.widgets import WaveformWidget

        data, sample_rate = sample_audio
        widget = WaveformWidget()
        widget.set_audio(data, sample_rate)

        # Widget should have duration set
        assert widget._duration == pytest.approx(1.0, rel=0.01)

    def test_zoom_operations(self, qapp, sample_audio):
        """Test zoom operations."""
        from magpy.ui.widgets import WaveformWidget

        data, sample_rate = sample_audio
        widget = WaveformWidget()
        widget.set_audio(data, sample_rate)

        # Get initial range
        start, end = widget.get_view_range()

        # Zoom in
        widget.zoom_in()
        new_start, new_end = widget.get_view_range()
        assert new_end - new_start < end - start

        # Zoom fit
        widget.zoom_fit()
        fit_start, fit_end = widget.get_view_range()
        assert fit_end >= 0.9  # Should show most of the audio

    def test_set_view_range(self, qapp, sample_audio):
        """Test setting view range."""
        from magpy.ui.widgets import WaveformWidget

        data, sample_rate = sample_audio
        widget = WaveformWidget()
        widget.set_audio(data, sample_rate)

        widget.set_view_range(0.2, 0.8)
        start, end = widget.get_view_range()

        assert start == pytest.approx(0.2, abs=0.01)
        assert end == pytest.approx(0.8, abs=0.01)

    def test_playback_position(self, qapp, sample_audio):
        """Test playback position indicator."""
        from magpy.ui.widgets import WaveformWidget

        data, sample_rate = sample_audio
        widget = WaveformWidget()
        widget.set_audio(data, sample_rate)

        widget.set_playback_position(0.5)
        assert widget._playback_line.isVisible()

        widget.clear_playback_position()
        assert not widget._playback_line.isVisible()


class TestSpectrogramWidget:
    """Tests for SpectrogramWidget."""

    def test_create_widget(self, qapp):
        """Test creating a spectrogram widget."""
        from magpy.ui.widgets import SpectrogramWidget

        widget = SpectrogramWidget()
        assert widget is not None

    def test_set_spectrogram(self, qapp, sample_audio):
        """Test setting spectrogram data."""
        from magpy.ui.widgets import SpectrogramWidget
        from magpy.core import SpectrogramGenerator

        data, sample_rate = sample_audio
        generator = SpectrogramGenerator()
        result = generator.compute(data, sample_rate)

        widget = SpectrogramWidget()
        widget.set_spectrogram(result)

        assert widget._spectrogram_result is not None

    def test_colormap_change(self, qapp):
        """Test changing colormap."""
        from magpy.ui.widgets.spectrogram import SpectrogramWidget, SpectrogramColormap

        widget = SpectrogramWidget()

        for cmap in SpectrogramColormap:
            widget.set_colormap(cmap)
            assert widget._colormap == cmap

    def test_brightness_contrast(self, qapp, sample_audio):
        """Test brightness and contrast adjustment."""
        from magpy.ui.widgets import SpectrogramWidget
        from magpy.core import SpectrogramGenerator

        data, sample_rate = sample_audio
        generator = SpectrogramGenerator()
        result = generator.compute(data, sample_rate)

        widget = SpectrogramWidget()
        widget.set_spectrogram(result)

        # Adjust brightness and contrast
        widget.set_brightness(0.5)
        widget.set_contrast(1.5)

        assert widget._brightness != 0
        assert widget._contrast == 1.5


class TestSelectionTableWidget:
    """Tests for SelectionTableWidget."""

    def test_create_widget(self, qapp):
        """Test creating a selection table widget."""
        from magpy.ui.widgets import SelectionTableWidget

        widget = SelectionTableWidget()
        assert widget is not None

    def test_set_selection_table(self, qapp):
        """Test setting selection table."""
        from magpy.ui.widgets import SelectionTableWidget
        from magpy.core import Selection, SelectionTable

        table = SelectionTable("Test")
        table.add(Selection(begin_time=0, end_time=1))
        table.add(Selection(begin_time=1, end_time=2))

        widget = SelectionTableWidget()
        widget.set_selection_table(table)

        assert widget._table.rowCount() == 2

    def test_filter_table(self, qapp):
        """Test filtering selections."""
        from magpy.ui.widgets import SelectionTableWidget
        from magpy.core import Selection, SelectionTable

        table = SelectionTable("Test")
        sel1 = Selection(begin_time=0, end_time=1)
        sel1.annotations["Species"] = "Bird"
        sel2 = Selection(begin_time=1, end_time=2)
        sel2.annotations["Species"] = "Whale"
        table.add(sel1)
        table.add(sel2)

        widget = SelectionTableWidget()
        widget.set_selection_table(table)

        # Filter by "Bird"
        widget._filter_table("Bird")

        # Count visible rows
        visible = sum(
            1 for row in range(widget._table.rowCount())
            if not widget._table.isRowHidden(row)
        )
        assert visible == 1


class TestPlaybackControls:
    """Tests for PlaybackControls."""

    def test_create_widget(self, qapp):
        """Test creating playback controls."""
        from magpy.ui.widgets import PlaybackControls

        widget = PlaybackControls()
        assert widget is not None

    def test_set_duration(self, qapp):
        """Test setting duration."""
        from magpy.ui.widgets import PlaybackControls

        widget = PlaybackControls()
        widget.set_duration(60.5)

        assert widget._duration == 60.5
        assert "01:00" in widget._duration_label.text()

    def test_time_formatting(self, qapp):
        """Test time formatting."""
        from magpy.ui.widgets import PlaybackControls

        widget = PlaybackControls()

        # Test various time formats
        assert widget._format_time(0) == "00:00.000"
        assert widget._format_time(1.5) == "00:01.500"
        assert widget._format_time(65.123) == "01:05.123"
        assert widget._format_time(3661.5) == "61:01.500"

    def test_seek_to(self, qapp, sample_audio):
        """Test seeking to position."""
        from magpy.ui.widgets import PlaybackControls
        from magpy.core import AudioFile

        data, sample_rate = sample_audio
        audio = AudioFile.from_array(data, sample_rate)

        widget = PlaybackControls()
        widget.set_audio(audio)
        widget.seek_to(0.5)

        assert widget._position == pytest.approx(0.5, abs=0.01)


class TestMainWindow:
    """Tests for MainWindow."""

    def test_create_window(self, qapp):
        """Test creating main window."""
        from magpy.ui import MainWindow

        window = MainWindow()
        assert window is not None
        assert window.windowTitle() == "MagPy - Bioacoustics Analysis"

    def test_window_has_components(self, qapp):
        """Test window has all expected components."""
        from magpy.ui import MainWindow

        window = MainWindow()

        # Check key components exist
        assert window._waveform is not None
        assert window._spectrogram is not None
        assert window._selection_table_widget is not None
        assert window._playback is not None

    def test_menu_bar(self, qapp):
        """Test menu bar exists."""
        from magpy.ui import MainWindow

        window = MainWindow()
        menubar = window.menuBar()

        assert menubar is not None
        # Check menus exist
        actions = [action.text() for action in menubar.actions()]
        assert any("File" in a for a in actions)
        assert any("Edit" in a for a in actions)
        assert any("View" in a for a in actions)
