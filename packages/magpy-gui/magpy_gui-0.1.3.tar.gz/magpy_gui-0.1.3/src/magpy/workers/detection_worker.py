"""
Detection Worker
================

QThread worker for running detection operations without blocking the UI.
Supports both ML-based models (AST, BirdNET) and signal-based detectors.

Example:
    >>> from magpy.workers import DetectionWorker, DetectionConfig
    >>>
    >>> config = DetectionConfig(
    ...     model_type="ast",
    ...     model_path="MIT/ast-finetuned-audioset-10-10-0.4593",
    ...     min_confidence=0.5,
    ... )
    >>> worker = DetectionWorker(["audio1.wav", "audio2.wav"], config)
    >>> worker.progress.connect(on_progress)
    >>> worker.result.connect(on_result)
    >>> worker.error.connect(on_error)
    >>> worker.start()
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PyQt6.QtCore import QThread, pyqtSignal


class DetectorType(Enum):
    """Available detector types."""

    # ML-based models
    AST = "ast"
    BIRDNET = "birdnet"
    OPENSOUNDSCAPE = "opensoundscape"

    # Signal-based detectors
    ENERGY = "energy"
    RIBBIT = "ribbit"
    CWT = "cwt"
    ACCELERATING = "accelerating"


@dataclass
class DetectionConfig:
    """
    Configuration for detection operations.

    Attributes:
        detector_type: Type of detector to use.
        model_path: Path to model (for ML detectors) or None for signal detectors.
        min_confidence: Minimum confidence threshold (0-1).
        top_k: Number of top predictions per segment (ML models).
        clip_duration: Clip duration in seconds (ML models).
        overlap: Overlap between clips (0-1).
        batch_size: Batch size for processing.
        use_gpu: Whether to use GPU acceleration.
        detector_params: Additional parameters for signal-based detectors.
    """

    detector_type: DetectorType = DetectorType.AST
    model_path: Optional[str] = None
    min_confidence: float = 0.0
    top_k: int = 5
    clip_duration: float = 3.0
    overlap: float = 0.0
    batch_size: int = 8
    use_gpu: bool = True
    detector_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Set default model paths for ML detectors
        if self.model_path is None and self.detector_type == DetectorType.AST:
            self.model_path = "MIT/ast-finetuned-audioset-10-10-0.4593"


@dataclass
class DetectionResult:
    """
    Result from a single detection.

    Attributes:
        start_time: Start time in seconds.
        end_time: End time in seconds.
        confidence: Detection confidence (0-1).
        label: Detection label/class.
        frequency_low: Lower frequency bound (Hz), if applicable.
        frequency_high: Upper frequency bound (Hz), if applicable.
        filepath: Source audio file path.
        metadata: Additional metadata.
    """

    start_time: float
    end_time: float
    confidence: float
    label: str
    frequency_low: Optional[float] = None
    frequency_high: Optional[float] = None
    filepath: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Duration in seconds."""
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "confidence": self.confidence,
            "label": self.label,
            "duration": self.duration,
            "frequency_low": self.frequency_low,
            "frequency_high": self.frequency_high,
            "filepath": self.filepath,
            **self.metadata,
        }


@dataclass
class BatchDetectionResult:
    """
    Results from batch detection.

    Attributes:
        detections: List of all detection results.
        total_files: Total number of files.
        files_processed: Number of files successfully processed.
        files_failed: Number of files that failed.
        processing_time: Total processing time in seconds.
    """

    detections: List[DetectionResult]
    total_files: int
    files_processed: int
    files_failed: int
    processing_time: float

    def filter_by_confidence(self, min_confidence: float) -> List[DetectionResult]:
        """Filter detections by minimum confidence."""
        return [d for d in self.detections if d.confidence >= min_confidence]

    def filter_by_label(self, labels: List[str]) -> List[DetectionResult]:
        """Filter detections by label."""
        return [d for d in self.detections if d.label in labels]

    def group_by_file(self) -> Dict[str, List[DetectionResult]]:
        """Group detections by source file."""
        grouped: Dict[str, List[DetectionResult]] = {}
        for det in self.detections:
            key = det.filepath or "unknown"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(det)
        return grouped


class DetectionWorker(QThread):
    """
    QThread worker for running detection operations.

    Signals:
        progress(current, total, message): Emitted during processing.
        file_complete(filepath, detections): Emitted when a file is processed.
        result(BatchDetectionResult): Emitted when all processing is complete.
        error(message): Emitted when an error occurs.

    Example:
        >>> config = DetectionConfig(detector_type=DetectorType.AST)
        >>> worker = DetectionWorker(["audio.wav"], config)
        >>> worker.progress.connect(lambda c, t, m: print(f"{c}/{t}: {m}"))
        >>> worker.result.connect(lambda r: print(f"Found {len(r.detections)} detections"))
        >>> worker.start()
    """

    # Signals
    progress = pyqtSignal(int, int, str)  # current, total, message
    file_complete = pyqtSignal(str, list)  # filepath, list of DetectionResult
    result = pyqtSignal(object)  # BatchDetectionResult
    error = pyqtSignal(str)  # error message

    def __init__(
        self,
        files: List[Union[str, Path]],
        config: DetectionConfig,
        parent=None,
    ):
        """
        Initialize the detection worker.

        Args:
            files: List of audio file paths to process.
            config: Detection configuration.
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self.files = [str(f) for f in files]
        self.config = config
        self._cancelled = False
        self._model = None
        self._detector = None

    def cancel(self) -> None:
        """Request cancellation of the detection process."""
        self._cancelled = True

    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._cancelled

    def run(self) -> None:
        """Execute the detection process."""
        import time

        start_time = time.time()
        all_detections: List[DetectionResult] = []
        files_processed = 0
        files_failed = 0

        try:
            # Initialize detector
            self.progress.emit(0, len(self.files), "Loading model...")
            self._init_detector()

            # Process each file
            for i, filepath in enumerate(self.files):
                if self._cancelled:
                    self.progress.emit(i, len(self.files), "Cancelled")
                    break

                filename = Path(filepath).name
                self.progress.emit(i, len(self.files), f"Processing {filename}...")

                try:
                    detections = self._process_file(filepath)
                    all_detections.extend(detections)
                    files_processed += 1

                    # Emit file completion signal
                    self.file_complete.emit(filepath, detections)

                except Exception as e:
                    files_failed += 1
                    self.progress.emit(
                        i + 1, len(self.files), f"Error processing {filename}: {e}"
                    )

            # Calculate processing time
            processing_time = time.time() - start_time

            # Emit final result
            batch_result = BatchDetectionResult(
                detections=all_detections,
                total_files=len(self.files),
                files_processed=files_processed,
                files_failed=files_failed,
                processing_time=processing_time,
            )

            self.progress.emit(
                len(self.files),
                len(self.files),
                f"Complete: {len(all_detections)} detections in {processing_time:.1f}s",
            )
            self.result.emit(batch_result)

        except Exception as e:
            self.error.emit(str(e))

        finally:
            self._cleanup()

    def _init_detector(self) -> None:
        """Initialize the detector based on configuration."""
        detector_type = self.config.detector_type

        if detector_type in (DetectorType.AST, DetectorType.BIRDNET, DetectorType.OPENSOUNDSCAPE):
            self._init_ml_model()
        else:
            self._init_signal_detector()

    def _init_ml_model(self) -> None:
        """Initialize ML-based model."""
        try:
            from bioamla.core.ml import ModelConfig, load_model

            config = ModelConfig(
                min_confidence=self.config.min_confidence,
                top_k=self.config.top_k,
                clip_duration=self.config.clip_duration,
                overlap=self.config.overlap,
                batch_size=self.config.batch_size,
                device="cuda" if self.config.use_gpu else "cpu",
            )

            self._model = load_model(
                model_type=self.config.detector_type.value,
                model_path=self.config.model_path,
                config=config,
            )

        except ImportError as e:
            raise RuntimeError(
                f"bioamla ML module not available. Install bioamla with ML support: {e}"
            )

    def _init_signal_detector(self) -> None:
        """Initialize signal-based detector."""
        try:
            from bioamla.core.detection.detectors import (
                AcceleratingPatternDetector,
                BandLimitedEnergyDetector,
                CWTPeakDetector,
                RibbitDetector,
            )

            params = self.config.detector_params
            detector_type = self.config.detector_type

            if detector_type == DetectorType.ENERGY:
                self._detector = BandLimitedEnergyDetector(
                    low_freq=params.get("low_freq", 500.0),
                    high_freq=params.get("high_freq", 5000.0),
                    threshold_db=params.get("threshold_db", -20.0),
                    min_duration=params.get("min_duration", 0.05),
                )
            elif detector_type == DetectorType.RIBBIT:
                self._detector = RibbitDetector(
                    pulse_rate_hz=params.get("pulse_rate_hz", 10.0),
                    low_freq=params.get("low_freq", 500.0),
                    high_freq=params.get("high_freq", 5000.0),
                    min_score=params.get("min_score", 0.3),
                )
            elif detector_type == DetectorType.CWT:
                self._detector = CWTPeakDetector(
                    snr_threshold=params.get("snr_threshold", 2.0),
                    min_peak_distance=params.get("min_peak_distance", 0.01),
                    low_freq=params.get("low_freq"),
                    high_freq=params.get("high_freq"),
                )
            elif detector_type == DetectorType.ACCELERATING:
                self._detector = AcceleratingPatternDetector(
                    min_pulses=params.get("min_pulses", 5),
                    acceleration_threshold=params.get("acceleration_threshold", 1.5),
                    low_freq=params.get("low_freq", 500.0),
                    high_freq=params.get("high_freq", 5000.0),
                )
            else:
                raise ValueError(f"Unknown detector type: {detector_type}")

        except ImportError as e:
            raise RuntimeError(
                f"bioamla detection module not available. Install bioamla: {e}"
            )

    def _process_file(self, filepath: str) -> List[DetectionResult]:
        """Process a single audio file."""
        if self._model is not None:
            return self._process_with_ml_model(filepath)
        elif self._detector is not None:
            return self._process_with_signal_detector(filepath)
        else:
            raise RuntimeError("No detector initialized")

    def _process_with_ml_model(self, filepath: str) -> List[DetectionResult]:
        """Process file using ML model."""
        predictions = self._model.predict(filepath)

        detections = []
        for pred in predictions:
            # Filter by confidence
            if pred.confidence < self.config.min_confidence:
                continue

            detection = DetectionResult(
                start_time=pred.start_time,
                end_time=pred.end_time,
                confidence=pred.confidence,
                label=pred.label,
                filepath=filepath,
                metadata=pred.metadata if hasattr(pred, "metadata") else {},
            )
            detections.append(detection)

        return detections

    def _process_with_signal_detector(self, filepath: str) -> List[DetectionResult]:
        """Process file using signal-based detector."""
        import librosa

        # Load audio
        audio, sample_rate = librosa.load(filepath, sr=None, mono=True)

        # Run detection
        raw_detections = self._detector.detect(audio, sample_rate)

        # Convert to DetectionResult
        detections = []
        for det in raw_detections:
            # Filter by confidence
            if det.confidence < self.config.min_confidence:
                continue

            detection = DetectionResult(
                start_time=det.start_time,
                end_time=det.end_time,
                confidence=det.confidence,
                label=det.label,
                frequency_low=det.frequency_low,
                frequency_high=det.frequency_high,
                filepath=filepath,
                metadata=det.metadata if hasattr(det, "metadata") else {},
            )
            detections.append(detection)

        return detections

    def _cleanup(self) -> None:
        """Clean up resources."""
        self._model = None
        self._detector = None


class SingleFileDetectionWorker(QThread):
    """
    Simplified worker for detecting on a single file with audio array.

    Useful when the audio is already loaded in memory.

    Signals:
        progress(message): Status updates.
        result(detections): List of DetectionResult.
        error(message): Error message.
    """

    progress = pyqtSignal(str)
    result = pyqtSignal(list)  # List[DetectionResult]
    error = pyqtSignal(str)

    def __init__(
        self,
        audio_data,
        sample_rate: int,
        config: DetectionConfig,
        filepath: Optional[str] = None,
        parent=None,
    ):
        """
        Initialize single file detection worker.

        Args:
            audio_data: Audio samples as numpy array.
            sample_rate: Sample rate in Hz.
            config: Detection configuration.
            filepath: Optional source filepath for metadata.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.config = config
        self.filepath = filepath
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation."""
        self._cancelled = True

    def run(self) -> None:
        """Execute detection on audio data."""
        try:
            self.progress.emit("Initializing detector...")

            detector_type = self.config.detector_type

            if detector_type in (DetectorType.AST, DetectorType.BIRDNET, DetectorType.OPENSOUNDSCAPE):
                detections = self._run_ml_detection()
            else:
                detections = self._run_signal_detection()

            self.progress.emit(f"Complete: {len(detections)} detections found")
            self.result.emit(detections)

        except Exception as e:
            self.error.emit(str(e))

    def _run_ml_detection(self) -> List[DetectionResult]:
        """Run ML-based detection on audio array."""
        try:
            from bioamla.core.ml import ModelConfig, load_model

            config = ModelConfig(
                min_confidence=self.config.min_confidence,
                top_k=self.config.top_k,
                clip_duration=self.config.clip_duration,
                overlap=self.config.overlap,
                device="cuda" if self.config.use_gpu else "cpu",
            )

            model = load_model(
                model_type=self.config.detector_type.value,
                model_path=self.config.model_path,
                config=config,
            )

            self.progress.emit("Running inference...")
            predictions = model.predict(self.audio_data, sample_rate=self.sample_rate)

            detections = []
            for pred in predictions:
                if pred.confidence < self.config.min_confidence:
                    continue

                detection = DetectionResult(
                    start_time=pred.start_time,
                    end_time=pred.end_time,
                    confidence=pred.confidence,
                    label=pred.label,
                    filepath=self.filepath,
                )
                detections.append(detection)

            return detections

        except ImportError as e:
            raise RuntimeError(f"bioamla ML module not available: {e}")

    def _run_signal_detection(self) -> List[DetectionResult]:
        """Run signal-based detection on audio array."""
        try:
            from bioamla.core.detection.detectors import (
                AcceleratingPatternDetector,
                BandLimitedEnergyDetector,
                CWTPeakDetector,
                RibbitDetector,
            )

            params = self.config.detector_params
            detector_type = self.config.detector_type

            # Create detector
            if detector_type == DetectorType.ENERGY:
                detector = BandLimitedEnergyDetector(**params)
            elif detector_type == DetectorType.RIBBIT:
                detector = RibbitDetector(**params)
            elif detector_type == DetectorType.CWT:
                detector = CWTPeakDetector(**params)
            elif detector_type == DetectorType.ACCELERATING:
                detector = AcceleratingPatternDetector(**params)
            else:
                raise ValueError(f"Unknown detector type: {detector_type}")

            self.progress.emit("Running detection...")

            # Ensure mono
            audio = self.audio_data
            if audio.ndim > 1:
                audio = audio.mean(axis=0)

            raw_detections = detector.detect(audio, self.sample_rate)

            detections = []
            for det in raw_detections:
                if det.confidence < self.config.min_confidence:
                    continue

                detection = DetectionResult(
                    start_time=det.start_time,
                    end_time=det.end_time,
                    confidence=det.confidence,
                    label=det.label,
                    frequency_low=det.frequency_low,
                    frequency_high=det.frequency_high,
                    filepath=self.filepath,
                    metadata=det.metadata if hasattr(det, "metadata") else {},
                )
                detections.append(detection)

            return detections

        except ImportError as e:
            raise RuntimeError(f"bioamla detection module not available: {e}")
