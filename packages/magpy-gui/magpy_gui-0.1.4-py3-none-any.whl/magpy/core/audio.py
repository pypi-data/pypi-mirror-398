"""
Audio file handling module for loading, saving, and manipulating audio data.

Supports WAV, AIFF, FLAC, and MP3 formats with multi-channel support.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import numpy as np
import soundfile as sf


@dataclass
class AudioMetadata:
    """Metadata for an audio file."""

    sample_rate: int
    channels: int
    duration: float
    frames: int
    format: str
    subtype: str
    bit_depth: Optional[int] = None

    @property
    def duration_str(self) -> str:
        """Return duration as a formatted string (HH:MM:SS.mmm)."""
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = self.duration % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"


class AudioFile:
    """
    Represents an audio file with support for reading, writing, and analysis.

    Supports paged reading for large files to avoid memory issues.
    """

    def __init__(self, filepath: Optional[Union[str, Path]] = None):
        """
        Initialize an AudioFile.

        Args:
            filepath: Path to the audio file. If None, creates an empty AudioFile.
        """
        self._filepath: Optional[Path] = None
        self._data: Optional[np.ndarray] = None
        self._sample_rate: int = 44100
        self._metadata: Optional[AudioMetadata] = None

        if filepath is not None:
            self.load(filepath)

    @property
    def filepath(self) -> Optional[Path]:
        """Return the file path."""
        return self._filepath

    @property
    def data(self) -> Optional[np.ndarray]:
        """Return the audio data as numpy array (samples x channels)."""
        return self._data

    @property
    def sample_rate(self) -> int:
        """Return the sample rate in Hz."""
        return self._sample_rate

    @property
    def metadata(self) -> Optional[AudioMetadata]:
        """Return audio metadata."""
        return self._metadata

    @property
    def duration(self) -> float:
        """Return duration in seconds."""
        if self._data is None:
            return 0.0
        return len(self._data) / self._sample_rate

    @property
    def num_channels(self) -> int:
        """Return number of channels."""
        if self._data is None:
            return 0
        if self._data.ndim == 1:
            return 1
        return self._data.shape[1]

    @property
    def num_samples(self) -> int:
        """Return total number of samples."""
        if self._data is None:
            return 0
        return len(self._data)

    def load(self, filepath: Union[str, Path]) -> None:
        """
        Load an audio file.

        Args:
            filepath: Path to the audio file.

        Raises:
            FileNotFoundError: If the file does not exist.
            RuntimeError: If the file cannot be read.
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Audio file not found: {filepath}")

        try:
            self._data, self._sample_rate = sf.read(filepath, dtype="float32")
            info = sf.info(filepath)

            # Ensure data is 2D (samples x channels)
            if self._data.ndim == 1:
                self._data = self._data.reshape(-1, 1)

            # Determine bit depth from subtype
            bit_depth = None
            subtype = info.subtype
            if "PCM_16" in subtype:
                bit_depth = 16
            elif "PCM_24" in subtype:
                bit_depth = 24
            elif "PCM_32" in subtype or "FLOAT" in subtype:
                bit_depth = 32
            elif "PCM_8" in subtype:
                bit_depth = 8

            self._metadata = AudioMetadata(
                sample_rate=info.samplerate,
                channels=info.channels,
                duration=info.duration,
                frames=info.frames,
                format=info.format,
                subtype=info.subtype,
                bit_depth=bit_depth,
            )
            self._filepath = filepath

        except Exception as e:
            raise RuntimeError(f"Failed to load audio file: {e}") from e

    def load_segment(
        self,
        filepath: Union[str, Path],
        start_time: float,
        end_time: float,
    ) -> None:
        """
        Load a segment of an audio file (paged reading for large files).

        Args:
            filepath: Path to the audio file.
            start_time: Start time in seconds.
            end_time: End time in seconds.
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Audio file not found: {filepath}")

        info = sf.info(filepath)
        start_frame = int(start_time * info.samplerate)
        end_frame = int(end_time * info.samplerate)
        num_frames = end_frame - start_frame

        self._data, self._sample_rate = sf.read(
            filepath,
            start=start_frame,
            frames=num_frames,
            dtype="float32",
        )

        if self._data.ndim == 1:
            self._data = self._data.reshape(-1, 1)

        self._filepath = filepath
        self._metadata = AudioMetadata(
            sample_rate=info.samplerate,
            channels=info.channels,
            duration=num_frames / info.samplerate,
            frames=num_frames,
            format=info.format,
            subtype=info.subtype,
        )

    def save(
        self,
        filepath: Union[str, Path],
        format: Optional[str] = None,
        subtype: Optional[str] = None,
    ) -> None:
        """
        Save audio data to a file.

        Args:
            filepath: Output file path.
            format: Audio format (e.g., 'WAV', 'FLAC'). Auto-detected from extension if None.
            subtype: Audio subtype (e.g., 'PCM_16', 'PCM_24'). Uses default if None.
        """
        if self._data is None:
            raise ValueError("No audio data to save")

        filepath = Path(filepath)
        data = self._data.squeeze() if self._data.shape[1] == 1 else self._data

        sf.write(
            filepath,
            data,
            self._sample_rate,
            format=format,
            subtype=subtype,
        )

    def get_channel(self, channel: int) -> np.ndarray:
        """
        Get data for a specific channel.

        Args:
            channel: Channel index (0-based).

        Returns:
            1D numpy array of audio samples for the channel.
        """
        if self._data is None:
            raise ValueError("No audio data loaded")
        if channel < 0 or channel >= self.num_channels:
            raise ValueError(f"Invalid channel index: {channel}")

        return self._data[:, channel]

    def get_time_range(
        self,
        start_time: float,
        end_time: float,
        channel: Optional[int] = None,
    ) -> np.ndarray:
        """
        Get audio data for a time range.

        Args:
            start_time: Start time in seconds.
            end_time: End time in seconds.
            channel: Channel index. If None, returns all channels.

        Returns:
            Audio data for the specified time range.
        """
        if self._data is None:
            raise ValueError("No audio data loaded")

        start_sample = int(start_time * self._sample_rate)
        end_sample = int(end_time * self._sample_rate)

        start_sample = max(0, start_sample)
        end_sample = min(len(self._data), end_sample)

        if channel is not None:
            return self._data[start_sample:end_sample, channel]
        return self._data[start_sample:end_sample]

    def time_to_sample(self, time: float) -> int:
        """Convert time in seconds to sample index."""
        return int(time * self._sample_rate)

    def sample_to_time(self, sample: int) -> float:
        """Convert sample index to time in seconds."""
        return sample / self._sample_rate

    @classmethod
    def from_array(
        cls,
        data: np.ndarray,
        sample_rate: int,
    ) -> "AudioFile":
        """
        Create an AudioFile from a numpy array.

        Args:
            data: Audio data as numpy array.
            sample_rate: Sample rate in Hz.

        Returns:
            New AudioFile instance.
        """
        audio = cls()
        audio._data = data.astype(np.float32)
        if audio._data.ndim == 1:
            audio._data = audio._data.reshape(-1, 1)
        audio._sample_rate = sample_rate
        audio._metadata = AudioMetadata(
            sample_rate=sample_rate,
            channels=audio._data.shape[1],
            duration=len(audio._data) / sample_rate,
            frames=len(audio._data),
            format="RAW",
            subtype="FLOAT",
        )
        return audio

    def __repr__(self) -> str:
        if self._filepath:
            return f"AudioFile('{self._filepath.name}', {self.duration:.2f}s, {self.num_channels}ch, {self._sample_rate}Hz)"
        return f"AudioFile(empty)"
