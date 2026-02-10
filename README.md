# Pipeline n8n Alternative

A pipeline automation tool with agentic AI capabilities. This system allows you to define and execute complex multi-step workflows with AI agents, scripts, and human interaction.

## Quick Status

**Phase 1 (Foundation & Core Infrastructure)** - ✅ COMPLETE (5/5 slices)
- Slice 1: Foundation - DB models, file manager, API setup
- Slice 2: Create & List Pipelines - Full CRUD API + Frontend
- Slice 3: Update & Delete Pipelines - Edit page, enhanced UI
- Slice 4: Create Checkpoint Definitions - Human-only mode
- Slice 5: Update & Delete Checkpoints + Reorder

**Phase 2 (Pipeline Execution Engine)** - 🔄 IN PROGRESS (2/5 slices)
- Slice 6: Start Pipeline Run - ✅ **COMPLETE**
- Slice 7: Execute Human-Only Checkpoints - ✅ **COMPLETE**
- Slice 8: Pause & Resume Runs - ⏳ **NEXT**
- Slice 9: View Run History & Artifacts
- Slice 10: Extend Previous Run (Version Extension)

**Phase 3: Rollback System** - ⏳ PENDING
**Phase 4: Agent Execution** - ⏳ PENDING
**Phase 5: Script Execution & Polish** - ⏳ PENDING

---

## Features

- **Pipeline Definition**: Define pipelines with multiple checkpoints/steps
- **Agentic Execution**: Run AI agents with meta-agent, predefined, or single agent modes
- **Script Execution**: Run Python scripts with optional user input
- **Human Interaction**: Require approval and allow revisions at each checkpoint
- **Version Management**: Track pipeline runs with version history (v1, v2, v3...)
- **Rollback Support**: Rollback to previous checkpoints or runs with automatic archiving
- **Artifact Management**: Track and manage outputs from each checkpoint
- **SQLite Database**: Source of truth for all pipeline state

---

## Architecture

```
{pipeline_id}/
├── .pipeline_system/        # Hidden system directory
│   ├── db/
│   │   └── state.db         # SOURCE OF TRUTH
│   ├── definitions/
│   │   ├── pipeline.json
│   │   └── checkpoints/
│   │       └── {checkpoint_id}.json
│   └── logs/
│       └── system.log
├── runs/                    # User-visible cache
│   ├── v1/
│   ├── v2/
│   └── latest -> v2
├── .temp/
│   └── exec_{execution_id}/ # Persists across retries
├── .archived/
│   └── rollback_{id}_{datetime}/
└── .errored/
    └── exec_{id}_{datetime}/
```

---

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your OpenAI API key and base URL
```

3. **Run the server:**
```bash
python main.py
```

The API will be available at `http://localhost:8000`

---

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `OPENAI_API_KEY` | Your API key | *required* |
| `OPENAI_BASE_URL` | Custom API endpoint | `https://api.openai.com/v1` |
| `DEFAULT_MODEL` | Default model to use | `gpt-4o` |
| `DEFAULT_MAX_TOKENS` | Max tokens for LLM responses | `8000` |
| `DEFAULT_TEMPERATURE` | LLM temperature | `0.7` |
| `BASE_PIPELINES_PATH` | Path to store pipeline data | `./pipelines` |
| `LOG_LEVEL` | Logging level | `INFO` |

---

## API Documentation

Once the server is running:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Project Structure

```
├── config.py                      # Configuration
├── main.py                        # Server entry point
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
│
├── src/
│   ├── api/
│   │   ├── app.py                # FastAPI application (includes checkpoint & run routes)
│   │   └── routes/
│   │       ├── pipelines.py      # Pipeline routes
│   │       ├── runs.py           # Pipeline run routes (Slice 6)
│   │       ├── checkpoints.py    # Checkpoint routes (Slice 4)
│   │       └── executions.py     # Execution control routes (Slice 7)
│   ├── core/
│   │   └── file_manager.py       # File operations
│   ├── db/
│   │   ├── database.py           # DB connection
│   │   └── models.py             # SQLAlchemy models
│   ├── models/
│   │   └── schemas.py            # Pydantic schemas (includes checkpoint & run schemas)
│   └── services/
│       ├── pipeline_service.py   # Pipeline business logic
│       ├── checkpoint_service.py # Checkpoint business logic
│       ├── run_service.py        # Run business logic (Slice 6)
│       └── execution_service.py  # Execution workflow logic (Slice 7)
│
├── frontend/
│   ├── package.json              # NPM dependencies
│   ├── vite.config.ts            # Vite config
│   ├── tsconfig.json             # TypeScript config
│   ├── index.html                # HTML entry
│   └── src/
│       ├── components/
│       │   ├── Header.tsx        # Navigation header
│       │   └── PipelineCard.tsx  # Pipeline card component
│       ├── lib/
│       │   └── api.ts            # API client
│       ├── pages/
│       │   ├── PipelineList.tsx  # Pipeline list page
│       │   ├── CreatePipeline.tsx # Create pipeline form
│       │   ├── EditPipeline.tsx   # Edit pipeline form
│       │   ├── PipelineDetail.tsx # Pipeline detail view
│       │   ├── CreateCheckpoint.tsx # Create checkpoint form
│       │   ├── EditCheckpoint.tsx   # Edit checkpoint form
│       │   └── RunDetail.tsx      # Run detail view (Slice 6)
│       ├── types/
│       │   └── pipeline.ts       # TypeScript types
│       ├── App.tsx               # Main app with routing
│       ├── main.tsx              # React entry
│       └── index.css             # Global styles
│
├── pipelines/                    # Pipeline data directory
├── completion_status.md          # Detailed progress tracking
└── README.md                     # This file
```

---

## Development Progress

### ✅ Phase 1, Slice 1: Foundation (COMPLETE - 2026-02-10)

**Implemented:**
- [x] Project structure and configuration
- [x] Database models (SQLAlchemy) - 11 tables with relationships
- [x] Database connection management
- [x] File system manager (directories, artifacts, temp, archives)
- [x] Basic FastAPI application with health check

**Files Created:**
- `config.py` - Central configuration with OpenAI-compatible API settings
- `src/db/models.py` - SQLAlchemy ORM models (Pipeline, CheckpointDefinition, PipelineRun, etc.)
- `src/db/database.py` - Database engine, session management, initialization
- `src/core/file_manager.py` - File system operations manager
- `src/api/app.py` - FastAPI application with CORS
- `main.py` - Server entry point
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template
- `completion_status.md` - Slice completion tracking

**Bug Fixes Applied:**
- SQLAlchemy `metadata` reserved name conflict → renamed to `event_metadata`
- Uvicorn reload warning → changed to import string format

---

### ✅ Phase 1, Slice 2: Create & List Pipelines (COMPLETE - 2026-02-10)

**Implemented:**
- [x] Pydantic models for request/response validation
- [x] Pipeline CRUD operations (Create, Read, Update, Delete)
- [x] API routes for `/api/pipelines`
- [x] React frontend with Vite
- [x] Pipeline list and create pages

**Files Created:**
- `src/models/schemas.py` - Pydantic schemas
- `src/services/pipeline_service.py` - Business logic
- `src/api/routes/pipelines.py` - Pipeline API endpoints
- `frontend/` - Complete React frontend

**Features:**
- Create, view, list, and delete pipelines
- Responsive UI with Tailwind CSS
- Form validation and error handling

---

### ✅ Phase 1, Slice 3: Update & Delete Pipelines (COMPLETE - 2026-02-10)

**Implemented:**
- [x] Edit pipeline page with pre-filled form
- [x] Update pipeline metadata (name, description, auto-advance)
- [x] Edit button on pipeline detail page

**Files Created:**
- `frontend/src/pages/EditPipeline.tsx` - Edit pipeline form page

**Files Modified:**
- `frontend/src/App.tsx` - Added edit route
- `frontend/src/pages/PipelineDetail.tsx` - Added Edit button

**Features:**
- Edit pipeline name, description, and auto-advance setting
- Form validation with error messages
- Info box explaining change impacts

---

### ✅ Phase 1, Slice 4: Create Simple Checkpoint Definitions (COMPLETE - 2026-02-10)

**Implemented:**
- [x] Checkpoint CRUD operations (Create, Read, List)
- [x] API routes for `/api/checkpoints`
- [x] Human-only checkpoint mode
- [x] Checkpoint form builder with input fields
- [x] Checkpoint list in pipeline view

**Files Created:**
- `src/services/checkpoint_service.py` - Checkpoint business logic
- `src/api/routes/checkpoints.py` - Checkpoint API endpoints
- `frontend/src/pages/CreateCheckpoint.tsx` - Checkpoint creation form

**Files Modified:**
- `src/models/schemas.py` - Added checkpoint schemas
- `src/api/app.py` - Registered checkpoints router
- `frontend/src/types/pipeline.ts` - Added checkpoint types
- `frontend/src/lib/api.ts` - Added checkpoint API methods
- `frontend/src/App.tsx` - Added checkpoint route
- `frontend/src/pages/PipelineDetail.tsx` - Added Add Checkpoint button

**Features:**
- Create human-only checkpoints with form input fields
- Dynamic input field builder (text, number, boolean, file, multiline_text)
- Human interaction settings (approval to start/complete, max revisions)
- Output artifact definitions
- Save form data as artifact option

---

### ✅ Phase 1, Slice 5: Update & Delete Checkpoints + Reorder (COMPLETE - 2026-02-10)

**Implemented:**
- [x] Edit checkpoint form
- [x] Delete checkpoint with confirmation
- [x] Drag-and-drop checkpoint reordering
- [x] Update pipeline `checkpoint_order` array

**Files Created:**
- `frontend/src/pages/EditCheckpoint.tsx` - Full checkpoint edit page

**Files Modified:**
- `frontend/src/App.tsx` - Added edit checkpoint route
- `frontend/src/pages/PipelineDetail.tsx` - Added Edit/Delete buttons and up/down reorder arrows
- `frontend/src/lib/api.ts` - Added `updateCheckpoint()`, `deleteCheckpoint()`, `reorderCheckpoints()`
- `frontend/src/types/pipeline.ts` - Added `CheckpointUpdate` type
- `src/models/schemas.py` - Added `CheckpointUpdate` and `HumanOnlyConfigUpdate` schemas
- `src/services/checkpoint_service.py` - Added `update_checkpoint()` and `delete_checkpoint()` methods
- `src/services/pipeline_service.py` - Added `reorder_checkpoints()` method
- `src/core/file_manager.py` - Added `delete_checkpoint_definition()` method

**UI Features:**
- ✅ Edit button for each checkpoint in pipeline detail view
- ✅ Delete button with confirmation dialog
- ✅ Up/down arrows for checkpoint reordering
- ✅ Full edit form with pre-filled data (name, description, instructions, input fields, human interaction settings, output artifacts)

---

### ✅ Phase 2, Slice 6: Start Pipeline Run (COMPLETE - 2026-02-10)

**Implemented:**
- [x] Pipeline run lifecycle management
- [x] Create PipelineRun model (already existed in models.py)
- [x] Create CheckpointExecution model (already existed in models.py)
- [x] API: `POST /api/runs` - Create new run
- [x] API: `POST /api/runs/{id}/start` - Start run (creates first checkpoint execution)
- [x] API: `GET /api/runs` - List runs for pipeline
- [x] API: `GET /api/runs/{id}` - Get run details
- [x] Temp workspace creation
- [x] Run detail page with progress tracking
- [x] "Start Run" button on pipeline detail

**Files Created:**
- `src/services/run_service.py` - Business logic for run management
- `src/api/routes/runs.py` - FastAPI routes for run endpoints
- `frontend/src/pages/RunDetail.tsx` - Run detail view page

**Files Modified:**
- `src/models/schemas.py` - Added PipelineRunCreate, PipelineRunResponse, PipelineRunDetailResponse, CheckpointExecutionSummary, CheckpointExecutionResponse schemas
- `src/api/app.py` - Registered runs router
- `frontend/src/types/pipeline.ts` - Added run types (PipelineRun, PipelineRunDetail, PipelineRunSummary, CheckpointExecutionSummary)
- `frontend/src/lib/api.ts` - Added run API methods (createRun, startRun, getRun, listRuns)
- `frontend/src/App.tsx` - Added run route pattern with case-insensitive regex
- `frontend/src/pages/PipelineDetail.tsx` - Added "Start Run" button and Pipeline Runs section

**Features Delivered:**
1. **Pipeline Run Creation**
   - Create new run (v1, v2, v3...)
   - Automatically increments run version
   - Optionally extends from previous run (for Slice 10)
   - Creates run directory in file system (runs/v1/, runs/v2/, etc.)
   - Saves run_info.json to file system

2. **Start Pipeline Run**
   - Starts a run from "not_started" to "in_progress" status
   - Creates first checkpoint execution
   - Creates temp workspace (`.temp/exec_{execution_id}/`)
   - Creates permanent output directory structure
   - Sets checkpoint status based on `requires_approval_to_start`

3. **Run Detail Page** (`/runs/{runId}`)
   - Displays run status (not_started, in_progress, paused, completed, failed)
   - Shows progress bar (completed checkpoints / total checkpoints)
   - Lists all checkpoint executions with status badges
   - "Start Pipeline Run" button for not_started runs
   - Navigation back to pipeline detail

4. **Pipeline Runs Section** (on Pipeline Detail page)
   - Lists recent runs (up to 5)
   - Shows run version (v1, v2, etc.)
   - Shows run status with color-coded badges
   - "New Run" button to create new runs
   - "View Details" link to run detail page
   - Empty state with helpful message

**Bug Fixes Applied (Slice 6):**
1. **FastAPI dependency injection with Annotated** - Fixed by using simpler `Session = Depends(get_db)` pattern
2. **PipelineRun.checkpoint_execution_history attribute** - Fixed by removing non-existent attribute (SQLAlchemy relationship handles this automatically)
3. **useNavigate() without Router context** - Fixed by using `window.location.href` navigation instead of React Router's `useNavigate()`

**Run Status Flow:**
```
not_started → [POST /api/runs/{id}/start] → in_progress
                                          ↓
                                      pending / waiting_approval_to_start
```

---

### ✅ Phase 2, Slice 7: Execute Human-Only Checkpoints (COMPLETE ✅)

**Implemented:**
- [x] Approve checkpoint start
- [x] Submit human form data
- [x] Approve checkpoint completion
- [x] Promote temp → permanent artifacts
- [x] Move to next checkpoint automatically
- [x] Request revision with feedback
- [x] Auto-advance to next checkpoint

**API Endpoints Implemented:**
- `GET /api/executions/{id}` - Get execution details with form config
- `POST /api/executions/{id}/approve-start` - Approve checkpoint start
- `POST /api/executions/{id}/submit` - Submit human form data
- `POST /api/executions/{id}/approve-complete` - Approve checkpoint completion
- `POST /api/executions/{id}/request-revision` - Request revision

**Bug Fixes Applied (Slice 7):**
1. **FastAPI parameter ordering** - Fixed: path params → session → body with default
2. **Duplicate dependency annotation** - Fixed: removed duplicate `= Depends(get_db)`
3. **Checkpoints with 0 input fields stuck** - Fixed: added "Continue" button
4. **Pipeline completion buttons not disappearing** - Fixed: clear `currentExecution` state
5. **Revision form data not updating** - Fixed: sort interactions by timestamp
6. **Checkpoint order not persisting** - Fixed: added `flag_modified()` calls

**Key Files Created (Slice 7):**
- `src/services/execution_service.py` - Checkpoint execution business logic
- `src/api/routes/executions.py` - Execution control endpoints

**Key Files Modified (Slice 7):**
- `src/models/schemas.py` - Added execution control schemas
- `src/api/app.py` - Registered executions router
- `frontend/src/lib/api.ts` - Added execution API methods
- `frontend/src/types/pipeline.ts` - Added execution types
- `frontend/src/pages/RunDetail.tsx` - Complete rewrite with execution controls UI

---

### ⏳ Phase 2, Slice 8: Pause & Resume Runs

**Planned:**
- [ ] Pause run between checkpoints
- [ ] Resume paused run
- [ ] Store and display pause state

---

### ⏳ Phase 2, Slice 9: View Run History & Artifacts

**Planned:**
- [ ] List runs for pipeline
- [ ] View checkpoint executions
- [ ] Download artifacts
- [ ] Artifact preview (JSON, Markdown)

---

### ⏳ Phase 2, Slice 10: Extend Previous Run (Version Extension)

**Planned:**
- [ ] Find previous run version
- [ ] Set `previous_run_id` and `extends_from_run_version`
- [ ] Load previous version artifacts for context
- [ ] Version display in UI

---

### ⏳ Phase 3: Rollback System

**Planned:**
- [ ] Checkpoint-level rollback
- [ ] Run-level rollback
- [ ] Archive creation and management
- [ ] Rollback history UI

---

### ⏳ Phase 4: Agent Execution

**Planned:**
- [ ] OpenAI client integration
- [ ] Single agent execution
- [ ] Predefined agents execution
- [ ] Meta-agent creation mode
- [ ] Discussion modes (sequential, council, parallel, debate)
- [ ] Context injection (previous versions, checkpoint references)

---

### ⏳ Phase 5: Script Execution & Polish

**Planned:**
- [ ] Python script runner
- [ ] User input collection for scripts
- [ ] Event system & audit trail
- [ ] Validation & retry logic
- [ ] UI polish & final touches

---

## Database Schema

### Core Tables

| Table | Description |
|-------|-------------|
| `pipelines` | Pipeline definitions with version tracking |
| `checkpoint_definitions` | Checkpoint configurations |
| `pipeline_runs` | Pipeline runtime state |
| `checkpoint_executions` | Checkpoint runtime state |
| `execution_logs` | Execution log entries |
| `human_interactions` | Human interaction records |
| `artifacts` | Artifact metadata |
| `rollback_events` | Rollback operation records |
| `archived_items` | Archived item records |
| `events` | General event logging |

---

## Running Tests

```bash
# Run all tests (when implemented)
pytest

# Run with coverage
pytest --cov=src
```

---

## Contributing

This is an active development project. See `completion_status.md` for detailed progress tracking.

---

## License

TBD
