"""
FastAPI Application

Main application entry point for the Pipeline n8n alternative API.
"""

import traceback
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.db.database import init_system_db, get_db
import config

# Import schemas for checkpoints
from src.models.schemas import (
    CheckpointCreate,
    CheckpointUpdate,
    CheckpointResponse,
    CheckpointSummary,
    HumanOnlyConfigUpdate,
    HumanInteractionCreate,
    InputFieldCreate,
    OutputArtifactCreate,
)
from src.services.checkpoint_service import CheckpointService


# Exception handler for all unhandled exceptions
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to log all errors."""
    print(f"ERROR: {exc}")
    print(f"URL: {request.url}")
    print(f"Method: {request.method}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan event handler for the FastAPI application.

    Initializes the database on startup.
    """
    # Startup
    print("Initializing Pipeline System...")
    init_system_db()
    print("Database initialized successfully")
    print(f"Pipeline base path: {config.BASE_PIPELINES_PATH}")
    print(f"Using OpenAI API at: {config.OPENAI_BASE_URL}")

    yield

    # Shutdown
    print("Shutting down Pipeline System...")


# Create FastAPI application
app = FastAPI(
    title="Pipeline n8n Alternative",
    description="A pipeline automation tool with agentic AI capabilities",
    version="1.0.0",
    lifespan=lifespan,
)

# Register global exception handler
app.add_exception_handler(Exception, global_exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "Pipeline n8n Alternative",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "Pipeline n8n Alternative",
        "description": "A pipeline automation tool with agentic AI capabilities",
        "docs": "/docs",
        "health": "/health"
    }


# Import routers
from src.api.routes.pipelines import router as pipelines_router
from src.api.routes.runs import router as runs_router
from src.api.routes.executions import router as executions_router

# Include route modules
app.include_router(pipelines_router, prefix="/api/pipelines", tags=["Pipelines"])
app.include_router(runs_router, prefix="/api/runs", tags=["Pipeline Runs"])
app.include_router(executions_router, tags=["Checkpoint Executions"])

# =============================================================================
# Checkpoints routes - directly in app.py to avoid import issues
# =============================================================================

# Dependency to get database session
DBSession = Annotated[Session, Depends(get_db)]

# Checkpoints router
checkpoints_router = APIRouter()


@checkpoints_router.get(
    "",
    response_model=list[CheckpointSummary],
    summary="List checkpoints for pipeline",
    description="Get all checkpoints for a specific pipeline.",
)
def list_checkpoints(
    session: DBSession,
    pipeline_id: str = Query(..., description="Pipeline ID to get checkpoints for"),
) -> list[CheckpointSummary]:
    """List all checkpoints for a pipeline."""
    return CheckpointService.get_checkpoints_for_pipeline(session, pipeline_id)


@checkpoints_router.post(
    "",
    response_model=CheckpointResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new checkpoint",
    description="Create a new checkpoint for a pipeline. Currently supports human_only mode only.",
)
def create_checkpoint(
    data: CheckpointCreate,
    session: DBSession,
    pipeline_id: str = Query(..., description="Pipeline ID to add the checkpoint to"),
) -> CheckpointResponse:
    """Create a new checkpoint."""
    try:
        return CheckpointService.create_checkpoint(session, pipeline_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@checkpoints_router.get(
    "/{checkpoint_id}",
    response_model=CheckpointResponse,
    summary="Get checkpoint details",
    description="Get detailed information about a specific checkpoint.",
)
def get_checkpoint(
    checkpoint_id: str,
    session: DBSession,
) -> CheckpointResponse:
    """Get a checkpoint by ID."""
    checkpoint = CheckpointService.get_checkpoint(session, checkpoint_id)

    if not checkpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint with ID '{checkpoint_id}' not found",
        )

    return checkpoint

@checkpoints_router.put(
    "/{checkpoint_id}",
    response_model=CheckpointResponse,
    summary="Update checkpoint details",
    description="Update an existing checkpoint.",
)
async def update_checkpoint(
    checkpoint_id: str,
    data: CheckpointUpdate,
    session: DBSession,
) -> CheckpointResponse:
    """Update a checkpoint by ID."""
    try:
        return CheckpointService.update_checkpoint(session, checkpoint_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@checkpoints_router.delete(
    "/{checkpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete checkpoint",
    description="Delete a checkpoint from its pipeline.",
)
def delete_checkpoint(
    checkpoint_id: str,
    session: DBSession,
) -> None:
    """Delete a checkpoint by ID."""
    deleted = CheckpointService.delete_checkpoint(session, checkpoint_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint with ID '{checkpoint_id}' not found",
        )

    return None


# Include checkpoints router - NOW IN THIS FILE
app.include_router(checkpoints_router, prefix="/api/checkpoints", tags=["Checkpoints"])

# Additional routes (to be implemented in later slices)
# from src.api.routes import rollback, artifacts
# app.include_router(rollback.router, prefix="/api/rollback", tags=["Rollback"])
# app.include_router(artifacts.router, prefix="/api/artifacts", tags=["Artifacts"])
