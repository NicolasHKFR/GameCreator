# Build Plan: AI Game Asset Factory

## Technology Stack

| Component | Technology | Source |
|-----------|------------|--------|
| Language | Python 3.11 | TDD |
| UI Framework | PySide6 (Qt) | TDD + Confirmed |
| AI Framework | PyTorch 2.x + CUDA 12.x | TDD |
| Image Gen | Diffusers + SD 1.5 | TDD + Confirmed |
| Background Removal | Rembg (ISNet) | TDD |
| Classification | CLIP | TDD |
| Computer Vision | OpenCV, NumPy, Pillow, Scikit-Image | TDD |
| Database | SQLite + SQLAlchemy | TDD |
| Metadata | JSON | TDD |
| Animation | TBD (AnimateDiff / pose-based) | TDD + ADR-PENDING-001 |

## Project Structure

```
D:\allai\GameCreator\
├── app/
│   ├── __init__.py
│   ├── main.py                    # Application entry point
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py         # Main window shell + navigation
│   │   ├── dashboard_screen.py    # Project list / create / open / delete
│   │   ├── style_editor_screen.py # Style profile editor
│   │   ├── generation_screen.py   # Asset generation form + preview
│   │   ├── review_screen.py       # Asset review + actions
│   │   ├── animation_screen.py    # Animation gen (feature-flagged)
│   │   └── export_screen.py       # Export dialog
│   ├── services/
│   │   ├── __init__.py
│   │   ├── project_service.py     # Project CRUD
│   │   ├── style_service.py       # Style profile management
│   │   ├── generation_service.py  # SD image generation
│   │   ├── background_service.py  # Rembg integration
│   │   ├── extraction_service.py  # Sprite extraction
│   │   ├── classification_service.py  # CLIP classification
│   │   ├── texture_service.py     # Seamless tiling
│   │   ├── animation_service.py   # Animation generation
│   │   ├── metadata_service.py    # Metadata create/validate
│   │   └── export_service.py      # Export packaging
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── workflow_engine.py     # Pipeline orchestrator
│   │   ├── job_queue.py           # FIFO single-worker queue
│   │   └── progress_tracker.py    # Progress reporting
│   ├── models/
│   │   ├── __init__.py
│   │   ├── model_manager.py       # Download, load, unload, VRAM monitor
│   │   └── model_registry.py      # Model config + validation
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLite + SQLAlchemy setup
│   │   ├── project_repo.py        # Project DB access
│   │   ├── style_repo.py          # Style profile DB access
│   │   └── asset_repo.py          # Asset + animation DB access
│   ├── exporters/
│   │   ├── __init__.py
│   │   ├── png_exporter.py
│   │   ├── gif_exporter.py
│   │   └── manifest_exporter.py   # JSON metadata export
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # App configuration
│       ├── logger.py              # Logging setup
│       ├── image_utils.py         # Shared image helpers
│       └── errors.py              # Error codes + recovery
├── projects/                      # Runtime user project storage
├── model_cache/                   # Downloaded model files
├── logs/                          # Application logs
├── config/
│   ├── app_config.json            # User settings
│   └── model_registry.json        # Model definitions
├── requirements.txt
├── BUILD_PLAN.md
└── README.md
```

---

## Implementation Phases

### Phase 0 — Foundation

**Goal:** Project skeleton, database, config, and verification everything runs.

| Step | Task | Key File(s) | Verification |
|------|------|-------------|--------------|
| 0.1 | Initialize Python project with `pyproject.toml`, virtual env, `requirements.txt` | `pyproject.toml`, `requirements.txt` | `pip install -r requirements.txt` succeeds |
| 0.2 | Create all directory folders | — | All folders exist |
| 0.3 | Implement app config loader (`app_config.json` + `model_registry.json`) | `app/utils/config.py` | Config loads, missing fields default |
| 0.4 | Set up logging to `logs/application.log` | `app/utils/logger.py` | Log file created on first run |
| 0.5 | Define error codes (APP-001 through APP-005) and structured error response | `app/utils/errors.py` | Error raised, JSON serializable |
| 0.6 | Create SQLite schema — tables: `projects`, `style_profiles`, `assets`, `animations` | `app/storage/database.py` | `database.db` created with correct schema |
| 0.7 | Create `main.py` — init DB, load config, launch empty PySide6 window | `app/main.py` | Window appears, DB file created, clean exit |

---

### Phase 1 — Project Management & Style Profiles

**Goal:** User can create/open/delete projects and configure style profiles.

| Step | Task | Key File(s) | Verification |
|------|------|-------------|--------------|
| 1.1 | Implement `ProjectService` (create, load, delete, list) + `ProjectRepo` | `app/services/project_service.py`, `app/storage/project_repo.py` | CRUD operations work against DB |
| 1.2 | Implement `StyleService` (create, update, get, apply) + `StyleRepo` | `app/services/style_service.py`, `app/storage/style_repo.py` | Style profiles save/load correctly |
| 1.3 | Build PySide6 `MainWindow` shell — stacked widget + sidebar navigation | `app/ui/main_window.py` | Navigate between screens |
| 1.4 | Build `DashboardScreen` — project list, create/open/delete buttons | `app/ui/dashboard_screen.py` | Create → project appears; delete → removed |
| 1.5 | Build `StyleEditorScreen` — name, base prompt, negative prompt, params, reference images | `app/ui/style_editor_screen.py` | All fields save and reload |
| 1.6 | Wire services to UI via Qt signals/slots | `main_window.py` | UI reflects DB state |

---

### Phase 2 — Model Manager

**Goal:** AI models can be downloaded, loaded, used, and unloaded with VRAM tracking.

| Step | Task | Key File(s) | Verification |
|------|------|-------------|--------------|
| 2.1 | Build `ModelRegistry` — reads `model_registry.json`, validates paths | `app/models/model_registry.py` | Registry loads valid models |
| 2.2 | Build `ModelManager` — `load_model()`, `unload_model()`, `unload_all()`, VRAM monitor | `app/models/model_manager.py` | Load → VRAM > 0; unload → VRAM freed |
| 2.3 | Integrate SD 1.5 pipeline via Diffusers txt2img | `app/models/model_manager.py` | Image generated from prompt |
| 2.4 | Integrate Rembg pipeline for background removal | `app/models/model_manager.py` | Background removed from image |
| 2.5 | Integrate CLIP model for classification | `app/models/model_manager.py` | Classification returns label + confidence |
| 2.6 | VRAM watchdog — poll `pynvml` every 2s, enforce 7.5 GB ceiling | `app/models/model_manager.py` | OOM triggers recovery, no crash |

---

### Phase 3 — Asset Generation

**Goal:** User enters a prompt, picks asset type, gets a 512×512 PNG.

| Step | Task | Key File(s) | Verification |
|------|------|-------------|--------------|
| 3.1 | Implement `GenerationService.generate_asset()` — compose prompt with style profile, run SD pipeline, save PNG + thumbnail | `app/services/generation_service.py` | PNG created at 512×512 |
| 3.2 | Implement `MetadataService` — create metadata JSON per asset | `app/services/metadata_service.py` | Valid JSON with all required fields |
| 3.3 | Build `GenerationScreen` — category dropdown, prompt input, quantity spinner, generate button | `app/ui/generation_screen.py` | Form submits, generation starts |
| 3.4 | Implement batch generation (`generate_batch`) | `app/services/generation_service.py` | N assets generated in loop |
| 3.5 | Show generation progress per image (signal to UI) | `app/ui/generation_screen.py` | Progress bar updates |

---

### Phase 4 — Background Removal & Sprite Extraction

**Goal:** Assets are transparent, sprites are extracted from sheets.

| Step | Task | Key File(s) | Verification |
|------|------|-------------|--------------|
| 4.1 | Implement `BackgroundRemovalService.remove_background()` — wrap Rembg, output RGBA PNG | `app/services/background_service.py` | Transparent PNG output |
| 4.2 | Implement `BackgroundRemovalService.batch_remove()` | `app/services/background_service.py` | Batch of images processed |
| 4.3 | Implement `SpriteExtractionService.extract_sprites()` — contour detection, bounding boxes, crop, auto-name | `app/services/extraction_service.py` | Sprites detected and extracted |
| 4.4 | Wire bg removal into generation pipeline (automatic after gen) | `app/workflows/workflow_engine.py` | Gen + BG removal = single step |
| 4.5 | Build `ReviewScreen` — asset grid, select, rename, delete, regenerate, animate, tile, export buttons | `app/ui/review_screen.py` | All actions work on selected asset |

---

### Phase 5 — Classification & Texture Tiling

**Goal:** Assets auto-classified, seamless tiles generated.

| Step | Task | Key File(s) | Verification |
|------|------|-------------|--------------|
| 5.1 | Implement `ClassificationService.classify_asset()` — CLIP inference, return type + confidence | `app/services/classification_service.py` | Labels match expected categories |
| 5.2 | Wire classification into sprite extraction flow | `app/services/extraction_service.py` | Extracted sprites have correct names |
| 5.3 | Implement `TextureService.make_seamless()` — offset → mask → inpaint center seams → validate | `app/services/texture_service.py` | Tile loops without visible seam |
| 5.4 | Add tile generation button on ReviewScreen | `app/ui/review_screen.py` | Tile created from selected asset |

---

### Phase 6 — Export System

**Goal:** Export project as organized folder structure.

| Step | Task | Key File(s) | Verification |
|------|------|-------------|--------------|
| 6.1 | Implement `ExportService` — create directory tree, copy assets/animations/metadata | `app/services/export_service.py` | Folder structure matches spec |
| 6.2 | Implement manifest JSON generation | `app/exporters/manifest_exporter.py` | Valid JSON with file listing |
| 6.3 | Build `ExportScreen` — format selector (PNG/GIF/JSON), destination picker, export button + progress | `app/ui/export_screen.py` | Export completes, files in correct folders |

---

### Phase 7 — Animation Pipeline (Feature Flagged)

**Goal:** Generate looping sprite animations (idle, walk, run, attack, hurt, death).

| Step | Task | Key File(s) | Verification |
|------|------|-------------|--------------|
| 7.1 | Research spike: choose animation approach (resolve ADR-PENDING-001) | Spike report | Decision documented |
| 7.2 | Implement `AnimationService` — per-type methods, 8 FPS, PNG sequence | `app/services/animation_service.py` | Frames generated at correct rate |
| 7.3 | Implement loop validator — compare first/last frame similarity ≥ 95% | `app/services/animation_service.py` | Validator rejects bad loops |
| 7.4 | Implement GIF export for animation preview | `app/exporters/gif_exporter.py` | GIF plays smoothly |
| 7.5 | Build `AnimationScreen` — asset picker, animation type, frame count, FPS, Generate + Preview | `app/ui/animation_screen.py` | Animation generates and previews |
| 7.6 | Gate behind feature flag `enable_animation` in config (default: false) | `app/utils/config.py` | Flag hides animation UI/features |

---

### Phase 8 — One-Click Pipeline & Job Queue

**Goal:** User hits one button → full pipeline executes with progress.

| Step | Task | Key File(s) | Verification |
|------|------|-------------|--------------|
| 8.1 | Build `WorkflowEngine` — orchestrates: Gen → BG → Extract → Metadata → (Anim) → Export | `app/workflows/workflow_engine.py` | Pipeline runs end-to-end |
| 8.2 | Build `JobQueue` — FIFO, single concurrent GPU job, queue display | `app/workflows/job_queue.py` | Jobs execute sequentially |
| 8.3 | Build `ProgressTracker` — step-by-step signals (progress %, current step, status text) | `app/workflows/progress_tracker.py` | UI updates in real time |
| 8.4 | Wire "Run Pipeline" button on GenerationScreen | `app/ui/generation_screen.py` | One click triggers full pipeline |
| 8.5 | Add checkpoint recovery — save state after each pipeline step | `app/workflows/workflow_engine.py` | Resume from last completed step on restart |

---

### Phase 9 — Performance Optimization

**Goal:** Meet all performance targets from the TDD.

| Target | Current | Goal | Measurement |
|--------|---------|------|-------------|
| App startup | — | < 20s | Start to window ready |
| Single asset gen | — | < 60s | Prompt to PNG saved |
| Background removal | — | < 5s | Per asset |
| Sprite extraction | — | < 10s | Per sheet |
| Animation generation | — | < 180s | Per animation |
| Export | — | < 30s | Per project |
| Peak VRAM | — | < 8 GB | `pynvml` during stress test |

| Step | Task | Key File(s) |
|------|------|-------------|
| 9.1 | Profile startup — optimize imports, lazy model loading | `app/main.py` |
| 9.2 | Benchmark generation — tune inference steps and scheduler | `app/services/generation_service.py` |
| 9.3 | Optimize background removal — batch processing, resolution tuning | `app/services/background_service.py` |
| 9.4 | Optimize sprite extraction — contour parameter tuning | `app/services/extraction_service.py` |
| 9.5 | Optimize animation generation | `app/services/animation_service.py` |
| 9.6 | Stress test — 50 consecutive pipeline runs, track VRAM | WorkflowEngine |
| 9.7 | Build Performance Dashboard (load times, VRAM graph, ops count) | New UI widget |

---

### Phase 10 — Release Preparation

**Goal:** Ship stable, packaged installer.

| Step | Task | Key File(s) |
|------|------|-------------|
| 10.1 | Package with PyInstaller or Nuitka | `pyproject.toml` |
| 10.2 | Build installer (Inno Setup / NSIS) | — |
| 10.3 | Build model downloader tool — first-run wizard | `app/models/model_manager.py` |
| 10.4 | Configuration wizard — output dir, model selection, VRAM budget | New UI screen |
| 10.5 | Write user documentation | — |
| 10.6 | Run full acceptance criteria (AC-1 through AC-10) | — |

---

## VRAM Management Strategy

```
Budget:
  SD 1.5 Generation:         4.5 GB
  Animation Model:           5.5 GB
  Background Removal:        0.5 GB
  System Safety Margin:      1.0 GB
  ─────────────────────────────────
  Max Available:             8.0 GB

Rule: Only ONE AI model category loaded at any time.
```

Enforcement:
- `ModelManager.current_model_category` tracks loaded category
- `load_model()` calls `unload_all()` before loading new model
- `unload_all()` does: `del pipeline` → `torch.cuda.empty_cache()` → `gc.collect()`
- VRAM watchdog polls via `pynvml` every 2s during inference
- If VRAM > 7.5 GB → pause, unload, alert user with recovery action
- WorkflowEngine calls `unload_all()` between pipeline stages

---

## Dependency Map

```
Phase 0 (Foundation)
  └── Phase 1 (Projects + Styles)
        └── Phase 2 (Model Manager)
              └── Phase 3 (Generation) ──► Phase 4 (BG + Extraction)
                     │                          └── Phase 5 (Classify + Tiling)
                     │                                └── Phase 6 (Export)
                     └── Phase 7 (Animation) ───────────┘
                            └── Phase 8 (One-Click Pipeline)
                                   └── Phase 9 (Optimization)
                                          └── Phase 10 (Release)
```

## Risk Register

| ID | Risk | Score | Mitigation |
|----|------|-------|------------|
| RISK-001 | Cross-session style drift | 20 | Style profile with references + prompt templates |
| RISK-002 | Animation quality issues | 20 | Feature flag, research spike, loop validator ≥ 95% |
| RISK-003 | GPU OOM | 20 | Single-model loading, VRAM watchdog, auto-unload |
| RISK-004 | Slow generation | 12 | Benchmark, step tuning, optional Turbo mode |
| RISK-005 | Poor sprite extraction | 12 | Contour tuning + manual correction mode |
| RISK-008 | Workflow failure mid-pipeline | 12 | Checkpoint persistence after each step |

## Key Architectural Decisions

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-001 | Desktop app (PySide6) | Offline, GPU access, no web stack |
| ADR-003 | SQLite database | Single user, no server needed |
| ADR-007 | One AI model at a time | 8 GB VRAM constraint |
| ADR-008 | Animation isolated behind flag | Highest risk component |
| ADR-009 | Project-centric organization | Consistency across assets |
| ADR-010 | JSON + SQLite metadata | Human-readable + searchable |
| ADR-012 | Centralized Workflow Engine | Single execution path for recovery |

---

## Verification Checklist

- [ ] Phase 0: App starts, DB initialized, config loaded
- [ ] Phase 1: Projects + style profiles CRUD working
- [ ] Phase 2: Models load/unload, VRAM < 8 GB
- [ ] Phase 3: 512×512 PNG generated from prompt + style
- [ ] Phase 4: Transparent PNGs, sprites extracted from sheets
- [ ] Phase 5: Assets classified, seamless tiles generated
- [ ] Phase 6: Exported folder structure matches spec
- [ ] Phase 7: Animations loop cleanly (feature flag gated)
- [ ] Phase 8: One-click pipeline end-to-end with progress
- [ ] Phase 9: All performance targets met
- [ ] Phase 10: Packaged installer, all ACs pass
