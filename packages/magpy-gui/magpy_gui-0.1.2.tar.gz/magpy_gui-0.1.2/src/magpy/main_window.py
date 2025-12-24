"""
Main application window for MagPy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QSettings, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QIcon
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QFileDialog,
    QMessageBox,
    QStatusBar,
    QLabel,
    QMenuBar,
    QMenu,
    QToolBar,
    QDockWidget,
    QApplication,
)

from magpy.core import AudioFile, SelectionTable, SpectrogramGenerator, SpectrogramConfig
from magpy.controllers import AudioController
from magpy.widgets import (
    WaveformWidget,
    SpectrogramWidget,
    SelectionTableWidget,
    PlaybackControls,
    PropertiesPanel,
    NavigationBar,
    ViewType,
)
from magpy.screens import (
    TerminalScreen,
    PipelineScreen,
    TrainingScreen,
    BatchScreen,
)


class MainWindow(QMainWindow):
    """
    Main application window for MagPy bioacoustics analysis.

    Features:
    - Waveform and spectrogram visualization
    - Selection and annotation tools
    - Playback controls
    - Measurement display
    - Multi-view navigation (Audio, Pipeline, Training, Batch)
    """

    # Signals
    file_loaded = pyqtSignal(str)
    selection_changed = pyqtSignal(object)
    playback_position_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()

        self._audio: Optional[AudioFile] = None
        self._selection_table = SelectionTable()
        self._current_channel = 0
        self._spectrogram_generator = SpectrogramGenerator()
        self._audio_controller = AudioController()
        self._current_view = ViewType.AUDIO

        # Store dock widgets for view switching
        self._audio_docks: list[QDockWidget] = []

        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._setup_connections()
        self._load_settings()

    def _setup_ui(self):
        """Set up the main UI layout."""
        self.setWindowTitle("MagPy")
        self.setMinimumSize(1200, 800)

        # Apply modern dark theme
        self._apply_style()

        # Central widget with horizontal layout: navbar | content
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Navigation bar on the left
        self._nav_bar = NavigationBar()
        self._nav_bar.view_changed.connect(self._on_view_changed)
        main_layout.addWidget(self._nav_bar)

        # Stacked widget for different views
        self._view_stack = QStackedWidget()
        main_layout.addWidget(self._view_stack, stretch=1)

        # Create all views
        self._create_audio_view()
        self._create_other_views()

        # Create dock widgets for audio view
        self._create_audio_docks()

    def _create_audio_view(self):
        """Create the audio analysis view."""
        audio_view = QWidget()
        layout = QVBoxLayout(audio_view)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Waveform view
        self._waveform = WaveformWidget()
        layout.addWidget(self._waveform, stretch=1)

        # Spectrogram view
        self._spectrogram = SpectrogramWidget()
        layout.addWidget(self._spectrogram, stretch=2)

        # Playback controls
        self._playback = PlaybackControls()
        layout.addWidget(self._playback)

        self._audio_view = audio_view
        self._view_stack.addWidget(audio_view)

    def _create_other_views(self):
        """Create placeholder views for other screens."""
        # Pipeline view
        self._pipeline_screen = PipelineScreen()
        self._view_stack.addWidget(self._pipeline_screen)

        # Training view
        self._training_screen = TrainingScreen()
        self._view_stack.addWidget(self._training_screen)

        # Batch view
        self._batch_screen = BatchScreen()
        self._view_stack.addWidget(self._batch_screen)

        # Map view types to widgets
        self._view_widgets = {
            ViewType.AUDIO: self._audio_view,
            ViewType.PIPELINE: self._pipeline_screen,
            ViewType.TRAINING: self._training_screen,
            ViewType.BATCH: self._batch_screen,
        }

    def _create_audio_docks(self):
        """Create dock widgets for the audio view."""
        # Selection table dock
        self._selection_table_widget = SelectionTableWidget()
        selection_dock = QDockWidget("Selections", self)
        selection_dock.setObjectName("SelectionsDock")
        selection_dock.setWidget(self._selection_table_widget)
        selection_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, selection_dock)
        self._audio_docks.append(selection_dock)

        # Properties panel dock
        self._properties_panel = PropertiesPanel()
        properties_dock = QDockWidget("Properties", self)
        properties_dock.setObjectName("PropertiesDock")
        properties_dock.setWidget(self._properties_panel)
        properties_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, properties_dock)
        self._audio_docks.append(properties_dock)

        # Terminal dock
        self._terminal = TerminalScreen()
        terminal_dock = QDockWidget("Terminal", self)
        terminal_dock.setObjectName("TerminalDock")
        terminal_dock.setWidget(self._terminal)
        terminal_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, terminal_dock)
        self._audio_docks.append(terminal_dock)

        # Tabify terminal with selections dock
        self.tabifyDockWidget(selection_dock, terminal_dock)
        selection_dock.raise_()  # Show selections by default

    def _on_view_changed(self, view_type: ViewType):
        """Handle navigation bar view change."""
        self._current_view = view_type

        # Switch the stacked widget
        widget = self._view_widgets.get(view_type)
        if widget:
            self._view_stack.setCurrentWidget(widget)

        # Show/hide audio docks based on view
        is_audio_view = (view_type == ViewType.AUDIO)
        for dock in self._audio_docks:
            dock.setVisible(is_audio_view)

        # Update window title
        view_names = {
            ViewType.AUDIO: "Audio",
            ViewType.PIPELINE: "Pipeline",
            ViewType.TRAINING: "Training",
            ViewType.BATCH: "Batch",
        }
        self.setWindowTitle(f"MagPy - {view_names.get(view_type, 'Audio')}")

    def _apply_style(self):
        """Apply modern dark theme styling."""
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
                font-size: 13px;
            }
            QMenuBar {
                background-color: #252526;
                border-bottom: 1px solid #3c3c3c;
                padding: 4px;
            }
            QMenuBar::item {
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #094771;
            }
            QMenu {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 32px 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3c3c3c;
                margin: 4px 8px;
            }
            QToolBar {
                background-color: #252526;
                border: none;
                spacing: 4px;
                padding: 4px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 6px;
            }
            QToolButton:hover {
                background-color: #3c3c3c;
                border-color: #4c4c4c;
            }
            QToolButton:pressed {
                background-color: #094771;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
            }
            QDockWidget {
                titlebar-close-icon: url(close.png);
                titlebar-normal-icon: url(float.png);
            }
            QDockWidget::title {
                background-color: #252526;
                padding: 8px;
                border-bottom: 1px solid #3c3c3c;
            }
            QSplitter::handle {
                background-color: #3c3c3c;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #5a5a5a;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #787878;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar:horizontal {
                background-color: #1e1e1e;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #5a5a5a;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #787878;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #3c3c3c;
                border: none;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
            QTableWidget::item:selected {
                background-color: #094771;
            }
            QHeaderView::section {
                background-color: #252526;
                padding: 8px;
                border: none;
                border-right: 1px solid #3c3c3c;
                border-bottom: 1px solid #3c3c3c;
            }
            QPushButton {
                background-color: #0e639c;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #094771;
            }
            QPushButton:disabled {
                background-color: #3c3c3c;
                color: #808080;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background-color: #3c3c3c;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background-color: #0e639c;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background-color: #1177bb;
            }
            QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QComboBox:hover {
                border-color: #0e639c;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background-color: #3c3c3c;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                padding: 6px 8px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #0e639c;
            }
            """
        )

    def _setup_menus(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        self._recent_menu = file_menu.addMenu("Recent Files")
        self._update_recent_files_menu()

        file_menu.addSeparator()

        save_selection_action = QAction("Save Selections...", self)
        save_selection_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_selection_action.triggered.connect(self._save_selections)
        file_menu.addAction(save_selection_action)

        load_selection_action = QAction("Load Selections...", self)
        load_selection_action.triggered.connect(self._load_selections)
        file_menu.addAction(load_selection_action)

        file_menu.addSeparator()

        export_clip_action = QAction("Export Selection Clips...", self)
        export_clip_action.triggered.connect(self._export_clips)
        file_menu.addAction(export_clip_action)

        export_image_action = QAction("Export Image...", self)
        export_image_action.triggered.connect(self._export_image)
        file_menu.addAction(export_image_action)

        file_menu.addSeparator()

        # Export annotations submenu
        export_menu = file_menu.addMenu("Export Annotations")

        export_csv_action = QAction("Export as CSV...", self)
        export_csv_action.triggered.connect(self._export_annotations_csv)
        export_menu.addAction(export_csv_action)

        export_parquet_action = QAction("Export as Parquet...", self)
        export_parquet_action.triggered.connect(self._export_annotations_parquet)
        export_menu.addAction(export_parquet_action)

        export_json_action = QAction("Export as JSON...", self)
        export_json_action.triggered.connect(self._export_annotations_json)
        export_menu.addAction(export_json_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        self._undo_action = QAction("&Undo", self)
        self._undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self._undo_action.setEnabled(False)
        self._undo_action.triggered.connect(self._undo)
        edit_menu.addAction(self._undo_action)

        self._redo_action = QAction("&Redo", self)
        self._redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self._redo_action.setEnabled(False)
        self._redo_action.triggered.connect(self._redo)
        edit_menu.addAction(self._redo_action)

        edit_menu.addSeparator()

        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        edit_menu.addAction(select_all_action)

        delete_selection_action = QAction("&Delete Selection", self)
        delete_selection_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_selection_action.triggered.connect(self._delete_selection)
        edit_menu.addAction(delete_selection_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self._zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self._zoom_out)
        view_menu.addAction(zoom_out_action)

        zoom_fit_action = QAction("Zoom to &Fit", self)
        zoom_fit_action.setShortcut(QKeySequence("Ctrl+0"))
        zoom_fit_action.triggered.connect(self._zoom_fit)
        view_menu.addAction(zoom_fit_action)

        view_menu.addSeparator()

        show_waveform_action = QAction("Show &Waveform", self)
        show_waveform_action.setCheckable(True)
        show_waveform_action.setChecked(True)
        show_waveform_action.triggered.connect(self._toggle_waveform)
        view_menu.addAction(show_waveform_action)

        show_spectrogram_action = QAction("Show &Spectrogram", self)
        show_spectrogram_action.setCheckable(True)
        show_spectrogram_action.setChecked(True)
        show_spectrogram_action.triggered.connect(self._toggle_spectrogram)
        view_menu.addAction(show_spectrogram_action)

        # Analysis menu
        analysis_menu = menubar.addMenu("&Analysis")

        measure_action = QAction("&Measure Selection", self)
        measure_action.setShortcut(QKeySequence("Ctrl+M"))
        measure_action.triggered.connect(self._measure_selection)
        analysis_menu.addAction(measure_action)

        analysis_menu.addSeparator()

        spectrogram_settings_action = QAction("Spectrogram &Settings...", self)
        spectrogram_settings_action.triggered.connect(self._spectrogram_settings)
        analysis_menu.addAction(spectrogram_settings_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About MagPy", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        """Set up the main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # File operations
        open_btn = QAction("Open", self)
        open_btn.setToolTip("Open audio file (Ctrl+O)")
        open_btn.triggered.connect(self._open_file)
        toolbar.addAction(open_btn)

        toolbar.addSeparator()

        # Selection tools
        select_btn = QAction("Select", self)
        select_btn.setToolTip("Selection tool")
        select_btn.setCheckable(True)
        select_btn.setChecked(True)
        toolbar.addAction(select_btn)

        zoom_btn = QAction("Zoom", self)
        zoom_btn.setToolTip("Zoom tool")
        zoom_btn.setCheckable(True)
        toolbar.addAction(zoom_btn)

        toolbar.addSeparator()

        # Zoom controls
        zoom_in_btn = QAction("+", self)
        zoom_in_btn.setToolTip("Zoom in")
        zoom_in_btn.triggered.connect(self._zoom_in)
        toolbar.addAction(zoom_in_btn)

        zoom_out_btn = QAction("-", self)
        zoom_out_btn.setToolTip("Zoom out")
        zoom_out_btn.triggered.connect(self._zoom_out)
        toolbar.addAction(zoom_out_btn)

        zoom_fit_btn = QAction("Fit", self)
        zoom_fit_btn.setToolTip("Zoom to fit")
        zoom_fit_btn.triggered.connect(self._zoom_fit)
        toolbar.addAction(zoom_fit_btn)

    def _setup_statusbar(self):
        """Set up the status bar."""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)

        self._file_label = QLabel("No file loaded")
        self._statusbar.addWidget(self._file_label)

        self._position_label = QLabel("")
        self._statusbar.addPermanentWidget(self._position_label)

        self._selection_label = QLabel("")
        self._statusbar.addPermanentWidget(self._selection_label)

    def _setup_connections(self):
        """Set up signal/slot connections."""
        # Connect waveform and spectrogram for synchronized navigation
        self._waveform.view_range_changed.connect(self._spectrogram.set_view_range)
        self._spectrogram.view_range_changed.connect(self._waveform.set_view_range)

        # Selection synchronization
        self._waveform.selection_created.connect(self._on_selection_created)
        self._spectrogram.selection_created.connect(self._on_selection_created)

        # Playback connections
        self._playback.play_clicked.connect(self._on_play)
        self._playback.pause_clicked.connect(self._on_pause)
        self._playback.stop_clicked.connect(self._on_stop)
        self._playback.position_changed.connect(self._on_playback_position_changed)

        # Seek connections (Ctrl+Click to seek)
        self._waveform.seek_requested.connect(self._on_seek_requested)
        self._spectrogram.seek_requested.connect(self._on_seek_requested)

        # Selection table connections
        self._selection_table_widget.selection_selected.connect(
            self._on_table_selection_selected
        )
        self._selection_table_widget.selection_deleted.connect(
            self._on_table_selection_deleted
        )
        self._selection_table_widget.undo_state_changed.connect(
            self._on_undo_state_changed
        )

    def _load_settings(self):
        """Load application settings."""
        settings = QSettings("MagPy", "MagPy")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)

    def _save_settings(self):
        """Save application settings."""
        settings = QSettings("MagPy", "MagPy")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    def closeEvent(self, event):
        """Handle window close event."""
        self._save_settings()
        event.accept()

    # File operations

    def _open_file(self):
        """Open an audio file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Audio File",
            "",
            "Audio Files (*.wav *.aiff *.flac *.mp3);;All Files (*)",
        )
        if filepath:
            self.load_file(filepath)

    def load_file(self, filepath: str):
        """Load an audio file."""
        try:
            self._audio = AudioFile(filepath)
            self._update_views()
            self._update_recent_files(filepath)
            self._file_label.setText(f"{Path(filepath).name}")
            self._properties_panel.set_audio(self._audio)
            self._properties_panel.set_selection(None)
            self.file_loaded.emit(filepath)
            self.statusBar().showMessage(f"Loaded: {filepath}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")

    def _update_views(self):
        """Update all views with current audio data."""
        if self._audio is None:
            return

        # Update waveform
        self._waveform.set_audio(
            self._audio.data[:, self._current_channel],
            self._audio.sample_rate,
        )

        # Compute and update spectrogram
        result = self._spectrogram_generator.compute(
            self._audio.data,
            self._audio.sample_rate,
            channel=self._current_channel,
        )
        self._spectrogram.set_spectrogram(result)

        # Update playback controls
        self._playback.set_duration(self._audio.duration)
        self._playback.set_audio(self._audio)

    def _update_recent_files(self, filepath: str):
        """Update recent files list."""
        settings = QSettings("MagPy", "MagPy")
        recent = settings.value("recentFiles", []) or []

        if filepath in recent:
            recent.remove(filepath)
        recent.insert(0, filepath)
        recent = recent[:10]  # Keep last 10

        settings.setValue("recentFiles", recent)
        self._update_recent_files_menu()

    def _update_recent_files_menu(self):
        """Update the recent files menu."""
        self._recent_menu.clear()
        settings = QSettings("MagPy", "MagPy")
        recent = settings.value("recentFiles", []) or []

        for filepath in recent:
            action = QAction(Path(filepath).name, self)
            action.setData(filepath)
            action.triggered.connect(lambda checked, f=filepath: self.load_file(f))
            self._recent_menu.addAction(action)

        if not recent:
            action = QAction("No recent files", self)
            action.setEnabled(False)
            self._recent_menu.addAction(action)

    def _save_selections(self):
        """Save selections to file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Selections",
            "",
            "Tab-delimited (*.txt);;CSV (*.csv)",
        )
        if filepath:
            fmt = "csv" if filepath.endswith(".csv") else "tsv"
            self._selection_table.save(filepath, format=fmt)
            self.statusBar().showMessage(f"Saved selections to: {filepath}", 3000)

    def _load_selections(self):
        """Load selections from file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Selections",
            "",
            "Selection Tables (*.txt *.csv);;All Files (*)",
        )
        if filepath:
            self._selection_table = SelectionTable.load(filepath)
            self._selection_table_widget.set_selection_table(self._selection_table)
            self._update_selection_overlays()
            self.statusBar().showMessage(f"Loaded selections from: {filepath}", 3000)

    def _export_clips(self):
        """Export selection clips."""
        if self._audio is None:
            QMessageBox.warning(self, "Warning", "No audio file loaded")
            return
        if len(self._selection_table) == 0:
            QMessageBox.warning(self, "Warning", "No selections to export")
            return

        output_dir = QFileDialog.getExistingDirectory(
            self, "Select Output Directory"
        )
        if output_dir:
            exported = self._selection_table.export_clips(
                self._audio.filepath, output_dir, padding=0.1
            )
            self.statusBar().showMessage(f"Exported {len(exported)} clips", 3000)

    def _export_image(self):
        """Export spectrogram image."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Image",
            "",
            "PNG (*.png);;JPEG (*.jpg);;TIFF (*.tiff)",
        )
        if filepath:
            self._spectrogram.export_image(filepath)
            self.statusBar().showMessage(f"Exported image to: {filepath}", 3000)

    def _selections_to_annotation_dicts(self):
        """Convert current selections to annotation dicts for bioamla export."""
        annotations = []
        for selection in self._selection_table:
            ann = {
                "start_time": selection.begin_time,
                "end_time": selection.end_time,
                "low_freq": selection.low_freq,
                "high_freq": selection.high_freq,
                "label": selection.annotations.get("Label", ""),
                "channel": selection.channel,
            }
            # Include other annotations as custom fields
            for key, value in selection.annotations.items():
                if key != "Label":
                    ann[key] = value
            annotations.append(ann)
        return annotations

    def _export_annotations_csv(self):
        """Export annotations to CSV using bioamla."""
        if len(self._selection_table) == 0:
            QMessageBox.warning(self, "No Selections", "There are no selections to export.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Annotations as CSV",
            "annotations.csv",
            "CSV Files (*.csv)",
        )

        if not filepath:
            return

        annotations = self._selections_to_annotation_dicts()
        success, message = self._audio_controller.export_csv_annotations(annotations, filepath)

        if success:
            self.statusBar().showMessage(message, 3000)
        else:
            QMessageBox.critical(self, "Export Error", message)

    def _export_annotations_parquet(self):
        """Export annotations to Parquet using bioamla."""
        if len(self._selection_table) == 0:
            QMessageBox.warning(self, "No Selections", "There are no selections to export.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Annotations as Parquet",
            "annotations.parquet",
            "Parquet Files (*.parquet)",
        )

        if not filepath:
            return

        annotations = self._selections_to_annotation_dicts()
        success, message = self._audio_controller.export_parquet_annotations(annotations, filepath)

        if success:
            self.statusBar().showMessage(message, 3000)
        else:
            QMessageBox.critical(self, "Export Error", message)

    def _export_annotations_json(self):
        """Export annotations to JSON using bioamla."""
        if len(self._selection_table) == 0:
            QMessageBox.warning(self, "No Selections", "There are no selections to export.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Annotations as JSON",
            "annotations.json",
            "JSON Files (*.json)",
        )

        if not filepath:
            return

        annotations = self._selections_to_annotation_dicts()
        success, message = self._audio_controller.export_json_annotations(annotations, filepath)

        if success:
            self.statusBar().showMessage(message, 3000)
        else:
            QMessageBox.critical(self, "Export Error", message)

    # View operations

    def _zoom_in(self):
        """Zoom in on views."""
        self._waveform.zoom_in()
        self._spectrogram.zoom_in()

    def _zoom_out(self):
        """Zoom out on views."""
        self._waveform.zoom_out()
        self._spectrogram.zoom_out()

    def _zoom_fit(self):
        """Fit view to show all data."""
        self._waveform.zoom_fit()
        self._spectrogram.zoom_fit()

    def _toggle_waveform(self, visible: bool):
        """Toggle waveform visibility."""
        self._waveform.setVisible(visible)

    def _toggle_spectrogram(self, visible: bool):
        """Toggle spectrogram visibility."""
        self._spectrogram.setVisible(visible)

    # Selection operations

    def _on_selection_created(self, start_time: float, end_time: float,
                              low_freq: Optional[float] = None,
                              high_freq: Optional[float] = None):
        """Handle new selection creation."""
        from .core import Selection

        selection = Selection(
            begin_time=start_time,
            end_time=end_time,
            low_freq=low_freq,
            high_freq=high_freq,
            channel=self._current_channel + 1,
        )
        # Use undo-aware method to add selection
        self._selection_table_widget.add_selection_with_undo(selection)
        self._update_selection_overlays()
        self._properties_panel.set_selection(selection)
        self.selection_changed.emit(selection)

    def _delete_selection(self):
        """Delete the currently selected selection."""
        current_id = self._selection_table_widget.get_selected_id()
        if current_id:
            self._selection_table.remove_by_id(current_id)
            self._selection_table_widget.set_selection_table(self._selection_table)
            self._update_selection_overlays()

    def _on_table_selection_selected(self, selection_id: str):
        """Handle selection from table."""
        selection = self._selection_table.get_by_id(selection_id)
        if selection:
            # Zoom to selection
            self._waveform.set_view_range(selection.begin_time, selection.end_time)
            self._spectrogram.set_view_range(selection.begin_time, selection.end_time)
            # Update properties panel
            self._properties_panel.set_selection(selection)

    def _on_table_selection_deleted(self, selection_id: str):
        """Handle deletion from table."""
        self._selection_table.remove_by_id(selection_id)
        self._update_selection_overlays()
        self._properties_panel.set_selection(None)

    def _update_selection_overlays(self):
        """Update selection overlays on views."""
        self._waveform.set_selections(list(self._selection_table))
        self._spectrogram.set_selections(list(self._selection_table))

    # Playback operations

    def _on_play(self):
        """Handle play button."""
        if self._audio:
            self._playback.play()
            self._waveform.set_playing(True)
            self._spectrogram.set_playing(True)

    def _on_pause(self):
        """Handle pause button."""
        self._playback.pause()
        self._waveform.set_playing(False)
        self._spectrogram.set_playing(False)

    def _on_stop(self):
        """Handle stop button."""
        self._playback.stop()
        self._waveform.set_playing(False)
        self._spectrogram.set_playing(False)

    def _on_seek_requested(self, position: float):
        """Handle seek request from waveform/spectrogram (Ctrl+Click)."""
        if self._audio is None:
            return
        # Clamp position to valid range
        position = max(0, min(position, self._audio.duration))
        self._playback.seek_to(position)
        self._waveform.set_playback_position(position)
        self._spectrogram.set_playback_position(position)
        self._position_label.setText(f"{position:.3f}s")

    def _on_playback_position_changed(self, position: float):
        """Handle playback position update."""
        self._waveform.set_playback_position(position)
        self._spectrogram.set_playback_position(position)
        self._position_label.setText(f"{position:.3f}s")
        self.playback_position_changed.emit(position)

    # Analysis operations

    def _measure_selection(self):
        """Measure the current selection."""
        if self._audio is None:
            return

        current_id = self._selection_table_widget.get_selected_id()
        if not current_id:
            self.statusBar().showMessage("No selection to measure", 3000)
            return

        selection = self._selection_table.get_by_id(current_id)
        if selection:
            from .core import MeasurementCalculator, SelectionBounds

            calc = MeasurementCalculator()
            bounds = SelectionBounds(
                start_time=selection.begin_time,
                end_time=selection.end_time,
                low_freq=selection.low_freq,
                high_freq=selection.high_freq,
            )
            result = calc.compute_all(
                self._audio.data,
                self._audio.sample_rate,
                bounds,
                channel=self._current_channel,
            )
            selection.measurements = result.to_dict()
            self._selection_table_widget.set_selection_table(self._selection_table)
            self.statusBar().showMessage("Measurements computed", 3000)

    def _spectrogram_settings(self):
        """Show spectrogram settings dialog."""
        # TODO: Implement settings dialog
        pass

    # Undo/Redo operations

    def _undo(self):
        """Undo the last annotation operation."""
        self._selection_table_widget.undo()
        self._update_selection_overlays()

    def _redo(self):
        """Redo the last undone annotation operation."""
        self._selection_table_widget.redo()
        self._update_selection_overlays()

    def _on_undo_state_changed(self, can_undo: bool, can_redo: bool):
        """Update undo/redo action enabled states."""
        self._undo_action.setEnabled(can_undo)
        self._redo_action.setEnabled(can_redo)

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About MagPy",
            """<h2>MagPy</h2>
            <p>A modern Python bioacoustics analysis application.</p>
            <p>Version 0.1.0</p>
            """,
        )
