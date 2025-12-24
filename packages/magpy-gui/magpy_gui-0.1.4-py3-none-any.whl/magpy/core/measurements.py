"""
Acoustic measurements module implementing 70+ measurements from time-frequency selections.

Provides comprehensive acoustic analysis for bioacoustics research.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import numpy as np
from scipy import signal
from scipy.fft import rfft, rfftfreq


@dataclass
class SelectionBounds:
    """Time-frequency bounds for a selection."""

    start_time: float  # seconds
    end_time: float  # seconds
    low_freq: Optional[float] = None  # Hz (None = 0)
    high_freq: Optional[float] = None  # Hz (None = Nyquist)

    @property
    def duration(self) -> float:
        """Selection duration in seconds."""
        return self.end_time - self.start_time

    @property
    def bandwidth(self) -> Optional[float]:
        """Selection bandwidth in Hz, if defined."""
        if self.low_freq is not None and self.high_freq is not None:
            return self.high_freq - self.low_freq
        return None


@dataclass
class TimeMeasurements:
    """Time-domain measurements."""

    begin_time: float  # seconds
    end_time: float  # seconds
    delta_time: float  # duration in seconds
    center_time: float  # seconds
    time_5: float  # time at 5% cumulative energy
    time_25: float  # time at 25% cumulative energy
    time_50: float  # time at 50% cumulative energy (median)
    time_75: float  # time at 75% cumulative energy
    time_95: float  # time at 95% cumulative energy
    # Relative versions (as proportion of duration)
    rel_time_5: float
    rel_time_25: float
    rel_time_50: float
    rel_time_75: float
    rel_time_95: float


@dataclass
class FrequencyMeasurements:
    """Frequency-domain measurements."""

    low_freq: float  # Hz
    high_freq: float  # Hz
    delta_freq: float  # bandwidth in Hz
    center_freq: float  # Hz
    peak_freq: float  # frequency of maximum power
    freq_5: float  # 5th percentile frequency
    freq_25: float  # 25th percentile frequency
    freq_50: float  # median frequency
    freq_75: float  # 75th percentile frequency
    freq_95: float  # 95th percentile frequency


@dataclass
class PeakFrequencyContour:
    """Peak frequency contour measurements."""

    times: np.ndarray  # time points
    frequencies: np.ndarray  # peak frequencies at each time
    avg_freq: float  # average peak frequency
    min_freq: float  # minimum peak frequency
    max_freq: float  # maximum peak frequency
    avg_slope: float  # average slope (Hz/s)
    max_slope: float  # maximum slope
    min_slope: float  # minimum slope
    num_inflections: int  # number of inflection points


@dataclass
class AmplitudeMeasurements:
    """Amplitude measurements from waveform."""

    rms_amplitude: float
    peak_amplitude: float
    min_amplitude: float
    max_amplitude: float
    peak_to_peak: float


@dataclass
class PowerMeasurements:
    """Power measurements from spectrogram."""

    avg_power: float  # average power (dB)
    peak_power: float  # maximum power (dB)
    min_power: float  # minimum power (dB)
    delta_power: float  # power range (dB)
    inband_power: float  # total power in selection band
    leq: float  # equivalent continuous sound level
    sel: float  # sound exposure level


@dataclass
class EntropyMeasurements:
    """Entropy measurements quantifying signal disorder."""

    avg_entropy: float  # average entropy across time
    aggregate_entropy: float  # entropy of aggregated spectrum
    min_entropy: float
    max_entropy: float


@dataclass
class MeasurementResult:
    """Complete measurement result for a selection."""

    time: TimeMeasurements
    frequency: FrequencyMeasurements
    amplitude: AmplitudeMeasurements
    power: PowerMeasurements
    entropy: EntropyMeasurements
    peak_contour: Optional[PeakFrequencyContour] = None

    def to_dict(self) -> Dict[str, float]:
        """Convert all measurements to a flat dictionary."""
        result = {}

        # Time measurements
        for field_name in [
            "begin_time",
            "end_time",
            "delta_time",
            "center_time",
            "time_5",
            "time_25",
            "time_50",
            "time_75",
            "time_95",
            "rel_time_5",
            "rel_time_25",
            "rel_time_50",
            "rel_time_75",
            "rel_time_95",
        ]:
            result[field_name] = getattr(self.time, field_name)

        # Frequency measurements
        for field_name in [
            "low_freq",
            "high_freq",
            "delta_freq",
            "center_freq",
            "peak_freq",
            "freq_5",
            "freq_25",
            "freq_50",
            "freq_75",
            "freq_95",
        ]:
            result[field_name] = getattr(self.frequency, field_name)

        # Amplitude measurements
        for field_name in [
            "rms_amplitude",
            "peak_amplitude",
            "min_amplitude",
            "max_amplitude",
            "peak_to_peak",
        ]:
            result[field_name] = getattr(self.amplitude, field_name)

        # Power measurements
        for field_name in [
            "avg_power",
            "peak_power",
            "min_power",
            "delta_power",
            "inband_power",
            "leq",
            "sel",
        ]:
            result[field_name] = getattr(self.power, field_name)

        # Entropy measurements
        for field_name in ["avg_entropy", "aggregate_entropy", "min_entropy", "max_entropy"]:
            result[field_name] = getattr(self.entropy, field_name)

        # Peak contour measurements
        if self.peak_contour is not None:
            for field_name in [
                "avg_freq",
                "min_freq",
                "max_freq",
                "avg_slope",
                "max_slope",
                "min_slope",
                "num_inflections",
            ]:
                result[f"pfc_{field_name}"] = getattr(self.peak_contour, field_name)

        return result


class MeasurementCalculator:
    """
    Calculates comprehensive acoustic measurements from audio selections.
    """

    def __init__(
        self,
        window_size: int = 1024,
        hop_size: int = 256,
        ref_pressure: float = 20e-6,  # Reference pressure for SPL (20 µPa for air)
    ):
        """
        Initialize the measurement calculator.

        Args:
            window_size: FFT window size in samples.
            hop_size: Hop size between frames in samples.
            ref_pressure: Reference pressure for dB calculations.
        """
        self.window_size = window_size
        self.hop_size = hop_size
        self.ref_pressure = ref_pressure

    def compute_all(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        bounds: SelectionBounds,
        channel: int = 0,
    ) -> MeasurementResult:
        """
        Compute all measurements for a selection.

        Args:
            audio_data: Audio samples (samples,) or (samples, channels).
            sample_rate: Sample rate in Hz.
            bounds: Time-frequency selection bounds.
            channel: Channel to analyze.

        Returns:
            MeasurementResult containing all computed measurements.
        """
        # Extract channel and time segment
        if audio_data.ndim == 2:
            audio_data = audio_data[:, channel]

        start_sample = int(bounds.start_time * sample_rate)
        end_sample = int(bounds.end_time * sample_rate)
        segment = audio_data[start_sample:end_sample].astype(np.float32)

        # Compute spectrogram for spectral analysis
        spectrogram, frequencies, times = self._compute_spectrogram(segment, sample_rate)

        # Apply frequency bounds
        low_freq = bounds.low_freq or 0
        high_freq = bounds.high_freq or (sample_rate / 2)
        freq_mask = (frequencies >= low_freq) & (frequencies <= high_freq)

        bounded_spec = spectrogram[freq_mask, :]
        bounded_freqs = frequencies[freq_mask]

        # Compute all measurement categories
        time_meas = self._compute_time_measurements(
            segment, sample_rate, bounds.start_time, bounds.end_time
        )
        freq_meas = self._compute_frequency_measurements(
            bounded_spec, bounded_freqs, low_freq, high_freq
        )
        amp_meas = self._compute_amplitude_measurements(segment)
        power_meas = self._compute_power_measurements(
            bounded_spec, bounds.duration, sample_rate
        )
        entropy_meas = self._compute_entropy_measurements(bounded_spec)
        peak_contour = self._compute_peak_frequency_contour(
            bounded_spec, bounded_freqs, times + bounds.start_time
        )

        return MeasurementResult(
            time=time_meas,
            frequency=freq_meas,
            amplitude=amp_meas,
            power=power_meas,
            entropy=entropy_meas,
            peak_contour=peak_contour,
        )

    def _compute_spectrogram(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute power spectrogram (linear scale)."""
        window = signal.windows.hann(self.window_size)
        num_samples = len(audio_data)
        num_frames = max(1, (num_samples - self.window_size) // self.hop_size + 1)
        num_freqs = self.window_size // 2 + 1

        spectrogram = np.zeros((num_freqs, num_frames), dtype=np.float32)

        for i in range(num_frames):
            start = i * self.hop_size
            end = start + self.window_size
            if end > num_samples:
                break

            frame = audio_data[start:end] * window
            spectrum = rfft(frame)
            spectrogram[:, i] = np.abs(spectrum) ** 2

        frequencies = rfftfreq(self.window_size, 1.0 / sample_rate)
        times = np.arange(num_frames) * self.hop_size / sample_rate

        return spectrogram, frequencies, times

    def _compute_time_measurements(
        self,
        segment: np.ndarray,
        sample_rate: int,
        start_time: float,
        end_time: float,
    ) -> TimeMeasurements:
        """Compute time-domain measurements."""
        duration = end_time - start_time

        # Compute cumulative energy
        energy = segment**2
        cumulative = np.cumsum(energy)
        total_energy = cumulative[-1] if len(cumulative) > 0 else 1e-10
        cumulative_norm = cumulative / total_energy

        # Find percentile times
        def find_percentile_time(pct: float) -> float:
            idx = np.searchsorted(cumulative_norm, pct / 100.0)
            return start_time + idx / sample_rate

        time_5 = find_percentile_time(5)
        time_25 = find_percentile_time(25)
        time_50 = find_percentile_time(50)
        time_75 = find_percentile_time(75)
        time_95 = find_percentile_time(95)

        return TimeMeasurements(
            begin_time=start_time,
            end_time=end_time,
            delta_time=duration,
            center_time=start_time + duration / 2,
            time_5=time_5,
            time_25=time_25,
            time_50=time_50,
            time_75=time_75,
            time_95=time_95,
            rel_time_5=(time_5 - start_time) / duration if duration > 0 else 0,
            rel_time_25=(time_25 - start_time) / duration if duration > 0 else 0,
            rel_time_50=(time_50 - start_time) / duration if duration > 0 else 0,
            rel_time_75=(time_75 - start_time) / duration if duration > 0 else 0,
            rel_time_95=(time_95 - start_time) / duration if duration > 0 else 0,
        )

    def _compute_frequency_measurements(
        self,
        spectrogram: np.ndarray,
        frequencies: np.ndarray,
        low_freq: float,
        high_freq: float,
    ) -> FrequencyMeasurements:
        """Compute frequency-domain measurements."""
        # Average spectrum across time
        avg_spectrum = np.mean(spectrogram, axis=1)

        # Peak frequency
        peak_idx = np.argmax(avg_spectrum)
        peak_freq = frequencies[peak_idx] if len(frequencies) > 0 else 0

        # Center frequency (power-weighted centroid)
        total_power = np.sum(avg_spectrum)
        if total_power > 0:
            center_freq = np.sum(frequencies * avg_spectrum) / total_power
        else:
            center_freq = (low_freq + high_freq) / 2

        # Frequency percentiles
        cumulative = np.cumsum(avg_spectrum)
        cumulative_norm = cumulative / (total_power + 1e-10)

        def find_freq_percentile(pct: float) -> float:
            idx = np.searchsorted(cumulative_norm, pct / 100.0)
            return frequencies[min(idx, len(frequencies) - 1)]

        return FrequencyMeasurements(
            low_freq=low_freq,
            high_freq=high_freq,
            delta_freq=high_freq - low_freq,
            center_freq=center_freq,
            peak_freq=peak_freq,
            freq_5=find_freq_percentile(5),
            freq_25=find_freq_percentile(25),
            freq_50=find_freq_percentile(50),
            freq_75=find_freq_percentile(75),
            freq_95=find_freq_percentile(95),
        )

    def _compute_amplitude_measurements(
        self,
        segment: np.ndarray,
    ) -> AmplitudeMeasurements:
        """Compute amplitude measurements from waveform."""
        if len(segment) == 0:
            return AmplitudeMeasurements(
                rms_amplitude=0,
                peak_amplitude=0,
                min_amplitude=0,
                max_amplitude=0,
                peak_to_peak=0,
            )

        rms = np.sqrt(np.mean(segment**2))
        min_amp = float(np.min(segment))
        max_amp = float(np.max(segment))
        peak = float(np.max(np.abs(segment)))

        return AmplitudeMeasurements(
            rms_amplitude=rms,
            peak_amplitude=peak,
            min_amplitude=min_amp,
            max_amplitude=max_amp,
            peak_to_peak=max_amp - min_amp,
        )

    def _compute_power_measurements(
        self,
        spectrogram: np.ndarray,
        duration: float,
        sample_rate: int,
    ) -> PowerMeasurements:
        """Compute power measurements from spectrogram."""
        if spectrogram.size == 0:
            return PowerMeasurements(
                avg_power=-80,
                peak_power=-80,
                min_power=-80,
                delta_power=0,
                inband_power=-80,
                leq=-80,
                sel=-80,
            )

        # Convert to dB
        power_db = 10 * np.log10(spectrogram + 1e-10)

        avg_power = float(np.mean(power_db))
        peak_power = float(np.max(power_db))
        min_power = float(np.min(power_db))

        # Total inband power
        total_power = np.sum(spectrogram)
        inband_power = 10 * np.log10(total_power + 1e-10)

        # Leq (equivalent continuous sound level)
        mean_power = np.mean(spectrogram)
        leq = 10 * np.log10(mean_power + 1e-10)

        # SEL (Sound Exposure Level) = Leq + 10*log10(duration)
        sel = leq + 10 * np.log10(duration + 1e-10)

        return PowerMeasurements(
            avg_power=avg_power,
            peak_power=peak_power,
            min_power=min_power,
            delta_power=peak_power - min_power,
            inband_power=inband_power,
            leq=leq,
            sel=sel,
        )

    def _compute_entropy_measurements(
        self,
        spectrogram: np.ndarray,
    ) -> EntropyMeasurements:
        """Compute entropy measurements."""
        if spectrogram.size == 0:
            return EntropyMeasurements(
                avg_entropy=0,
                aggregate_entropy=0,
                min_entropy=0,
                max_entropy=0,
            )

        def compute_spectral_entropy(spectrum: np.ndarray) -> float:
            """Compute entropy of a single spectrum."""
            # Normalize to probability distribution
            total = np.sum(spectrum)
            if total == 0:
                return 0
            p = spectrum / total
            # Avoid log(0)
            p = p[p > 0]
            # Compute entropy
            entropy = -np.sum(p * np.log2(p))
            # Normalize by max possible entropy
            max_entropy = np.log2(len(spectrum))
            return entropy / max_entropy if max_entropy > 0 else 0

        # Entropy for each time frame
        entropies = np.array([compute_spectral_entropy(spectrogram[:, i])
                             for i in range(spectrogram.shape[1])])

        # Aggregate spectrum entropy
        aggregate_spectrum = np.mean(spectrogram, axis=1)
        aggregate_entropy = compute_spectral_entropy(aggregate_spectrum)

        return EntropyMeasurements(
            avg_entropy=float(np.mean(entropies)) if len(entropies) > 0 else 0,
            aggregate_entropy=aggregate_entropy,
            min_entropy=float(np.min(entropies)) if len(entropies) > 0 else 0,
            max_entropy=float(np.max(entropies)) if len(entropies) > 0 else 0,
        )

    def _compute_peak_frequency_contour(
        self,
        spectrogram: np.ndarray,
        frequencies: np.ndarray,
        times: np.ndarray,
    ) -> Optional[PeakFrequencyContour]:
        """Compute peak frequency contour and its statistics."""
        if spectrogram.size == 0 or len(frequencies) == 0:
            return None

        # Find peak frequency at each time frame
        peak_indices = np.argmax(spectrogram, axis=0)
        peak_freqs = frequencies[peak_indices]

        if len(peak_freqs) < 2:
            return PeakFrequencyContour(
                times=times,
                frequencies=peak_freqs,
                avg_freq=float(np.mean(peak_freqs)) if len(peak_freqs) > 0 else 0,
                min_freq=float(np.min(peak_freqs)) if len(peak_freqs) > 0 else 0,
                max_freq=float(np.max(peak_freqs)) if len(peak_freqs) > 0 else 0,
                avg_slope=0,
                max_slope=0,
                min_slope=0,
                num_inflections=0,
            )

        # Compute slopes (Hz/s)
        dt = times[1] - times[0] if len(times) > 1 else 1
        slopes = np.diff(peak_freqs) / dt

        # Count inflection points (sign changes in slope)
        if len(slopes) > 1:
            slope_signs = np.sign(slopes)
            inflections = np.sum(np.abs(np.diff(slope_signs)) == 2)
        else:
            inflections = 0

        return PeakFrequencyContour(
            times=times,
            frequencies=peak_freqs,
            avg_freq=float(np.mean(peak_freqs)),
            min_freq=float(np.min(peak_freqs)),
            max_freq=float(np.max(peak_freqs)),
            avg_slope=float(np.mean(slopes)) if len(slopes) > 0 else 0,
            max_slope=float(np.max(slopes)) if len(slopes) > 0 else 0,
            min_slope=float(np.min(slopes)) if len(slopes) > 0 else 0,
            num_inflections=int(inflections),
        )
