"""
Selection table widget for displaying and editing annotations.

Provides a spreadsheet-like interface for managing selections.
"""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QLineEdit,
    QComboBox,
    QLabel,
    QMenu,
    QAbstractItemView,
)

from ..core.selection import Selection, SelectionTable


class SelectionTableWidget(QWidget):
    """
    Widget for displaying and editing selection tables.

    Features:
    - Spreadsheet-like display
    - Column sorting
    - Selection highlighting
    - Quick annotation editing
    - Context menu for operations
    """

    # Signals
    selection_selected = pyqtSignal(str)  # selection_id
    selection_deleted = pyqtSignal(str)  # selection_id
    selection_edited = pyqtSignal(str)  # selection_id

    # Standard columns
    STANDARD_COLUMNS = [
        ("Selection", "ID"),
        ("Channel", "Ch"),
        ("Begin Time (s)", "Begin"),
        ("End Time (s)", "End"),
        ("Delta Time (s)", "Duration"),
        ("Low Freq (Hz)", "Low Freq"),
        ("High Freq (Hz)", "High Freq"),
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._selection_table: Optional[SelectionTable] = None
        self._selected_row: int = -1

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        # Search/filter
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Filter selections...")
        self._search_input.setClearButtonEnabled(True)
        toolbar_layout.addWidget(self._search_input)

        # Add column button
        add_col_btn = QPushButton("+ Column")
        add_col_btn.setFixedWidth(80)
        add_col_btn.clicked.connect(self._add_column)
        toolbar_layout.addWidget(add_col_btn)

        # Delete selection button
        delete_btn = QPushButton("Delete")
        delete_btn.setFixedWidth(60)
        delete_btn.clicked.connect(self._delete_selected)
        toolbar_layout.addWidget(delete_btn)

        layout.addLayout(toolbar_layout)

        # Table
        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setSortingEnabled(True)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Style the table
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
            QHeaderView::section:hover {
                background-color: #3c3c3c;
            }
            """
        )

        # Configure header
        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionsMovable(True)
        header.setHighlightSections(False)

        layout.addWidget(self._table)

        # Status bar
        status_layout = QHBoxLayout()
        self._status_label = QLabel("0 selections")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Initialize with empty columns
        self._setup_columns()

    def _setup_columns(self):
        """Set up table columns."""
        column_names = [name for _, name in self.STANDARD_COLUMNS]
        self._table.setColumnCount(len(column_names))
        self._table.setHorizontalHeaderLabels(column_names)

    def _setup_connections(self):
        """Set up signal connections."""
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._search_input.textChanged.connect(self._filter_table)
        self._table.cellChanged.connect(self._on_cell_changed)

    def set_selection_table(self, table: SelectionTable):
        """Set the selection table to display."""
        self._selection_table = table
        self._refresh_table()

    def _refresh_table(self):
        """Refresh the table display."""
        if self._selection_table is None:
            self._table.setRowCount(0)
            self._status_label.setText("0 selections")
            return

        # Block signals during update
        self._table.blockSignals(True)

        # Determine columns (standard + annotation columns)
        all_columns = list(self.STANDARD_COLUMNS)
        for col_name in self._selection_table.annotation_columns:
            all_columns.append((col_name, col_name))

        # Set up columns
        column_names = [name for _, name in all_columns]
        self._table.setColumnCount(len(column_names))
        self._table.setHorizontalHeaderLabels(column_names)

        # Populate rows
        self._table.setRowCount(len(self._selection_table))

        for row, selection in enumerate(self._selection_table):
            self._populate_row(row, selection, all_columns)

        # Restore signals
        self._table.blockSignals(False)

        # Update status
        self._status_label.setText(f"{len(self._selection_table)} selections")

        # Resize columns to content
        self._table.resizeColumnsToContents()

    def _populate_row(self, row: int, selection: Selection, columns: list):
        """Populate a single row with selection data."""
        data = selection.to_dict()

        for col, (col_key, _) in enumerate(columns):
            value = data.get(col_key, "")

            # Format numeric values
            if isinstance(value, float):
                if "Freq" in col_key:
                    text = f"{value:.1f}"
                elif "Time" in col_key:
                    text = f"{value:.4f}"
                else:
                    text = f"{value:.3f}"
            else:
                text = str(value) if value is not None else ""

            item = QTableWidgetItem(text)

            # Store selection ID in first column
            if col == 0:
                item.setData(Qt.ItemDataRole.UserRole, selection.id)

            # Make standard columns read-only except annotations
            if col < len(self.STANDARD_COLUMNS):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            else:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

            self._table.setItem(row, col, item)

    def _on_selection_changed(self):
        """Handle table selection change."""
        selected = self._table.selectedItems()
        if selected:
            row = selected[0].row()
            self._selected_row = row

            # Get selection ID from first column
            id_item = self._table.item(row, 0)
            if id_item:
                selection_id = id_item.data(Qt.ItemDataRole.UserRole)
                if selection_id:
                    self.selection_selected.emit(selection_id)

    def _on_cell_changed(self, row: int, col: int):
        """Handle cell value changes (for annotation editing)."""
        if self._selection_table is None:
            return

        # Only handle annotation columns
        if col < len(self.STANDARD_COLUMNS):
            return

        # Get selection ID
        id_item = self._table.item(row, 0)
        if not id_item:
            return

        selection_id = id_item.data(Qt.ItemDataRole.UserRole)
        selection = self._selection_table.get_by_id(selection_id)
        if not selection:
            return

        # Get column name and new value
        col_name = self._table.horizontalHeaderItem(col).text()
        new_value = self._table.item(row, col).text()

        # Update annotation
        selection.annotations[col_name] = new_value
        self.selection_edited.emit(selection_id)

    def _filter_table(self, text: str):
        """Filter table rows based on search text."""
        text = text.lower()

        for row in range(self._table.rowCount()):
            match = False
            for col in range(self._table.columnCount()):
                item = self._table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self._table.setRowHidden(row, not match)

    def _add_column(self):
        """Add a new annotation column."""
        # TODO: Show dialog to get column name
        if self._selection_table:
            col_name = f"Annotation{len(self._selection_table.annotation_columns) + 1}"
            self._selection_table.add_annotation_column(col_name)
            self._refresh_table()

    def _delete_selected(self):
        """Delete the selected selection."""
        if self._selected_row >= 0:
            id_item = self._table.item(self._selected_row, 0)
            if id_item:
                selection_id = id_item.data(Qt.ItemDataRole.UserRole)
                if selection_id:
                    self.selection_deleted.emit(selection_id)
                    self._refresh_table()

    def _show_context_menu(self, pos):
        """Show context menu."""
        item = self._table.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)

        # Go to selection
        go_action = menu.addAction("Go to Selection")
        go_action.triggered.connect(
            lambda: self.selection_selected.emit(
                self._table.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
            )
        )

        menu.addSeparator()

        # Delete
        delete_action = menu.addAction("Delete Selection")
        delete_action.triggered.connect(self._delete_selected)

        menu.exec(self._table.mapToGlobal(pos))

    def get_selected_id(self) -> Optional[str]:
        """Get the ID of the currently selected selection."""
        if self._selected_row >= 0:
            id_item = self._table.item(self._selected_row, 0)
            if id_item:
                return id_item.data(Qt.ItemDataRole.UserRole)
        return None

    def select_by_id(self, selection_id: str):
        """Select a row by selection ID."""
        for row in range(self._table.rowCount()):
            id_item = self._table.item(row, 0)
            if id_item and id_item.data(Qt.ItemDataRole.UserRole) == selection_id:
                self._table.selectRow(row)
                break
