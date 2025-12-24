"""
Selection table widget for displaying and editing annotations.

Provides a spreadsheet-like interface for managing selections with:
- Label column with autocomplete
- Quick label hotkeys (1-9)
- Raven selection table import/export
- Right-click context menu for operations
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
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
    QCompleter,
    QInputDialog,
    QFileDialog,
    QMessageBox,
)

from ..core.selection import Selection, SelectionTable, AnnotationKeymap


@dataclass
class UndoAction:
    """Represents an undoable action."""
    action_type: str  # "add", "delete", "edit"
    selection_id: str
    selection_data: Optional[Dict] = None  # Serialized selection state
    old_value: Optional[str] = None  # For edits
    new_value: Optional[str] = None  # For edits
    field_name: Optional[str] = None  # For edits


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
    selection_added = pyqtSignal(str)  # selection_id (for undo tracking)
    undo_state_changed = pyqtSignal(bool, bool)  # can_undo, can_redo

    # Standard columns (Label is editable, others are read-only)
    STANDARD_COLUMNS = [
        ("Selection", "ID"),
        ("Channel", "Ch"),
        ("Begin Time (s)", "Begin"),
        ("End Time (s)", "End"),
        ("Delta Time (s)", "Duration"),
        ("Low Freq (Hz)", "Low Freq"),
        ("High Freq (Hz)", "High Freq"),
        ("Label", "Label"),
    ]

    # Column index for Label
    LABEL_COL_INDEX = 7

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._selection_table: Optional[SelectionTable] = None
        self._selected_row: int = -1

        # Undo/redo stacks
        self._undo_stack: List[UndoAction] = []
        self._redo_stack: List[UndoAction] = []
        self._max_undo_size = 50

        # Label autocomplete
        self._known_labels: Set[str] = set()
        self._label_completer: Optional[QCompleter] = None

        # Quick label hotkeys (1-9)
        self._label_keymap = AnnotationKeymap("Label")

        self._setup_ui()
        self._setup_connections()
        self._setup_hotkeys()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        # Import button
        import_btn = QPushButton("Import")
        import_btn.setFixedWidth(60)
        import_btn.setToolTip("Import Raven selection table (Ctrl+I)")
        import_btn.clicked.connect(self._import_raven_table)
        toolbar_layout.addWidget(import_btn)

        # Export button
        export_btn = QPushButton("Export")
        export_btn.setFixedWidth(60)
        export_btn.setToolTip("Export as Raven selection table (Ctrl+E)")
        export_btn.clicked.connect(self._export_raven_table)
        toolbar_layout.addWidget(export_btn)

        toolbar_layout.addSpacing(10)

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
            # Handle Label column specially
            if col_key == "Label":
                # Get label from annotations if present
                value = selection.annotations.get("Label", "")
            else:
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

            # Make Label column and annotation columns editable
            if col_key == "Label" or col >= len(self.STANDARD_COLUMNS):
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            else:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self._table.setItem(row, col, item)

            # Track known labels for autocomplete
            if col_key == "Label" and text:
                self._known_labels.add(text)

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
        """Handle cell value changes (for annotation/label editing)."""
        if self._selection_table is None:
            return

        # Get column name
        header_item = self._table.horizontalHeaderItem(col)
        if not header_item:
            return
        col_name = header_item.text()

        # Only handle Label column and annotation columns
        if col_name != "Label" and col < len(self.STANDARD_COLUMNS):
            return

        # Get selection ID
        id_item = self._table.item(row, 0)
        if not id_item:
            return

        selection_id = id_item.data(Qt.ItemDataRole.UserRole)
        selection = self._selection_table.get_by_id(selection_id)
        if not selection:
            return

        # Get new value
        cell_item = self._table.item(row, col)
        if not cell_item:
            return
        new_value = cell_item.text()

        # Get old value for undo
        old_value = selection.annotations.get(col_name, "")

        # Only push to undo if value actually changed
        if old_value != new_value:
            action = UndoAction(
                action_type="edit",
                selection_id=selection_id,
                old_value=old_value,
                new_value=new_value,
                field_name=col_name,
            )
            self._push_undo(action)

        # Update annotation
        selection.annotations[col_name] = new_value

        # Track label for autocomplete
        if col_name == "Label" and new_value:
            self._known_labels.add(new_value)
            self._update_label_completer()

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
        if not self._selection_table:
            return

        col_name, ok = QInputDialog.getText(
            self,
            "Add Annotation Column",
            "Column name:",
            QLineEdit.EchoMode.Normal,
            f"Annotation{len(self._selection_table.annotation_columns) + 1}",
        )

        if ok and col_name:
            col_name = col_name.strip()
            if col_name:
                self._selection_table.add_annotation_column(col_name)
                self._refresh_table()

    def _delete_selected(self):
        """Delete the selected selection."""
        if self._selected_row < 0 or self._selected_row >= self._table.rowCount():
            return

        id_item = self._table.item(self._selected_row, 0)
        if not id_item:
            return

        selection_id = id_item.data(Qt.ItemDataRole.UserRole)
        if not selection_id:
            return

        # Get the selection before removing (for undo)
        if self._selection_table:
            selection = self._selection_table.get_by_id(selection_id)
            if selection:
                # Push to undo stack before removing
                action = UndoAction(
                    action_type="delete",
                    selection_id=selection_id,
                    selection_data=self._serialize_selection(selection),
                )
                self._push_undo(action)

            # Remove from our local selection table
            self._selection_table.remove_by_id(selection_id)

        # Reset selected row before refresh
        self._selected_row = -1

        # Emit signal for external handlers
        self.selection_deleted.emit(selection_id)

        # Refresh the display
        self._refresh_table()

    def _show_context_menu(self, pos):
        """Show context menu."""
        item = self._table.itemAt(pos)
        if not item:
            return

        row = item.row()
        id_item = self._table.item(row, 0)
        if not id_item:
            return

        selection_id = id_item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)

        # Go to selection
        go_action = menu.addAction("Go to Selection")
        go_action.triggered.connect(
            lambda: self.selection_selected.emit(selection_id)
        )

        menu.addSeparator()

        # Quick label submenu
        label_menu = menu.addMenu("Set Label")

        # Show configured hotkey labels
        for key, value in self._label_keymap.mappings.items():
            action = label_menu.addAction(f"{key}: {value}")
            action.triggered.connect(
                lambda checked, v=value: self._set_label_for_selection(selection_id, v)
            )

        if self._label_keymap.mappings:
            label_menu.addSeparator()

        # Custom label option
        custom_action = label_menu.addAction("Custom...")
        custom_action.triggered.connect(
            lambda: self._set_custom_label(selection_id)
        )

        # Configure labels
        config_action = label_menu.addAction("Configure Hotkeys...")
        config_action.triggered.connect(self._configure_label_hotkeys)

        menu.addSeparator()

        # Copy selection info
        copy_action = menu.addAction("Copy Info")
        copy_action.triggered.connect(
            lambda: self._copy_selection_info(selection_id)
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

    # =========================================================================
    # Hotkey Setup
    # =========================================================================

    def _setup_hotkeys(self):
        """Set up keyboard shortcuts for quick labeling."""
        # Number keys 1-9 for quick labels
        for i in range(1, 10):
            shortcut = QShortcut(QKeySequence(str(i)), self)
            shortcut.activated.connect(lambda key=str(i): self._apply_label_hotkey(key))

        # Import/Export shortcuts
        import_shortcut = QShortcut(QKeySequence("Ctrl+I"), self)
        import_shortcut.activated.connect(self._import_raven_table)

        export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        export_shortcut.activated.connect(self._export_raven_table)

        # Delete shortcut
        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self._delete_selected)

        # Undo/Redo shortcuts
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        undo_shortcut.activated.connect(self.undo)

        redo_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        redo_shortcut.activated.connect(self.redo)

        redo_shortcut2 = QShortcut(QKeySequence("Ctrl+Y"), self)
        redo_shortcut2.activated.connect(self.redo)

    def _apply_label_hotkey(self, key: str):
        """Apply a label hotkey to the selected selection."""
        selection_id = self.get_selected_id()
        if not selection_id or not self._selection_table:
            return

        selection = self._selection_table.get_by_id(selection_id)
        if not selection:
            return

        # Apply the keymap
        if self._label_keymap.apply(key, selection):
            self._refresh_table()
            self.selection_edited.emit(selection_id)

    # =========================================================================
    # Label Autocomplete
    # =========================================================================

    def _update_label_completer(self):
        """Update the label completer with known labels."""
        if self._known_labels:
            self._label_completer = QCompleter(sorted(self._known_labels))
            self._label_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def add_known_labels(self, labels: List[str]):
        """Add labels to the known labels set for autocomplete."""
        self._known_labels.update(labels)
        self._update_label_completer()

    # =========================================================================
    # Label Operations
    # =========================================================================

    def _set_label_for_selection(self, selection_id: str, label: str):
        """Set the label for a selection."""
        if not self._selection_table:
            return

        selection = self._selection_table.get_by_id(selection_id)
        if selection:
            selection.annotations["Label"] = label
            self._known_labels.add(label)
            self._refresh_table()
            self.selection_edited.emit(selection_id)

    def _set_custom_label(self, selection_id: str):
        """Show dialog to set a custom label."""
        if not self._selection_table:
            return

        selection = self._selection_table.get_by_id(selection_id)
        if not selection:
            return

        current_label = selection.annotations.get("Label", "")

        label, ok = QInputDialog.getText(
            self,
            "Set Label",
            "Enter label:",
            QLineEdit.EchoMode.Normal,
            current_label,
        )

        if ok:
            self._set_label_for_selection(selection_id, label)

    def _configure_label_hotkeys(self):
        """Show dialog to configure label hotkeys."""
        # Build current config display
        current_config = "\n".join(
            f"{k}: {v}" for k, v in sorted(self._label_keymap.mappings.items())
        )

        text, ok = QInputDialog.getMultiLineText(
            self,
            "Configure Label Hotkeys",
            "Enter hotkey mappings (one per line, format: key: label):\n"
            "Example:\n1: bird\n2: frog\n3: insect",
            current_config,
        )

        if ok:
            # Parse the new config
            self._label_keymap = AnnotationKeymap("Label")
            for line in text.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value:
                        self._label_keymap.add_mapping(key, value)
                        self._known_labels.add(value)

            self._update_label_completer()

    def _copy_selection_info(self, selection_id: str):
        """Copy selection info to clipboard."""
        if not self._selection_table:
            return

        selection = self._selection_table.get_by_id(selection_id)
        if not selection:
            return

        from PyQt6.QtWidgets import QApplication

        info = (
            f"Selection: {selection.id}\n"
            f"Channel: {selection.channel}\n"
            f"Begin: {selection.begin_time:.4f}s\n"
            f"End: {selection.end_time:.4f}s\n"
            f"Duration: {selection.duration:.4f}s\n"
        )

        if selection.low_freq is not None:
            info += f"Low Freq: {selection.low_freq:.1f} Hz\n"
        if selection.high_freq is not None:
            info += f"High Freq: {selection.high_freq:.1f} Hz\n"

        label = selection.annotations.get("Label", "")
        if label:
            info += f"Label: {label}\n"

        clipboard = QApplication.clipboard()
        clipboard.setText(info)

    # =========================================================================
    # Import/Export
    # =========================================================================

    def _import_raven_table(self):
        """Import a Raven selection table."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Raven Selection Table",
            "",
            "Selection Tables (*.txt *.csv *.tsv);;All Files (*)",
        )

        if not filepath:
            return

        try:
            table = SelectionTable.load(filepath)

            if self._selection_table is None:
                self._selection_table = table
            else:
                # Merge with existing table
                for selection in table:
                    self._selection_table.add(selection)

                # Merge annotation columns
                for col in table.annotation_columns:
                    if col not in self._selection_table.annotation_columns:
                        self._selection_table.add_annotation_column(col)

            # Ensure Label column exists
            if "Label" not in self._selection_table.annotation_columns:
                self._selection_table.add_annotation_column("Label")

            self._refresh_table()

            QMessageBox.information(
                self,
                "Import Complete",
                f"Imported {len(table)} selections from:\n{Path(filepath).name}",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import selection table:\n{e}",
            )

    def _export_raven_table(self):
        """Export to a Raven selection table."""
        if not self._selection_table or len(self._selection_table) == 0:
            QMessageBox.warning(
                self,
                "No Selections",
                "There are no selections to export.",
            )
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Raven Selection Table",
            "selections.txt",
            "Tab-delimited (*.txt);;CSV (*.csv)",
        )

        if not filepath:
            return

        try:
            # Determine format from extension
            ext = Path(filepath).suffix.lower()
            fmt = "csv" if ext == ".csv" else "tsv"

            self._selection_table.save(filepath, format=fmt)

            QMessageBox.information(
                self,
                "Export Complete",
                f"Exported {len(self._selection_table)} selections to:\n{Path(filepath).name}",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export selection table:\n{e}",
            )

    # =========================================================================
    # Public API
    # =========================================================================

    def set_label_hotkeys(self, mappings: Dict[str, str]):
        """Set the label hotkey mappings.

        Args:
            mappings: Dictionary mapping keys (1-9) to label values.
        """
        self._label_keymap = AnnotationKeymap("Label")
        for key, value in mappings.items():
            self._label_keymap.add_mapping(key, value)
            self._known_labels.add(value)
        self._update_label_completer()

    def get_label_hotkeys(self) -> Dict[str, str]:
        """Get the current label hotkey mappings."""
        return self._label_keymap.mappings

    def get_all_labels(self) -> List[str]:
        """Get all known labels."""
        return sorted(self._known_labels)

    def get_selection_table(self) -> Optional[SelectionTable]:
        """Get the current selection table."""
        return self._selection_table

    # =========================================================================
    # Undo/Redo Operations
    # =========================================================================

    def _push_undo(self, action: UndoAction):
        """Push an action to the undo stack."""
        self._undo_stack.append(action)
        # Limit stack size
        if len(self._undo_stack) > self._max_undo_size:
            self._undo_stack.pop(0)
        # Clear redo stack on new action
        self._redo_stack.clear()
        # Emit state change
        self.undo_state_changed.emit(self.can_undo(), self.can_redo())

    def _serialize_selection(self, selection: Selection) -> Dict:
        """Serialize a selection for undo/redo storage."""
        return {
            "id": selection.id,
            "channel": selection.channel,
            "begin_time": selection.begin_time,
            "end_time": selection.end_time,
            "low_freq": selection.low_freq,
            "high_freq": selection.high_freq,
            "annotations": copy.deepcopy(selection.annotations),
            "measurements": copy.deepcopy(selection.measurements),
            "begin_file": selection.begin_file,
            "end_file": selection.end_file,
        }

    def _deserialize_selection(self, data: Dict) -> Selection:
        """Deserialize a selection from undo/redo storage."""
        return Selection(
            id=data["id"],
            channel=data["channel"],
            begin_time=data["begin_time"],
            end_time=data["end_time"],
            low_freq=data["low_freq"],
            high_freq=data["high_freq"],
            annotations=copy.deepcopy(data.get("annotations", {})),
            measurements=copy.deepcopy(data.get("measurements", {})),
            begin_file=data.get("begin_file"),
            end_file=data.get("end_file"),
        )

    def undo(self):
        """Undo the last action."""
        if not self._undo_stack or not self._selection_table:
            return

        action = self._undo_stack.pop()

        if action.action_type == "add":
            # Undo add = delete the selection
            self._selection_table.remove_by_id(action.selection_id)
            self._redo_stack.append(action)

        elif action.action_type == "delete":
            # Undo delete = re-add the selection
            if action.selection_data:
                selection = self._deserialize_selection(action.selection_data)
                self._selection_table.add(selection)
                self._redo_stack.append(action)

        elif action.action_type == "edit":
            # Undo edit = restore old value
            selection = self._selection_table.get_by_id(action.selection_id)
            if selection and action.field_name:
                selection.annotations[action.field_name] = action.old_value or ""
                self._redo_stack.append(action)

        self._refresh_table()
        self.undo_state_changed.emit(self.can_undo(), self.can_redo())

    def redo(self):
        """Redo the last undone action."""
        if not self._redo_stack or not self._selection_table:
            return

        action = self._redo_stack.pop()

        if action.action_type == "add":
            # Redo add = re-add the selection
            if action.selection_data:
                selection = self._deserialize_selection(action.selection_data)
                self._selection_table.add(selection)
                self._undo_stack.append(action)

        elif action.action_type == "delete":
            # Redo delete = delete again
            self._selection_table.remove_by_id(action.selection_id)
            self._undo_stack.append(action)

        elif action.action_type == "edit":
            # Redo edit = apply new value
            selection = self._selection_table.get_by_id(action.selection_id)
            if selection and action.field_name:
                selection.annotations[action.field_name] = action.new_value or ""
                self._undo_stack.append(action)

        self._refresh_table()
        self.undo_state_changed.emit(self.can_undo(), self.can_redo())

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0

    def clear_undo_history(self):
        """Clear undo/redo history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.undo_state_changed.emit(False, False)

    def add_selection_with_undo(self, selection: Selection):
        """Add a selection and push to undo stack.

        Call this when creating selections from external sources (e.g., spectrogram)
        to enable undo support.

        Args:
            selection: The selection to add
        """
        if self._selection_table is None:
            return

        # Add to table
        self._selection_table.add(selection)

        # Push to undo stack
        action = UndoAction(
            action_type="add",
            selection_id=selection.id,
            selection_data=self._serialize_selection(selection),
        )
        self._push_undo(action)

        # Refresh display
        self._refresh_table()

        # Emit signal
        self.selection_added.emit(selection.id)
