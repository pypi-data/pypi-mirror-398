# MagPy Development TODO

## Current Focus: Phase 3 - Annotation & Detection

### Phase 2: Core Viewer - COMPLETE

#### Application Shell - DONE
- [x] `magpy/__main__.py` - Entry point
- [x] `magpy/app.py` - QApplication setup
- [x] `magpy/main_window.py` - Main window with menus, toolbar, statusbar

#### Core Widgets - DONE
- [x] `widgets/waveform.py` - Waveform display with zoom/pan
- [x] `widgets/spectrogram.py` - Spectrogram display with colormaps
- [x] `widgets/playback.py` - Transport controls (play, pause, stop, loop)
- [x] `widgets/selection_table.py` - Selection table widget

#### Core Processing - DONE
- [x] `core/audio.py` - Audio file loading
- [x] `core/spectrogram.py` - Spectrogram computation
- [x] `core/selection.py` - Selection model and table
- [x] `core/measurements.py` - Measurement calculator

#### Remaining Phase 2 Tasks - DONE

- [x] Synchronized playhead across waveform and spectrogram views
- [x] Selection tool for time-frequency regions (spectrogram box selection)
- [x] Properties panel (`widgets/properties_panel.py`)
- [x] `controllers/audio_controller.py` - Bridge to bioamla core

#### Terminal Screen - DONE

- [x] `screens/terminal.py` - Embedded bioamla CLI interface

#### Bioamla Integration - DONE

- [x] AnnotationController in bioamla (Raven import/export, CRUD, measurements)
- [x] MagPy audio_controller updated with annotation methods

---

## Phase 3: Annotation & Multi-View Architecture

### 3.1 Annotation Interface - COMPLETE

- [x] Selection table panel with Label column
- [x] Raven selection table import/export (Import/Export buttons)
- [x] Keyboard shortcuts for rapid annotation (1-9 for labels)
- [x] Right-click context menu (Go to, Set Label, Copy, Delete)
- [x] Configure label hotkeys dialog
- [x] Label autocomplete support
- [x] Click-drag selection box drawing on spectrogram (Shift+drag with visual feedback)
- [x] Undo/redo for annotation operations
- [x] Export to CSV, Parquet, JSON (use bioamla AnnotationController)

### 3.2 Navigation Sidebar & Multi-View Architecture - COMPLETE

#### 3.2.1 Navigation Sidebar

- [x] Create `widgets/navigation_bar.py` - Vertical icon bar (left side, VS Code activity bar style)
- [x] Icon buttons for each main view (exclusive selection)
- [x] Tooltip labels on hover
- [x] Visual indicator for active view
- [ ] Collapsible/expandable sidebar (future enhancement)

#### 3.2.2 View Management

- [x] Create `screens/base.py` - Base screen class for stateful views
- [x] View state preservation when switching (each view maintains its state)
- [x] View switching via QStackedWidget
- [x] Audio docks hide when switching to other views (proper view isolation)
- [ ] View-specific menu/toolbar updates (future enhancement)

#### 3.2.3 Main Views

**Audio View** (current main_window content)
- [x] Audio content integrated in main_window with nav bar
- [x] Icon: musical note (🎵)

**Pipeline/Workflow View** - UI COMPLETE (awaiting bioamla integration)
- [x] Create `screens/pipeline_screen.py`
- [x] Node-based visual editor with drag-and-drop
- [x] Visual connection of step outputs to inputs (bezier wires)
- [x] Parameter editing panel per node
- [x] Node palette with categorized nodes (Input, Audio, Analysis, Detection, Output, Utility)
- [x] Save/load pipeline as JSON
- [ ] TOML import/export (pending bioamla pipeline API)
- [ ] Run workflow with progress visualization (pending bioamla integration)

**Model Training View** (placeholder created)
- [x] Create `screens/training_screen.py`
- [ ] Dataset selection and splitting UI
- [ ] Hyperparameter configuration panel
- [ ] Training progress visualization (loss curves, metrics)
- [ ] TensorBoard/MLflow integration
- [ ] Model export and HuggingFace push

**Batch Analysis View** (placeholder created)
- [x] Create `screens/batch_screen.py`
- [ ] File/folder selection for batch processing
- [ ] Task queue with progress tracking
- [ ] Results aggregation and export
- [ ] Parallel processing configuration

### 3.3 Detection Interface - COMPLETE

- [x] Model selection dialog (AST, BirdNET, custom) - `widgets/detection_dialog.py`
- [x] Detection progress with cancel support (QThread worker) - `workers/detection_worker.py`
- [x] Detection overlay on spectrogram (colored boxes) - `widgets/spectrogram.py`
- [x] Results table with sorting, filtering, confidence threshold - `widgets/detection_results.py`
- [x] Detection → annotation conversion - integrated in `main_window.py`
- [x] Batch detection dialog - `widgets/detection_dialog.py`

#### Detection Worker Implementation - DONE

- [x] `DetectionWorker` - QThread for batch file processing with progress signals
- [x] `SingleFileDetectionWorker` - QThread for in-memory audio detection
- [x] `DetectionConfig` - Configuration dataclass for all detector types
- [x] `DetectionResult` / `BatchDetectionResult` - Result data structures
- [x] `DetectorType` enum - Support for AST, BirdNET, OpenSoundscape, Energy, RIBBIT, CWT, Accelerating
- [x] Integration with bioamla ML models (`bioamla.core.ml`)
- [x] Integration with bioamla signal detectors (`bioamla.core.detection`)

#### Detection UI Implementation - DONE

- [x] `ModelSelectionDialog` - Configure detector type and parameters
- [x] `DetectionProgressDialog` - Progress tracking with cancel
- [x] `BatchDetectionDialog` - Multi-file detection with file selection
- [x] `DetectionResultsWidget` - Table with filtering, sorting, label colors
- [x] Spectrogram detection overlay with color-coded boxes
- [x] Detection → annotation conversion with undo support
- [x] Analysis menu with Run Detection (Ctrl+D) and Batch Detection
- [x] Detections dock widget (tabbed with Selections and Terminal)

---

## Phase 4: Advanced Features

### 4.1 Embedding Visualization
- [ ] UMAP/t-SNE projection display
- [ ] Color by cluster, species, or custom label
- [ ] Click to play associated audio
- [ ] Selection for batch operations

### 4.2 Services Browser
- [ ] iNaturalist observation search and download
- [ ] Xeno-canto recording search
- [ ] eBird checklist integration
- [ ] Download queue manager

---

## Bug Fixes / Technical Debt

- [x] Fix relative imports (`...core` → `..core` in widgets)
- [x] Fix thread-safety in playback controls (Qt timer warning)
- [x] Export `SelectionBounds` from `core/__init__.py`
