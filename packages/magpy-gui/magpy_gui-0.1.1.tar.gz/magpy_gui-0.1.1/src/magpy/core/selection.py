"""
Selection and annotation module for managing time-frequency selections.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union
import uuid

import pandas as pd


@dataclass
class Selection:
    """
    Represents a time-frequency selection with optional annotations.

    Supports standard bioacoustics selection table formats.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    channel: int = 1
    begin_time: float = 0.0  # seconds
    end_time: float = 0.0  # seconds
    low_freq: Optional[float] = None  # Hz
    high_freq: Optional[float] = None  # Hz
    annotations: Dict[str, Any] = field(default_factory=dict)
    measurements: Dict[str, float] = field(default_factory=dict)

    # Optional file reference for multi-file selections
    begin_file: Optional[str] = None
    end_file: Optional[str] = None

    @property
    def duration(self) -> float:
        """Selection duration in seconds."""
        return self.end_time - self.begin_time

    @property
    def bandwidth(self) -> Optional[float]:
        """Selection bandwidth in Hz, if frequency bounds are set."""
        if self.low_freq is not None and self.high_freq is not None:
            return self.high_freq - self.low_freq
        return None

    @property
    def center_time(self) -> float:
        """Center time of the selection."""
        return (self.begin_time + self.end_time) / 2

    @property
    def center_freq(self) -> Optional[float]:
        """Center frequency of the selection."""
        if self.low_freq is not None and self.high_freq is not None:
            return (self.low_freq + self.high_freq) / 2
        return None

    def overlaps_time(self, start: float, end: float) -> bool:
        """Check if this selection overlaps with a time range."""
        return not (self.end_time <= start or self.begin_time >= end)

    def overlaps_freq(self, low: float, high: float) -> bool:
        """Check if this selection overlaps with a frequency range."""
        if self.low_freq is None or self.high_freq is None:
            return True  # Unbounded in frequency
        return not (self.high_freq <= low or self.low_freq >= high)

    def contains_point(self, time: float, freq: Optional[float] = None) -> bool:
        """Check if a time-frequency point is within this selection."""
        in_time = self.begin_time <= time <= self.end_time
        if freq is None or self.low_freq is None or self.high_freq is None:
            return in_time
        return in_time and self.low_freq <= freq <= self.high_freq

    def to_dict(self) -> Dict[str, Any]:
        """Convert selection to dictionary for serialization."""
        result = {
            "Selection": self.id,
            "Channel": self.channel,
            "Begin Time (s)": self.begin_time,
            "End Time (s)": self.end_time,
            "Delta Time (s)": self.duration,
        }

        if self.low_freq is not None:
            result["Low Freq (Hz)"] = self.low_freq
        if self.high_freq is not None:
            result["High Freq (Hz)"] = self.high_freq
        if self.bandwidth is not None:
            result["Delta Freq (Hz)"] = self.bandwidth

        if self.begin_file:
            result["Begin File"] = self.begin_file
        if self.end_file:
            result["End File"] = self.end_file

        # Add annotations
        result.update(self.annotations)

        # Add measurements
        result.update(self.measurements)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Selection":
        """Create a Selection from a dictionary."""
        # Standard columns
        selection_id = str(data.get("Selection", str(uuid.uuid4())[:8]))
        channel = int(data.get("Channel", 1))
        begin_time = float(data.get("Begin Time (s)", 0))
        end_time = float(data.get("End Time (s)", 0))
        low_freq = data.get("Low Freq (Hz)")
        high_freq = data.get("High Freq (Hz)")
        begin_file = data.get("Begin File")
        end_file = data.get("End File")

        if low_freq is not None:
            low_freq = float(low_freq)
        if high_freq is not None:
            high_freq = float(high_freq)

        # Separate annotations from known columns
        known_columns = {
            "Selection",
            "Channel",
            "Begin Time (s)",
            "End Time (s)",
            "Delta Time (s)",
            "Low Freq (Hz)",
            "High Freq (Hz)",
            "Delta Freq (Hz)",
            "Begin File",
            "End File",
        }

        annotations = {}
        measurements = {}

        for key, value in data.items():
            if key not in known_columns:
                # Try to determine if it's a measurement or annotation
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    measurements[key] = float(value)
                else:
                    annotations[key] = value

        return cls(
            id=selection_id,
            channel=channel,
            begin_time=begin_time,
            end_time=end_time,
            low_freq=low_freq,
            high_freq=high_freq,
            annotations=annotations,
            measurements=measurements,
            begin_file=begin_file,
            end_file=end_file,
        )


class SelectionTable:
    """
    Manages a collection of selections with annotation support.

    Supports tab-delimited and CSV selection table formats.
    """

    def __init__(self, name: str = "Untitled"):
        """
        Initialize an empty selection table.

        Args:
            name: Name of the selection table.
        """
        self.name = name
        self._selections: List[Selection] = []
        self._annotation_columns: List[str] = []
        self._created: datetime = datetime.now()
        self._modified: datetime = datetime.now()
        self._filepath: Optional[Path] = None

    @property
    def selections(self) -> List[Selection]:
        """Return list of selections."""
        return self._selections

    @property
    def annotation_columns(self) -> List[str]:
        """Return list of user-defined annotation column names."""
        return self._annotation_columns

    def __len__(self) -> int:
        return len(self._selections)

    def __iter__(self) -> Iterator[Selection]:
        return iter(self._selections)

    def __getitem__(self, index: int) -> Selection:
        return self._selections[index]

    def add(self, selection: Selection) -> None:
        """Add a selection to the table."""
        self._selections.append(selection)
        self._modified = datetime.now()

    def remove(self, selection: Selection) -> None:
        """Remove a selection from the table."""
        self._selections.remove(selection)
        self._modified = datetime.now()

    def remove_by_id(self, selection_id: str) -> bool:
        """Remove a selection by its ID."""
        for i, sel in enumerate(self._selections):
            if sel.id == selection_id:
                del self._selections[i]
                self._modified = datetime.now()
                return True
        return False

    def clear(self) -> None:
        """Remove all selections."""
        self._selections.clear()
        self._modified = datetime.now()

    def get_by_id(self, selection_id: str) -> Optional[Selection]:
        """Get a selection by its ID."""
        for sel in self._selections:
            if sel.id == selection_id:
                return sel
        return None

    def find_at_time(self, time: float, channel: Optional[int] = None) -> List[Selection]:
        """Find all selections containing a specific time point."""
        results = []
        for sel in self._selections:
            if channel is not None and sel.channel != channel:
                continue
            if sel.begin_time <= time <= sel.end_time:
                results.append(sel)
        return results

    def find_in_range(
        self,
        start_time: float,
        end_time: float,
        low_freq: Optional[float] = None,
        high_freq: Optional[float] = None,
        channel: Optional[int] = None,
    ) -> List[Selection]:
        """Find all selections overlapping a time-frequency range."""
        results = []
        for sel in self._selections:
            if channel is not None and sel.channel != channel:
                continue
            if not sel.overlaps_time(start_time, end_time):
                continue
            if low_freq is not None and high_freq is not None:
                if not sel.overlaps_freq(low_freq, high_freq):
                    continue
            results.append(sel)
        return results

    def add_annotation_column(self, name: str) -> None:
        """Add a new annotation column."""
        if name not in self._annotation_columns:
            self._annotation_columns.append(name)
            self._modified = datetime.now()

    def remove_annotation_column(self, name: str) -> None:
        """Remove an annotation column (also removes from all selections)."""
        if name in self._annotation_columns:
            self._annotation_columns.remove(name)
            for sel in self._selections:
                sel.annotations.pop(name, None)
            self._modified = datetime.now()

    def sort_by_time(self, ascending: bool = True) -> None:
        """Sort selections by begin time."""
        self._selections.sort(key=lambda s: s.begin_time, reverse=not ascending)
        self._modified = datetime.now()

    def sort_by_channel(self, ascending: bool = True) -> None:
        """Sort selections by channel."""
        self._selections.sort(key=lambda s: s.channel, reverse=not ascending)
        self._modified = datetime.now()

    def to_dataframe(self) -> pd.DataFrame:
        """Convert selection table to pandas DataFrame."""
        rows = [sel.to_dict() for sel in self._selections]
        return pd.DataFrame(rows)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, name: str = "Imported") -> "SelectionTable":
        """Create a SelectionTable from a pandas DataFrame."""
        table = cls(name=name)
        for _, row in df.iterrows():
            selection = Selection.from_dict(row.to_dict())
            table.add(selection)
        return table

    def save(self, filepath: Union[str, Path], format: str = "tsv") -> None:
        """
        Save selection table to file.

        Args:
            filepath: Output file path.
            format: File format ('tsv' for tab-delimited, 'csv' for comma-delimited).
        """
        filepath = Path(filepath)
        df = self.to_dataframe()

        if format == "tsv":
            df.to_csv(filepath, sep="\t", index=False)
        elif format == "csv":
            df.to_csv(filepath, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

        self._filepath = filepath
        self._modified = datetime.now()

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "SelectionTable":
        """
        Load selection table from file.

        Args:
            filepath: Path to selection table file (TSV or CSV).

        Returns:
            Loaded SelectionTable.
        """
        filepath = Path(filepath)

        # Detect delimiter
        with open(filepath, "r") as f:
            first_line = f.readline()
            delimiter = "\t" if "\t" in first_line else ","

        df = pd.read_csv(filepath, delimiter=delimiter)
        table = cls.from_dataframe(df, name=filepath.stem)
        table._filepath = filepath

        # Detect annotation columns
        standard_columns = {
            "Selection",
            "Channel",
            "Begin Time (s)",
            "End Time (s)",
            "Delta Time (s)",
            "Low Freq (Hz)",
            "High Freq (Hz)",
            "Delta Freq (Hz)",
            "Begin File",
            "End File",
        }

        for col in df.columns:
            if col not in standard_columns:
                # Check if it's likely an annotation (non-numeric)
                if df[col].dtype == object:
                    table.add_annotation_column(col)

        return table

    def export_clips(
        self,
        audio_filepath: Union[str, Path],
        output_dir: Union[str, Path],
        padding: float = 0.0,
        filename_pattern: str = "<ii>_<a>",
    ) -> List[Path]:
        """
        Export audio clips for each selection.

        Args:
            audio_filepath: Path to source audio file.
            output_dir: Directory for output clips.
            padding: Padding before/after each selection in seconds.
            filename_pattern: Pattern for output filenames.
                <ii>: selection index
                <cc>: channel
                <a>: first annotation value
                <bt>: begin time
                <et>: end time

        Returns:
            List of paths to exported clips.
        """
        from .audio import AudioFile

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        audio = AudioFile(audio_filepath)
        exported = []

        for i, sel in enumerate(self._selections):
            # Build filename
            filename = filename_pattern
            filename = filename.replace("<ii>", f"{i:04d}")
            filename = filename.replace("<cc>", str(sel.channel))
            filename = filename.replace("<bt>", f"{sel.begin_time:.3f}")
            filename = filename.replace("<et>", f"{sel.end_time:.3f}")

            # Get first annotation value if available
            annotation = ""
            if sel.annotations:
                annotation = str(next(iter(sel.annotations.values())))
                annotation = annotation.replace(" ", "_").replace("/", "-")
            filename = filename.replace("<a>", annotation)

            # Get audio segment with padding
            start = max(0, sel.begin_time - padding)
            end = min(audio.duration, sel.end_time + padding)

            segment_data = audio.get_time_range(start, end, sel.channel - 1)

            # Save clip
            clip = AudioFile.from_array(segment_data, audio.sample_rate)
            output_path = output_dir / f"{filename}.wav"
            clip.save(output_path)
            exported.append(output_path)

        return exported

    def __repr__(self) -> str:
        return f"SelectionTable('{self.name}', {len(self)} selections)"


class AnnotationKeymap:
    """
    Maps keyboard keys to annotation values for rapid labeling.
    """

    def __init__(self, column: str):
        """
        Initialize an annotation keymap.

        Args:
            column: The annotation column this keymap applies to.
        """
        self.column = column
        self._mappings: Dict[str, str] = {}

    def add_mapping(self, key: str, value: str) -> None:
        """Add a key-to-value mapping."""
        self._mappings[key.lower()] = value

    def remove_mapping(self, key: str) -> None:
        """Remove a key mapping."""
        self._mappings.pop(key.lower(), None)

    def get_value(self, key: str) -> Optional[str]:
        """Get the annotation value for a key."""
        return self._mappings.get(key.lower())

    def apply(self, key: str, selection: Selection) -> bool:
        """
        Apply the keymap to a selection.

        Returns True if a mapping was found and applied.
        """
        value = self.get_value(key)
        if value is not None:
            selection.annotations[self.column] = value
            return True
        return False

    @property
    def mappings(self) -> Dict[str, str]:
        """Return all key-value mappings."""
        return self._mappings.copy()

    def save(self, filepath: Union[str, Path]) -> None:
        """Save keymap to JSON file."""
        import json

        filepath = Path(filepath)
        data = {"column": self.column, "mappings": self._mappings}
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "AnnotationKeymap":
        """Load keymap from JSON file."""
        import json

        filepath = Path(filepath)
        with open(filepath, "r") as f:
            data = json.load(f)

        keymap = cls(data["column"])
        keymap._mappings = data.get("mappings", {})
        return keymap
