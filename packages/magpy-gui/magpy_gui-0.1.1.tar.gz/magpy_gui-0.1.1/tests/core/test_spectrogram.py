"""Tests for the spectrogram module."""

import numpy as np
import pytest

from magpy.core.spectrogram import (
    SpectrogramConfig,
    SpectrogramGenerator,
    SpectrogramResult,
    WindowFunction,
)


@pytest.fixture
def pure_tone():
    """Generate a pure tone signal for testing."""
    sample_rate = 44100
    duration = 1.0
    frequency = 1000  # Hz
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    signal = np.sin(2 * np.pi * frequency * t)
    return signal, sample_rate, frequency


@pytest.fixture
def chirp_signal():
    """Generate a chirp signal (frequency sweep) for testing."""
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    # Sweep from 500 Hz to 5000 Hz
    f0, f1 = 500, 5000
    signal = np.sin(2 * np.pi * (f0 * t + (f1 - f0) * t**2 / (2 * duration)))
    return signal.astype(np.float32), sample_rate


@pytest.fixture
def noise_signal():
    """Generate white noise for testing."""
    sample_rate = 44100
    duration = 0.5
    np.random.seed(42)
    signal = np.random.randn(int(sample_rate * duration)).astype(np.float32) * 0.1
    return signal, sample_rate


class TestSpectrogramConfig:
    """Tests for SpectrogramConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SpectrogramConfig()

        assert config.window_size == 1024
        assert config.hop_size == 256
        assert config.dft_size == 1024
        assert config.window_function == WindowFunction.HANN
        assert config.log_power is True
        assert config.min_db == -80.0
        assert config.max_db == 0.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = SpectrogramConfig(
            window_size=2048,
            hop_size=512,
            dft_size=4096,
            window_function=WindowFunction.BLACKMAN,
            log_power=False,
        )

        assert config.window_size == 2048
        assert config.hop_size == 512
        assert config.dft_size == 4096
        assert config.window_function == WindowFunction.BLACKMAN
        assert config.log_power is False

    def test_dft_size_defaults_to_window_size(self):
        """Test that DFT size defaults to window size if not specified."""
        config = SpectrogramConfig(window_size=512, dft_size=None)
        assert config.dft_size == 512


class TestSpectrogramGenerator:
    """Tests for SpectrogramGenerator."""

    def test_compute_basic(self, pure_tone):
        """Test basic spectrogram computation."""
        signal, sample_rate, freq = pure_tone
        generator = SpectrogramGenerator()

        result = generator.compute(signal, sample_rate)

        assert isinstance(result, SpectrogramResult)
        assert result.spectrogram.ndim == 2
        assert len(result.frequencies) == result.spectrogram.shape[0]
        assert len(result.times) == result.spectrogram.shape[1]
        assert result.sample_rate == sample_rate

    def test_pure_tone_peak_frequency(self, pure_tone):
        """Test that pure tone has peak at expected frequency."""
        signal, sample_rate, expected_freq = pure_tone
        config = SpectrogramConfig(log_power=True)
        generator = SpectrogramGenerator(config)

        result = generator.compute(signal, sample_rate)

        # Average spectrum
        avg_spectrum = np.mean(result.spectrogram, axis=1)
        peak_idx = np.argmax(avg_spectrum)
        peak_freq = result.frequencies[peak_idx]

        # Allow tolerance for frequency resolution and spectral leakage
        assert abs(peak_freq - expected_freq) < 200  # Within 200 Hz

    def test_window_functions(self, pure_tone):
        """Test that all window functions work."""
        signal, sample_rate, _ = pure_tone

        for window in WindowFunction:
            config = SpectrogramConfig(window_function=window)
            generator = SpectrogramGenerator(config)
            result = generator.compute(signal, sample_rate)

            assert result.spectrogram.shape[0] > 0
            assert result.spectrogram.shape[1] > 0

    def test_linear_power(self, pure_tone):
        """Test spectrogram with linear (non-dB) power."""
        signal, sample_rate, _ = pure_tone
        config = SpectrogramConfig(log_power=False)
        generator = SpectrogramGenerator(config)

        result = generator.compute(signal, sample_rate)

        # Linear power should be non-negative
        assert np.all(result.spectrogram >= 0)

    def test_frequency_range(self, pure_tone):
        """Test that frequency range is correct."""
        signal, sample_rate, _ = pure_tone
        generator = SpectrogramGenerator()

        result = generator.compute(signal, sample_rate)

        assert result.frequencies[0] == 0
        assert result.frequencies[-1] <= sample_rate / 2
        assert result.frequencies[-1] >= sample_rate / 2 - 100  # Close to Nyquist

    def test_multichannel_input(self, pure_tone):
        """Test with multichannel input."""
        signal, sample_rate, _ = pure_tone
        stereo = np.column_stack([signal, signal * 0.5])
        generator = SpectrogramGenerator()

        result0 = generator.compute(stereo, sample_rate, channel=0)
        result1 = generator.compute(stereo, sample_rate, channel=1)

        # Channel 1 should have lower power (0.5 amplitude = -6dB)
        assert np.mean(result0.spectrogram) > np.mean(result1.spectrogram)

    def test_compute_slice(self, pure_tone):
        """Test computing a single spectral slice."""
        signal, sample_rate, expected_freq = pure_tone
        generator = SpectrogramGenerator()

        power, freqs = generator.compute_slice(signal, sample_rate, time_point=0.5)

        assert len(power) == len(freqs)
        peak_idx = np.argmax(power)
        peak_freq = freqs[peak_idx]

        # Verify peak is at expected frequency (allow tolerance for spectral leakage)
        assert abs(peak_freq - expected_freq) < 200  # Within 200 Hz

    def test_compute_selection_spectrum(self, pure_tone):
        """Test computing average spectrum over a selection."""
        signal, sample_rate, expected_freq = pure_tone
        generator = SpectrogramGenerator()

        avg_power, freqs = generator.compute_selection_spectrum(
            signal, sample_rate, start_time=0.2, end_time=0.8
        )

        assert len(avg_power) == len(freqs)
        peak_idx = np.argmax(avg_power)
        peak_freq = freqs[peak_idx]

        # Allow tolerance for frequency resolution and spectral leakage
        assert abs(peak_freq - expected_freq) < 200  # Within 200 Hz

    def test_selection_spectrum_with_freq_bounds(self, noise_signal):
        """Test selection spectrum with frequency bounds."""
        signal, sample_rate = noise_signal
        generator = SpectrogramGenerator()

        avg_power, freqs = generator.compute_selection_spectrum(
            signal,
            sample_rate,
            start_time=0.0,
            end_time=0.5,
            low_freq=1000,
            high_freq=5000,
        )

        assert freqs[0] >= 1000
        assert freqs[-1] <= 5000


class TestSpectrogramResult:
    """Tests for SpectrogramResult."""

    def test_properties(self, pure_tone):
        """Test SpectrogramResult properties."""
        signal, sample_rate, _ = pure_tone
        generator = SpectrogramGenerator()
        result = generator.compute(signal, sample_rate)

        assert result.duration > 0
        assert result.frequency_resolution > 0
        assert result.time_resolution > 0

    def test_time_resolution(self, pure_tone):
        """Test time resolution calculation."""
        signal, sample_rate, _ = pure_tone
        config = SpectrogramConfig(hop_size=512)
        generator = SpectrogramGenerator(config)
        result = generator.compute(signal, sample_rate)

        expected_resolution = 512 / sample_rate
        assert abs(result.time_resolution - expected_resolution) < 1e-6


class TestWindowSizeHelpers:
    """Tests for window size helper functions."""

    def test_window_size_from_bandwidth(self):
        """Test calculating window size from bandwidth."""
        sample_rate = 44100
        bandwidth = 100  # Hz

        window_size = SpectrogramGenerator.window_size_from_bandwidth(bandwidth, sample_rate)

        # For Hann window, bandwidth ≈ 1.44 * fs / N
        expected = int(1.44 * sample_rate / bandwidth)
        assert window_size == expected

    def test_window_size_from_time(self):
        """Test calculating window size from time."""
        sample_rate = 44100
        time_ms = 23.2  # milliseconds (~1024 samples at 44100 Hz)

        window_size = SpectrogramGenerator.window_size_from_time(time_ms, sample_rate)

        expected = int(time_ms * sample_rate / 1000)
        assert window_size == expected
