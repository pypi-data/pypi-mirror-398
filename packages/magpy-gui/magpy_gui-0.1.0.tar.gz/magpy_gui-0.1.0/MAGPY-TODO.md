# MagPy Development TODO

## Current Focus: Phase 2 - Core Viewer Completion

### Critical Path (Complete Before Next Phase)

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

#### Remaining Phase 2 Tasks
- [ ] Synchronized playhead across waveform and spectrogram views
- [ ] Selection tool for time-frequency regions (spectrogram box selection)
- [ ] Properties panel (duration, sample rate, channels, bit depth)
- [ ] `controllers/audio_controller.py` - Bridge to bioamla core (when available)

#### Terminal Screen (Deferred)
- [ ] QPlainTextEdit-based terminal emulator
- [ ] Command history (up/down arrows)
- [ ] Auto-completion for bioamla commands
- [ ] Real-time output streaming

---

## Phase 3: Annotation & Detection

**Blocked by:** Bioamla Phase 0 + Phase 1 completion

### 3.1 Annotation Interface
- [ ] Click-drag selection box drawing on spectrogram
- [ ] Selection table panel (time start, end, freq low, high, label)
- [ ] Raven selection table import/export
- [ ] Keyboard shortcuts for rapid annotation (1-9 for labels)
- [ ] Undo/redo for annotation operations
- [ ] Export to CSV, Parquet, JSON

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
