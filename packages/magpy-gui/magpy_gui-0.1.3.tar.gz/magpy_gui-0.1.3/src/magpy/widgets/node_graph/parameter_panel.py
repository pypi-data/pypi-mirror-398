"""
ParameterPanel - Widget for editing node parameters.

Displays and edits the parameters of the currently selected node.
"""

from __future__ import annotations

from typing import Any, Optional, Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QFrame,
    QScrollArea,
    QPushButton,
    QFileDialog,
)

from .node import Node, ParameterDefinition


class ParameterWidget(QWidget):
    """Base widget for editing a single parameter."""

    value_changed = pyqtSignal(str, object)  # param_name, new_value

    def __init__(self, param_def: ParameterDefinition, parent=None):
        super().__init__(parent)
        self.param_def = param_def
        self._setup_ui()

    def _setup_ui(self):
        """Override in subclasses."""
        pass

    def get_value(self) -> Any:
        """Get the current value."""
        raise NotImplementedError

    def set_value(self, value: Any):
        """Set the value."""
        raise NotImplementedError


class StringParameterWidget(ParameterWidget):
    """Widget for string parameters."""

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._edit = QLineEdit()
        self._edit.setPlaceholderText(str(self.param_def.default or ""))
        self._edit.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #4c4c4c;
                border-radius: 3px;
                padding: 4px;
                color: #cccccc;
            }
            QLineEdit:focus {
                border: 1px solid #4a9eff;
            }
        """)
        self._edit.textChanged.connect(
            lambda text: self.value_changed.emit(self.param_def.name, text)
        )
        layout.addWidget(self._edit)

    def get_value(self) -> str:
        return self._edit.text()

    def set_value(self, value: Any):
        self._edit.setText(str(value) if value is not None else "")


class IntParameterWidget(ParameterWidget):
    """Widget for integer parameters."""

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._spin = QSpinBox()
        self._spin.setStyleSheet("""
            QSpinBox {
                background-color: #3c3c3c;
                border: 1px solid #4c4c4c;
                border-radius: 3px;
                padding: 4px;
                color: #cccccc;
            }
            QSpinBox:focus {
                border: 1px solid #4a9eff;
            }
        """)

        if self.param_def.min_value is not None:
            self._spin.setMinimum(int(self.param_def.min_value))
        else:
            self._spin.setMinimum(-999999)

        if self.param_def.max_value is not None:
            self._spin.setMaximum(int(self.param_def.max_value))
        else:
            self._spin.setMaximum(999999)

        if self.param_def.default is not None:
            self._spin.setValue(int(self.param_def.default))

        self._spin.valueChanged.connect(
            lambda value: self.value_changed.emit(self.param_def.name, value)
        )
        layout.addWidget(self._spin)

    def get_value(self) -> int:
        return self._spin.value()

    def set_value(self, value: Any):
        if value is not None:
            self._spin.setValue(int(value))


class FloatParameterWidget(ParameterWidget):
    """Widget for float parameters."""

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._spin = QDoubleSpinBox()
        self._spin.setDecimals(3)
        self._spin.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #3c3c3c;
                border: 1px solid #4c4c4c;
                border-radius: 3px;
                padding: 4px;
                color: #cccccc;
            }
            QDoubleSpinBox:focus {
                border: 1px solid #4a9eff;
            }
        """)

        if self.param_def.min_value is not None:
            self._spin.setMinimum(self.param_def.min_value)
        else:
            self._spin.setMinimum(-999999.0)

        if self.param_def.max_value is not None:
            self._spin.setMaximum(self.param_def.max_value)
        else:
            self._spin.setMaximum(999999.0)

        if self.param_def.default is not None:
            self._spin.setValue(float(self.param_def.default))

        self._spin.valueChanged.connect(
            lambda value: self.value_changed.emit(self.param_def.name, value)
        )
        layout.addWidget(self._spin)

    def get_value(self) -> float:
        return self._spin.value()

    def set_value(self, value: Any):
        if value is not None:
            self._spin.setValue(float(value))


class BoolParameterWidget(ParameterWidget):
    """Widget for boolean parameters."""

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._check = QCheckBox()
        self._check.setStyleSheet("""
            QCheckBox {
                color: #cccccc;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)

        if self.param_def.default:
            self._check.setChecked(bool(self.param_def.default))

        self._check.stateChanged.connect(
            lambda: self.value_changed.emit(self.param_def.name, self._check.isChecked())
        )
        layout.addWidget(self._check)
        layout.addStretch()

    def get_value(self) -> bool:
        return self._check.isChecked()

    def set_value(self, value: Any):
        self._check.setChecked(bool(value) if value is not None else False)


class ChoiceParameterWidget(ParameterWidget):
    """Widget for choice parameters."""

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._combo = QComboBox()
        self._combo.setStyleSheet("""
            QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #4c4c4c;
                border-radius: 3px;
                padding: 4px;
                color: #cccccc;
            }
            QComboBox:focus {
                border: 1px solid #4a9eff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                selection-background-color: #094771;
                color: #cccccc;
            }
        """)

        for choice in self.param_def.choices:
            self._combo.addItem(choice)

        if self.param_def.default in self.param_def.choices:
            self._combo.setCurrentText(str(self.param_def.default))

        self._combo.currentTextChanged.connect(
            lambda text: self.value_changed.emit(self.param_def.name, text)
        )
        layout.addWidget(self._combo)

    def get_value(self) -> str:
        return self._combo.currentText()

    def set_value(self, value: Any):
        if value is not None:
            self._combo.setCurrentText(str(value))


class FileParameterWidget(ParameterWidget):
    """Widget for file path parameters."""

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._edit = QLineEdit()
        self._edit.setPlaceholderText("Select file...")
        self._edit.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #4c4c4c;
                border-radius: 3px;
                padding: 4px;
                color: #cccccc;
            }
            QLineEdit:focus {
                border: 1px solid #4a9eff;
            }
        """)
        self._edit.textChanged.connect(
            lambda text: self.value_changed.emit(self.param_def.name, text)
        )
        layout.addWidget(self._edit)

        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(30)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #4c4c4c;
                border: none;
                border-radius: 3px;
                color: #cccccc;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #5c5c5c;
            }
        """)
        browse_btn.clicked.connect(self._browse)
        layout.addWidget(browse_btn)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {self.param_def.label or self.param_def.name}",
            "",
            "All Files (*.*)",
        )
        if path:
            self._edit.setText(path)

    def get_value(self) -> str:
        return self._edit.text()

    def set_value(self, value: Any):
        self._edit.setText(str(value) if value is not None else "")


class DirParameterWidget(ParameterWidget):
    """Widget for directory path parameters."""

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._edit = QLineEdit()
        self._edit.setPlaceholderText("Select folder...")
        self._edit.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #4c4c4c;
                border-radius: 3px;
                padding: 4px;
                color: #cccccc;
            }
            QLineEdit:focus {
                border: 1px solid #4a9eff;
            }
        """)
        self._edit.textChanged.connect(
            lambda text: self.value_changed.emit(self.param_def.name, text)
        )
        layout.addWidget(self._edit)

        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(30)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #4c4c4c;
                border: none;
                border-radius: 3px;
                color: #cccccc;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #5c5c5c;
            }
        """)
        browse_btn.clicked.connect(self._browse)
        layout.addWidget(browse_btn)

    def _browse(self):
        path = QFileDialog.getExistingDirectory(
            self,
            f"Select {self.param_def.label or self.param_def.name}",
            "",
        )
        if path:
            self._edit.setText(path)

    def get_value(self) -> str:
        return self._edit.text()

    def set_value(self, value: Any):
        self._edit.setText(str(value) if value is not None else "")


def create_parameter_widget(param_def: ParameterDefinition) -> ParameterWidget:
    """Create the appropriate widget for a parameter type."""
    widget_map = {
        "string": StringParameterWidget,
        "int": IntParameterWidget,
        "float": FloatParameterWidget,
        "bool": BoolParameterWidget,
        "choice": ChoiceParameterWidget,
        "file": FileParameterWidget,
        "dir": DirParameterWidget,
    }

    widget_class = widget_map.get(param_def.param_type, StringParameterWidget)
    return widget_class(param_def)


class ParameterPanel(QWidget):
    """Panel for editing node parameters."""

    parameters_changed = pyqtSignal(Node)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_node: Optional[Node] = None
        self._param_widgets: dict = {}

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-bottom: 1px solid #3c3c3c;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(12, 12, 12, 12)

        self._title_label = QLabel("Properties")
        self._title_label.setStyleSheet("color: #cccccc; font-size: 12px; font-weight: bold;")
        header_layout.addWidget(self._title_label)

        self._node_type_label = QLabel("")
        self._node_type_label.setStyleSheet("color: #858585; font-size: 10px;")
        header_layout.addWidget(self._node_type_label)

        layout.addWidget(header)

        # Scroll area for parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background-color: #4c4c4c;
                border-radius: 4px;
                min-height: 20px;
            }
        """)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(12, 12, 12, 12)
        self._content_layout.setSpacing(12)
        self._content_layout.addStretch()

        scroll.setWidget(self._content)
        layout.addWidget(scroll)

        # Placeholder when no node selected
        self._placeholder = QLabel("Select a node to edit its properties")
        self._placeholder.setStyleSheet("color: #858585; padding: 20px;")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.insertWidget(0, self._placeholder)

    def set_node(self, node: Optional[Node]):
        """Set the node to edit."""
        self._current_node = node
        self._rebuild_ui()

    def _rebuild_ui(self):
        """Rebuild the parameter UI for the current node."""
        # Clear existing widgets
        self._param_widgets.clear()
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget() and item.widget() != self._placeholder:
                item.widget().deleteLater()

        if not self._current_node:
            self._title_label.setText("Properties")
            self._node_type_label.setText("")
            self._placeholder.setVisible(True)
            return

        self._placeholder.setVisible(False)
        self._title_label.setText(self._current_node.definition.name)
        self._node_type_label.setText(self._current_node.definition.node_type)

        # Add parameter widgets
        for param_def in self._current_node.definition.parameters:
            # Parameter group
            group = QFrame()
            group.setStyleSheet("""
                QFrame {
                    background-color: #252526;
                    border: 1px solid #3c3c3c;
                    border-radius: 4px;
                }
            """)
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(10, 8, 10, 8)
            group_layout.setSpacing(4)

            # Label
            label_text = param_def.label or param_def.name
            label = QLabel(label_text)
            label.setStyleSheet("color: #cccccc; font-size: 11px; border: none;")
            group_layout.addWidget(label)

            # Description
            if param_def.description:
                desc = QLabel(param_def.description)
                desc.setStyleSheet("color: #858585; font-size: 9px; border: none;")
                desc.setWordWrap(True)
                group_layout.addWidget(desc)

            # Value widget
            widget = create_parameter_widget(param_def)
            widget.setStyleSheet("border: none;")

            # Set current value
            current_value = self._current_node.parameters.get(param_def.name, param_def.default)
            widget.set_value(current_value)

            # Connect value changes
            widget.value_changed.connect(self._on_param_changed)

            group_layout.addWidget(widget)
            self._param_widgets[param_def.name] = widget

            self._content_layout.insertWidget(
                self._content_layout.count() - 1, group
            )

    def _on_param_changed(self, param_name: str, value: Any):
        """Handle parameter value change."""
        if self._current_node:
            self._current_node.parameters[param_name] = value
            self.parameters_changed.emit(self._current_node)

    def get_current_node(self) -> Optional[Node]:
        """Get the currently edited node."""
        return self._current_node
