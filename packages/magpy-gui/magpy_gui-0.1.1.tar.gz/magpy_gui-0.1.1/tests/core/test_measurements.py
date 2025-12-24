"""Tests for the measurements module."""

import numpy as np
import pytest

from magpy.core.measurements import (
    AmplitudeMeasurements,
    EntropyMeasurements,
    FrequencyMeasurements,
    MeasurementCalculator,
    MeasurementResult,
    PowerMeasurements,
    SelectionBounds,
    TimeMeasurements,
)


@pytest.fixture
def pure_tone():
    """Generate a pure tone signal for testing."""
    sample_rate = 44100
    duration = 1.0
    frequency = 1000  # Hz
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    signal = np.sin(2 * np.pi * frequency * t) * 0.5  # Amplitude 0.5
    return signal, sample_rate, frequency


@pytest.fixture
def chirp_signal():
    """Generate a chirp signal for testing."""
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    f0, f1 = 500, 2000
    signal = np.sin(2 * np.pi * (f0 * t + (f1 - f0) * t**2 / (2 * duration))) * 0.5
    return signal.astype(np.float32), sample_rate, f0, f1


@pytest.fixture
def noise_signal():
    """Generate white noise for testing."""
    sample_rate = 44100
    duration = 1.0
    np.random.seed(42)
    signal = np.random.randn(int(sample_rate * duration)).astype(np.float32) * 0.1
    return signal, sample_rate


class TestSelectionBounds:
    """Tests for SelectionBounds."""

    def test_duration(self):
        """Test duration calculation."""
        bounds = SelectionBounds(start_time=0.5, end_time=1.5)
        assert bounds.duration == 1.0

    def test_bandwidth(self):
        """Test bandwidth calculation."""
        bounds = SelectionBounds(
            start_time=0, end_time=1, low_freq=500, high_freq=2000
        )
        assert bounds.bandwidth == 1500

    def test_bandwidth_none_when_unbounded(self):
        """Test bandwidth is None when frequency bounds not set."""
        bounds = SelectionBounds(start_time=0, end_time=1)
        assert bounds.bandwidth is None


class TestMeasurementCalculator:
    """Tests for MeasurementCalculator."""

    def test_compute_all_returns_result(self, pure_tone):
        """Test that compute_all returns a MeasurementResult."""
        signal, sample_rate, _ = pure_tone
        calc = MeasurementCalculator()
        bounds = SelectionBounds(start_time=0.1, end_time=0.9)

        result = calc.compute_all(signal, sample_rate, bounds)

        assert isinstance(result, MeasurementResult)
        assert isinstance(result.time, TimeMeasurements)
        assert isinstance(result.frequency, FrequencyMeasurements)
        assert isinstance(result.amplitude, AmplitudeMeasurements)
        assert isinstance(result.power, PowerMeasurements)
        assert isinstance(result.entropy, EntropyMeasurements)

    def test_time_measurements(self, pure_tone):
        """Test time-domain measurements."""
        signal, sample_rate, _ = pure_tone
        calc = MeasurementCalculator()
        bounds = SelectionBounds(start_time=0.2, end_time=0.8)

        result = calc.compute_all(signal, sample_rate, bounds)
        time_meas = result.time

        assert time_meas.begin_time == 0.2
        assert time_meas.end_time == 0.8
        assert abs(time_meas.delta_time - 0.6) < 1e-6
        assert abs(time_meas.center_time - 0.5) < 1e-6

        # Percentile times should be within bounds
        assert 0.2 <= time_meas.time_5 <= 0.8
        assert 0.2 <= time_meas.time_50 <= 0.8
        assert 0.2 <= time_meas.time_95 <= 0.8

        # Relative times should be between 0 and 1
        assert 0 <= time_meas.rel_time_5 <= 1
        assert 0 <= time_meas.rel_time_50 <= 1
        assert 0 <= time_meas.rel_time_95 <= 1

    def test_frequency_measurements_pure_tone(self, pure_tone):
        """Test frequency measurements on a pure tone."""
        signal, sample_rate, expected_freq = pure_tone
        calc = MeasurementCalculator()
        bounds = SelectionBounds(
            start_time=0.1, end_time=0.9, low_freq=0, high_freq=sample_rate / 2
        )

        result = calc.compute_all(signal, sample_rate, bounds)
        freq_meas = result.frequency

        # Peak frequency should be close to the tone frequency
        assert abs(freq_meas.peak_freq - expected_freq) < 100  # Within 100 Hz

        # Center frequency should also be near the tone
        assert abs(freq_meas.center_freq - expected_freq) < 200

    def test_amplitude_measurements(self, pure_tone):
        """Test amplitude measurements."""
        signal, sample_rate, _ = pure_tone
        calc = MeasurementCalculator()
        bounds = SelectionBounds(start_time=0.1, end_time=0.9)

        result = calc.compute_all(signal, sample_rate, bounds)
        amp_meas = result.amplitude

        # For a sine wave with amplitude 0.5:
        # RMS should be 0.5 / sqrt(2) ≈ 0.354
        expected_rms = 0.5 / np.sqrt(2)
        assert abs(amp_meas.rms_amplitude - expected_rms) < 0.05

        # Peak should be close to 0.5
        assert abs(amp_meas.peak_amplitude - 0.5) < 0.05

        # Peak-to-peak should be close to 1.0
        assert abs(amp_meas.peak_to_peak - 1.0) < 0.1

    def test_power_measurements(self, pure_tone):
        """Test power measurements."""
        signal, sample_rate, _ = pure_tone
        calc = MeasurementCalculator()
        bounds = SelectionBounds(start_time=0.1, end_time=0.9)

        result = calc.compute_all(signal, sample_rate, bounds)
        power_meas = result.power

        # Power values should be finite
        assert np.isfinite(power_meas.avg_power)
        assert np.isfinite(power_meas.peak_power)
        assert np.isfinite(power_meas.leq)
        assert np.isfinite(power_meas.sel)

        # Peak should be >= average
        assert power_meas.peak_power >= power_meas.avg_power

    def test_entropy_measurements_pure_tone(self, pure_tone):
        """Test entropy measurements on a pure tone."""
        signal, sample_rate, _ = pure_tone
        calc = MeasurementCalculator()
        bounds = SelectionBounds(start_time=0.1, end_time=0.9)

        result = calc.compute_all(signal, sample_rate, bounds)
        entropy_meas = result.entropy

        # Pure tone should have low entropy (energy concentrated at one frequency)
        assert entropy_meas.avg_entropy < 0.5  # Normalized entropy

    def test_entropy_measurements_noise(self, noise_signal):
        """Test entropy measurements on noise."""
        signal, sample_rate = noise_signal
        calc = MeasurementCalculator()
        bounds = SelectionBounds(start_time=0.1, end_time=0.9)

        result = calc.compute_all(signal, sample_rate, bounds)
        entropy_meas = result.entropy

        # Noise should have higher entropy than pure tone
        assert entropy_meas.avg_entropy > 0.5

    def test_peak_frequency_contour(self, chirp_signal):
        """Test peak frequency contour measurements."""
        signal, sample_rate, f0, f1 = chirp_signal
        calc = MeasurementCalculator()
        bounds = SelectionBounds(start_time=0.1, end_time=0.9)

        result = calc.compute_all(signal, sample_rate, bounds)
        pfc = result.peak_contour

        assert pfc is not None
        assert len(pfc.times) > 0
        assert len(pfc.frequencies) == len(pfc.times)

        # For a chirp, min freq should be lower than max
        assert pfc.min_freq < pfc.max_freq

        # Average slope should be positive (ascending chirp)
        assert pfc.avg_slope > 0

    def test_multichannel_input(self, pure_tone):
        """Test with multichannel input."""
        signal, sample_rate, _ = pure_tone
        stereo = np.column_stack([signal, signal * 0.5])
        calc = MeasurementCalculator()
        bounds = SelectionBounds(start_time=0.1, end_time=0.9)

        result0 = calc.compute_all(stereo, sample_rate, bounds, channel=0)
        result1 = calc.compute_all(stereo, sample_rate, bounds, channel=1)

        # Channel 1 should have lower amplitude
        assert result0.amplitude.rms_amplitude > result1.amplitude.rms_amplitude

    def test_frequency_bounds(self, noise_signal):
        """Test with frequency bounds."""
        signal, sample_rate = noise_signal
        calc = MeasurementCalculator()
        bounds = SelectionBounds(
            start_time=0.1, end_time=0.9, low_freq=1000, high_freq=5000
        )

        result = calc.compute_all(signal, sample_rate, bounds)

        # Frequency measurements should respect bounds
        assert result.frequency.low_freq == 1000
        assert result.frequency.high_freq == 5000
        assert result.frequency.delta_freq == 4000


class TestMeasurementResult:
    """Tests for MeasurementResult."""

    def test_to_dict(self, pure_tone):
        """Test conversion to dictionary."""
        signal, sample_rate, _ = pure_tone
        calc = MeasurementCalculator()
        bounds = SelectionBounds(start_time=0.1, end_time=0.9)

        result = calc.compute_all(signal, sample_rate, bounds)
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)

        # Check some expected keys
        assert "begin_time" in result_dict
        assert "end_time" in result_dict
        assert "delta_time" in result_dict
        assert "peak_freq" in result_dict
        assert "rms_amplitude" in result_dict
        assert "avg_power" in result_dict
        assert "avg_entropy" in result_dict

        # Check PFC keys if present
        if result.peak_contour is not None:
            assert "pfc_avg_freq" in result_dict
            assert "pfc_avg_slope" in result_dict

    def test_to_dict_values_are_numeric(self, pure_tone):
        """Test that all values in the dict are numeric."""
        signal, sample_rate, _ = pure_tone
        calc = MeasurementCalculator()
        bounds = SelectionBounds(start_time=0.1, end_time=0.9)

        result = calc.compute_all(signal, sample_rate, bounds)
        result_dict = result.to_dict()

        for key, value in result_dict.items():
            # Check for numeric types (including numpy types)
            assert isinstance(value, (int, float, np.integer, np.floating)), \
                f"{key} is not numeric: {type(value)}"
            assert np.isfinite(value), f"{key} is not finite: {value}"
