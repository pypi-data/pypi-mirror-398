"""Tests for the selection module."""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import soundfile as sf

from magpy.core.selection import AnnotationKeymap, Selection, SelectionTable


class TestSelection:
    """Tests for Selection class."""

    def test_create_selection(self):
        """Test creating a basic selection."""
        sel = Selection(
            begin_time=1.0,
            end_time=2.0,
            low_freq=500,
            high_freq=2000,
        )

        assert sel.begin_time == 1.0
        assert sel.end_time == 2.0
        assert sel.low_freq == 500
        assert sel.high_freq == 2000
        assert sel.channel == 1
        assert sel.id is not None

    def test_duration(self):
        """Test duration property."""
        sel = Selection(begin_time=0.5, end_time=2.5)
        assert sel.duration == 2.0

    def test_bandwidth(self):
        """Test bandwidth property."""
        sel = Selection(begin_time=0, end_time=1, low_freq=1000, high_freq=5000)
        assert sel.bandwidth == 4000

    def test_bandwidth_none_when_unbounded(self):
        """Test bandwidth is None when frequency not specified."""
        sel = Selection(begin_time=0, end_time=1)
        assert sel.bandwidth is None

    def test_center_time(self):
        """Test center_time property."""
        sel = Selection(begin_time=1.0, end_time=3.0)
        assert sel.center_time == 2.0

    def test_center_freq(self):
        """Test center_freq property."""
        sel = Selection(begin_time=0, end_time=1, low_freq=1000, high_freq=3000)
        assert sel.center_freq == 2000

    def test_overlaps_time_true(self):
        """Test time overlap detection (overlapping)."""
        sel = Selection(begin_time=1.0, end_time=3.0)

        assert sel.overlaps_time(0.5, 1.5)  # Overlaps start
        assert sel.overlaps_time(2.5, 3.5)  # Overlaps end
        assert sel.overlaps_time(1.5, 2.5)  # Contained
        assert sel.overlaps_time(0.0, 4.0)  # Contains selection

    def test_overlaps_time_false(self):
        """Test time overlap detection (non-overlapping)."""
        sel = Selection(begin_time=1.0, end_time=3.0)

        assert not sel.overlaps_time(0.0, 1.0)  # Before (touching)
        assert not sel.overlaps_time(3.0, 4.0)  # After (touching)
        assert not sel.overlaps_time(0.0, 0.5)  # Before
        assert not sel.overlaps_time(3.5, 4.0)  # After

    def test_overlaps_freq(self):
        """Test frequency overlap detection."""
        sel = Selection(begin_time=0, end_time=1, low_freq=1000, high_freq=3000)

        assert sel.overlaps_freq(500, 1500)  # Overlaps low
        assert sel.overlaps_freq(2500, 4000)  # Overlaps high
        assert sel.overlaps_freq(1500, 2500)  # Contained
        assert not sel.overlaps_freq(3500, 4000)  # Above
        assert not sel.overlaps_freq(100, 500)  # Below

    def test_overlaps_freq_unbounded(self):
        """Test frequency overlap when selection is unbounded."""
        sel = Selection(begin_time=0, end_time=1)  # No freq bounds
        assert sel.overlaps_freq(0, 10000)  # Always overlaps

    def test_contains_point(self):
        """Test point containment."""
        sel = Selection(begin_time=1.0, end_time=3.0, low_freq=500, high_freq=2000)

        assert sel.contains_point(2.0, 1000)  # Inside
        assert sel.contains_point(1.0, 500)  # On boundary
        assert not sel.contains_point(0.5, 1000)  # Outside time
        assert not sel.contains_point(2.0, 3000)  # Outside freq

    def test_to_dict(self):
        """Test conversion to dictionary."""
        sel = Selection(
            id="test123",
            channel=2,
            begin_time=1.0,
            end_time=2.0,
            low_freq=500,
            high_freq=2000,
        )
        sel.annotations["Species"] = "Bird"
        sel.measurements["peak_freq"] = 1250.0

        d = sel.to_dict()

        assert d["Selection"] == "test123"
        assert d["Channel"] == 2
        assert d["Begin Time (s)"] == 1.0
        assert d["End Time (s)"] == 2.0
        assert d["Low Freq (Hz)"] == 500
        assert d["High Freq (Hz)"] == 2000
        assert d["Delta Time (s)"] == 1.0
        assert d["Species"] == "Bird"
        assert d["peak_freq"] == 1250.0

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            "Selection": "abc123",
            "Channel": 1,
            "Begin Time (s)": 0.5,
            "End Time (s)": 1.5,
            "Low Freq (Hz)": 1000,
            "High Freq (Hz)": 5000,
            "Species": "Whale",
            "rms_amplitude": 0.25,
        }

        sel = Selection.from_dict(d)

        assert sel.id == "abc123"
        assert sel.channel == 1
        assert sel.begin_time == 0.5
        assert sel.end_time == 1.5
        assert sel.low_freq == 1000
        assert sel.high_freq == 5000
        assert sel.annotations["Species"] == "Whale"
        assert sel.measurements["rms_amplitude"] == 0.25


class TestSelectionTable:
    """Tests for SelectionTable class."""

    def test_create_empty_table(self):
        """Test creating an empty selection table."""
        table = SelectionTable("Test Table")

        assert table.name == "Test Table"
        assert len(table) == 0

    def test_add_selection(self):
        """Test adding selections."""
        table = SelectionTable()
        sel = Selection(begin_time=0, end_time=1)

        table.add(sel)

        assert len(table) == 1
        assert table[0] == sel

    def test_remove_selection(self):
        """Test removing selections."""
        table = SelectionTable()
        sel1 = Selection(begin_time=0, end_time=1)
        sel2 = Selection(begin_time=1, end_time=2)
        table.add(sel1)
        table.add(sel2)

        table.remove(sel1)

        assert len(table) == 1
        assert table[0] == sel2

    def test_remove_by_id(self):
        """Test removing selection by ID."""
        table = SelectionTable()
        sel = Selection(id="remove_me", begin_time=0, end_time=1)
        table.add(sel)

        result = table.remove_by_id("remove_me")

        assert result is True
        assert len(table) == 0

    def test_remove_by_id_not_found(self):
        """Test removing nonexistent selection."""
        table = SelectionTable()

        result = table.remove_by_id("nonexistent")

        assert result is False

    def test_clear(self):
        """Test clearing all selections."""
        table = SelectionTable()
        for i in range(5):
            table.add(Selection(begin_time=i, end_time=i + 1))

        table.clear()

        assert len(table) == 0

    def test_get_by_id(self):
        """Test getting selection by ID."""
        table = SelectionTable()
        sel = Selection(id="find_me", begin_time=0, end_time=1)
        table.add(sel)

        found = table.get_by_id("find_me")

        assert found == sel

    def test_find_at_time(self):
        """Test finding selections at a time point."""
        table = SelectionTable()
        sel1 = Selection(begin_time=0, end_time=2)
        sel2 = Selection(begin_time=1, end_time=3)
        sel3 = Selection(begin_time=4, end_time=5)
        table.add(sel1)
        table.add(sel2)
        table.add(sel3)

        found = table.find_at_time(1.5)

        assert len(found) == 2
        assert sel1 in found
        assert sel2 in found
        assert sel3 not in found

    def test_find_in_range(self):
        """Test finding selections in a range."""
        table = SelectionTable()
        sel1 = Selection(begin_time=0, end_time=1, low_freq=500, high_freq=1000)
        sel2 = Selection(begin_time=0.5, end_time=1.5, low_freq=1500, high_freq=2000)
        sel3 = Selection(begin_time=2, end_time=3, low_freq=500, high_freq=1000)
        table.add(sel1)
        table.add(sel2)
        table.add(sel3)

        # Find overlapping time and frequency
        found = table.find_in_range(0.3, 0.8, low_freq=400, high_freq=1200)

        assert len(found) == 1
        assert sel1 in found

    def test_annotation_columns(self):
        """Test annotation column management."""
        table = SelectionTable()

        table.add_annotation_column("Species")
        table.add_annotation_column("Call Type")

        assert "Species" in table.annotation_columns
        assert "Call Type" in table.annotation_columns

        table.remove_annotation_column("Species")
        assert "Species" not in table.annotation_columns

    def test_sort_by_time(self):
        """Test sorting by time."""
        table = SelectionTable()
        table.add(Selection(begin_time=2, end_time=3))
        table.add(Selection(begin_time=0, end_time=1))
        table.add(Selection(begin_time=1, end_time=2))

        table.sort_by_time()

        assert table[0].begin_time == 0
        assert table[1].begin_time == 1
        assert table[2].begin_time == 2

    def test_to_dataframe(self):
        """Test conversion to DataFrame."""
        table = SelectionTable()
        sel1 = Selection(begin_time=0, end_time=1)
        sel1.annotations["Species"] = "Bird"
        sel2 = Selection(begin_time=1, end_time=2)
        sel2.annotations["Species"] = "Whale"
        table.add(sel1)
        table.add(sel2)

        df = table.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "Species" in df.columns

    def test_from_dataframe(self):
        """Test creation from DataFrame."""
        df = pd.DataFrame(
            {
                "Selection": ["1", "2"],
                "Channel": [1, 1],
                "Begin Time (s)": [0.0, 1.0],
                "End Time (s)": [1.0, 2.0],
                "Species": ["Bird", "Whale"],
            }
        )

        table = SelectionTable.from_dataframe(df)

        assert len(table) == 2
        assert table[0].annotations["Species"] == "Bird"
        assert table[1].annotations["Species"] == "Whale"

    def test_save_and_load_tsv(self):
        """Test saving and loading TSV format."""
        table = SelectionTable("Test")
        sel = Selection(begin_time=0, end_time=1, low_freq=500, high_freq=2000)
        sel.annotations["Label"] = "Test Label"
        table.add(sel)

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            filepath = Path(f.name)

        try:
            table.save(filepath, format="tsv")
            loaded = SelectionTable.load(filepath)

            assert len(loaded) == 1
            assert loaded[0].begin_time == 0
            assert loaded[0].end_time == 1
            assert loaded[0].annotations.get("Label") == "Test Label"
        finally:
            filepath.unlink()

    def test_save_and_load_csv(self):
        """Test saving and loading CSV format."""
        table = SelectionTable("Test")
        table.add(Selection(begin_time=0, end_time=1))
        table.add(Selection(begin_time=1, end_time=2))

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            filepath = Path(f.name)

        try:
            table.save(filepath, format="csv")
            loaded = SelectionTable.load(filepath)

            assert len(loaded) == 2
        finally:
            filepath.unlink()

    def test_iteration(self):
        """Test iterating over selections."""
        table = SelectionTable()
        for i in range(3):
            table.add(Selection(begin_time=i, end_time=i + 1))

        times = [sel.begin_time for sel in table]

        assert times == [0, 1, 2]


class TestAnnotationKeymap:
    """Tests for AnnotationKeymap class."""

    def test_create_keymap(self):
        """Test creating a keymap."""
        keymap = AnnotationKeymap("Species")

        assert keymap.column == "Species"
        assert len(keymap.mappings) == 0

    def test_add_mapping(self):
        """Test adding key mappings."""
        keymap = AnnotationKeymap("Species")

        keymap.add_mapping("b", "Bird")
        keymap.add_mapping("w", "Whale")

        assert keymap.get_value("b") == "Bird"
        assert keymap.get_value("w") == "Whale"

    def test_case_insensitive(self):
        """Test case-insensitive key lookup."""
        keymap = AnnotationKeymap("Species")
        keymap.add_mapping("B", "Bird")

        assert keymap.get_value("b") == "Bird"
        assert keymap.get_value("B") == "Bird"

    def test_apply_to_selection(self):
        """Test applying keymap to a selection."""
        keymap = AnnotationKeymap("Species")
        keymap.add_mapping("b", "Bird")

        sel = Selection(begin_time=0, end_time=1)
        result = keymap.apply("b", sel)

        assert result is True
        assert sel.annotations["Species"] == "Bird"

    def test_apply_unknown_key(self):
        """Test applying unknown key."""
        keymap = AnnotationKeymap("Species")
        keymap.add_mapping("b", "Bird")

        sel = Selection(begin_time=0, end_time=1)
        result = keymap.apply("x", sel)

        assert result is False
        assert "Species" not in sel.annotations

    def test_remove_mapping(self):
        """Test removing a mapping."""
        keymap = AnnotationKeymap("Species")
        keymap.add_mapping("b", "Bird")

        keymap.remove_mapping("b")

        assert keymap.get_value("b") is None

    def test_save_and_load(self):
        """Test saving and loading keymap."""
        keymap = AnnotationKeymap("Call Type")
        keymap.add_mapping("s", "Song")
        keymap.add_mapping("c", "Call")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = Path(f.name)

        try:
            keymap.save(filepath)
            loaded = AnnotationKeymap.load(filepath)

            assert loaded.column == "Call Type"
            assert loaded.get_value("s") == "Song"
            assert loaded.get_value("c") == "Call"
        finally:
            filepath.unlink()
