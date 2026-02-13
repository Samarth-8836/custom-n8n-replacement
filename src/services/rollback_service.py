"""
Rollback Service

Handles rollback operations for pipeline runs.
Supports checkpoint-level and run-level rollbacks with archiving.
"""

from datetime import datetime
from uuid import uuid4
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from src.db.models import (
    PipelineRun,
    CheckpointExecution,
    RollbackEvent,
    ArchivedItem,
    Artifact,
    Event,
    CheckpointDefinition,
    Pipeline
)
from src.core.file_manager import FileManager
import config


# =============================================================================
# Rollback Service
# =============================================================================


class RollbackService:
    """
    Service for managing rollback operations.

    Rollback allows users to revert to a previous state:
    - Checkpoint-level: Rollback within same run (deletes checkpoints AFTER target)
    - Run-level: Rollback to previous run version (deletes entire runs)

    All deleted items are archived before removal.
    """

    def __init__(self, session: Session, pipeline_id: str):
        """
        Initialize RollbackService for a specific pipeline.

        Args:
            session: SQLAlchemy database session
            pipeline_id: The pipeline UUID
        """
        self.session = session
        self.pipeline_id = pipeline_id
        self.fm = FileManager(pipeline_id)

    # -------------------------------------------------------------------------
    # Checkpoint-Level Rollback (within same run)
    # -------------------------------------------------------------------------

    def checkpoint_level_rollback(
        self,
        run_id: str,
        target_checkpoint_position: int,
        user_reason: Optional[str] = None
    ) -> dict:
        """
        Perform checkpoint-level rollback within the same run.

        Deletes all checkpoint executions AFTER the target position.
        Archives deleted artifacts before deletion.

        Args:
            run_id: The run ID to rollback within
            target_checkpoint_position: Rollback to this checkpoint position
            user_reason: Optional reason for rollback

        Returns:
            dict: Rollback event details with:
                - rollback_id: UUID of rollback event
                - deleted_executions: List of deleted execution IDs
                - archived_artifacts: List of archived artifact paths
                - target_checkpoint_position: Position rolled back to
        """
        # Get the run
        run = self.session.get(PipelineRun, run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        if run.pipeline_id != self.pipeline_id:
            raise ValueError(f"Run {run_id} does not belong to pipeline {self.pipeline_id}")

        # Get checkpoint at target position (from pipeline definition)
        target_checkpoint = self._get_checkpoint_at_position(target_checkpoint_position)
        if not target_checkpoint:
            raise ValueError(f"No checkpoint found at position {target_checkpoint_position}")

        # Find executions to delete (those AFTER target position)
        executions_to_delete = self.session.execute(
            select(CheckpointExecution)
            .where(
                and_(
                    CheckpointExecution.run_id == run_id,
                    CheckpointExecution.checkpoint_position > target_checkpoint_position
                )
            )
            .order_by(CheckpointExecution.checkpoint_position.desc())
        ).scalars().all()

        if not executions_to_delete:
            # Nothing to rollback - already at or before target position
            return {
                "rollback_id": None,
                "deleted_executions": [],
                "archived_artifacts": [],
                "target_checkpoint_position": target_checkpoint_position,
                "message": "No checkpoints to delete - already at or before target position"
            }

        # Generate rollback ID
        rollback_id = str(uuid4())

        # Create archive directory
        archive_dir = self.fm.create_rollback_directory(rollback_id)

        # Collect artifacts to archive
        archived_artifacts = []
        deleted_executions = []

        for execution in executions_to_delete:
            deleted_executions.append(execution.execution_id)

            # Archive artifacts from this execution
            artifacts = self.session.execute(
                select(Artifact)
                .where(Artifact.execution_id == execution.execution_id)
            ).scalars().all()

            for artifact in artifacts:
                archived_path = self._archive_artifact(
                    artifact, archive_dir / "archived_data", run.run_version
                )
                archived_artifacts.append({
                    "artifact_record_id": artifact.artifact_record_id,
                    "artifact_id": artifact.artifact_id,
                    "artifact_name": artifact.artifact_name,
                    "original_path": artifact.file_path,
                    "archived_path": str(archived_path),
                    "size_bytes": artifact.size_bytes
                })

                # Create archived item record
                archived_item = ArchivedItem(
                    rollback_id=rollback_id,
                    item_type="artifact",
                    item_id=artifact.artifact_record_id,
                    original_path=artifact.file_path,
                    archived_path=str(archived_path),
                    size_bytes=artifact.size_bytes
                )
                self.session.add(archived_item)

            # Delete temp workspace if exists
            if execution.temp_workspace_path:
                import shutil
                temp_path = self.fm.base_path / execution.temp_workspace_path
                if temp_path.exists():
                    shutil.rmtree(temp_path)

            # Create archived item for execution
            archived_exec_item = ArchivedItem(
                rollback_id=rollback_id,
                item_type="checkpoint_execution",
                item_id=execution.execution_id,
                original_path=f"execution_{execution.execution_id}",
                archived_path=f"archived_data/execution_{execution.execution_id}",
                size_bytes=0
            )
            self.session.add(archived_exec_item)

            # Delete the execution (cascade will delete logs, interactions, artifacts)
            self.session.delete(execution)

        # Create rollback event record
        rollback_event = RollbackEvent(
            rollback_id=rollback_id,
            source_run_id=run_id,
            source_run_version=run.run_version,
            rollback_type="checkpoint_level",
            target_run_id=run_id,  # Same run for checkpoint-level
            target_checkpoint_id=target_checkpoint.checkpoint_id,
            target_checkpoint_position=target_checkpoint_position,
            archive_location=str(archive_dir),
            triggered_by="user_request",
            user_reason=user_reason,
            rolled_back_items={
                "deleted_runs": [],
                "deleted_checkpoint_executions": [
                    {
                        "execution_id": exec_id,
                        "checkpoint_position": 0  # Will be filled below
                    }
                    for exec_id in deleted_executions
                ],
                "archived_artifacts": archived_artifacts
            }
        )
        self.session.add(rollback_event)

        # Update run status if it was completed
        if run.status == "completed":
            run.status = "in_progress"
            run.completed_at = None

        # Update current checkpoint position
        run.current_checkpoint_id = target_checkpoint.checkpoint_id
        run.current_checkpoint_position = target_checkpoint_position

        # Create event log
        self._create_rollback_event(
            rollback_id=rollback_id,
            run_id=run_id,
            target_checkpoint_id=target_checkpoint.checkpoint_id,
            description=f"Checkpoint-level rollback to position {target_checkpoint_position}"
        )

        self.session.commit()

        return {
            "rollback_id": rollback_id,
            "deleted_executions": deleted_executions,
            "archived_artifacts": archived_artifacts,
            "target_checkpoint_position": target_checkpoint_position,
            "archive_location": str(archive_dir),
            "run_status": run.status
        }

    # -------------------------------------------------------------------------
    # Run-Level Rollback (to previous run version)
    # -------------------------------------------------------------------------

    def run_level_rollback(
        self,
        current_run_id: str,
        target_run_id: str,
        target_checkpoint_position: int,
        user_reason: Optional[str] = None
    ) -> dict:
        """
        Perform run-level rollback to a previous run version.

        Deletes all runs AFTER the target run.
        Sets current run to continue from target run's checkpoint.

        Args:
            current_run_id: The current run ID (initiating rollback)
            target_run_id: The run ID to rollback to
            target_checkpoint_position: Checkpoint position in target run
            user_reason: Optional reason for rollback

        Returns:
            dict: Rollback event details
        """
        # Get both runs
        current_run = self.session.get(PipelineRun, current_run_id)
        target_run = self.session.get(PipelineRun, target_run_id)

        if not current_run:
            raise ValueError(f"Current run {current_run_id} not found")
        if not target_run:
            raise ValueError(f"Target run {target_run_id} not found")
        if current_run.pipeline_id != self.pipeline_id or target_run.pipeline_id != self.pipeline_id:
            raise ValueError(f"Runs do not belong to pipeline {self.pipeline_id}")

        # Get target checkpoint
        target_checkpoint = self._get_checkpoint_at_position(target_checkpoint_position)
        if not target_checkpoint:
            raise ValueError(f"No checkpoint found at position {target_checkpoint_position}")

        # Find runs to delete (those with version > target run version)
        runs_to_delete = self.session.execute(
            select(PipelineRun)
            .where(
                and_(
                    PipelineRun.pipeline_id == self.pipeline_id,
                    PipelineRun.run_version > target_run.run_version
                )
            )
            .order_by(PipelineRun.run_version.desc())
        ).scalars().all()

        # Include current run if it's newer than target
        if current_run.run_version > target_run.run_version:
            if current_run not in runs_to_delete:
                runs_to_delete.insert(0, current_run)

        if not runs_to_delete:
            return {
                "rollback_id": None,
                "deleted_runs": [],
                "archived_artifacts": [],
                "message": "No runs to delete"
            }

        # Generate rollback ID
        rollback_id = str(uuid4())

        # Create archive directory
        archive_dir = self.fm.create_rollback_directory(rollback_id)

        archived_artifacts = []
        deleted_runs = []
        deleted_executions = []

        # Process each run to delete
        for run in runs_to_delete:
            deleted_runs.append({
                "run_id": run.run_id,
                "run_version": run.run_version
            })

            # Get all executions for this run
            executions = self.session.execute(
                select(CheckpointExecution)
                .where(CheckpointExecution.run_id == run.run_id)
            ).scalars().all()

            for execution in executions:
                deleted_executions.append(execution.execution_id)

                # Archive artifacts
                artifacts = self.session.execute(
                    select(Artifact)
                    .where(Artifact.execution_id == execution.execution_id)
                ).scalars().all()

                for artifact in artifacts:
                    archived_path = self._archive_artifact(
                        artifact, archive_dir / "archived_data", run.run_version
                    )
                    archived_artifacts.append({
                        "artifact_record_id": artifact.artifact_record_id,
                        "artifact_id": artifact.artifact_id,
                        "artifact_name": artifact.artifact_name,
                        "original_path": artifact.file_path,
                        "archived_path": str(archived_path),
                        "size_bytes": artifact.size_bytes
                    })

                    # Create archived item record
                    archived_item = ArchivedItem(
                        rollback_id=rollback_id,
                        item_type="artifact",
                        item_id=artifact.artifact_record_id,
                        original_path=artifact.file_path,
                        archived_path=str(archived_path),
                        size_bytes=artifact.size_bytes
                    )
                    self.session.add(archived_item)

                # Delete temp workspace
                if execution.temp_workspace_path:
                    import shutil
                    temp_path = self.fm.base_path / execution.temp_workspace_path
                    if temp_path.exists():
                        shutil.rmtree(temp_path)

                # Create archived execution item
                archived_exec_item = ArchivedItem(
                    rollback_id=rollback_id,
                    item_type="checkpoint_execution",
                    item_id=execution.execution_id,
                    original_path=f"execution_{execution.execution_id}",
                    archived_path=f"archived_data/execution_{execution.execution_id}",
                    size_bytes=0
                )
                self.session.add(archived_exec_item)

                # Delete execution
                self.session.delete(execution)

            # Archive the entire run directory
            import shutil
            run_dir = self.fm.get_run_directory(run.run_version)
            if run_dir.exists():
                archived_run_dir = archive_dir / "archived_data" / f"v{run.run_version}"
                shutil.copytree(run_dir, archived_run_dir)

                # Create archived run item
                archived_run_item = ArchivedItem(
                    rollback_id=rollback_id,
                    item_type="run",
                    item_id=run.run_id,
                    original_path=str(run_dir),
                    archived_path=str(archived_run_dir),
                    size_bytes=0
                )
                self.session.add(archived_run_item)

            # Delete the run
            self.session.delete(run)

        # Create rollback event record
        rollback_event = RollbackEvent(
            rollback_id=rollback_id,
            source_run_id=current_run_id,
            source_run_version=current_run.run_version,
            rollback_type="run_level",
            target_run_id=target_run_id,
            target_checkpoint_id=target_checkpoint.checkpoint_id,
            target_checkpoint_position=target_checkpoint_position,
            archive_location=str(archive_dir),
            triggered_by="user_request",
            user_reason=user_reason,
            rolled_back_items={
                "deleted_runs": deleted_runs,
                "deleted_checkpoint_executions": deleted_executions,
                "archived_artifacts": archived_artifacts
            }
        )
        self.session.add(rollback_event)

        # Update target run status to continue from checkpoint
        if target_run.status == "completed":
            target_run.status = "in_progress"
            target_run.completed_at = None

        target_run.current_checkpoint_id = target_checkpoint.checkpoint_id
        target_run.current_checkpoint_position = target_checkpoint_position

        # Update latest symlink to point to target run
        self.fm.update_latest_symlink(target_run.run_version)

        # Create event log
        self._create_rollback_event(
            rollback_id=rollback_id,
            run_id=target_run_id,
            target_checkpoint_id=target_checkpoint.checkpoint_id,
            description=f"Run-level rollback to v{target_run.run_version} checkpoint {target_checkpoint_position}"
        )

        self.session.commit()

        return {
            "rollback_id": rollback_id,
            "deleted_runs": deleted_runs,
            "archived_artifacts": archived_artifacts,
            "target_run_version": target_run.run_version,
            "target_checkpoint_position": target_checkpoint_position,
            "archive_location": str(archive_dir)
        }

    # -------------------------------------------------------------------------
    # Rollback History and Options
    # -------------------------------------------------------------------------

    def get_rollback_history(self, run_id: Optional[str] = None, limit: int = 50) -> List[dict]:
        """
        Get rollback event history.

        Args:
            run_id: Optional run ID to filter by
            limit: Maximum number of events to return

        Returns:
            List of rollback event summaries
        """
        query = select(RollbackEvent).where(RollbackEvent.source_run_id == self.pipeline_id)

        if run_id:
            query = query.where(RollbackEvent.source_run_id == run_id)

        query = query.order_by(RollbackEvent.created_at.desc()).limit(limit)

        events = self.session.execute(query).scalars().all()

        return [
            {
                "rollback_id": event.rollback_id,
                "rollback_type": event.rollback_type,
                "source_run_version": event.source_run_version,
                "target_run_id": event.target_run_id,
                "target_checkpoint_position": event.target_checkpoint_position,
                "triggered_by": event.triggered_by,
                "user_reason": event.user_reason,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "archive_location": event.archive_location,
                "rolled_back_items": event.rolled_back_items
            }
            for event in events
        ]

    def get_available_rollback_points(self, run_id: str) -> List[dict]:
        """
        Get available rollback points for a run.

        Returns completed checkpoints that can be rolled back to.

        Args:
            run_id: The run ID

        Returns:
            List of available rollback points
        """
        run = self.session.get(PipelineRun, run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        # Get completed executions for this run
        completed_executions = self.session.execute(
            select(CheckpointExecution)
            .where(
                and_(
                    CheckpointExecution.run_id == run_id,
                    CheckpointExecution.status == "completed"
                )
            )
            .order_by(CheckpointExecution.checkpoint_position)
        ).scalars().all()

        # Get pipeline checkpoints to get names
        pipeline = self.session.get(Pipeline, self.pipeline_id)
        checkpoint_map = {cp.checkpoint_id: cp for cp in pipeline.checkpoint_definitions}

        rollback_points = []
        for execution in completed_executions:
            cp_def = checkpoint_map.get(execution.checkpoint_id)
            if cp_def:
                rollback_points.append({
                    "checkpoint_id": execution.checkpoint_id,
                    "checkpoint_name": cp_def.checkpoint_name,
                    "checkpoint_position": execution.checkpoint_position,
                    "execution_id": execution.execution_id,
                    "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                    "is_current": execution.checkpoint_position == run.current_checkpoint_position
                })

        return rollback_points

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _get_checkpoint_at_position(self, position: int) -> Optional[CheckpointDefinition]:
        """Get checkpoint definition at a specific position in pipeline."""
        pipeline = self.session.get(Pipeline, self.pipeline_id)
        if not pipeline:
            return None

        for cp_id in pipeline.checkpoint_order:
            cp = self.session.get(CheckpointDefinition, cp_id)
            if cp and cp.checkpoint_description:  # Has position stored in description for now
                # For Slice 11, we need to map by checking stored positions
                pass

        # Since we don't have position in checkpoint definition yet,
        # we query by checkpoint executions to find which checkpoint is at this position
        # For now, let's get all checkpoints and return by index
        checkpoints = []
        for cp_id in pipeline.checkpoint_order:
            cp = self.session.get(CheckpointDefinition, cp_id)
            if cp:
                checkpoints.append(cp)

        if 0 <= position < len(checkpoints):
            return checkpoints[position]

        return None

    def _archive_artifact(
        self,
        artifact: Artifact,
        archive_base_path,
        run_version: int
    ) -> str:
        """
        Archive an artifact file to the rollback archive directory.

        Args:
            artifact: The Artifact model instance
            archive_base_path: Base path for archive
            run_version: Run version for naming

        Returns:
            str: Path to archived file
        """
        from pathlib import Path
        import shutil

        original_path = Path(artifact.file_path)
        if not original_path.exists():
            return str(archive_base_path / "missing" / original_path.name)

        # Create unique archived path
        archived_path = archive_base_path / "artifacts"
        archived_path.mkdir(parents=True, exist_ok=True)

        # Preserve version in filename
        archived_filename = f"{artifact.artifact_name}_{artifact.artifact_id}_v{run_version}{original_path.suffix}"
        final_path = archived_path / archived_filename

        shutil.copy2(str(original_path), str(final_path))
        return str(final_path)

    def _create_rollback_event(
        self,
        rollback_id: str,
        run_id: str,
        target_checkpoint_id: str,
        description: str
    ) -> None:
        """Create an event log for rollback operation."""
        event = Event(
            event_type="rollback_initiated",
            pipeline_id=self.pipeline_id,
            run_id=run_id,
            checkpoint_id=target_checkpoint_id,
            rollback_id=rollback_id,
            timestamp=datetime.utcnow(),
            description=description,
            event_metadata={}
        )
        self.session.add(event)
