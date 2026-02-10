"""
Checkpoint API Routes

Routes for checkpoint CRUD operations.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.models.schemas import (
    CheckpointCreate,
    CheckpointUpdate,
    CheckpointResponse,
    CheckpointSummary,
    ErrorResponse,
)
from src.services.checkpoint_service import CheckpointService

router = APIRouter()


# Dependency to get database session
DBSession = Annotated[Session, Depends(get_db)]


@router.get(
    "",
    response_model=list[CheckpointSummary],
    summary="List checkpoints for pipeline",
    description="Get all checkpoints for a specific pipeline.",
)
def list_checkpoints(
    session: DBSession,
    pipeline_id: str = Query(..., description="Pipeline ID to get checkpoints for"),
) -> list[CheckpointSummary]:
    """
    List all checkpoints for a pipeline.

    Returns a summary list of checkpoints including:
    - Checkpoint ID
    - Name and description
    - Execution mode
    - Timestamps
    """
    return CheckpointService.get_checkpoints_for_pipeline(session, pipeline_id)


@router.post(
    "",
    response_model=CheckpointResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new checkpoint",
    description="Create a new checkpoint for a pipeline. Currently supports human_only mode only.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        404: {"model": ErrorResponse, "description": "Pipeline not found"},
    },
)
def create_checkpoint(
    data: CheckpointCreate,
    session: DBSession,
    pipeline_id: str = Query(..., description="Pipeline ID to add the checkpoint to"),
) -> CheckpointResponse:
    """
    Create a new checkpoint.

    - **pipeline_id**: ID of the pipeline to add the checkpoint to (query parameter)
    - **checkpoint_name**: Name of the checkpoint (required, 1-255 characters)
    - **checkpoint_description**: Description of the checkpoint (required, 1-5000 characters)
    - **execution_mode**: Mode of execution - only 'human_only' supported in Slice 4
    - **human_only_config**: Configuration for human-only checkpoints
    - **human_interaction**: Human interaction settings
    - **output_artifacts**: Expected output artifacts from this checkpoint

    For Slice 4, only human_only mode is supported. Agentic and script modes will be added in later slices.
    """
    try:
        return CheckpointService.create_checkpoint(session, pipeline_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{checkpoint_id}",
    response_model=CheckpointResponse,
    summary="Get checkpoint details",
    description="Get detailed information about a specific checkpoint.",
    responses={
        404: {"model": ErrorResponse, "description": "Checkpoint not found"},
    },
)
def get_checkpoint(
    checkpoint_id: str,
    session: DBSession,
) -> CheckpointResponse:
    """
    Get a checkpoint by ID.

    Returns detailed checkpoint information including:
    - Basic metadata
    - Execution configuration
    - Human-only config
    - Human interaction settings
    - Output artifacts
    """
    checkpoint = CheckpointService.get_checkpoint(session, checkpoint_id)

    if not checkpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint with ID '{checkpoint_id}' not found",
        )

    return checkpoint


@router.put(
    "/{checkpoint_id}",
    response_model=CheckpointResponse,
    summary="Update checkpoint details",
    description="Update an existing checkpoint.",
    responses={
        404: {"model": ErrorResponse, "description": "Checkpoint not found"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
    },
)
def update_checkpoint(
    checkpoint_id: str,
    data: CheckpointUpdate,
    session: DBSession,
) -> CheckpointResponse:
    """
    Update a checkpoint by ID.

    - **checkpoint_id**: ID of the checkpoint to update
    - **checkpoint_name**: New name for the checkpoint (optional)
    - **checkpoint_description**: New description for the checkpoint (optional)
    - **human_only_config**: New human-only configuration (optional)
    - **human_interaction**: New human interaction settings (optional)
    - **output_artifacts**: New output artifacts list (optional)

    Only the fields that are provided will be updated. All other fields remain unchanged.
    """
    try:
        return CheckpointService.update_checkpoint(session, checkpoint_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{checkpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete checkpoint",
    description="Delete a checkpoint from its pipeline.",
    responses={
        404: {"model": ErrorResponse, "description": "Checkpoint not found"},
    },
)
def delete_checkpoint(
    checkpoint_id: str,
    session: DBSession,
) -> None:
    """
    Delete a checkpoint by ID.

    This will:
    - Remove the checkpoint from the pipeline
    - Remove the checkpoint from the pipeline's checkpoint_order
    - Delete the checkpoint definition file
    - Delete the checkpoint from the database

    This operation cannot be undone.
    """
    deleted = CheckpointService.delete_checkpoint(session, checkpoint_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint with ID '{checkpoint_id}' not found",
        )

    return None

