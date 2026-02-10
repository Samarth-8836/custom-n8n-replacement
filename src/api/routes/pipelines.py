"""
Pipeline API Routes

Routes for pipeline CRUD operations.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.models.schemas import (
    ErrorResponse,
    PipelineCreate,
    PipelineDetailResponse,
    PipelineListResponse,
    PipelineResponse,
    PipelineUpdate,
)
from src.services.pipeline_service import PipelineService

router = APIRouter()


# Dependency to get database session
DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=PipelineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new pipeline",
    description="Create a new pipeline with the given name and description.",
    responses={
        400: {"model": ErrorResponse, "description": "Pipeline with same name already exists"},
    },
)
def create_pipeline(
    data: PipelineCreate,
    session: DBSession,
) -> PipelineResponse:
    """
    Create a new pipeline.

    - **pipeline_name**: Name of the pipeline (required, 1-255 characters)
    - **pipeline_description**: Description of the pipeline (optional, max 5000 characters)
    - **auto_advance**: Whether to auto-start next checkpoint (default: false)
    """
    try:
        return PipelineService.create_pipeline(session, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=PipelineListResponse,
    summary="List all pipelines",
    description="Get a paginated list of all pipelines.",
)
def list_pipelines(
    session: DBSession,
    page: Annotated[int, Query(ge=1, description="Page number (1-indexed)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Number of items per page")] = 50,
) -> PipelineListResponse:
    """List all pipelines with pagination."""
    pipelines, total_count = PipelineService.list_pipelines(session, page, page_size)

    return PipelineListResponse(
        pipelines=pipelines,
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{pipeline_id}",
    response_model=PipelineDetailResponse,
    summary="Get pipeline details",
    description="Get detailed information about a specific pipeline including its checkpoints.",
    responses={
        404: {"model": ErrorResponse, "description": "Pipeline not found"},
    },
)
def get_pipeline(
    pipeline_id: str,
    session: DBSession,
) -> PipelineDetailResponse:
    """
    Get a pipeline by ID.

    Returns detailed information including:
    - Pipeline metadata
    - Checkpoint definitions
    - Checkpoint count
    """
    pipeline = PipelineService.get_pipeline_detail(session, pipeline_id)

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline with ID '{pipeline_id}' not found",
        )

    return pipeline


@router.put(
    "/{pipeline_id}",
    response_model=PipelineResponse,
    summary="Update a pipeline",
    description="Update pipeline name, description, or auto_advance setting.",
    responses={
        400: {"model": ErrorResponse, "description": "Name conflict or validation error"},
        404: {"model": ErrorResponse, "description": "Pipeline not found"},
    },
)
def update_pipeline(
    pipeline_id: str,
    data: PipelineUpdate,
    session: DBSession,
) -> PipelineResponse:
    """
    Update a pipeline.

    Can update:
    - **pipeline_name**: New name for the pipeline
    - **pipeline_description**: New description
    - **auto_advance**: Auto-advance setting

    Note: Changes to checkpoint_order create a new pipeline version.
    """
    try:
        pipeline = PipelineService.update_pipeline(session, pipeline_id, data)

        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pipeline with ID '{pipeline_id}' not found",
            )

        return pipeline
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{pipeline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a pipeline",
    description="Delete a pipeline and all its associated data.",
    responses={
        404: {"model": ErrorResponse, "description": "Pipeline not found"},
    },
)
def delete_pipeline(
    pipeline_id: str,
    session: DBSession,
) -> None:
    """
    Delete a pipeline.

    This will delete:
    - Pipeline definition
    - All checkpoint definitions
    - All runs and executions
    - Associated artifacts

    In production, data would be archived before deletion.
    """
    deleted = PipelineService.delete_pipeline(session, pipeline_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline with ID '{pipeline_id}' not found",
        )


@router.put(
    "/{pipeline_id}/checkpoint-order",
    response_model=PipelineResponse,
    summary="Reorder checkpoints",
    description="Update the order of checkpoints in a pipeline.",
    responses={
        404: {"model": ErrorResponse, "description": "Pipeline not found"},
        400: {"model": ErrorResponse, "description": "Invalid checkpoint order"},
    },
)
def reorder_checkpoints(
    pipeline_id: str,
    checkpoint_order: list[str],
    session: DBSession,
) -> PipelineResponse:
    """
    Reorder checkpoints in a pipeline.

    - **checkpoint_order**: New ordered list of checkpoint IDs

    All existing checkpoints must be included in the list.
    Invalid or missing checkpoint IDs will result in an error.

    Note: Reordering checkpoints increments the pipeline definition version.
    """
    try:
        return PipelineService.reorder_checkpoints(session, pipeline_id, checkpoint_order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
