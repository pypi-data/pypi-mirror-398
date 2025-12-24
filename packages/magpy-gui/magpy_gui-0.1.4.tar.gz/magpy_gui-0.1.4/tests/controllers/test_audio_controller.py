"""Tests for the AudioController."""

import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from magpy.controllers.audio_controller import (
    AudioController,
    AudioMetadata,
    TransformOperation,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def controller():
    """Create a fresh AudioController instance."""
    return AudioController()


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
    if filepath.exists():
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

    if filepath.exists():
        filepath.unlink()


@pytest.fixture
def controller_with_audio(controller, sample_audio_file):
    """Controller with audio already loaded."""
    success, _, _ = controller.load_file(str(sample_audio_file))
    assert success
    return controller


# =============================================================================
# Initialization Tests
# =============================================================================


class TestAudioControllerInit:
    """Tests for AudioController initialization."""

    def test_default_init(self, controller):
        """Test default initialization."""
        assert controller._max_undo_levels == 50
        assert controller._current_audio is None
        assert controller._current_sample_rate is None
        assert controller._source_path is None
        assert len(controller._undo_stack) == 0
        assert len(controller._redo_stack) == 0

    def test_custom_undo_levels(self):
        """Test initialization with custom undo levels."""
        controller = AudioController(max_undo_levels=10)
        assert controller._max_undo_levels == 10

    def test_bioamla_available_property(self, controller):
        """Test bioamla_available property."""
        # Property should return a boolean regardless of bioamla status
        assert isinstance(controller.bioamla_available, bool)


# =============================================================================
# Property Tests
# =============================================================================


class TestAudioControllerProperties:
    """Tests for AudioController properties."""

    def test_has_audio_false_initially(self, controller):
        """Test has_audio is False when no audio loaded."""
        assert controller.has_audio is False

    def test_has_audio_true_after_load(self, controller_with_audio):
        """Test has_audio is True after loading audio."""
        assert controller_with_audio.has_audio is True

    def test_can_undo_false_initially(self, controller):
        """Test can_undo is False when undo stack is empty."""
        assert controller.can_undo is False

    def test_can_redo_false_initially(self, controller):
        """Test can_redo is False when redo stack is empty."""
        assert controller.can_redo is False

    def test_undo_description_none_initially(self, controller):
        """Test undo_description is None when undo stack is empty."""
        assert controller.undo_description is None

    def test_redo_description_none_initially(self, controller):
        """Test redo_description is None when redo stack is empty."""
        assert controller.redo_description is None


# =============================================================================
# File Operations Tests
# =============================================================================


class TestFileOperations:
    """Tests for file loading and saving operations."""

    def test_load_file_success(self, controller, sample_audio_file):
        """Test successful file loading."""
        success, message, metadata = controller.load_file(str(sample_audio_file))

        assert success is True
        assert "Loaded" in message or "loaded" in message.lower()
        assert metadata is not None
        assert metadata["sample_rate"] == 44100
        assert metadata["channels"] == 2
        assert abs(metadata["duration"] - 1.0) < 0.01

    def test_load_file_updates_state(self, controller, sample_audio_file):
        """Test that loading updates internal state."""
        controller.load_file(str(sample_audio_file))

        assert controller._current_audio is not None
        assert controller._current_sample_rate == 44100
        assert controller._source_path == str(sample_audio_file)

    def test_load_file_clears_undo_stacks(self, controller_with_audio, mono_audio_file):
        """Test that loading a new file clears undo stacks."""
        # Add something to undo stack by setting audio manually
        controller_with_audio._push_undo("Test", {})
        assert controller_with_audio.can_undo

        # Load new file
        controller_with_audio.load_file(str(mono_audio_file))

        assert controller_with_audio.can_undo is False
        assert controller_with_audio.can_redo is False

    def test_load_nonexistent_file(self, controller):
        """Test loading a nonexistent file."""
        success, message, metadata = controller.load_file("/nonexistent/path.wav")

        assert success is False
        assert metadata is None
        # Message could be "Failed" or "does not exist" depending on bioamla availability
        assert any(x in message.lower() for x in ["failed", "not exist", "error"])

    def test_save_file_success(self, controller_with_audio):
        """Test successful file saving."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = Path(f.name)

        try:
            success, message = controller_with_audio.save_file(str(output_path))

            assert success is True
            assert output_path.exists()
            assert "Saved" in message or "saved" in message.lower()

            # Verify the saved file can be loaded
            info = sf.info(output_path)
            assert info.samplerate == 44100
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_save_file_no_audio(self, controller):
        """Test saving when no audio is loaded."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = Path(f.name)

        try:
            success, message = controller.save_file(str(output_path))

            assert success is False
            assert "No audio" in message
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_save_file_with_custom_audio(self, controller):
        """Test saving with custom audio data."""
        sample_rate = 16000
        audio = np.random.randn(16000).astype(np.float32)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = Path(f.name)

        try:
            success, message = controller.save_file(
                str(output_path), audio=audio, sample_rate=sample_rate
            )

            assert success is True
            assert output_path.exists()

            info = sf.info(output_path)
            assert info.samplerate == sample_rate
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_get_metadata_success(self, controller, sample_audio_file):
        """Test getting file metadata."""
        success, metadata = controller.get_metadata(str(sample_audio_file))

        assert success is True
        assert metadata is not None
        assert isinstance(metadata, AudioMetadata)
        assert metadata.sample_rate == 44100
        assert metadata.channels == 2
        assert abs(metadata.duration - 1.0) < 0.01

    def test_get_metadata_nonexistent(self, controller):
        """Test getting metadata for nonexistent file."""
        success, metadata = controller.get_metadata("/nonexistent/path.wav")

        assert success is False
        assert metadata is None


# =============================================================================
# Undo/Redo Tests
# =============================================================================


class TestUndoRedo:
    """Tests for undo/redo functionality."""

    def test_push_undo_creates_entry(self, controller_with_audio):
        """Test that _push_undo creates an undo entry."""
        controller_with_audio._push_undo("Test Operation", {"param": "value"})

        assert controller_with_audio.can_undo is True
        assert controller_with_audio.undo_description == "Test Operation"
        assert len(controller_with_audio._undo_stack) == 1

    def test_push_undo_clears_redo(self, controller_with_audio):
        """Test that _push_undo clears the redo stack."""
        # Setup: create redo entry
        controller_with_audio._redo_stack.append(
            TransformOperation("Redo Op", {})
        )
        assert controller_with_audio.can_redo

        # Push new undo
        controller_with_audio._push_undo("New Op", {})

        assert controller_with_audio.can_redo is False

    def test_push_undo_limits_stack_size(self):
        """Test that undo stack is limited to max_undo_levels."""
        controller = AudioController(max_undo_levels=3)
        controller._current_audio = np.zeros(100)
        controller._current_sample_rate = 16000

        for i in range(5):
            controller._push_undo(f"Operation {i}", {})

        assert len(controller._undo_stack) == 3
        # Most recent should be at the end
        assert controller._undo_stack[-1].name == "Operation 4"

    def test_undo_restores_state(self, controller_with_audio):
        """Test that undo restores previous audio state."""
        original_audio = controller_with_audio._current_audio.copy()

        # Push undo with current state
        controller_with_audio._push_undo("Test", {})

        # Modify audio
        controller_with_audio._current_audio = np.zeros_like(original_audio)

        # Undo
        success, message = controller_with_audio.undo()

        assert success is True
        assert "Undid" in message
        assert np.allclose(controller_with_audio._current_audio, original_audio)

    def test_undo_creates_redo_entry(self, controller_with_audio):
        """Test that undo creates a redo entry."""
        controller_with_audio._push_undo("Test", {})

        assert controller_with_audio.can_redo is False

        controller_with_audio.undo()

        assert controller_with_audio.can_redo is True

    def test_undo_empty_stack(self, controller):
        """Test undo when stack is empty."""
        success, message = controller.undo()

        assert success is False
        assert "Nothing to undo" in message

    def test_redo_restores_state(self, controller_with_audio):
        """Test that redo restores the redone state."""
        original_audio = controller_with_audio._current_audio.copy()

        # Push undo and then undo it
        controller_with_audio._push_undo("Test", {})
        modified_audio = np.zeros_like(original_audio)
        controller_with_audio._current_audio = modified_audio.copy()

        # Now the undo stack has original audio
        controller_with_audio.undo()

        # Audio should be original
        assert np.allclose(controller_with_audio._current_audio, original_audio)

        # Redo should restore to modified
        success, message = controller_with_audio.redo()

        assert success is True
        assert "Redid" in message
        assert np.allclose(controller_with_audio._current_audio, modified_audio)

    def test_redo_empty_stack(self, controller):
        """Test redo when stack is empty."""
        success, message = controller.redo()

        assert success is False
        assert "Nothing to redo" in message

    def test_undo_redo_cycle(self, controller_with_audio):
        """Test multiple undo/redo cycles."""
        states = [controller_with_audio._current_audio.copy()]

        # Make several modifications
        for i in range(3):
            controller_with_audio._push_undo(f"Op {i}", {})
            controller_with_audio._current_audio = np.random.randn(
                *controller_with_audio._current_audio.shape
            ).astype(np.float32)
            states.append(controller_with_audio._current_audio.copy())

        # Undo all operations
        for i in range(3):
            controller_with_audio.undo()

        # Should be back to original
        assert np.allclose(controller_with_audio._current_audio, states[0])

        # Redo all operations
        for i in range(3):
            controller_with_audio.redo()

        # Should be back to final state
        assert np.allclose(controller_with_audio._current_audio, states[3])


# =============================================================================
# Utility Method Tests
# =============================================================================


class TestUtilityMethods:
    """Tests for utility methods."""

    def test_get_current_audio(self, controller_with_audio):
        """Test getting current audio data."""
        audio, sample_rate = controller_with_audio.get_current_audio()

        assert audio is not None
        assert sample_rate == 44100
        assert audio.shape[0] == 44100  # 1 second at 44100 Hz

    def test_get_current_audio_empty(self, controller):
        """Test getting current audio when none loaded."""
        audio, sample_rate = controller.get_current_audio()

        assert audio is None
        assert sample_rate is None

    def test_set_current_audio(self, controller):
        """Test setting current audio data."""
        audio = np.random.randn(1000).astype(np.float32)
        sample_rate = 16000

        controller.set_current_audio(audio, sample_rate)

        assert np.allclose(controller._current_audio, audio)
        assert controller._current_sample_rate == sample_rate

    def test_clear(self, controller_with_audio):
        """Test clearing controller state."""
        # Add some undo entries
        controller_with_audio._push_undo("Test", {})

        controller_with_audio.clear()

        assert controller_with_audio._current_audio is None
        assert controller_with_audio._current_sample_rate is None
        assert controller_with_audio._source_path is None
        assert controller_with_audio.can_undo is False
        assert controller_with_audio.can_redo is False


# =============================================================================
# Transform Operation Tests (Stubs when bioamla not available)
# =============================================================================


class TestTransformOperations:
    """Tests for transform operations."""

    def test_bandpass_no_audio(self, controller):
        """Test bandpass filter when no audio loaded."""
        success, message = controller.apply_bandpass(500, 2000)

        assert success is False
        assert "No audio" in message

    def test_normalize_no_audio(self, controller):
        """Test normalize when no audio loaded."""
        success, message = controller.apply_normalize(-20.0)

        assert success is False
        assert "No audio" in message

    def test_denoise_no_audio(self, controller):
        """Test denoise when no audio loaded."""
        success, message = controller.apply_denoise(1.0)

        assert success is False
        assert "No audio" in message

    def test_resample_no_audio(self, controller):
        """Test resample when no audio loaded."""
        success, message = controller.apply_resample(22050)

        assert success is False
        assert "No audio" in message

    def test_resample_same_rate(self, controller_with_audio):
        """Test resample to same sample rate."""
        success, message = controller_with_audio.apply_resample(44100)

        assert success is True
        assert "already" in message.lower() or "Already" in message

    def test_trim_no_audio(self, controller):
        """Test trim when no audio loaded."""
        success, message = controller.apply_trim(0.0, 1.0)

        assert success is False
        assert "No audio" in message


# =============================================================================
# Analysis Operation Tests
# =============================================================================


class TestAnalysisOperations:
    """Tests for analysis operations."""

    def test_compute_indices_no_audio(self, controller):
        """Test computing indices when no audio loaded."""
        success, message, indices = controller.compute_indices()

        assert success is False
        assert "No audio" in message
        assert indices is None

    def test_get_available_indices(self, controller):
        """Test getting available indices."""
        indices = controller.get_available_indices()

        # Should return a list (empty if bioamla not available)
        assert isinstance(indices, list)


# =============================================================================
# AudioMetadata Tests
# =============================================================================


class TestAudioMetadata:
    """Tests for AudioMetadata dataclass."""

    def test_create_metadata(self):
        """Test creating AudioMetadata."""
        metadata = AudioMetadata(
            filepath="/path/to/file.wav",
            duration=10.5,
            sample_rate=44100,
            channels=2,
            bit_depth=16,
            format="WAV (PCM_16)",
            file_size=1843200,
        )

        assert metadata.filepath == "/path/to/file.wav"
        assert metadata.duration == 10.5
        assert metadata.sample_rate == 44100
        assert metadata.channels == 2
        assert metadata.bit_depth == 16
        assert metadata.file_size == 1843200

    def test_metadata_optional_fields(self):
        """Test AudioMetadata with optional fields."""
        metadata = AudioMetadata(
            filepath="/path/to/file.wav",
            duration=5.0,
            sample_rate=22050,
            channels=1,
        )

        assert metadata.bit_depth is None
        assert metadata.format is None
        assert metadata.file_size is None


# =============================================================================
# TransformOperation Tests
# =============================================================================


class TestTransformOperation:
    """Tests for TransformOperation dataclass."""

    def test_create_transform_operation(self):
        """Test creating TransformOperation."""
        audio = np.zeros(100)
        op = TransformOperation(
            name="Bandpass Filter",
            parameters={"low_hz": 500, "high_hz": 2000},
            audio_before=audio,
            sample_rate_before=44100,
        )

        assert op.name == "Bandpass Filter"
        assert op.parameters["low_hz"] == 500
        assert op.parameters["high_hz"] == 2000
        assert np.array_equal(op.audio_before, audio)
        assert op.sample_rate_before == 44100

    def test_transform_operation_optional_fields(self):
        """Test TransformOperation with optional fields."""
        op = TransformOperation(
            name="Test",
            parameters={},
        )

        assert op.audio_before is None
        assert op.sample_rate_before is None
