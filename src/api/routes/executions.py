"""
Checkpoint Execution API Routes

API endpoints for checkpoint execution control.
Slice 7: Human-only checkpoint execution workflow.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.models.schemas import (
    ApproveCompleteRequest,
    ApproveStartRequest,
    CheckpointExecutionDetailResponse,
    RequestRevisionRequest,
    SubmitFormDataRequest,
)
from src.services.execution_service import ExecutionService


router = APIRouter(prefix="/api/executions", tags=["executions"])


# Type alias for database session dependency
DBSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/{execution_id}",
    response_model=CheckpointExecutionDetailResponse,
    summary="Get checkpoint execution details",
    description="Get detailed information about a checkpoint execution including form configuration."
)
def get_execution(execution_id: str, session: DBSession):
    """
    Get detailed checkpoint execution information.

    Returns the execution status, form fields (for human-only checkpoints),
    submitted form data, and staged artifacts.
    """
    execution_detail = ExecutionService.get_execution_detail(session, execution_id)

    if not execution_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution with ID '{execution_id}' not found"
        )

    return execution_detail


@router.get(
    "/{execution_id}/form-fields",
    summary="Get checkpoint form fields",
    description="Get the input field definitions for a human-only checkpoint."
)
def get_execution_form_fields(execution_id: str, session: DBSession):
    """
    Get the form field definitions for a human-only checkpoint.

    Returns the list of input fields configured for this checkpoint.
    """
    try:
        form_fields = ExecutionService.get_execution_form_fields(session, execution_id)
        return {"form_fields": form_fields}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{execution_id}/approve-start",
    summary="Approve checkpoint start",
    description="Approve the start of a checkpoint execution. Transitions from waiting_approval_to_start to in_progress."
)
def approve_start(execution_id: str, session: DBSession):
    """
    Approve the start of a checkpoint execution.

    This endpoint should be called when a user approves starting a checkpoint
    that requires approval to start.
    """
    try:
        execution = ExecutionService.approve_start(session, execution_id)
        return {
            "execution_id": execution.execution_id,
            "status": execution.status,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "message": "Checkpoint start approved. Execution is now in progress."
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{execution_id}/submit",
    summary="Submit checkpoint form data",
    description="Submit form data for a human-only checkpoint. Saves to staging and creates artifact if configured."
)
def submit_form_data(
    execution_id: str,
    request: SubmitFormDataRequest,
    session: DBSession
):
    """
    Submit form data for a human-only checkpoint.

    Saves the form data to the staging area and optionally creates an artifact
    if the checkpoint is configured to save form data as an artifact.

    If approval is required to complete, the status changes to waiting_approval_to_complete.
    Otherwise, the checkpoint is auto-completed.
    """
    try:
        execution, artifacts = ExecutionService.submit_form_data(
            session=session,
            execution_id=execution_id,
            form_data=request.form_data
        )

        # Get run status to determine if pipeline completed
        from src.db.models import PipelineRun
        from sqlalchemy import select

        run = session.execute(
            select(PipelineRun).where(PipelineRun.run_id == execution.run_id)
        ).scalar_one_or_none()

        response_data = {
            "execution_id": execution.execution_id,
            "status": execution.status,
            "artifacts_created": artifacts,
            "run_status": run.status if run else None,
            "form_data": request.form_data,  # Include submitted form data in response
            "message": (
                "Form data submitted successfully. "
                f"Status is now '{execution.status}'."
            )
        }

        # Add next checkpoint info if pipeline is still running
        if run and run.status == "in_progress" and execution.status == "completed":
            response_data["next_checkpoint_id"] = run.current_checkpoint_id

        return response_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{execution_id}/approve-complete",
    summary="Approve checkpoint completion",
    description="Approve the completion of a checkpoint execution. Promotes artifacts and optionally starts next checkpoint."
)
def approve_complete(
    execution_id: str,
    session: DBSession,
    request: ApproveCompleteRequest = ApproveCompleteRequest(),
):
    """
    Approve the completion of a checkpoint execution.

    Promotes artifacts from the staging area to permanent storage and
    optionally starts the next checkpoint based on pipeline configuration.

    Returns information about:
    - The completed execution
    - Promoted artifacts
    - Next checkpoint (if any)
    - Updated run status
    """
    try:
        result = ExecutionService.approve_complete(
            session=session,
            execution_id=execution_id,
            promote_artifacts=request.promote_artifacts
        )

        response_data = {
            "execution_id": result["execution"].execution_id,
            "status": result["execution"].status,
            "completed_at": result["execution"].completed_at.isoformat() if result["execution"].completed_at else None,
            "promoted_artifacts": result["promoted_artifacts"],
            "run_status": result["run_status"],
            "message": "Checkpoint completed successfully.",
        }

        if result["next_checkpoint_id"]:
            response_data["next_checkpoint_id"] = result["next_checkpoint_id"]
            response_data["next_execution_id"] = result["next_execution_id"]

            if result["run_status"] == "completed":
                response_data["message"] += " Pipeline completed!"
            else:
                response_data["message"] += " Next checkpoint created."
        else:
            response_data["message"] += " Pipeline completed!"

        return response_data

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{execution_id}/request-revision",
    summary="Request checkpoint revision",
    description="Request a revision for a checkpoint. Resets to in_progress and increments revision counter."
)
def request_revision(
    execution_id: str,
    request: RequestRevisionRequest,
    session: DBSession
):
    """
    Request a revision for a checkpoint execution.

    Increments the revision iteration counter and resets the status to in_progress.
    Fails if max_revision_iterations is exceeded.
    """
    try:
        execution = ExecutionService.request_revision(
            session=session,
            execution_id=execution_id,
            feedback=request.feedback
        )

        return {
            "execution_id": execution.execution_id,
            "status": execution.status,
            "revision_iteration": execution.revision_iteration,
            "max_revision_iterations": execution.max_revision_iterations,
            "message": f"Revision #{execution.revision_iteration} requested. Status reset to in_progress."
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
