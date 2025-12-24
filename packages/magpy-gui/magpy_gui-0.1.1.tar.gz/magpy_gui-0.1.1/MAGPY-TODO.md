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

## Phase 3: Annotation & Detection

### 3.1 Annotation Interface - IN PROGRESS

- [x] Selection table panel with Label column
- [x] Raven selection table import/export (Import/Export buttons)
- [x] Keyboard shortcuts for rapid annotation (1-9 for labels)
- [x] Right-click context menu (Go to, Set Label, Copy, Delete)
- [x] Configure label hotkeys dialog
- [x] Label autocomplete support
- [x] Click-drag selection box drawing on spectrogram (Shift+drag with visual feedback)
- [ ] Undo/redo for annotation operations
- [ ] Export to CSV, Parquet, JSON (use bioamla AnnotationController)

### 3.2 Detection Interface
- [ ] Model selection dialog (AST, BirdNET, custom)
- [ ] Detection progress with cancel support (QThread worker)
- [ ] Detection overlay on spectrogram (colored boxes)
- [ ] Results table with sorting, filtering, confidence threshold
- [ ] Detection → annotation conversion
- [ ] Batch detection dialog

---

## Phase 4: Visual Pipeline Editor

**Blocked by:** Bioamla workflow engine completion

- [ ] Node palette (drag bioamla commands onto canvas)
- [ ] Visual connection of step outputs to inputs
- [ ] Parameter editing panel per node
- [ ] TOML import/export
- [ ] Run workflow with progress visualization

---

## Phase 5: LLM Assistant Screen

**Blocked by:** Bioamla LLM integration completion

- [ ] Chat interface for natural language input
- [ ] Generated command preview with syntax highlighting
- [ ] One-click execution with confirmation
- [ ] Command history and regeneration
- [ ] Inline documentation lookup

---

## Phase 6: Advanced Features

**Blocked by:** All prior phases complete

### 6.1 Training Wizard
- [ ] Dataset selection and splitting
- [ ] Hyperparameter configuration
- [ ] Training progress visualization
- [ ] TensorBoard/MLflow integration
- [ ] Model export and HuggingFace push

### 6.2 Embedding Visualization
- [ ] UMAP/t-SNE projection display
- [ ] Color by cluster, species, or custom label
- [ ] Click to play associated audio
- [ ] Selection for batch operations

### 6.3 Services Browser
- [ ] iNaturalist observation search and download
- [ ] Xeno-canto recording search
- [ ] eBird checklist integration
- [ ] Download queue manager

---

## Bug Fixes / Technical Debt

- [x] Fix relative imports (`...core` → `..core` in widgets)
- [x] Fix thread-safety in playback controls (Qt timer warning)
- [x] Export `SelectionBounds` from `core/__init__.py`
