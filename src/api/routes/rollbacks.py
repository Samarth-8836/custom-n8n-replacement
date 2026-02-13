"""
Rollback API Routes

Handles rollback operations for pipeline runs.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.services.rollback_service import RollbackService
from src.models.schemas import (
    RollbackRequest,
    RollbackResponse,
    RollbackPointSummary,
    RollbackHistoryResponse,
    ErrorResponse
)


router = APIRouter(prefix="/api/rollbacks", tags=["rollbacks"])


# =============================================================================
# Rollback Endpoints (Slice 11)
# =============================================================================


@router.post("/runs/{run_id}/rollback", response_model=RollbackResponse)
def initiate_rollback(
    run_id: str,
    request: RollbackRequest,
    session: Session = Depends(get_db)
) -> RollbackResponse:
    """
    Initiate a rollback operation.

    - checkpoint_level: Rollback within same run to a specific checkpoint position
    - run_level: Rollback to a previous run version

    Checkpoints AFTER the target position will be deleted and archived.
    """
    try:
        # Get the run to find pipeline_id
        from src.db.models import PipelineRun
        run = session.get(PipelineRun, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found"
            )

        # Get pipeline_id from run
        pipeline_id = run.pipeline_id

        # Create rollback service
        rollback_svc = RollbackService(session, pipeline_id)

        # Perform rollback based on type
        if request.rollback_type == "checkpoint_level":
            result = rollback_svc.checkpoint_level_rollback(
                run_id=run_id,
                target_checkpoint_position=request.target_checkpoint_position,
                user_reason=request.user_reason
            )

            # Get target checkpoint ID
            target_checkpoint = rollback_svc._get_checkpoint_at_position(
                request.target_checkpoint_position
            )

            return RollbackResponse(
                rollback_id=result.get("rollback_id", ""),
                rollback_type="checkpoint_level",
                deleted_executions=result.get("deleted_executions", []),
                archived_artifacts=result.get("archived_artifacts", []),
                target_checkpoint_position=result.get("target_checkpoint_position", 0),
                target_checkpoint_id=target_checkpoint.checkpoint_id if target_checkpoint else "",
                archive_location=result.get("archive_location", ""),
                run_status=result.get("run_status", ""),
                message=result.get("message")
            )

        elif request.rollback_type == "run_level":
            if not request.target_run_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="target_run_id is required for run_level rollback"
                )

            result = rollback_svc.run_level_rollback(
                current_run_id=run_id,
                target_run_id=request.target_run_id,
                target_checkpoint_position=request.target_checkpoint_position,
                user_reason=request.user_reason
            )

            # Get target checkpoint ID
            target_checkpoint = rollback_svc._get_checkpoint_at_position(
                request.target_checkpoint_position
            )

            return RollbackResponse(
                rollback_id=result.get("rollback_id", ""),
                rollback_type="run_level",
                deleted_executions=result.get("deleted_executions", []),
                archived_artifacts=result.get("archived_artifacts", []),
                target_checkpoint_position=result.get("target_checkpoint_position", 0),
                target_checkpoint_id=target_checkpoint.checkpoint_id if target_checkpoint else "",
                archive_location=result.get("archive_location", ""),
                run_status="in_progress",
                message=result.get("message")
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid rollback_type: {request.rollback_type}"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rollback failed: {str(e)}"
        )


@router.get("/runs/{run_id}/rollback-points", response_model=list[RollbackPointSummary])
def get_rollback_points(
    run_id: str,
    session: Session = Depends(get_db)
) -> list[RollbackPointSummary]:
    """
    Get available rollback points for a run.

    Returns all completed checkpoints that can be rolled back to.
    """
    try:
        from src.db.models import PipelineRun

        run = session.get(PipelineRun, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found"
            )

        # Create rollback service
        rollback_svc = RollbackService(session, run.pipeline_id)

        # Get available rollback points
        points = rollback_svc.get_available_rollback_points(run_id)

        return points

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rollback points: {str(e)}"
        )


@router.get("/runs/{run_id}/history", response_model=RollbackHistoryResponse)
def get_rollback_history(
    run_id: str,
    limit: int = 50,
    session: Session = Depends(get_db)
) -> RollbackHistoryResponse:
    """
    Get rollback event history for a run.

    Returns list of all rollback operations performed on this run.
    """
    try:
        from src.db.models import PipelineRun

        run = session.get(PipelineRun, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found"
            )

        # Create rollback service
        rollback_svc = RollbackService(session, run.pipeline_id)

        # Get rollback history
        events = rollback_svc.get_rollback_history(run_id=run_id, limit=limit)

        return RollbackHistoryResponse(
            rollback_events=events,
            total_count=len(events)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rollback history: {str(e)}"
        )


@router.get("/history", response_model=RollbackHistoryResponse)
def get_pipeline_rollback_history(
    pipeline_id: str,
    limit: int = 50,
    session: Session = Depends(get_db)
) -> RollbackHistoryResponse:
    """
    Get rollback event history for an entire pipeline.

    Returns list of all rollback operations across all runs.
    """
    try:
        from src.db.models import Pipeline

        pipeline = session.get(Pipeline, pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pipeline {pipeline_id} not found"
            )

        # Create rollback service
        rollback_svc = RollbackService(session, pipeline_id)

        # Get rollback history for pipeline
        events = rollback_svc.get_rollback_history(limit=limit)

        return RollbackHistoryResponse(
            rollback_events=events,
            total_count=len(events)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rollback history: {str(e)}"
        )


@router.get("/events/{rollback_id}", response_model=dict)
def get_rollback_event(
    rollback_id: str,
    session: Session = Depends(get_db)
) -> dict:
    """
    Get details of a specific rollback event.
    """
    try:
        from src.db.models import RollbackEvent

        event = session.get(RollbackEvent, rollback_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rollback event {rollback_id} not found"
            )

        return {
            "rollback_id": event.rollback_id,
            "rollback_type": event.rollback_type,
            "source_run_id": event.source_run_id,
            "source_run_version": event.source_run_version,
            "target_run_id": event.target_run_id,
            "target_checkpoint_id": event.target_checkpoint_id,
            "target_checkpoint_position": event.target_checkpoint_position,
            "archive_location": event.archive_location,
            "triggered_by": event.triggered_by,
            "user_reason": event.user_reason,
            "rolled_back_items": event.rolled_back_items,
            "created_at": event.created_at.isoformat() if event.created_at else None
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rollback event: {str(e)}"
        )
