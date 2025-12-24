"""
Detection results table widget.

Displays detection results with:
- Sortable columns
- Confidence threshold filtering
- Label filtering
- Conversion to annotations
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QLabel,
    QDoubleSpinBox,
    QLineEdit,
    QComboBox,
    QMenu,
    QAbstractItemView,
    QMessageBox,
)

from magpy.workers import DetectionResult, BatchDetectionResult


# Color palette for detection labels
DETECTION_COLORS = [
    "#4e9a06",  # Green
    "#c4a000",  # Yellow
    "#ce5c00",  # Orange
    "#cc0000",  # Red
    "#75507b",  # Purple
    "#3465a4",  # Blue
    "#06989a",  # Cyan
    "#8f5902",  # Brown
    "#2e3436",  # Dark gray
    "#4e9a06",  # Green (repeat)
]


def get_label_color(label: str, label_index: Dict[str, int]) -> str:
    """Get a consistent color for a label."""
    if label not in label_index:
        label_index[label] = len(label_index)
    idx = label_index[label] % len(DETECTION_COLORS)
    return DETECTION_COLORS[idx]


class DetectionResultsWidget(QWidget):
    """
    Widget for displaying and managing detection results.

    Features:
    - Sortable table with all detection properties
    - Confidence threshold slider for filtering
    - Label filter with checkboxes
    - Convert selected detections to annotations
    - Go to detection in spectrogram
    """

    # Signals
    detection_selected = pyqtSignal(object)  # DetectionResult
    convert_to_annotations = pyqtSignal(list)  # List[DetectionResult]
    go_to_detection = pyqtSignal(float, float)  # start_time, end_time

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._detections: List[DetectionResult] = []
        self._filtered_detections: List[DetectionResult] = []
        self._label_index: Dict[str, int] = {}
        self._visible_labels: Set[str] = set()

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        # Confidence threshold
        toolbar_layout.addWidget(QLabel("Min Confidence:"))
        self._confidence_spin = QDoubleSpinBox()
        self._confidence_spin.setRange(0.0, 1.0)
        self._confidence_spin.setValue(0.5)
        self._confidence_spin.setSingleStep(0.05)
        self._confidence_spin.valueChanged.connect(self._apply_filters)
        toolbar_layout.addWidget(self._confidence_spin)

        toolbar_layout.addSpacing(16)

        # Label filter
        toolbar_layout.addWidget(QLabel("Label:"))
        self._label_combo = QComboBox()
        self._label_combo.addItem("All Labels", None)
        self._label_combo.currentIndexChanged.connect(self._apply_filters)
        toolbar_layout.addWidget(self._label_combo)

        toolbar_layout.addSpacing(16)

        # Search
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search labels...")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._apply_filters)
        toolbar_layout.addWidget(self._search_edit)

        toolbar_layout.addStretch()

        # Convert button
        convert_btn = QPushButton("Convert to Annotations")
        convert_btn.setToolTip("Convert selected detections to annotations")
        convert_btn.clicked.connect(self._convert_selected)
        toolbar_layout.addWidget(convert_btn)

        layout.addLayout(toolbar_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Label", "Confidence", "Start (s)", "End (s)",
            "Duration (s)", "Low Freq", "High Freq"
        ])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setSortingEnabled(True)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)

        # Style
        self._table.setStyleSheet(
            """
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252526;
                gridline-color: #3c3c3c;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 4px 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #094771;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #d4d4d4;
                padding: 8px;
                border: none;
                border-right: 1px solid #3c3c3c;
                border-bottom: 1px solid #3c3c3c;
                font-weight: 600;
            }
            """
        )

        # Configure header
        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        layout.addWidget(self._table)

        # Status bar
        status_layout = QHBoxLayout()
        self._status_label = QLabel("0 detections")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()

        self._selected_label = QLabel("")
        status_layout.addWidget(self._selected_label)

        layout.addLayout(status_layout)

    def _setup_connections(self):
        """Set up signal connections."""
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)

    def set_detections(self, detections: List[DetectionResult]):
        """Set the detection results to display."""
        self._detections = detections
        self._label_index.clear()

        # Collect all unique labels
        labels = sorted(set(d.label for d in detections))
        self._visible_labels = set(labels)

        # Update label combo
        self._label_combo.blockSignals(True)
        self._label_combo.clear()
        self._label_combo.addItem("All Labels", None)
        for label in labels:
            self._label_combo.addItem(label, label)
        self._label_combo.blockSignals(False)

        self._apply_filters()

    def set_batch_result(self, result: BatchDetectionResult):
        """Set detection results from a batch result."""
        self.set_detections(result.detections)

    def _apply_filters(self):
        """Apply current filters and refresh table."""
        min_confidence = self._confidence_spin.value()
        selected_label = self._label_combo.currentData()
        search_text = self._search_edit.text().lower()

        self._filtered_detections = []
        for det in self._detections:
            # Confidence filter
            if det.confidence < min_confidence:
                continue

            # Label filter
            if selected_label and det.label != selected_label:
                continue

            # Search filter
            if search_text and search_text not in det.label.lower():
                continue

            self._filtered_detections.append(det)

        self._refresh_table()

    def _refresh_table(self):
        """Refresh the table with filtered detections."""
        self._table.blockSignals(True)
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(self._filtered_detections))

        for row, det in enumerate(self._filtered_detections):
            self._populate_row(row, det)

        self._table.setSortingEnabled(True)
        self._table.blockSignals(False)

        # Update status
        total = len(self._detections)
        showing = len(self._filtered_detections)
        self._status_label.setText(
            f"Showing {showing} of {total} detections"
        )

    def _populate_row(self, row: int, det: DetectionResult):
        """Populate a single table row."""
        # Label with color indicator
        label_item = QTableWidgetItem(det.label)
        color = get_label_color(det.label, self._label_index)
        label_item.setBackground(QColor(color))
        label_item.setForeground(QColor("#ffffff"))
        label_item.setData(Qt.ItemDataRole.UserRole, det)
        self._table.setItem(row, 0, label_item)

        # Confidence
        conf_item = QTableWidgetItem(f"{det.confidence:.3f}")
        conf_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._table.setItem(row, 1, conf_item)

        # Start time
        start_item = QTableWidgetItem(f"{det.start_time:.4f}")
        start_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._table.setItem(row, 2, start_item)

        # End time
        end_item = QTableWidgetItem(f"{det.end_time:.4f}")
        end_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._table.setItem(row, 3, end_item)

        # Duration
        dur_item = QTableWidgetItem(f"{det.duration:.4f}")
        dur_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._table.setItem(row, 4, dur_item)

        # Frequencies (optional)
        low_freq = f"{det.frequency_low:.1f}" if det.frequency_low else "-"
        high_freq = f"{det.frequency_high:.1f}" if det.frequency_high else "-"

        low_item = QTableWidgetItem(low_freq)
        low_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._table.setItem(row, 5, low_item)

        high_item = QTableWidgetItem(high_freq)
        high_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._table.setItem(row, 6, high_item)

    def _on_selection_changed(self):
        """Handle table selection change."""
        selected = self._table.selectedItems()
        if selected:
            # Get detection from first column
            row = selected[0].row()
            label_item = self._table.item(row, 0)
            if label_item:
                det = label_item.data(Qt.ItemDataRole.UserRole)
                if det:
                    self.detection_selected.emit(det)
                    self._selected_label.setText(f"Selected: {det.label}")

        count = len(self._table.selectedItems()) // self._table.columnCount()
        if count > 0:
            self._selected_label.setText(f"{count} selected")

    def _on_cell_double_clicked(self, row: int, col: int):
        """Handle double-click to go to detection."""
        label_item = self._table.item(row, 0)
        if label_item:
            det = label_item.data(Qt.ItemDataRole.UserRole)
            if det:
                self.go_to_detection.emit(det.start_time, det.end_time)

    def _show_context_menu(self, pos):
        """Show context menu for selected detections."""
        selected_rows = set(item.row() for item in self._table.selectedItems())
        if not selected_rows:
            return

        menu = QMenu(self)

        # Go to detection
        if len(selected_rows) == 1:
            row = list(selected_rows)[0]
            label_item = self._table.item(row, 0)
            if label_item:
                det = label_item.data(Qt.ItemDataRole.UserRole)
                go_action = menu.addAction("Go to Detection")
                go_action.triggered.connect(
                    lambda: self.go_to_detection.emit(det.start_time, det.end_time)
                )

        menu.addSeparator()

        # Convert to annotations
        convert_action = menu.addAction(f"Convert to Annotations ({len(selected_rows)})")
        convert_action.triggered.connect(self._convert_selected)

        menu.addSeparator()

        # Copy info
        copy_action = menu.addAction("Copy Info")
        copy_action.triggered.connect(self._copy_selected_info)

        menu.exec(self._table.mapToGlobal(pos))

    def _convert_selected(self):
        """Convert selected detections to annotations."""
        selected_rows = set(item.row() for item in self._table.selectedItems())
        if not selected_rows:
            QMessageBox.information(
                self, "No Selection",
                "Select detections to convert to annotations."
            )
            return

        detections = []
        for row in selected_rows:
            label_item = self._table.item(row, 0)
            if label_item:
                det = label_item.data(Qt.ItemDataRole.UserRole)
                if det:
                    detections.append(det)

        if detections:
            self.convert_to_annotations.emit(detections)

    def _copy_selected_info(self):
        """Copy selected detection info to clipboard."""
        from PyQt6.QtWidgets import QApplication

        selected_rows = sorted(set(item.row() for item in self._table.selectedItems()))

        lines = []
        for row in selected_rows:
            label_item = self._table.item(row, 0)
            if label_item:
                det = label_item.data(Qt.ItemDataRole.UserRole)
                if det:
                    lines.append(
                        f"{det.label}\t{det.confidence:.3f}\t"
                        f"{det.start_time:.4f}\t{det.end_time:.4f}"
                    )

        if lines:
            clipboard = QApplication.clipboard()
            clipboard.setText("\n".join(lines))

    def get_filtered_detections(self) -> List[DetectionResult]:
        """Get the currently filtered detections."""
        return self._filtered_detections

    def get_all_detections(self) -> List[DetectionResult]:
        """Get all detections."""
        return self._detections

    def get_label_colors(self) -> Dict[str, str]:
        """Get the label to color mapping."""
        return {
            label: get_label_color(label, self._label_index)
            for label in self._label_index
        }

    def clear(self):
        """Clear all detections."""
        self._detections.clear()
        self._filtered_detections.clear()
        self._label_index.clear()
        self._table.setRowCount(0)
        self._label_combo.clear()
        self._label_combo.addItem("All Labels", None)
        self._status_label.setText("0 detections")
