"""
Navigation Bar - Vertical icon bar for switching between main views.

VS Code activity bar style navigation with exclusive selection.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QButtonGroup,
    QSizePolicy,
)


class ViewType(Enum):
    """Available main views in the application."""
    AUDIO = auto()
    PIPELINE = auto()
    TRAINING = auto()
    BATCH = auto()


class NavButton(QPushButton):
    """Navigation button with icon and tooltip."""

    def __init__(self, icon: str, tooltip: str, parent: Optional[QWidget] = None):
        super().__init__(icon, parent)
        self.setToolTip(tooltip)
        self.setCheckable(True)
        self.setFixedSize(48, 48)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
            QPushButton:checked {
                background-color: #094771;
                border-left: 2px solid #0e639c;
            }
        """)


class NavigationBar(QWidget):
    """
    Vertical navigation bar for switching between main application views.

    Emits view_changed signal when user selects a different view.
    """

    view_changed = pyqtSignal(ViewType)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the navigation bar UI."""
        self.setFixedWidth(50)
        self.setStyleSheet("""
            QWidget {
                background-color: #252526;
                border-right: 1px solid #3c3c3c;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Button group for exclusive selection
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        # View buttons
        self._buttons: dict[ViewType, NavButton] = {}

        views = [
            (ViewType.AUDIO, "🎵", "Audio Analysis"),
            (ViewType.PIPELINE, "⚙️", "Pipeline Editor"),
            (ViewType.TRAINING, "🧠", "Model Training"),
            (ViewType.BATCH, "📚", "Batch Processing"),
        ]

        for view_type, icon, tooltip in views:
            btn = NavButton(icon, tooltip)
            self._buttons[view_type] = btn
            self._button_group.addButton(btn)
            layout.addWidget(btn)
            btn.clicked.connect(lambda checked, vt=view_type: self._on_button_clicked(vt))

        # Select audio view by default
        self._buttons[ViewType.AUDIO].setChecked(True)

        # Spacer to push buttons to top
        layout.addStretch()

    def _on_button_clicked(self, view_type: ViewType):
        """Handle navigation button click."""
        self.view_changed.emit(view_type)

    def set_current_view(self, view_type: ViewType):
        """Programmatically set the current view."""
        if view_type in self._buttons:
            self._buttons[view_type].setChecked(True)
