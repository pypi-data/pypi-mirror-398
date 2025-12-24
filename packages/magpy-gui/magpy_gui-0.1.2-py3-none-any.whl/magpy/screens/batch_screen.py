"""
Batch Screen - Batch processing interface for multiple files.

Provides UI for processing multiple audio files with task queue
management and parallel processing.
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


class BatchScreen(BaseScreen):
    """
    Batch processing screen.

    This screen will provide an interface for:
    - File/folder selection for batch processing
    - Task queue with progress tracking
    - Results aggregation and export
    - Parallel processing configuration

    Currently a placeholder - full implementation pending.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

    @property
    def screen_name(self) -> str:
        return "Batch"

    @property
    def screen_icon(self) -> str:
        return "📚"

    def _setup_ui(self):
        """Set up the batch screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

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

        icon_label = QLabel("📚")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_layout.addWidget(icon_label)

        title = QLabel("Batch Processing")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #d4d4d4;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_layout.addWidget(title)

        description = QLabel(
            "Process multiple audio files at once.\n\n"
            "- Select files or folders\n"
            "- Configure processing pipeline\n"
            "- Track progress in task queue\n"
            "- Aggregate and export results\n"
            "- Parallel processing support"
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
