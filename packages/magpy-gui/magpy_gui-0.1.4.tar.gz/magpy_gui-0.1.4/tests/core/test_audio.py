"""Tests for the audio module."""

import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from magpy.core.audio import AudioFile, AudioMetadata


@pytest.fixture
def sample_audio_file():
    """Create a temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        filepath = Path(f.name)

    # Generate a 1-second stereo test signal
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)

    # Left channel: 440 Hz sine wave
    left = np.sin(2 * np.pi * 440 * t)
    # Right channel: 880 Hz sine wave
    right = np.sin(2 * np.pi * 880 * t)

    data = np.column_stack([left, right]).astype(np.float32)
    sf.write(filepath, data, sample_rate)

    yield filepath

    # Cleanup
    filepath.unlink()


@pytest.fixture
def mono_audio_file():
    """Create a temporary mono audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        filepath = Path(f.name)

    sample_rate = 22050
    duration = 0.5
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    data = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
    sf.write(filepath, data, sample_rate)

    yield filepath

    filepath.unlink()


class TestAudioFile:
    """Tests for AudioFile class."""

    def test_load_stereo_file(self, sample_audio_file):
        """Test loading a stereo audio file."""
        audio = AudioFile(sample_audio_file)

        assert audio.filepath == sample_audio_file
        assert audio.sample_rate == 44100
        assert audio.num_channels == 2
        assert audio.num_samples == 44100
        assert abs(audio.duration - 1.0) < 0.01

    def test_load_mono_file(self, mono_audio_file):
        """Test loading a mono audio file."""
        audio = AudioFile(mono_audio_file)

        assert audio.num_channels == 1
        assert audio.sample_rate == 22050
        assert abs(audio.duration - 0.5) < 0.01

    def test_metadata(self, sample_audio_file):
        """Test audio metadata."""
        audio = AudioFile(sample_audio_file)
        meta = audio.metadata

        assert meta is not None
        assert meta.sample_rate == 44100
        assert meta.channels == 2
        assert abs(meta.duration - 1.0) < 0.01
        assert meta.format == "WAV"

    def test_get_channel(self, sample_audio_file):
        """Test extracting individual channels."""
        audio = AudioFile(sample_audio_file)

        left = audio.get_channel(0)
        right = audio.get_channel(1)

        assert len(left) == 44100
        assert len(right) == 44100
        assert left.ndim == 1
        assert right.ndim == 1

    def test_get_time_range(self, sample_audio_file):
        """Test extracting a time range."""
        audio = AudioFile(sample_audio_file)

        segment = audio.get_time_range(0.2, 0.4)

        expected_samples = int(0.2 * 44100)
        assert abs(len(segment) - expected_samples) <= 1
        assert segment.shape[1] == 2  # Both channels

    def test_get_time_range_single_channel(self, sample_audio_file):
        """Test extracting a time range for a single channel."""
        audio = AudioFile(sample_audio_file)

        segment = audio.get_time_range(0.0, 0.1, channel=0)

        assert segment.ndim == 1
        expected_samples = int(0.1 * 44100)
        assert abs(len(segment) - expected_samples) <= 1

    def test_time_sample_conversion(self, sample_audio_file):
        """Test time-sample conversions."""
        audio = AudioFile(sample_audio_file)

        sample = audio.time_to_sample(0.5)
        assert sample == 22050

        time = audio.sample_to_time(22050)
        assert time == 0.5

    def test_from_array(self):
        """Test creating AudioFile from numpy array."""
        sample_rate = 16000
        duration = 0.25
        t = np.linspace(0, duration, int(sample_rate * duration))
        data = np.sin(2 * np.pi * 500 * t).astype(np.float32)

        audio = AudioFile.from_array(data, sample_rate)

        assert audio.sample_rate == sample_rate
        assert audio.num_channels == 1
        assert abs(audio.duration - duration) < 0.01

    def test_save(self, sample_audio_file):
        """Test saving audio to file."""
        audio = AudioFile(sample_audio_file)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = Path(f.name)

        try:
            audio.save(output_path)
            assert output_path.exists()

            # Reload and verify
            audio2 = AudioFile(output_path)
            assert audio2.sample_rate == audio.sample_rate
            assert audio2.num_channels == audio.num_channels
            assert audio2.num_samples == audio.num_samples
        finally:
            output_path.unlink()

    def test_load_nonexistent_file(self):
        """Test error handling for nonexistent files."""
        with pytest.raises(FileNotFoundError):
            AudioFile("/nonexistent/path/audio.wav")

    def test_load_segment(self, sample_audio_file):
        """Test loading a segment of an audio file."""
        audio = AudioFile()
        audio.load_segment(sample_audio_file, 0.25, 0.75)

        assert abs(audio.duration - 0.5) < 0.01
        assert audio.num_channels == 2

    def test_empty_audio_file(self):
        """Test empty AudioFile initialization."""
        audio = AudioFile()

        assert audio.filepath is None
        assert audio.data is None
        assert audio.duration == 0.0
        assert audio.num_channels == 0
        assert audio.num_samples == 0

    def test_repr(self, sample_audio_file):
        """Test string representation."""
        audio = AudioFile(sample_audio_file)
        repr_str = repr(audio)

        assert "AudioFile" in repr_str
        assert "1.00s" in repr_str
        assert "2ch" in repr_str
        assert "44100Hz" in repr_str


class TestAudioMetadata:
    """Tests for AudioMetadata class."""

    def test_duration_str(self):
        """Test duration formatting."""
        meta = AudioMetadata(
            sample_rate=44100,
            channels=2,
            duration=3723.456,  # 1h 2m 3.456s
            frames=164186138,
            format="WAV",
            subtype="PCM_16",
        )

        assert meta.duration_str == "01:02:03.456"

    def test_duration_str_short(self):
        """Test duration formatting for short durations."""
        meta = AudioMetadata(
            sample_rate=44100,
            channels=1,
            duration=5.5,
            frames=242550,
            format="WAV",
            subtype="PCM_16",
        )

        assert meta.duration_str == "00:00:05.500"
