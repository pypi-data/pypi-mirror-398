"""
Pipeline Screen - Workflow/pipeline editing interface.

Provides UI for creating and running bioamla pipelines.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
)

from .base import BaseScreen


class PipelineScreen(BaseScreen):
    """
    Pipeline/workflow editing screen.

    This screen will provide an interface for:
    - Node-based visual editor (drag bioamla commands)
    - Visual connection of step outputs to inputs
    - Parameter editing panel per node
    - TOML import/export
    - Run workflow with progress visualization

    Currently a placeholder - full implementation pending.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

    @property
    def screen_name(self) -> str:
        return "Pipeline"

    @property
    def screen_icon(self) -> str:
        return "⚙️"

    def _setup_ui(self):
        """Set up the pipeline screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Placeholder content
        placeholder = QFrame()
        placeholder.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 2px dashed #3c3c3c;
                border-radius: 8px;
            }
        """)

        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("⚙️")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_layout.addWidget(icon_label)

        title = QLabel("Pipeline Editor")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #d4d4d4;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_layout.addWidget(title)

        description = QLabel(
            "Create and run bioamla workflows.\n\n"
            "- Drag and drop bioamla commands\n"
            "- Connect step outputs to inputs\n"
            "- Configure parameters per node\n"
            "- Import/export TOML pipelines\n"
            "- Run with progress visualization"
        )
        description.setStyleSheet("""
            font-size: 14px;
            color: #858585;
        """)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_layout.addWidget(description)

        badge = QLabel("Coming Soon")
        badge.setStyleSheet("""
            background-color: #0e639c;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        """)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_layout.addWidget(badge)

        layout.addWidget(placeholder)
