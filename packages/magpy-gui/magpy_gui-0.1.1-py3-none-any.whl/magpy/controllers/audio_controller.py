"""
Audio Controller - Bridge between MagPy GUI and bioamla core.

Provides a unified interface for audio operations, delegating to bioamla
controllers where available and providing fallback implementations as needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Try to import bioamla controllers
try:
    from bioamla.controllers import (
        AudioFileController as BioamlaFileController,
        AudioTransformController as BioamlaTransformController,
        IndicesController as BioamlaIndicesController,
        AnnotationController as BioamlaAnnotationController,
        ControllerResult,
        AudioData,
    )
    from bioamla.core.annotations import Annotation as CoreAnnotation
    BIOAMLA_AVAILABLE = True
except ImportError:
    BIOAMLA_AVAILABLE = False
    ControllerResult = None
    AudioData = None
    CoreAnnotation = None


@dataclass
class AudioMetadata:
    """Metadata for an audio file."""
    filepath: str
    duration: float
    sample_rate: int
    channels: int
    bit_depth: Optional[int] = None
    format: Optional[str] = None
    file_size: Optional[int] = None


@dataclass
class TransformOperation:
    """Record of a transform operation for undo support."""
    name: str
    parameters: Dict[str, Any]
    audio_before: Optional[np.ndarray] = None
    sample_rate_before: Optional[int] = None


class AudioController:
    """
    Bridge between MagPy GUI and bioamla core.

    Provides:
    - File operations (open, save, get metadata)
    - Transform operations (bandpass, normalize, denoise, etc.)
    - Analysis operations (acoustic indices)
    - Undo/redo support for transforms

    When bioamla is available, delegates to bioamla controllers.
    When bioamla is not available, provides stub implementations.
    """

    def __init__(self, max_undo_levels: int = 50):
        """
        Initialize the audio controller.

        Args:
            max_undo_levels: Maximum number of undo levels to maintain.
        """
        self._max_undo_levels = max_undo_levels
        self._undo_stack: List[TransformOperation] = []
        self._redo_stack: List[TransformOperation] = []

        # Current audio state
        self._current_audio: Optional[np.ndarray] = None
        self._current_sample_rate: Optional[int] = None
        self._source_path: Optional[str] = None

        # Initialize bioamla controllers if available
        if BIOAMLA_AVAILABLE:
            self._file_controller = BioamlaFileController()
            self._transform_controller = BioamlaTransformController()
            self._indices_controller = BioamlaIndicesController()
            self._annotation_controller = BioamlaAnnotationController()
        else:
            self._file_controller = None
            self._transform_controller = None
            self._indices_controller = None
            self._annotation_controller = None

    @property
    def bioamla_available(self) -> bool:
        """Check if bioamla is available."""
        return BIOAMLA_AVAILABLE

    @property
    def has_audio(self) -> bool:
        """Check if audio is currently loaded."""
        return self._current_audio is not None

    @property
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0

    @property
    def undo_description(self) -> Optional[str]:
        """Get description of the next undo operation."""
        if self._undo_stack:
            return self._undo_stack[-1].name
        return None

    @property
    def redo_description(self) -> Optional[str]:
        """Get description of the next redo operation."""
        if self._redo_stack:
            return self._redo_stack[-1].name
        return None

    # =========================================================================
    # File Operations
    # =========================================================================

    def load_file(self, filepath: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Load an audio file.

        Args:
            filepath: Path to the audio file.

        Returns:
            Tuple of (success, message, metadata_dict).
        """
        if BIOAMLA_AVAILABLE and self._file_controller:
            result = self._file_controller.open(filepath)
            if result.success:
                audio_data = result.data
                self._current_audio = audio_data.samples
                self._current_sample_rate = audio_data.sample_rate
                self._source_path = filepath
                self._clear_undo_stacks()

                metadata = {
                    "filepath": filepath,
                    "duration": audio_data.duration,
                    "sample_rate": audio_data.sample_rate,
                    "channels": audio_data.channels,
                }
                return True, result.message or "File loaded", metadata
            else:
                return False, result.error or "Failed to load file", None
        else:
            # Fallback: use soundfile directly
            try:
                import soundfile as sf
                audio, sr = sf.read(filepath, dtype="float32")
                info = sf.info(filepath)

                if audio.ndim == 1:
                    audio = audio.reshape(-1, 1)

                self._current_audio = audio
                self._current_sample_rate = sr
                self._source_path = filepath
                self._clear_undo_stacks()

                metadata = {
                    "filepath": filepath,
                    "duration": len(audio) / sr,
                    "sample_rate": sr,
                    "channels": audio.shape[1] if audio.ndim > 1 else 1,
                    "format": info.format,
                    "subtype": info.subtype,
                }
                return True, f"Loaded {filepath}", metadata

            except Exception as e:
                return False, f"Failed to load file: {e}", None

    def save_file(
        self,
        filepath: str,
        audio: Optional[np.ndarray] = None,
        sample_rate: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Save audio to a file.

        Args:
            filepath: Output file path.
            audio: Audio data (uses current if not provided).
            sample_rate: Sample rate (uses current if not provided).

        Returns:
            Tuple of (success, message).
        """
        audio = audio if audio is not None else self._current_audio
        sample_rate = sample_rate if sample_rate is not None else self._current_sample_rate

        if audio is None or sample_rate is None:
            return False, "No audio data to save"

        if BIOAMLA_AVAILABLE and self._file_controller:
            audio_data = AudioData(
                samples=audio.flatten() if audio.ndim > 1 and audio.shape[1] == 1 else audio,
                sample_rate=sample_rate,
                channels=1 if audio.ndim == 1 else audio.shape[1],
                source_path=self._source_path,
            )
            result = self._file_controller.save(audio_data, filepath)
            if result.success:
                return True, result.message or f"Saved to {filepath}"
            else:
                return False, result.error or "Failed to save file"
        else:
            # Fallback: use soundfile directly
            try:
                import soundfile as sf
                data = audio.squeeze() if audio.ndim > 1 and audio.shape[1] == 1 else audio
                sf.write(filepath, data, sample_rate)
                return True, f"Saved to {filepath}"
            except Exception as e:
                return False, f"Failed to save file: {e}"

    def get_metadata(self, filepath: str) -> Tuple[bool, Optional[AudioMetadata]]:
        """
        Get metadata for an audio file without loading it.

        Args:
            filepath: Path to the audio file.

        Returns:
            Tuple of (success, AudioMetadata or None).
        """
        try:
            import soundfile as sf
            import os

            info = sf.info(filepath)

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

            metadata = AudioMetadata(
                filepath=filepath,
                duration=info.duration,
                sample_rate=info.samplerate,
                channels=info.channels,
                bit_depth=bit_depth,
                format=f"{info.format} ({info.subtype})",
                file_size=os.path.getsize(filepath),
            )
            return True, metadata

        except Exception:
            return False, None

    # =========================================================================
    # Transform Operations
    # =========================================================================

    def _push_undo(self, name: str, parameters: Dict[str, Any]):
        """Push current state to undo stack before a transform."""
        if self._current_audio is not None:
            op = TransformOperation(
                name=name,
                parameters=parameters,
                audio_before=self._current_audio.copy(),
                sample_rate_before=self._current_sample_rate,
            )
            self._undo_stack.append(op)

            # Limit stack size
            while len(self._undo_stack) > self._max_undo_levels:
                self._undo_stack.pop(0)

            # Clear redo stack on new operation
            self._redo_stack.clear()

    def _get_audio_data(self) -> Optional[AudioData]:
        """Get current audio as AudioData object (for bioamla)."""
        if not BIOAMLA_AVAILABLE or self._current_audio is None:
            return None

        samples = self._current_audio
        if samples.ndim > 1 and samples.shape[1] == 1:
            samples = samples.flatten()

        return AudioData(
            samples=samples,
            sample_rate=self._current_sample_rate,
            channels=1 if samples.ndim == 1 else samples.shape[1],
            source_path=self._source_path,
        )

    def _update_from_audio_data(self, audio_data: AudioData):
        """Update current audio from AudioData object."""
        samples = audio_data.samples
        if samples.ndim == 1:
            samples = samples.reshape(-1, 1)
        self._current_audio = samples
        self._current_sample_rate = audio_data.sample_rate

    def apply_bandpass(
        self,
        low_hz: float,
        high_hz: float,
        order: int = 5,
    ) -> Tuple[bool, str]:
        """
        Apply bandpass filter to current audio.

        Args:
            low_hz: Lower cutoff frequency.
            high_hz: Upper cutoff frequency.
            order: Filter order.

        Returns:
            Tuple of (success, message).
        """
        if not self.has_audio:
            return False, "No audio loaded"

        self._push_undo("Bandpass Filter", {"low_hz": low_hz, "high_hz": high_hz, "order": order})

        if BIOAMLA_AVAILABLE and self._transform_controller:
            audio_data = self._get_audio_data()
            result = self._transform_controller.apply_bandpass(audio_data, low_hz, high_hz, order)
            if result.success:
                self._update_from_audio_data(result.data)
                return True, result.message or f"Applied bandpass filter {low_hz}-{high_hz}Hz"
            else:
                self._undo_stack.pop()  # Remove failed operation
                return False, result.error or "Bandpass filter failed"
        else:
            # Stub: bioamla not available
            return False, "Bandpass filter requires bioamla (not installed)"

    def apply_normalize(self, target_db: float = -20.0) -> Tuple[bool, str]:
        """
        Apply loudness normalization to current audio.

        Args:
            target_db: Target loudness in dBFS.

        Returns:
            Tuple of (success, message).
        """
        if not self.has_audio:
            return False, "No audio loaded"

        self._push_undo("Normalize", {"target_db": target_db})

        if BIOAMLA_AVAILABLE and self._transform_controller:
            audio_data = self._get_audio_data()
            result = self._transform_controller.normalize_loudness(audio_data, target_db)
            if result.success:
                self._update_from_audio_data(result.data)
                return True, result.message or f"Normalized to {target_db} dBFS"
            else:
                self._undo_stack.pop()
                return False, result.error or "Normalization failed"
        else:
            return False, "Normalize requires bioamla (not installed)"

    def apply_denoise(self, strength: float = 1.0) -> Tuple[bool, str]:
        """
        Apply noise reduction to current audio.

        Args:
            strength: Noise reduction strength (0.0 to 2.0).

        Returns:
            Tuple of (success, message).
        """
        if not self.has_audio:
            return False, "No audio loaded"

        self._push_undo("Denoise", {"strength": strength})

        if BIOAMLA_AVAILABLE and self._transform_controller:
            audio_data = self._get_audio_data()
            result = self._transform_controller.denoise(audio_data, strength)
            if result.success:
                self._update_from_audio_data(result.data)
                return True, result.message or f"Applied noise reduction (strength={strength})"
            else:
                self._undo_stack.pop()
                return False, result.error or "Denoise failed"
        else:
            return False, "Denoise requires bioamla (not installed)"

    def apply_resample(self, target_sample_rate: int) -> Tuple[bool, str]:
        """
        Resample current audio to a different sample rate.

        Args:
            target_sample_rate: Target sample rate in Hz.

        Returns:
            Tuple of (success, message).
        """
        if not self.has_audio:
            return False, "No audio loaded"

        if target_sample_rate == self._current_sample_rate:
            return True, "Already at target sample rate"

        self._push_undo("Resample", {"target_sample_rate": target_sample_rate})

        if BIOAMLA_AVAILABLE and self._transform_controller:
            audio_data = self._get_audio_data()
            result = self._transform_controller.resample(audio_data, target_sample_rate)
            if result.success:
                self._update_from_audio_data(result.data)
                return True, result.message or f"Resampled to {target_sample_rate}Hz"
            else:
                self._undo_stack.pop()
                return False, result.error or "Resample failed"
        else:
            return False, "Resample requires bioamla (not installed)"

    def apply_trim(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """
        Trim current audio to a time range.

        Args:
            start_time: Start time in seconds.
            end_time: End time in seconds.

        Returns:
            Tuple of (success, message).
        """
        if not self.has_audio:
            return False, "No audio loaded"

        self._push_undo("Trim", {"start_time": start_time, "end_time": end_time})

        if BIOAMLA_AVAILABLE and self._transform_controller:
            audio_data = self._get_audio_data()
            result = self._transform_controller.trim(audio_data, start_time, end_time)
            if result.success:
                self._update_from_audio_data(result.data)
                return True, result.message or f"Trimmed to {start_time or 0}s - {end_time or 'end'}"
            else:
                self._undo_stack.pop()
                return False, result.error or "Trim failed"
        else:
            return False, "Trim requires bioamla (not installed)"

    # =========================================================================
    # Analysis Operations
    # =========================================================================

    def compute_indices(self) -> Tuple[bool, str, Optional[Dict[str, float]]]:
        """
        Compute acoustic indices for current audio.

        Returns:
            Tuple of (success, message, indices_dict or None).
        """
        if not self.has_audio:
            return False, "No audio loaded", None

        if BIOAMLA_AVAILABLE and self._indices_controller:
            audio_data = self._get_audio_data()
            result = self._indices_controller.calculate(audio_data)
            if result.success:
                indices_dict = result.data.to_dict()
                return True, result.message or "Computed acoustic indices", indices_dict
            else:
                return False, result.error or "Index calculation failed", None
        else:
            return False, "Acoustic indices require bioamla (not installed)", None

    def get_available_indices(self) -> List[str]:
        """Get list of available acoustic index names."""
        if BIOAMLA_AVAILABLE and self._indices_controller:
            return self._indices_controller.get_available_indices()
        return []

    # =========================================================================
    # Undo/Redo
    # =========================================================================

    def undo(self) -> Tuple[bool, str]:
        """
        Undo the last transform operation.

        Returns:
            Tuple of (success, message).
        """
        if not self._undo_stack:
            return False, "Nothing to undo"

        op = self._undo_stack.pop()

        # Save current state for redo
        if self._current_audio is not None:
            redo_op = TransformOperation(
                name=op.name,
                parameters=op.parameters,
                audio_before=self._current_audio.copy(),
                sample_rate_before=self._current_sample_rate,
            )
            self._redo_stack.append(redo_op)

        # Restore previous state
        self._current_audio = op.audio_before
        self._current_sample_rate = op.sample_rate_before

        return True, f"Undid: {op.name}"

    def redo(self) -> Tuple[bool, str]:
        """
        Redo the last undone operation.

        Returns:
            Tuple of (success, message).
        """
        if not self._redo_stack:
            return False, "Nothing to redo"

        op = self._redo_stack.pop()

        # Save current state for undo
        if self._current_audio is not None:
            undo_op = TransformOperation(
                name=op.name,
                parameters=op.parameters,
                audio_before=self._current_audio.copy(),
                sample_rate_before=self._current_sample_rate,
            )
            self._undo_stack.append(undo_op)

        # Restore redo state
        self._current_audio = op.audio_before
        self._current_sample_rate = op.sample_rate_before

        return True, f"Redid: {op.name}"

    def _clear_undo_stacks(self):
        """Clear both undo and redo stacks."""
        self._undo_stack.clear()
        self._redo_stack.clear()

    # =========================================================================
    # Utility
    # =========================================================================

    def get_current_audio(self) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """
        Get the current audio data and sample rate.

        Returns:
            Tuple of (audio_array, sample_rate) or (None, None).
        """
        return self._current_audio, self._current_sample_rate

    def set_current_audio(self, audio: np.ndarray, sample_rate: int):
        """
        Set the current audio data (for external modifications).

        Args:
            audio: Audio samples.
            sample_rate: Sample rate.
        """
        self._current_audio = audio
        self._current_sample_rate = sample_rate

    def clear(self):
        """Clear all audio data and reset controller state."""
        self._current_audio = None
        self._current_sample_rate = None
        self._source_path = None
        self._clear_undo_stacks()

    # =========================================================================
    # Annotation Operations
    # =========================================================================

    def import_raven_annotations(
        self,
        filepath: str,
        label_column: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """
        Import annotations from a Raven selection table.

        Args:
            filepath: Path to the Raven selection table (.txt).
            label_column: Optional column name to use for labels.

        Returns:
            Tuple of (success, message, list of annotation dicts).
        """
        if BIOAMLA_AVAILABLE and self._annotation_controller:
            result = self._annotation_controller.import_raven(filepath, label_column=label_column)
            if result.success:
                annotations = [ann.to_dict() for ann in result.data.annotations]
                return True, result.message or "Imported annotations", annotations
            else:
                return False, result.error or "Failed to import annotations", None
        else:
            return False, "Annotation import requires bioamla (not installed)", None

    def import_csv_annotations(
        self,
        filepath: str,
        start_time_col: str = "start_time",
        end_time_col: str = "end_time",
        label_col: str = "label",
    ) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """
        Import annotations from a CSV file.

        Args:
            filepath: Path to the CSV file.
            start_time_col: Column name for start time.
            end_time_col: Column name for end time.
            label_col: Column name for label.

        Returns:
            Tuple of (success, message, list of annotation dicts).
        """
        if BIOAMLA_AVAILABLE and self._annotation_controller:
            result = self._annotation_controller.import_csv(
                filepath,
                start_time_col=start_time_col,
                end_time_col=end_time_col,
                label_col=label_col,
            )
            if result.success:
                annotations = [ann.to_dict() for ann in result.data.annotations]
                return True, result.message or "Imported annotations", annotations
            else:
                return False, result.error or "Failed to import annotations", None
        else:
            return False, "Annotation import requires bioamla (not installed)", None

    def export_raven_annotations(
        self,
        annotations: List[Dict[str, Any]],
        output_path: str,
    ) -> Tuple[bool, str]:
        """
        Export annotations to a Raven selection table.

        Args:
            annotations: List of annotation dicts.
            output_path: Output file path (.txt).

        Returns:
            Tuple of (success, message).
        """
        if BIOAMLA_AVAILABLE and self._annotation_controller:
            # Convert dicts to CoreAnnotation objects
            core_annotations = [CoreAnnotation.from_dict(a) for a in annotations]
            result = self._annotation_controller.export_raven(core_annotations, output_path)
            if result.success:
                return True, result.message or f"Exported to {output_path}"
            else:
                return False, result.error or "Failed to export annotations"
        else:
            return False, "Annotation export requires bioamla (not installed)"

    def export_csv_annotations(
        self,
        annotations: List[Dict[str, Any]],
        output_path: str,
    ) -> Tuple[bool, str]:
        """
        Export annotations to a CSV file.

        Args:
            annotations: List of annotation dicts.
            output_path: Output file path (.csv).

        Returns:
            Tuple of (success, message).
        """
        if BIOAMLA_AVAILABLE and self._annotation_controller:
            core_annotations = [CoreAnnotation.from_dict(a) for a in annotations]
            result = self._annotation_controller.export_csv(core_annotations, output_path)
            if result.success:
                return True, result.message or f"Exported to {output_path}"
            else:
                return False, result.error or "Failed to export annotations"
        else:
            return False, "Annotation export requires bioamla (not installed)"

    def export_parquet_annotations(
        self,
        annotations: List[Dict[str, Any]],
        output_path: str,
    ) -> Tuple[bool, str]:
        """
        Export annotations to a Parquet file.

        Args:
            annotations: List of annotation dicts.
            output_path: Output file path (.parquet).

        Returns:
            Tuple of (success, message).
        """
        if BIOAMLA_AVAILABLE and self._annotation_controller:
            core_annotations = [CoreAnnotation.from_dict(a) for a in annotations]
            result = self._annotation_controller.export_parquet(core_annotations, output_path)
            if result.success:
                return True, result.message or f"Exported to {output_path}"
            else:
                return False, result.error or "Failed to export annotations"
        else:
            return False, "Annotation export requires bioamla (not installed)"

    def extract_annotation_clips(
        self,
        annotations: List[Dict[str, Any]],
        audio_path: str,
        output_dir: str,
        padding_ms: float = 0.0,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Extract audio clips from annotations.

        Args:
            annotations: List of annotation dicts.
            audio_path: Path to the source audio file.
            output_dir: Directory for output clips.
            padding_ms: Padding in milliseconds.

        Returns:
            Tuple of (success, message, extraction result dict).
        """
        if BIOAMLA_AVAILABLE and self._annotation_controller:
            core_annotations = [CoreAnnotation.from_dict(a) for a in annotations]
            result = self._annotation_controller.extract_clips(
                core_annotations, audio_path, output_dir, padding_ms=padding_ms
            )
            if result.success:
                extraction_result = {
                    "total_clips": result.data.total_clips,
                    "extracted_clips": result.data.extracted_clips,
                    "failed_clips": result.data.failed_clips,
                    "output_directory": result.data.output_directory,
                }
                return True, result.message or "Extracted clips", extraction_result
            else:
                return False, result.error or "Failed to extract clips", None
        else:
            return False, "Clip extraction requires bioamla (not installed)", None

    def compute_annotation_measurements(
        self,
        annotation: Dict[str, Any],
        audio_path: Optional[str] = None,
        metrics: Optional[List[str]] = None,
    ) -> Tuple[bool, str, Optional[Dict[str, float]]]:
        """
        Compute measurements for an annotation.

        Args:
            annotation: Annotation dict.
            audio_path: Path to audio file (uses current source if not provided).
            metrics: List of metrics to compute.

        Returns:
            Tuple of (success, message, measurements dict).
        """
        if BIOAMLA_AVAILABLE and self._annotation_controller:
            audio_path = audio_path or self._source_path
            if not audio_path:
                return False, "No audio file specified", None

            core_annotation = CoreAnnotation.from_dict(annotation)
            result = self._annotation_controller.compute_measurements(
                core_annotation, audio_path, metrics=metrics
            )
            if result.success:
                return True, result.message or "Computed measurements", result.data.measurements
            else:
                return False, result.error or "Failed to compute measurements", None
        else:
            return False, "Measurements require bioamla (not installed)", None
