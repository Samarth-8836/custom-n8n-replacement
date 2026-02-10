"""
Pipeline Run Service

Business logic for pipeline run management.
Handles run creation, status tracking, and checkpoint execution initialization.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.file_manager import FileManager
from src.db.models import (
    CheckpointDefinition,
    CheckpointExecution,
    HumanInteraction,
    Pipeline,
    PipelineRun,
)


class RunService:
    """
    Service for managing pipeline runs.

    Handles creating new runs, finding previous runs,
    and initializing checkpoint executions.
    """

    @staticmethod
    def get_latest_valid_run(session: Session, pipeline_id: str) -> Optional[PipelineRun]:
        """
        Get the latest valid (non-archived, non-errored) run for a pipeline.

        Args:
            session: Database session
            pipeline_id: Pipeline ID

        Returns:
            Latest valid PipelineRun or None
        """
        # Get the latest run by version number
        # For now, we consider all runs as valid (archiving is in Phase 3)
        result = session.execute(
            select(PipelineRun)
            .where(PipelineRun.pipeline_id == pipeline_id)
            .order_by(PipelineRun.run_version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def get_next_run_version(session: Session, pipeline_id: str) -> int:
        """
        Get the next run version number for a pipeline.

        Args:
            session: Database session
            pipeline_id: Pipeline ID

        Returns:
            Next run version number (1 if no runs exist)
        """
        result = session.execute(
            select(func.max(PipelineRun.run_version))
            .where(PipelineRun.pipeline_id == pipeline_id)
        )
        max_version = result.scalar()
        return (max_version or 0) + 1

    @staticmethod
    def create_run(
        session: Session,
        pipeline_id: str,
        extends_from_run_id: Optional[str] = None
    ) -> PipelineRun:
        """
        Create a new pipeline run.

        Args:
            session: Database session
            pipeline_id: Pipeline ID to create run for
            extends_from_run_id: Optional run ID to extend from

        Returns:
            Created PipelineRun

        Raises:
            ValueError: If pipeline not found or has no checkpoints
        """
        # Get pipeline
        pipeline = session.execute(
            select(Pipeline).where(Pipeline.pipeline_id == pipeline_id)
        ).scalar_one_or_none()

        if not pipeline:
            raise ValueError(f"Pipeline with ID '{pipeline_id}' not found")

        # Check if pipeline has checkpoints
        if not pipeline.checkpoint_order:
            raise ValueError(f"Pipeline has no checkpoints. Add at least one checkpoint before starting a run.")

        # Determine previous run
        previous_run: Optional[PipelineRun] = None

        if extends_from_run_id:
            # Use the specified run
            previous_run = session.execute(
                select(PipelineRun).where(PipelineRun.run_id == extends_from_run_id)
            ).scalar_one_or_none()
            if not previous_run:
                raise ValueError(f"Run with ID '{extends_from_run_id}' not found")
            if previous_run.pipeline_id != pipeline_id:
                raise ValueError(f"Run '{extends_from_run_id}' does not belong to pipeline '{pipeline_id}'")
        else:
            # Find the latest valid run automatically
            previous_run = RunService.get_latest_valid_run(session, pipeline_id)

        # Get next run version
        run_version = RunService.get_next_run_version(session, pipeline_id)

        # Create the run
        run = PipelineRun(
            pipeline_id=pipeline_id,
            run_version=run_version,
            status="not_started",
            current_checkpoint_id=None,
            current_checkpoint_position=None,
            previous_run_id=previous_run.run_id if previous_run else None,
            extends_from_run_version=previous_run.run_version if previous_run else None,
        )

        session.add(run)
        session.flush()

        # Initialize file manager for the pipeline
        fm = FileManager(pipeline_id)
        fm.create_run_directory(run_version)

        # Save run info to file system
        fm.save_run_info(run_version, {
            "run_id": run.run_id,
            "pipeline_id": pipeline_id,
            "run_version": run_version,
            "status": run.status,
            "created_at": run.created_at.isoformat(),
            "previous_run_id": run.previous_run_id,
            "extends_from_run_version": run.extends_from_run_version,
        })

        return run

    @staticmethod
    def start_run(session: Session, run_id: str) -> PipelineRun:
        """
        Start a pipeline run by creating the first checkpoint execution.

        Args:
            session: Database session
            run_id: Run ID to start

        Returns:
            Updated PipelineRun with first checkpoint execution created

        Raises:
            ValueError: If run not found, already started, or has no checkpoints
        """
        # Get the run
        run = session.execute(
            select(PipelineRun).where(PipelineRun.run_id == run_id)
        ).scalar_one_or_none()

        if not run:
            raise ValueError(f"Run with ID '{run_id}' not found")

        if run.status != "not_started":
            raise ValueError(f"Run has already been started (current status: {run.status})")

        # Get pipeline to access checkpoint_order
        pipeline = session.execute(
            select(Pipeline).where(Pipeline.pipeline_id == run.pipeline_id)
        ).scalar_one()

        if not pipeline.checkpoint_order:
            raise ValueError(f"Pipeline has no checkpoints")

        # Get the first checkpoint ID from checkpoint_order
        first_checkpoint_id = pipeline.checkpoint_order[0]

        # Get the checkpoint definition
        checkpoint_def = session.execute(
            select(CheckpointDefinition).where(
                CheckpointDefinition.checkpoint_id == first_checkpoint_id
            )
        ).scalar_one_or_none()

        if not checkpoint_def:
            raise ValueError(f"First checkpoint '{first_checkpoint_id}' not found")

        # Initialize file manager
        fm = FileManager(run.pipeline_id)

        # Create the first checkpoint execution
        execution = RunService.create_checkpoint_execution(
            session=session,
            run=run,
            checkpoint_def=checkpoint_def,
            position=0,
            file_manager=fm,
        )

        # Update run status
        run.status = "in_progress"
        run.current_checkpoint_id = execution.checkpoint_id
        run.current_checkpoint_position = 0
        run.started_at = datetime.utcnow()

        session.flush()

        # Update latest symlink
        fm.update_latest_symlink(run.run_version)

        return run

    @staticmethod
    def create_checkpoint_execution(
        session: Session,
        run: PipelineRun,
        checkpoint_def: CheckpointDefinition,
        position: int,
        file_manager: FileManager,
    ) -> CheckpointExecution:
        """
        Create a checkpoint execution for a run.

        Args:
            session: Database session
            run: The PipelineRun
            checkpoint_def: The CheckpointDefinition
            position: Checkpoint position in pipeline
            file_manager: FileManager instance

        Returns:
            Created CheckpointExecution
        """
        execution_id = str(uuid4())

        # Create temp workspace
        temp_dir = file_manager.create_temp_execution_directory(execution_id)

        # Create permanent output directory
        permanent_dir = file_manager.create_checkpoint_outputs_directory(
            run.run_version,
            checkpoint_def.checkpoint_name,
            position,
        )

        # Get human interaction settings for retry/revision limits
        human_interaction = checkpoint_def.human_interaction or {}

        # Get retry config for max attempts
        retry_config = checkpoint_def.execution.get("retry_config", {})
        max_attempts = retry_config.get("max_auto_retries", 0) + 1  # +1 for initial attempt

        # Create execution
        execution = CheckpointExecution(
            execution_id=execution_id,
            run_id=run.run_id,
            checkpoint_id=checkpoint_def.checkpoint_id,
            checkpoint_position=position,
            status="pending",
            attempt_number=1,
            max_attempts=max_attempts,
            revision_iteration=0,
            max_revision_iterations=human_interaction.get("max_revision_iterations", 3),
            temp_workspace_path=str(temp_dir),
            permanent_output_path=str(permanent_dir),
        )

        session.add(execution)
        session.flush()

        # Check if approval is required to start
        requires_approval = human_interaction.get("requires_approval_to_start", False)

        if requires_approval:
            execution.status = "waiting_approval_to_start"

            # Create human interaction record
            interaction = HumanInteraction(
                execution_id=execution_id,
                interaction_type="approval_to_start",
                user_input=None,
                system_response="Waiting for user approval to start this checkpoint.",
            )
            session.add(interaction)
        else:
            # Auto-start - will be handled by execution flow (Slice 7)
            execution.status = "in_progress"
            execution.started_at = datetime.utcnow()

        session.flush()

        return execution

    @staticmethod
    def get_run(session: Session, run_id: str) -> Optional[PipelineRun]:
        """
        Get a pipeline run by ID.

        Args:
            session: Database session
            run_id: Run ID

        Returns:
            PipelineRun or None
        """
        return session.execute(
            select(PipelineRun).where(PipelineRun.run_id == run_id)
        ).scalar_one_or_none()

    @staticmethod
    def get_run_detail(session: Session, run_id: str) -> Optional[dict]:
        """
        Get detailed pipeline run information including checkpoint executions.

        Args:
            session: Database session
            run_id: Run ID

        Returns:
            Dictionary with run details or None
        """
        run = RunService.get_run(session, run_id)

        if not run:
            return None

        # Get pipeline for name
        pipeline = session.execute(
            select(Pipeline).where(Pipeline.pipeline_id == run.pipeline_id)
        ).scalar_one_or_none()

        # Get checkpoint executions
        executions = session.execute(
            select(CheckpointExecution)
            .where(CheckpointExecution.run_id == run_id)
            .order_by(CheckpointExecution.checkpoint_position)
        ).scalars().all()

        # Build checkpoint execution summaries
        execution_summaries = []
        for exec_obj in executions:
            checkpoint_def = session.execute(
                select(CheckpointDefinition).where(
                    CheckpointDefinition.checkpoint_id == exec_obj.checkpoint_id
                )
            ).scalar_one_or_none()

            execution_summaries.append({
                "execution_id": exec_obj.execution_id,
                "checkpoint_id": exec_obj.checkpoint_id,
                "checkpoint_name": checkpoint_def.checkpoint_name if checkpoint_def else None,
                "checkpoint_position": exec_obj.checkpoint_position,
                "status": exec_obj.status,
                "attempt_number": exec_obj.attempt_number,
                "revision_iteration": exec_obj.revision_iteration,
                "created_at": exec_obj.created_at.isoformat() if exec_obj.created_at else None,
                "started_at": exec_obj.started_at.isoformat() if exec_obj.started_at else None,
                "completed_at": exec_obj.completed_at.isoformat() if exec_obj.completed_at else None,
            })

        # Count completed checkpoints
        completed_count = sum(
            1 for e in executions
            if e.status in ("completed", "waiting_approval_to_complete")
        )

        return {
            "run_id": run.run_id,
            "pipeline_id": run.pipeline_id,
            "pipeline_name": pipeline.pipeline_name if pipeline else None,
            "run_version": run.run_version,
            "status": run.status,
            "current_checkpoint_id": run.current_checkpoint_id,
            "current_checkpoint_position": run.current_checkpoint_position,
            "previous_run_id": run.previous_run_id,
            "extends_from_run_version": run.extends_from_run_version,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "paused_at": run.paused_at.isoformat() if run.paused_at else None,
            "last_resumed_at": run.last_resumed_at.isoformat() if run.last_resumed_at else None,
            "checkpoint_count": len(pipeline.checkpoint_order) if pipeline else 0,
            "completed_checkpoints": completed_count,
            "checkpoint_executions": execution_summaries,
        }

    @staticmethod
    def list_runs_for_pipeline(
        session: Session,
        pipeline_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> list[PipelineRun]:
        """
        List all runs for a pipeline.

        Args:
            session: Database session
            pipeline_id: Pipeline ID
            limit: Max number of results
            offset: Number of results to skip

        Returns:
            List of PipelineRun objects
        """
        result = session.execute(
            select(PipelineRun)
            .where(PipelineRun.pipeline_id == pipeline_id)
            .order_by(PipelineRun.run_version.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    def count_runs_for_pipeline(session: Session, pipeline_id: str) -> int:
        """
        Count total runs for a pipeline.

        Args:
            session: Database session
            pipeline_id: Pipeline ID

        Returns:
            Total count of runs
        """
        result = session.execute(
            select(func.count(PipelineRun.run_id))
            .where(PipelineRun.pipeline_id == pipeline_id)
        )
        return result.scalar()
