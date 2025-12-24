"""
NodePalette - Sidebar widget for dragging nodes onto the graph.

Displays available node types organized by category.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, QMimeData, QByteArray
from PyQt6.QtGui import QDrag, QColor, QPainter, QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QSizePolicy,
)

from .node import NodeDefinition, PortDefinition, ParameterDefinition, PortType


@dataclass
class NodeCategory:
    """Category for organizing nodes in the palette."""
    name: str
    color: str
    icon: str = ""
    description: str = ""


# Default categories for pipeline nodes
DEFAULT_CATEGORIES = {
    "input": NodeCategory("Input", "#4a9eff", "📥", "Data input nodes"),
    "output": NodeCategory("Output", "#00d4aa", "📤", "Data output nodes"),
    "audio": NodeCategory("Audio", "#ff6b6b", "🎵", "Audio processing nodes"),
    "analysis": NodeCategory("Analysis", "#ffd93d", "📊", "Analysis nodes"),
    "detection": NodeCategory("Detection", "#c084fc", "🔍", "Detection nodes"),
    "transform": NodeCategory("Transform", "#fb923c", "🔄", "Transform nodes"),
    "utility": NodeCategory("Utility", "#6c6c6c", "🔧", "Utility nodes"),
}


class NodePaletteItem(QFrame):
    """A draggable node item in the palette."""

    def __init__(self, definition: NodeDefinition, parent=None):
        super().__init__(parent)
        self.definition = definition

        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setStyleSheet(f"""
            NodePaletteItem {{
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 8px;
            }}
            NodePaletteItem:hover {{
                background-color: #3c3c3c;
                border: 1px solid {definition.color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        # Header with color indicator
        header = QHBoxLayout()
        header.setSpacing(6)

        color_indicator = QFrame()
        color_indicator.setFixedSize(4, 20)
        color_indicator.setStyleSheet(f"background-color: {definition.color}; border-radius: 2px;")
        header.addWidget(color_indicator)

        name_label = QLabel(definition.name)
        name_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 11px;")
        header.addWidget(name_label)
        header.addStretch()

        layout.addLayout(header)

        # Description
        if definition.description:
            desc_label = QLabel(definition.description)
            desc_label.setStyleSheet("color: #858585; font-size: 10px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        self.setToolTip(
            f"{definition.name}\n\n"
            f"{definition.description}\n\n"
            f"Inputs: {', '.join(p.name for p in definition.inputs) or 'None'}\n"
            f"Outputs: {', '.join(p.name for p in definition.outputs) or 'None'}"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            # Start drag
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setData(
                "application/x-magpy-node",
                QByteArray(self.definition.node_type.encode())
            )
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.CopyAction)


class NodePalette(QWidget):
    """Sidebar widget showing available node types."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._categories: Dict[str, NodeCategory] = DEFAULT_CATEGORIES.copy()
        self._definitions: Dict[str, List[NodeDefinition]] = {}

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
        header_layout.setSpacing(8)

        title = QLabel("Nodes")
        title.setStyleSheet("color: #cccccc; font-size: 12px; font-weight: bold;")
        header_layout.addWidget(title)

        # Search box
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search nodes...")
        self._search_box.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #4c4c4c;
                border-radius: 4px;
                padding: 6px;
                color: #cccccc;
            }
            QLineEdit:focus {
                border: 1px solid #4a9eff;
            }
        """)
        self._search_box.textChanged.connect(self._filter_nodes)
        header_layout.addWidget(self._search_box)

        layout.addWidget(header)

        # Tree widget for categories
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                border: none;
                outline: none;
            }
            QTreeWidget::item {
                padding: 4px;
                color: #cccccc;
            }
            QTreeWidget::item:hover {
                background-color: #2d2d2d;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
            }
            QTreeWidget::branch {
                background-color: #1e1e1e;
            }
        """)
        layout.addWidget(self._tree)

        # Scroll area for node items
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
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        self._content_layout.setSpacing(6)
        self._content_layout.addStretch()

        scroll.setWidget(self._content)
        layout.addWidget(scroll)

    def add_category(self, category_id: str, category: NodeCategory):
        """Add a category."""
        self._categories[category_id] = category

    def add_node_definition(self, definition: NodeDefinition):
        """Add a node definition."""
        category = definition.category
        if category not in self._definitions:
            self._definitions[category] = []
        self._definitions[category].append(definition)
        self._rebuild_palette()

    def add_node_definitions(self, definitions: List[NodeDefinition]):
        """Add multiple node definitions."""
        for definition in definitions:
            category = definition.category
            if category not in self._definitions:
                self._definitions[category] = []
            self._definitions[category].append(definition)
        self._rebuild_palette()

    def clear_definitions(self):
        """Clear all node definitions."""
        self._definitions.clear()
        self._rebuild_palette()

    def _rebuild_palette(self):
        """Rebuild the palette UI."""
        # Clear existing items
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add categories and nodes
        for category_id, category in self._categories.items():
            if category_id not in self._definitions:
                continue

            definitions = self._definitions[category_id]
            if not definitions:
                continue

            # Category header
            header = QLabel(f"{category.icon} {category.name}")
            header.setStyleSheet(f"""
                color: {category.color};
                font-weight: bold;
                font-size: 11px;
                padding: 8px 0 4px 0;
            """)
            self._content_layout.insertWidget(
                self._content_layout.count() - 1, header
            )

            # Node items
            for definition in definitions:
                item = NodePaletteItem(definition)
                self._content_layout.insertWidget(
                    self._content_layout.count() - 1, item
                )

    def _filter_nodes(self, text: str):
        """Filter nodes by search text."""
        text = text.lower()

        for i in range(self._content_layout.count()):
            item = self._content_layout.itemAt(i)
            widget = item.widget()

            if isinstance(widget, NodePaletteItem):
                matches = (
                    text in widget.definition.name.lower() or
                    text in widget.definition.description.lower() or
                    text in widget.definition.node_type.lower()
                )
                widget.setVisible(matches or not text)
            elif isinstance(widget, QLabel):
                # Show category header if any of its nodes match
                widget.setVisible(not text)

    def get_definitions(self) -> List[NodeDefinition]:
        """Get all node definitions."""
        all_defs = []
        for defs in self._definitions.values():
            all_defs.extend(defs)
        return all_defs


def create_default_node_definitions() -> List[NodeDefinition]:
    """Create default node definitions for common pipeline operations."""
    return [
        # Input nodes
        NodeDefinition(
            node_type="input.audio_file",
            name="Audio File",
            description="Load audio file from disk",
            category="input",
            color="#4a9eff",
            inputs=[],
            outputs=[
                PortDefinition("audio", PortType.OUTPUT, "audio", description="Audio data"),
            ],
            parameters=[
                ParameterDefinition("path", "file", "File Path", "", "Path to audio file"),
            ],
        ),
        NodeDefinition(
            node_type="input.audio_folder",
            name="Audio Folder",
            description="Load audio files from folder",
            category="input",
            color="#4a9eff",
            inputs=[],
            outputs=[
                PortDefinition("files", PortType.OUTPUT, "file_list", description="List of audio files"),
            ],
            parameters=[
                ParameterDefinition("path", "dir", "Folder Path", "", "Path to folder"),
                ParameterDefinition("pattern", "string", "Pattern", "*.wav", "File pattern"),
                ParameterDefinition("recursive", "bool", "Recursive", False, "Search subdirectories"),
            ],
        ),

        # Audio processing nodes
        NodeDefinition(
            node_type="audio.resample",
            name="Resample",
            description="Change audio sample rate",
            category="audio",
            color="#ff6b6b",
            inputs=[
                PortDefinition("audio", PortType.INPUT, "audio", description="Input audio"),
            ],
            outputs=[
                PortDefinition("audio", PortType.OUTPUT, "audio", description="Resampled audio"),
            ],
            parameters=[
                ParameterDefinition("sample_rate", "int", "Sample Rate", 16000, "Target sample rate", min_value=8000, max_value=96000),
            ],
        ),
        NodeDefinition(
            node_type="audio.normalize",
            name="Normalize",
            description="Normalize audio levels",
            category="audio",
            color="#ff6b6b",
            inputs=[
                PortDefinition("audio", PortType.INPUT, "audio", description="Input audio"),
            ],
            outputs=[
                PortDefinition("audio", PortType.OUTPUT, "audio", description="Normalized audio"),
            ],
            parameters=[
                ParameterDefinition("target_db", "float", "Target dB", -20.0, "Target loudness", min_value=-60.0, max_value=0.0),
                ParameterDefinition("peak", "bool", "Peak Normalize", False, "Use peak instead of RMS"),
            ],
        ),
        NodeDefinition(
            node_type="audio.filter",
            name="Filter",
            description="Apply frequency filter",
            category="audio",
            color="#ff6b6b",
            inputs=[
                PortDefinition("audio", PortType.INPUT, "audio", description="Input audio"),
            ],
            outputs=[
                PortDefinition("audio", PortType.OUTPUT, "audio", description="Filtered audio"),
            ],
            parameters=[
                ParameterDefinition("filter_type", "choice", "Type", "bandpass", "Filter type", choices=["lowpass", "highpass", "bandpass"]),
                ParameterDefinition("low_freq", "float", "Low Freq", 500.0, "Low cutoff frequency", min_value=0.0, max_value=24000.0),
                ParameterDefinition("high_freq", "float", "High Freq", 8000.0, "High cutoff frequency", min_value=0.0, max_value=24000.0),
                ParameterDefinition("order", "int", "Order", 5, "Filter order", min_value=1, max_value=10),
            ],
        ),
        NodeDefinition(
            node_type="audio.trim",
            name="Trim",
            description="Trim audio to time range",
            category="audio",
            color="#ff6b6b",
            inputs=[
                PortDefinition("audio", PortType.INPUT, "audio", description="Input audio"),
            ],
            outputs=[
                PortDefinition("audio", PortType.OUTPUT, "audio", description="Trimmed audio"),
            ],
            parameters=[
                ParameterDefinition("start", "float", "Start (s)", 0.0, "Start time in seconds", min_value=0.0),
                ParameterDefinition("end", "float", "End (s)", 0.0, "End time (0 = end of file)", min_value=0.0),
            ],
        ),

        # Analysis nodes
        NodeDefinition(
            node_type="analysis.spectrogram",
            name="Spectrogram",
            description="Compute spectrogram",
            category="analysis",
            color="#ffd93d",
            inputs=[
                PortDefinition("audio", PortType.INPUT, "audio", description="Input audio"),
            ],
            outputs=[
                PortDefinition("spectrogram", PortType.OUTPUT, "array", description="Spectrogram data"),
            ],
            parameters=[
                ParameterDefinition("n_fft", "int", "FFT Size", 2048, "FFT window size", min_value=256, max_value=8192),
                ParameterDefinition("hop_length", "int", "Hop Length", 512, "Hop length", min_value=64, max_value=4096),
            ],
        ),
        NodeDefinition(
            node_type="analysis.indices",
            name="Acoustic Indices",
            description="Calculate acoustic indices",
            category="analysis",
            color="#ffd93d",
            inputs=[
                PortDefinition("audio", PortType.INPUT, "audio", description="Input audio"),
            ],
            outputs=[
                PortDefinition("indices", PortType.OUTPUT, "dict", description="Computed indices"),
            ],
            parameters=[
                ParameterDefinition("indices", "string", "Indices", "all", "Comma-separated list or 'all'"),
            ],
        ),
        NodeDefinition(
            node_type="analysis.embed",
            name="Embeddings",
            description="Extract audio embeddings",
            category="analysis",
            color="#ffd93d",
            inputs=[
                PortDefinition("audio", PortType.INPUT, "audio", description="Input audio"),
            ],
            outputs=[
                PortDefinition("embeddings", PortType.OUTPUT, "array", description="Embedding vectors"),
            ],
            parameters=[
                ParameterDefinition("model", "choice", "Model", "ast", "Embedding model", choices=["ast", "birdnet", "perch"]),
            ],
        ),
        NodeDefinition(
            node_type="analysis.cluster",
            name="Cluster",
            description="Cluster embeddings",
            category="analysis",
            color="#ffd93d",
            inputs=[
                PortDefinition("embeddings", PortType.INPUT, "array", description="Embeddings"),
            ],
            outputs=[
                PortDefinition("labels", PortType.OUTPUT, "array", description="Cluster labels"),
                PortDefinition("centers", PortType.OUTPUT, "array", description="Cluster centers"),
            ],
            parameters=[
                ParameterDefinition("method", "choice", "Method", "hdbscan", "Clustering method", choices=["hdbscan", "kmeans", "dbscan"]),
                ParameterDefinition("n_clusters", "int", "N Clusters", 0, "Number of clusters (0=auto)", min_value=0, max_value=100),
            ],
        ),

        # Detection nodes
        NodeDefinition(
            node_type="detection.ml",
            name="ML Detection",
            description="Run ML-based detection",
            category="detection",
            color="#c084fc",
            inputs=[
                PortDefinition("audio", PortType.INPUT, "audio", description="Input audio"),
            ],
            outputs=[
                PortDefinition("detections", PortType.OUTPUT, "detections", description="Detection results"),
            ],
            parameters=[
                ParameterDefinition("model", "choice", "Model", "birdnet", "Detection model", choices=["birdnet", "ast", "perch"]),
                ParameterDefinition("threshold", "float", "Threshold", 0.5, "Confidence threshold", min_value=0.0, max_value=1.0),
            ],
        ),
        NodeDefinition(
            node_type="detection.ribbit",
            name="RIBBIT",
            description="Run RIBBIT detection for amphibians",
            category="detection",
            color="#c084fc",
            inputs=[
                PortDefinition("audio", PortType.INPUT, "audio", description="Input audio"),
            ],
            outputs=[
                PortDefinition("detections", PortType.OUTPUT, "detections", description="Detection results"),
            ],
            parameters=[
                ParameterDefinition("preset", "choice", "Preset", "generic_mid_freq", "Detection preset",
                                  choices=["generic_low_freq", "generic_mid_freq", "generic_high_freq"]),
            ],
        ),
        NodeDefinition(
            node_type="detection.energy",
            name="Energy Detection",
            description="Simple energy-based detection",
            category="detection",
            color="#c084fc",
            inputs=[
                PortDefinition("audio", PortType.INPUT, "audio", description="Input audio"),
            ],
            outputs=[
                PortDefinition("detections", PortType.OUTPUT, "detections", description="Detection results"),
            ],
            parameters=[
                ParameterDefinition("threshold_db", "float", "Threshold (dB)", -30.0, "Energy threshold", min_value=-60.0, max_value=0.0),
                ParameterDefinition("min_duration", "float", "Min Duration", 0.1, "Minimum event duration", min_value=0.01, max_value=10.0),
            ],
        ),

        # Output nodes
        NodeDefinition(
            node_type="output.save_audio",
            name="Save Audio",
            description="Save audio to file",
            category="output",
            color="#00d4aa",
            inputs=[
                PortDefinition("audio", PortType.INPUT, "audio", description="Audio to save"),
            ],
            outputs=[],
            parameters=[
                ParameterDefinition("path", "file", "Output Path", "", "Output file path"),
                ParameterDefinition("format", "choice", "Format", "wav", "Output format", choices=["wav", "mp3", "flac"]),
            ],
        ),
        NodeDefinition(
            node_type="output.save_csv",
            name="Save CSV",
            description="Save data to CSV file",
            category="output",
            color="#00d4aa",
            inputs=[
                PortDefinition("data", PortType.INPUT, "any", description="Data to save"),
            ],
            outputs=[],
            parameters=[
                ParameterDefinition("path", "file", "Output Path", "", "Output CSV path"),
            ],
        ),
        NodeDefinition(
            node_type="output.export_annotations",
            name="Export Annotations",
            description="Export detections as annotations",
            category="output",
            color="#00d4aa",
            inputs=[
                PortDefinition("detections", PortType.INPUT, "detections", description="Detections to export"),
            ],
            outputs=[],
            parameters=[
                ParameterDefinition("path", "file", "Output Path", "", "Output file path"),
                ParameterDefinition("format", "choice", "Format", "raven", "Annotation format", choices=["raven", "audacity", "csv"]),
            ],
        ),

        # Utility nodes
        NodeDefinition(
            node_type="utility.merge",
            name="Merge",
            description="Merge multiple inputs",
            category="utility",
            color="#6c6c6c",
            inputs=[
                PortDefinition("input1", PortType.INPUT, "any", description="First input"),
                PortDefinition("input2", PortType.INPUT, "any", description="Second input"),
            ],
            outputs=[
                PortDefinition("output", PortType.OUTPUT, "list", description="Merged output"),
            ],
            parameters=[],
        ),
        NodeDefinition(
            node_type="utility.split",
            name="Split",
            description="Split list into items",
            category="utility",
            color="#6c6c6c",
            inputs=[
                PortDefinition("input", PortType.INPUT, "list", description="List to split"),
            ],
            outputs=[
                PortDefinition("item", PortType.OUTPUT, "any", description="Individual items"),
            ],
            parameters=[],
        ),
    ]
