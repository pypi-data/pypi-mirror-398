"""
Detection dialogs for model selection and batch detection.

Provides:
- ModelSelectionDialog: Choose detection model and configure parameters
- BatchDetectionDialog: Select files and run batch detection
- DetectionProgressDialog: Show progress during detection
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QWidget,
    QDialogButtonBox,
    QMessageBox,
    QSplitter,
    QAbstractItemView,
)

from magpy.workers import (
    DetectionWorker,
    DetectionConfig,
    DetectorType,
    DetectionResult,
    BatchDetectionResult,
)


class ModelSelectionDialog(QDialog):
    """
    Dialog for selecting and configuring a detection model.

    Allows users to:
    - Choose between ML models (AST, BirdNET) and signal detectors
    - Configure model-specific parameters
    - Set confidence thresholds and other options
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Detection Model")
        self.setMinimumWidth(500)
        self._config: Optional[DetectionConfig] = None
        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Model type selection
        type_group = QGroupBox("Detector Type")
        type_layout = QFormLayout(type_group)

        self._type_combo = QComboBox()
        self._type_combo.addItem("AST (Audio Spectrogram Transformer)", DetectorType.AST.value)
        self._type_combo.addItem("BirdNET", DetectorType.BIRDNET.value)
        self._type_combo.addItem("OpenSoundscape", DetectorType.OPENSOUNDSCAPE.value)
        self._type_combo.addItem("Band Energy Detector", DetectorType.ENERGY.value)
        self._type_combo.addItem("RIBBIT (Periodic Calls)", DetectorType.RIBBIT.value)
        self._type_combo.addItem("CWT Peak Detector", DetectorType.CWT.value)
        self._type_combo.addItem("Accelerating Pattern", DetectorType.ACCELERATING.value)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addRow("Detector:", self._type_combo)

        layout.addWidget(type_group)

        # Tabs for different parameter groups
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # ML Model tab
        ml_widget = QWidget()
        ml_layout = QFormLayout(ml_widget)

        self._model_path_edit = QLineEdit()
        self._model_path_edit.setPlaceholderText("HuggingFace model ID or local path")
        self._model_path_edit.setText("MIT/ast-finetuned-audioset-10-10-0.4593")
        ml_layout.addRow("Model Path:", self._model_path_edit)

        browse_layout = QHBoxLayout()
        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.clicked.connect(self._browse_model)
        browse_layout.addWidget(self._browse_btn)
        browse_layout.addStretch()
        ml_layout.addRow("", browse_layout)

        self._top_k_spin = QSpinBox()
        self._top_k_spin.setRange(1, 100)
        self._top_k_spin.setValue(5)
        ml_layout.addRow("Top K Predictions:", self._top_k_spin)

        self._clip_duration_spin = QDoubleSpinBox()
        self._clip_duration_spin.setRange(0.5, 60.0)
        self._clip_duration_spin.setValue(3.0)
        self._clip_duration_spin.setSuffix(" s")
        ml_layout.addRow("Clip Duration:", self._clip_duration_spin)

        self._overlap_spin = QDoubleSpinBox()
        self._overlap_spin.setRange(0.0, 0.9)
        self._overlap_spin.setValue(0.0)
        self._overlap_spin.setSingleStep(0.1)
        ml_layout.addRow("Overlap:", self._overlap_spin)

        self._use_gpu_check = QCheckBox("Use GPU (if available)")
        self._use_gpu_check.setChecked(True)
        ml_layout.addRow("", self._use_gpu_check)

        self._tabs.addTab(ml_widget, "ML Model")

        # Signal Detector tab
        signal_widget = QWidget()
        signal_layout = QFormLayout(signal_widget)

        self._low_freq_spin = QDoubleSpinBox()
        self._low_freq_spin.setRange(0, 22050)
        self._low_freq_spin.setValue(500)
        self._low_freq_spin.setSuffix(" Hz")
        signal_layout.addRow("Low Frequency:", self._low_freq_spin)

        self._high_freq_spin = QDoubleSpinBox()
        self._high_freq_spin.setRange(0, 22050)
        self._high_freq_spin.setValue(5000)
        self._high_freq_spin.setSuffix(" Hz")
        signal_layout.addRow("High Frequency:", self._high_freq_spin)

        self._threshold_spin = QDoubleSpinBox()
        self._threshold_spin.setRange(-80, 0)
        self._threshold_spin.setValue(-20)
        self._threshold_spin.setSuffix(" dB")
        signal_layout.addRow("Threshold:", self._threshold_spin)

        self._pulse_rate_spin = QDoubleSpinBox()
        self._pulse_rate_spin.setRange(0.1, 100)
        self._pulse_rate_spin.setValue(10.0)
        self._pulse_rate_spin.setSuffix(" Hz")
        signal_layout.addRow("Pulse Rate (RIBBIT):", self._pulse_rate_spin)

        self._tabs.addTab(signal_widget, "Signal Detector")

        # Common settings group
        common_group = QGroupBox("Common Settings")
        common_layout = QFormLayout(common_group)

        self._confidence_spin = QDoubleSpinBox()
        self._confidence_spin.setRange(0.0, 1.0)
        self._confidence_spin.setValue(0.5)
        self._confidence_spin.setSingleStep(0.05)
        common_layout.addRow("Min Confidence:", self._confidence_spin)

        self._batch_size_spin = QSpinBox()
        self._batch_size_spin.setRange(1, 64)
        self._batch_size_spin.setValue(8)
        common_layout.addRow("Batch Size:", self._batch_size_spin)

        layout.addWidget(common_group)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Initialize state
        self._on_type_changed()

    def _on_type_changed(self):
        """Handle detector type change."""
        detector_type = self._get_detector_type()
        is_ml = detector_type in (DetectorType.AST, DetectorType.BIRDNET, DetectorType.OPENSOUNDSCAPE)

        # Show appropriate tab
        self._tabs.setCurrentIndex(0 if is_ml else 1)

    def _get_detector_type(self) -> DetectorType:
        """Get the selected detector type."""
        type_value = self._type_combo.currentData()
        return DetectorType(type_value)

    def _browse_model(self):
        """Browse for local model file."""
        path = QFileDialog.getExistingDirectory(
            self, "Select Model Directory"
        )
        if path:
            self._model_path_edit.setText(path)

    def _on_accept(self):
        """Build configuration and accept dialog."""
        detector_type = self._get_detector_type()

        detector_params = {}
        if detector_type in (DetectorType.ENERGY, DetectorType.RIBBIT, DetectorType.CWT, DetectorType.ACCELERATING):
            detector_params = {
                "low_freq": self._low_freq_spin.value(),
                "high_freq": self._high_freq_spin.value(),
                "threshold_db": self._threshold_spin.value(),
                "pulse_rate_hz": self._pulse_rate_spin.value(),
            }

        self._config = DetectionConfig(
            detector_type=detector_type,
            model_path=self._model_path_edit.text() or None,
            min_confidence=self._confidence_spin.value(),
            top_k=self._top_k_spin.value(),
            clip_duration=self._clip_duration_spin.value(),
            overlap=self._overlap_spin.value(),
            batch_size=self._batch_size_spin.value(),
            use_gpu=self._use_gpu_check.isChecked(),
            detector_params=detector_params,
        )

        self.accept()

    def get_config(self) -> Optional[DetectionConfig]:
        """Get the configured detection config."""
        return self._config


class DetectionProgressDialog(QDialog):
    """
    Progress dialog for detection operations.

    Shows:
    - Progress bar
    - Current file being processed
    - Elapsed time
    - Cancel button
    """

    cancelled = pyqtSignal()

    def __init__(self, total_files: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Running Detection")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._total_files = total_files
        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Status label
        self._status_label = QLabel("Initializing...")
        layout.addWidget(self._status_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, self._total_files)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        # Details
        self._details_label = QLabel("")
        self._details_label.setStyleSheet("color: #808080;")
        layout.addWidget(self._details_label)

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(cancel_btn)

    def update_progress(self, current: int, total: int, message: str):
        """Update progress display."""
        self._progress_bar.setValue(current)
        self._status_label.setText(message)
        self._details_label.setText(f"{current} / {total} files processed")

    def _on_cancel(self):
        """Handle cancel button."""
        self.cancelled.emit()
        self.reject()


class BatchDetectionDialog(QDialog):
    """
    Dialog for batch detection across multiple files.

    Features:
    - File/folder selection
    - Model configuration
    - Progress tracking
    - Results preview
    """

    detection_complete = pyqtSignal(object)  # BatchDetectionResult

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Detection")
        self.setMinimumSize(700, 500)
        self._worker: Optional[DetectionWorker] = None
        self._config: Optional[DetectionConfig] = None
        self._files: List[str] = []
        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Splitter for file list and settings
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left side: File selection
        file_widget = QWidget()
        file_layout = QVBoxLayout(file_widget)
        file_layout.setContentsMargins(0, 0, 0, 0)

        file_label = QLabel("Audio Files:")
        file_layout.addWidget(file_label)

        self._file_list = QListWidget()
        self._file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        file_layout.addWidget(self._file_list)

        file_btn_layout = QHBoxLayout()

        add_files_btn = QPushButton("Add Files...")
        add_files_btn.clicked.connect(self._add_files)
        file_btn_layout.addWidget(add_files_btn)

        add_folder_btn = QPushButton("Add Folder...")
        add_folder_btn.clicked.connect(self._add_folder)
        file_btn_layout.addWidget(add_folder_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_selected)
        file_btn_layout.addWidget(remove_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_files)
        file_btn_layout.addWidget(clear_btn)

        file_layout.addLayout(file_btn_layout)
        splitter.addWidget(file_widget)

        # Right side: Settings and progress
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)

        # Model selection
        model_group = QGroupBox("Detection Model")
        model_layout = QVBoxLayout(model_group)

        self._model_label = QLabel("No model selected")
        model_layout.addWidget(self._model_label)

        select_model_btn = QPushButton("Select Model...")
        select_model_btn.clicked.connect(self._select_model)
        model_layout.addWidget(select_model_btn)

        settings_layout.addWidget(model_group)

        # Output options
        output_group = QGroupBox("Output Options")
        output_layout = QFormLayout(output_group)

        self._output_path_edit = QLineEdit()
        self._output_path_edit.setPlaceholderText("Optional: path to save results")
        output_layout.addRow("Save Results:", self._output_path_edit)

        output_btn_layout = QHBoxLayout()
        browse_output_btn = QPushButton("Browse...")
        browse_output_btn.clicked.connect(self._browse_output)
        output_btn_layout.addWidget(browse_output_btn)
        output_btn_layout.addStretch()
        output_layout.addRow("", output_btn_layout)

        self._export_format_combo = QComboBox()
        self._export_format_combo.addItem("CSV", "csv")
        self._export_format_combo.addItem("JSON", "json")
        self._export_format_combo.addItem("Parquet", "parquet")
        output_layout.addRow("Format:", self._export_format_combo)

        settings_layout.addWidget(output_group)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        progress_layout.addWidget(self._progress_bar)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(100)
        progress_layout.addWidget(self._log_text)

        settings_layout.addWidget(progress_group)
        settings_layout.addStretch()

        splitter.addWidget(settings_widget)
        splitter.setSizes([350, 350])

        # Dialog buttons
        button_layout = QHBoxLayout()

        self._run_btn = QPushButton("Run Detection")
        self._run_btn.clicked.connect(self._run_detection)
        self._run_btn.setEnabled(False)
        button_layout.addWidget(self._run_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._cancel_detection)
        self._cancel_btn.setEnabled(False)
        button_layout.addWidget(self._cancel_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _add_files(self):
        """Add audio files to the list."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Audio Files",
            "",
            "Audio Files (*.wav *.flac *.mp3 *.aiff *.ogg);;All Files (*)",
        )
        for f in files:
            if f not in self._files:
                self._files.append(f)
                self._file_list.addItem(Path(f).name)

        self._update_run_button()

    def _add_folder(self):
        """Add all audio files from a folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            folder_path = Path(folder)
            extensions = {".wav", ".flac", ".mp3", ".aiff", ".ogg"}
            for f in folder_path.rglob("*"):
                if f.suffix.lower() in extensions and str(f) not in self._files:
                    self._files.append(str(f))
                    self._file_list.addItem(f.name)

        self._update_run_button()

    def _remove_selected(self):
        """Remove selected files from the list."""
        selected = self._file_list.selectedItems()
        for item in selected:
            row = self._file_list.row(item)
            self._file_list.takeItem(row)
            del self._files[row]

        self._update_run_button()

    def _clear_files(self):
        """Clear all files from the list."""
        self._file_list.clear()
        self._files.clear()
        self._update_run_button()

    def _select_model(self):
        """Show model selection dialog."""
        dialog = ModelSelectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._config = dialog.get_config()
            if self._config:
                self._model_label.setText(
                    f"{self._config.detector_type.value} "
                    f"(confidence >= {self._config.min_confidence:.2f})"
                )
        self._update_run_button()

    def _browse_output(self):
        """Browse for output file path."""
        fmt = self._export_format_combo.currentData()
        ext_map = {"csv": "*.csv", "json": "*.json", "parquet": "*.parquet"}
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            f"detections.{fmt}",
            f"{fmt.upper()} Files ({ext_map[fmt]})",
        )
        if path:
            self._output_path_edit.setText(path)

    def _update_run_button(self):
        """Update run button enabled state."""
        can_run = len(self._files) > 0 and self._config is not None
        self._run_btn.setEnabled(can_run)

    def _run_detection(self):
        """Start the detection process."""
        if not self._files or not self._config:
            return

        self._run_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._progress_bar.setVisible(True)
        self._progress_bar.setRange(0, len(self._files))
        self._progress_bar.setValue(0)
        self._log_text.clear()
        self._log("Starting detection...")

        # Create and start worker
        self._worker = DetectionWorker(self._files, self._config)
        self._worker.progress.connect(self._on_progress)
        self._worker.file_complete.connect(self._on_file_complete)
        self._worker.result.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _cancel_detection(self):
        """Cancel the detection process."""
        if self._worker:
            self._worker.cancel()
            self._log("Cancelling...")

    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress update."""
        self._progress_bar.setValue(current)
        self._log(message)

    def _on_file_complete(self, filepath: str, detections: list):
        """Handle file completion."""
        filename = Path(filepath).name
        self._log(f"  {filename}: {len(detections)} detections")

    def _on_result(self, result: BatchDetectionResult):
        """Handle detection completion."""
        self._run_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)

        self._log(
            f"\nComplete: {result.files_processed} files, "
            f"{len(result.detections)} detections, "
            f"{result.processing_time:.1f}s"
        )

        # Save results if output path specified
        output_path = self._output_path_edit.text()
        if output_path:
            self._save_results(result, output_path)

        self.detection_complete.emit(result)

    def _on_error(self, message: str):
        """Handle error."""
        self._run_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._log(f"Error: {message}")
        QMessageBox.critical(self, "Detection Error", message)

    def _log(self, message: str):
        """Add message to log."""
        self._log_text.append(message)

    def _save_results(self, result: BatchDetectionResult, output_path: str):
        """Save detection results to file."""
        import json
        import csv

        fmt = self._export_format_combo.currentData()
        data = [d.to_dict() for d in result.detections]

        try:
            if fmt == "json":
                with open(output_path, "w") as f:
                    json.dump(data, f, indent=2)
            elif fmt == "csv":
                if data:
                    with open(output_path, "w", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            elif fmt == "parquet":
                try:
                    import pandas as pd
                    df = pd.DataFrame(data)
                    df.to_parquet(output_path, index=False)
                except ImportError:
                    self._log("Warning: pandas/pyarrow required for Parquet export")
                    return

            self._log(f"Results saved to: {output_path}")

        except Exception as e:
            self._log(f"Error saving results: {e}")
