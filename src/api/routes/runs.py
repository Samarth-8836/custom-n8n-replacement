"""
Pipeline Runs Routes

API endpoints for managing pipeline runs.
Slice 6: Create runs, list runs, get run details.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.models.schemas import (
    CheckpointExecutionSummary,
    PipelineRunCreate,
    PipelineRunDetailResponse,
    PipelineRunListResponse,
    PipelineRunResponse,
)
from src.services.run_service import RunService


# Create router
router = APIRouter()


@router.post(
    "",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new pipeline run",
    description="Create a new pipeline run. Returns the run in 'not_started' status.",
)
def create_run(
    pipeline_id: str = Query(..., description="Pipeline ID to create run for"),
    data: PipelineRunCreate | None = None,
    session: Session = Depends(get_db),
) -> PipelineRunResponse:
    """
    Create a new pipeline run.

    The run starts in 'not_started' status. Use POST /api/runs/{run_id}/start
    to actually start the run (creates first checkpoint execution).
    """
    try:
        extends_from_run_id = data.extends_from_run_id if data else None
        run = RunService.create_run(session, pipeline_id, extends_from_run_id)
        session.commit()

        # Get pipeline name for response
        from src.db.models import Pipeline
        pipeline = session.get(Pipeline, pipeline_id)

        response = PipelineRunResponse(
            run_id=run.run_id,
            pipeline_id=run.pipeline_id,
            run_version=run.run_version,
            status=run.status,
            current_checkpoint_id=run.current_checkpoint_id,
            current_checkpoint_position=run.current_checkpoint_position,
            previous_run_id=run.previous_run_id,
            extends_from_run_version=run.extends_from_run_version,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            paused_at=run.paused_at,
            last_resumed_at=run.last_resumed_at,
            pipeline_name=pipeline.pipeline_name if pipeline else None,
            checkpoint_count=len(pipeline.checkpoint_order) if pipeline else 0,
            completed_checkpoints=0,
        )
        return response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{run_id}/start",
    response_model=PipelineRunDetailResponse,
    summary="Start a pipeline run",
    description="Start a pipeline run by creating the first checkpoint execution.",
)
def start_run(
    run_id: str,
    session: Session = Depends(get_db),
) -> PipelineRunDetailResponse:
    """
    Start a pipeline run.

    This creates the first checkpoint execution and updates the run status
    to 'in_progress'. The checkpoint will be in 'pending' or 'waiting_approval_to_start'
    state depending on the checkpoint configuration.
    """
    try:
        run = RunService.start_run(session, run_id)
        session.commit()

        return RunService.get_run_detail(session, run_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=PipelineRunListResponse,
    summary="List pipeline runs",
    description="List all runs for a specific pipeline.",
)
def list_runs(
    pipeline_id: str = Query(..., description="Pipeline ID to list runs for"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    session: Session = Depends(get_db),
) -> PipelineRunListResponse:
    """
    List all runs for a pipeline.

    Returns runs ordered by version (newest first).
    """
    runs = RunService.list_runs_for_pipeline(
        session, pipeline_id, limit=page_size, offset=(page - 1) * page_size
    )
    total_count = RunService.count_runs_for_pipeline(session, pipeline_id)

    from src.models.schemas import PipelineRunSummary

    return PipelineRunListResponse(
        runs=[
            PipelineRunSummary(
                run_id=r.run_id,
                run_version=r.run_version,
                status=r.status,
                created_at=r.created_at,
                completed_at=r.completed_at,
            )
            for r in runs
        ],
        total_count=total_count,
    )


@router.get(
    "/{run_id}",
    response_model=PipelineRunDetailResponse,
    summary="Get pipeline run details",
    description="Get detailed information about a specific pipeline run including checkpoint executions.",
)
def get_run(
    run_id: str,
    session: Session = Depends(get_db),
) -> PipelineRunDetailResponse:
    """
    Get detailed information about a pipeline run.

    Includes checkpoint execution history and current status.
    """
    detail = RunService.get_run_detail(session, run_id)

    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with ID '{run_id}' not found",
        )

    # Convert checkpoint executions to proper schema objects
    checkpoint_executions = [
        CheckpointExecutionSummary(**ce) for ce in detail.pop("checkpoint_executions", [])
    ]

    return PipelineRunDetailResponse(
        checkpoint_executions=checkpoint_executions,
        **detail,
    )
