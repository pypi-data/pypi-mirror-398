"""
Pipeline Screen - Node-based workflow/pipeline editing interface.

Provides UI for creating and running pipelines using a visual node editor.
Generic interface ready for future bioamla integration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QFrame,
    QLabel,
    QPushButton,
    QToolBar,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtGui import QAction, QKeySequence

from .base import BaseScreen
from magpy.widgets.node_graph import (
    NodeGraphWidget,
    NodePalette,
    ParameterPanel,
    Node,
    create_default_node_definitions,
)


class PipelineScreen(BaseScreen):
    """
    Pipeline/workflow editing screen with node-based visual editor.

    Features:
    - Drag-and-drop node placement
    - Visual wire connections between nodes
    - Parameter editing panel
    - Save/load pipeline configurations
    - Ready for bioamla integration

    The interface is generic and will be wired to bioamla's
    pipeline system in a future release.
    """

    # Signals
    pipeline_changed = pyqtSignal()
    pipeline_saved = pyqtSignal(str)  # filepath

    def __init__(self, parent: Optional[QWidget] = None):
        self._graph: Optional[NodeGraphWidget] = None
        self._palette: Optional[NodePalette] = None
        self._param_panel: Optional[ParameterPanel] = None
        self._current_file: Optional[Path] = None
        self._is_modified = False

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Main content area with splitters
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3c3c3c;
            }
        """)

        # Left panel: Node palette
        self._palette = NodePalette()
        self._palette.setMinimumWidth(200)
        self._palette.setMaximumWidth(300)
        main_splitter.addWidget(self._palette)

        # Center: Node graph
        self._graph = NodeGraphWidget()
        self._graph.setMinimumWidth(400)
        main_splitter.addWidget(self._graph)

        # Right panel: Parameter editor
        self._param_panel = ParameterPanel()
        self._param_panel.setMinimumWidth(250)
        self._param_panel.setMaximumWidth(350)
        main_splitter.addWidget(self._param_panel)

        # Set splitter proportions
        main_splitter.setSizes([220, 600, 280])
        layout.addWidget(main_splitter)

        # Status bar
        self._status_bar = self._create_status_bar()
        layout.addWidget(self._status_bar)

        # Initialize with default nodes
        self._setup_default_nodes()

        # Connect signals
        self._connect_signals()

    def _create_toolbar(self) -> QToolBar:
        """Create the pipeline toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #252526;
                border-bottom: 1px solid #3c3c3c;
                padding: 4px;
                spacing: 4px;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                color: #cccccc;
            }
            QToolButton:hover {
                background-color: #3c3c3c;
            }
            QToolButton:pressed {
                background-color: #4c4c4c;
            }
        """)

        # New pipeline
        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setToolTip("New Pipeline (Ctrl+N)")
        new_action.triggered.connect(self._new_pipeline)
        toolbar.addAction(new_action)

        # Open pipeline
        open_action = QAction("Open", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setToolTip("Open Pipeline (Ctrl+O)")
        open_action.triggered.connect(self._open_pipeline)
        toolbar.addAction(open_action)

        # Save pipeline
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.setToolTip("Save Pipeline (Ctrl+S)")
        save_action.triggered.connect(self._save_pipeline)
        toolbar.addAction(save_action)

        # Save As
        save_as_action = QAction("Save As", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.setToolTip("Save Pipeline As...")
        save_as_action.triggered.connect(self._save_pipeline_as)
        toolbar.addAction(save_as_action)

        toolbar.addSeparator()

        # Run pipeline (placeholder)
        run_action = QAction("▶ Run", self)
        run_action.setShortcut(QKeySequence("F5"))
        run_action.setToolTip("Run Pipeline (F5) - Coming soon")
        run_action.triggered.connect(self._run_pipeline)
        toolbar.addAction(run_action)

        # Stop pipeline (placeholder)
        stop_action = QAction("⬛ Stop", self)
        stop_action.setToolTip("Stop Pipeline - Coming soon")
        stop_action.triggered.connect(self._stop_pipeline)
        stop_action.setEnabled(False)
        toolbar.addAction(stop_action)
        self._stop_action = stop_action

        toolbar.addSeparator()

        # Reset view
        reset_view_action = QAction("Reset View", self)
        reset_view_action.setShortcut(QKeySequence("Home"))
        reset_view_action.setToolTip("Reset View (Home)")
        reset_view_action.triggered.connect(self._reset_view)
        toolbar.addAction(reset_view_action)

        # Clear all
        clear_action = QAction("Clear All", self)
        clear_action.setToolTip("Clear All Nodes")
        clear_action.triggered.connect(self._clear_pipeline)
        toolbar.addAction(clear_action)

        return toolbar

    def _create_status_bar(self) -> QFrame:
        """Create the status bar."""
        status = QFrame()
        status.setStyleSheet("""
            QFrame {
                background-color: #007acc;
                padding: 2px 8px;
            }
            QLabel {
                color: white;
                font-size: 11px;
            }
        """)

        layout = QHBoxLayout(status)
        layout.setContentsMargins(8, 2, 8, 2)

        self._status_label = QLabel("Ready")
        layout.addWidget(self._status_label)

        layout.addStretch()

        self._node_count_label = QLabel("Nodes: 0")
        layout.addWidget(self._node_count_label)

        self._connection_count_label = QLabel("Connections: 0")
        layout.addWidget(self._connection_count_label)

        return status

    def _setup_default_nodes(self):
        """Set up the default node definitions."""
        definitions = create_default_node_definitions()

        # Register with palette
        self._palette.add_node_definitions(definitions)

        # Register with graph
        for definition in definitions:
            self._graph.register_node_definition(definition)

    def _connect_signals(self):
        """Connect internal signals."""
        # Graph signals
        self._graph.node_selected.connect(self._on_node_selected)
        self._graph.node_added.connect(self._on_graph_changed)
        self._graph.node_removed.connect(self._on_graph_changed)
        self._graph.connection_added.connect(self._on_graph_changed)
        self._graph.connection_removed.connect(self._on_graph_changed)
        self._graph.on_node_double_clicked = self._on_node_double_clicked

        # Parameter panel signals
        self._param_panel.parameters_changed.connect(self._on_parameters_changed)

        # Enable drop on graph
        self._graph.setAcceptDrops(True)
        self._graph.dragEnterEvent = self._graph_drag_enter
        self._graph.dropEvent = self._graph_drop

    def _on_node_selected(self, node: Node):
        """Handle node selection."""
        self._param_panel.set_node(node)

    def _on_node_double_clicked(self, node: Node):
        """Handle node double-click."""
        self._param_panel.set_node(node)

    def _on_graph_changed(self, _=None):
        """Handle graph changes."""
        self._is_modified = True
        self._update_status()
        self.pipeline_changed.emit()

    def _on_parameters_changed(self, node: Node):
        """Handle parameter changes."""
        self._is_modified = True

    def _update_status(self):
        """Update the status bar."""
        nodes = len(self._graph.get_nodes())
        connections = len(self._graph.get_connections())

        self._node_count_label.setText(f"Nodes: {nodes}")
        self._connection_count_label.setText(f"Connections: {connections}")

        if self._current_file:
            name = self._current_file.name
            if self._is_modified:
                name += " *"
            self._status_label.setText(name)
        else:
            if self._is_modified:
                self._status_label.setText("Untitled *")
            else:
                self._status_label.setText("Ready")

    def _graph_drag_enter(self, event):
        """Handle drag enter on graph."""
        if event.mimeData().hasFormat("application/x-magpy-node"):
            event.acceptProposedAction()

    def _graph_drop(self, event):
        """Handle drop on graph."""
        if event.mimeData().hasFormat("application/x-magpy-node"):
            node_type = bytes(event.mimeData().data("application/x-magpy-node")).decode()
            pos = self._graph.mapToScene(event.position().toPoint())
            self._graph.add_node(node_type, pos)
            event.acceptProposedAction()

    # =========================================================================
    # File Operations
    # =========================================================================

    def _new_pipeline(self):
        """Create a new pipeline."""
        if self._is_modified:
            result = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Save changes before creating a new pipeline?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
            )
            if result == QMessageBox.StandardButton.Save:
                if not self._save_pipeline():
                    return
            elif result == QMessageBox.StandardButton.Cancel:
                return

        self._graph.clear()
        self._param_panel.set_node(None)
        self._current_file = None
        self._is_modified = False
        self._update_status()

    def _open_pipeline(self):
        """Open a pipeline file."""
        if self._is_modified:
            result = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Save changes before opening another pipeline?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
            )
            if result == QMessageBox.StandardButton.Save:
                if not self._save_pipeline():
                    return
            elif result == QMessageBox.StandardButton.Cancel:
                return

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Pipeline",
            "",
            "Pipeline Files (*.json *.pipeline);;All Files (*.*)",
        )

        if filepath:
            self._load_pipeline_file(Path(filepath))

    def _load_pipeline_file(self, filepath: Path):
        """Load a pipeline from file."""
        try:
            with open(filepath) as f:
                data = json.load(f)

            self._graph.from_dict(data)
            self._current_file = filepath
            self._is_modified = False
            self._param_panel.set_node(None)
            self._update_status()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load pipeline: {e}",
            )

    def _save_pipeline(self) -> bool:
        """Save the current pipeline."""
        if self._current_file:
            return self._save_pipeline_to(self._current_file)
        else:
            return self._save_pipeline_as()

    def _save_pipeline_as(self) -> bool:
        """Save the pipeline with a new name."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Pipeline",
            "",
            "Pipeline Files (*.json);;All Files (*.*)",
        )

        if filepath:
            path = Path(filepath)
            if not path.suffix:
                path = path.with_suffix(".json")
            return self._save_pipeline_to(path)

        return False

    def _save_pipeline_to(self, filepath: Path) -> bool:
        """Save the pipeline to a specific file."""
        try:
            data = self._graph.to_dict()

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            self._current_file = filepath
            self._is_modified = False
            self._update_status()
            self.pipeline_saved.emit(str(filepath))

            return True

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save pipeline: {e}",
            )
            return False

    # =========================================================================
    # Pipeline Execution (placeholder)
    # =========================================================================

    def _run_pipeline(self):
        """Run the pipeline (placeholder for bioamla integration)."""
        nodes = self._graph.get_nodes()
        if not nodes:
            QMessageBox.information(
                self,
                "Empty Pipeline",
                "Add some nodes to the pipeline before running.",
            )
            return

        # Show info about future integration
        QMessageBox.information(
            self,
            "Pipeline Execution",
            f"Pipeline execution will be available when bioamla integration is complete.\n\n"
            f"This pipeline has {len(nodes)} nodes and "
            f"{len(self._graph.get_connections())} connections.",
        )

    def _stop_pipeline(self):
        """Stop the running pipeline."""
        # Placeholder for future implementation
        pass

    def _reset_view(self):
        """Reset the graph view."""
        self._graph.resetTransform()
        self._graph._zoom = 1.0
        self._graph.centerOn(0, 0)

    def _clear_pipeline(self):
        """Clear all nodes from the pipeline."""
        if not self._graph.get_nodes():
            return

        result = QMessageBox.question(
            self,
            "Clear Pipeline",
            "Are you sure you want to remove all nodes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if result == QMessageBox.StandardButton.Yes:
            self._graph.clear()
            self._param_panel.set_node(None)
            self._update_status()

    # =========================================================================
    # Screen Lifecycle
    # =========================================================================

    def on_activate(self):
        """Called when screen becomes active."""
        self._update_status()

    def on_deactivate(self):
        """Called when screen becomes inactive."""
        pass
