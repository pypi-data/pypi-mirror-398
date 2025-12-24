"""
Spectrogram generation module with configurable DSP parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

import numpy as np
from scipy import signal
from scipy.fft import rfft, rfftfreq


class WindowFunction(Enum):
    """Supported window functions for spectrogram computation."""

    BLACKMAN = "blackman"
    HAMMING = "hamming"
    HANN = "hann"
    KAISER = "kaiser"
    RECTANGULAR = "rectangular"
    TRIANGULAR = "triangular"


@dataclass
class SpectrogramConfig:
    """Configuration for spectrogram generation."""

    window_size: int = 1024
    hop_size: int = 256
    dft_size: Optional[int] = None  # If None, uses window_size
    window_function: WindowFunction = WindowFunction.HANN
    kaiser_beta: float = 14.0  # Beta parameter for Kaiser window
    log_power: bool = True
    ref_power: float = 1.0
    min_db: float = -80.0
    max_db: float = 0.0

    def __post_init__(self):
        if self.dft_size is None:
            self.dft_size = self.window_size


@dataclass
class SpectrogramResult:
    """Result of spectrogram computation."""

    spectrogram: np.ndarray  # Shape: (frequencies, time_frames)
    frequencies: np.ndarray  # Frequency bins in Hz
    times: np.ndarray  # Time points in seconds
    sample_rate: int
    config: SpectrogramConfig

    @property
    def duration(self) -> float:
        """Total duration in seconds."""
        return self.times[-1] if len(self.times) > 0 else 0.0

    @property
    def frequency_resolution(self) -> float:
        """Frequency resolution in Hz."""
        if len(self.frequencies) < 2:
            return 0.0
        return float(self.frequencies[1] - self.frequencies[0])

    @property
    def time_resolution(self) -> float:
        """Time resolution in seconds."""
        if len(self.times) < 2:
            return 0.0
        return float(self.times[1] - self.times[0])


class SpectrogramGenerator:
    """
    Generates spectrograms from audio data with configurable parameters.

    Supports six window functions for flexible time-frequency analysis.
    """

    def __init__(self, config: Optional[SpectrogramConfig] = None):
        """
        Initialize the spectrogram generator.

        Args:
            config: Spectrogram configuration. Uses defaults if None.
        """
        self.config = config or SpectrogramConfig()

    def _get_window(self, size: int) -> np.ndarray:
        """
        Get the window function array.

        Args:
            size: Window size in samples.

        Returns:
            Window function as numpy array.
        """
        wf = self.config.window_function

        if wf == WindowFunction.BLACKMAN:
            return signal.windows.blackman(size)
        elif wf == WindowFunction.HAMMING:
            return signal.windows.hamming(size)
        elif wf == WindowFunction.HANN:
            return signal.windows.hann(size)
        elif wf == WindowFunction.KAISER:
            return signal.windows.kaiser(size, self.config.kaiser_beta)
        elif wf == WindowFunction.RECTANGULAR:
            return np.ones(size)
        elif wf == WindowFunction.TRIANGULAR:
            return signal.windows.triang(size)
        else:
            return signal.windows.hann(size)

    def compute(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        channel: int = 0,
    ) -> SpectrogramResult:
        """
        Compute the spectrogram of audio data.

        Args:
            audio_data: Audio samples as numpy array (samples,) or (samples, channels).
            sample_rate: Sample rate in Hz.
            channel: Channel to analyze if multi-channel.

        Returns:
            SpectrogramResult containing the spectrogram and metadata.
        """
        # Extract single channel if needed
        if audio_data.ndim == 2:
            audio_data = audio_data[:, channel]

        # Ensure float type
        audio_data = audio_data.astype(np.float32)

        # Get configuration
        window_size = self.config.window_size
        hop_size = self.config.hop_size
        dft_size = self.config.dft_size or window_size

        # Pad DFT size if smaller than window
        if dft_size < window_size:
            dft_size = window_size

        # Get window function
        window = self._get_window(window_size)

        # Calculate number of frames
        num_samples = len(audio_data)
        num_frames = max(1, (num_samples - window_size) // hop_size + 1)

        # Number of frequency bins (positive frequencies only)
        num_freqs = dft_size // 2 + 1

        # Initialize spectrogram array
        spectrogram = np.zeros((num_freqs, num_frames), dtype=np.float32)

        # Compute STFT frame by frame
        for i in range(num_frames):
            start = i * hop_size
            end = start + window_size

            # Extract and window the frame
            frame = audio_data[start:end] * window

            # Zero-pad if DFT size is larger than window size
            if dft_size > window_size:
                frame = np.pad(frame, (0, dft_size - window_size))

            # Compute FFT and power spectrum
            spectrum = rfft(frame)
            power = np.abs(spectrum) ** 2

            spectrogram[:, i] = power

        # Convert to dB if requested
        if self.config.log_power:
            # Avoid log of zero
            spectrogram = np.maximum(spectrogram, 1e-10)
            spectrogram = 10 * np.log10(spectrogram / self.config.ref_power)
            spectrogram = np.clip(spectrogram, self.config.min_db, self.config.max_db)

        # Calculate frequency and time axes
        frequencies = rfftfreq(dft_size, 1.0 / sample_rate)
        times = np.arange(num_frames) * hop_size / sample_rate

        return SpectrogramResult(
            spectrogram=spectrogram,
            frequencies=frequencies,
            times=times,
            sample_rate=sample_rate,
            config=self.config,
        )

    def compute_slice(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        time_point: float,
        channel: int = 0,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute a single spectral slice at a specific time point.

        Args:
            audio_data: Audio samples.
            sample_rate: Sample rate in Hz.
            time_point: Time in seconds for the slice.
            channel: Channel to analyze.

        Returns:
            Tuple of (power_spectrum, frequencies).
        """
        if audio_data.ndim == 2:
            audio_data = audio_data[:, channel]

        # Get window parameters
        window_size = self.config.window_size
        dft_size = self.config.dft_size or window_size

        # Calculate center sample
        center_sample = int(time_point * sample_rate)
        start = center_sample - window_size // 2
        end = start + window_size

        # Handle boundaries
        if start < 0:
            start = 0
            end = window_size
        if end > len(audio_data):
            end = len(audio_data)
            start = max(0, end - window_size)

        # Extract and window
        frame = audio_data[start:end].astype(np.float32)
        if len(frame) < window_size:
            frame = np.pad(frame, (0, window_size - len(frame)))

        window = self._get_window(window_size)
        frame = frame * window

        # Zero-pad for DFT
        if dft_size > window_size:
            frame = np.pad(frame, (0, dft_size - window_size))

        # Compute spectrum
        spectrum = rfft(frame)
        power = np.abs(spectrum) ** 2

        if self.config.log_power:
            power = np.maximum(power, 1e-10)
            power = 10 * np.log10(power / self.config.ref_power)
            power = np.clip(power, self.config.min_db, self.config.max_db)

        frequencies = rfftfreq(dft_size, 1.0 / sample_rate)

        return power, frequencies

    def compute_selection_spectrum(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        start_time: float,
        end_time: float,
        low_freq: Optional[float] = None,
        high_freq: Optional[float] = None,
        channel: int = 0,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute average spectrum over a time-frequency selection.

        Args:
            audio_data: Audio samples.
            sample_rate: Sample rate in Hz.
            start_time: Start time in seconds.
            end_time: End time in seconds.
            low_freq: Low frequency bound (Hz). If None, uses 0.
            high_freq: High frequency bound (Hz). If None, uses Nyquist.
            channel: Channel to analyze.

        Returns:
            Tuple of (average_power_spectrum, frequencies).
        """
        # Compute full spectrogram for the selection
        if audio_data.ndim == 2:
            audio_data = audio_data[:, channel]

        start_sample = int(start_time * sample_rate)
        end_sample = int(end_time * sample_rate)

        segment = audio_data[start_sample:end_sample]
        result = self.compute(segment, sample_rate)

        # Average across time
        avg_spectrum = np.mean(result.spectrogram, axis=1)

        # Apply frequency bounds if specified
        if low_freq is not None or high_freq is not None:
            low_freq = low_freq or 0
            high_freq = high_freq or (sample_rate / 2)

            freq_mask = (result.frequencies >= low_freq) & (result.frequencies <= high_freq)
            return avg_spectrum[freq_mask], result.frequencies[freq_mask]

        return avg_spectrum, result.frequencies

    @staticmethod
    def window_size_from_bandwidth(bandwidth_hz: float, sample_rate: int) -> int:
        """
        Calculate window size from desired 3dB bandwidth.

        Args:
            bandwidth_hz: Desired bandwidth in Hz.
            sample_rate: Sample rate in Hz.

        Returns:
            Window size in samples.
        """
        # For Hann window, 3dB bandwidth ≈ 1.44 * (sample_rate / window_size)
        return int(1.44 * sample_rate / bandwidth_hz)

    @staticmethod
    def window_size_from_time(time_ms: float, sample_rate: int) -> int:
        """
        Calculate window size from desired time resolution.

        Args:
            time_ms: Desired window duration in milliseconds.
            sample_rate: Sample rate in Hz.

        Returns:
            Window size in samples.
        """
        return int(time_ms * sample_rate / 1000)
