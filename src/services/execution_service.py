"""
Checkpoint Execution Service

Business logic for checkpoint execution control.
Handles human-only checkpoint workflow: approve start, submit form, approve complete, request revision.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.file_manager import FileManager
from src.db.models import (
    Artifact,
    CheckpointDefinition,
    CheckpointExecution,
    HumanInteraction,
    Pipeline,
    PipelineRun,
)
from src.utils.logger import get_logger


class ExecutionService:
    """
    Service for managing checkpoint executions.

    Handles the workflow for human-only checkpoints:
    - Approving checkpoint start
    - Submitting form data
    - Approving checkpoint completion (with artifact promotion)
    - Requesting revisions
    - Auto-advancing to next checkpoint
    """

    @staticmethod
    def get_execution(session: Session, execution_id: str) -> Optional[CheckpointExecution]:
        """
        Get a checkpoint execution by ID.

        Args:
            session: Database session
            execution_id: Execution ID

        Returns:
            CheckpointExecution or None
        """
        return session.execute(
            select(CheckpointExecution).where(CheckpointExecution.execution_id == execution_id)
        ).scalar_one_or_none()

    @staticmethod
    def get_execution_detail(session: Session, execution_id: str) -> Optional[dict]:
        """
        Get detailed checkpoint execution information including form configuration.

        Args:
            session: Database session
            execution_id: Execution ID

        Returns:
            Dictionary with execution details or None
        """
        execution = ExecutionService.get_execution(session, execution_id)
        if not execution:
            return None

        # Get checkpoint definition
        checkpoint_def = session.execute(
            select(CheckpointDefinition).where(
                CheckpointDefinition.checkpoint_id == execution.checkpoint_id
            )
        ).scalar_one_or_none()

        # Get run for context
        run = session.execute(
            select(PipelineRun).where(PipelineRun.run_id == execution.run_id)
        ).scalar_one_or_none()

        # Get staged artifacts (files in temp/artifacts_staging)
        staged_artifacts = []
        temp_path = Path(execution.temp_workspace_path)
        staging_dir = temp_path / "artifacts_staging"
        if staging_dir.exists():
            for file_path in staging_dir.iterdir():
                if file_path.is_file():
                    staged_artifacts.append({
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                    })

        # Get submitted form data from human interactions (most recent first)
        form_data = None
        if execution.human_interactions:
            # Get all script_input interactions (form submissions) and sort by timestamp descending
            submit_interactions = [
                hi for hi in execution.human_interactions
                if hi.interaction_type == "script_input"  # Reusing script_input for form submission
            ]
            # Sort by timestamp descending to get the most recent submission
            submit_interactions.sort(key=lambda hi: hi.timestamp, reverse=True)
            submit_interaction = submit_interactions[0] if submit_interactions else None

            if submit_interaction and submit_interaction.user_input:
                try:
                    form_data = json.loads(submit_interaction.user_input)
                except json.JSONDecodeError:
                    form_data = {"raw": submit_interaction.user_input}

        return {
            "execution_id": execution.execution_id,
            "run_id": execution.run_id,
            "checkpoint_id": execution.checkpoint_id,
            "checkpoint_name": checkpoint_def.checkpoint_name if checkpoint_def else None,
            "checkpoint_position": execution.checkpoint_position,
            "status": execution.status,
            "attempt_number": execution.attempt_number,
            "revision_iteration": execution.revision_iteration,
            "max_attempts": execution.max_attempts,
            "max_revision_iterations": execution.max_revision_iterations,
            "created_at": execution.created_at.isoformat() if execution.created_at else None,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "failed_at": execution.failed_at.isoformat() if execution.failed_at else None,
            "temp_workspace_path": execution.temp_workspace_path,
            "permanent_output_path": execution.permanent_output_path,
            "execution_mode": checkpoint_def.execution.get("mode") if checkpoint_def else None,
            "checkpoint_description": checkpoint_def.checkpoint_description if checkpoint_def else None,
            "human_only_config": checkpoint_def.execution.get("human_only_config") if checkpoint_def else None,
            "human_interaction_settings": checkpoint_def.human_interaction if checkpoint_def else None,
            "form_data": form_data,
            "artifacts_staged": staged_artifacts,
            "run_version": run.run_version if run else None,
        }

    @staticmethod
    def approve_start(session: Session, execution_id: str) -> CheckpointExecution:
        """
        Approve the start of a checkpoint execution.

        Transitions status from waiting_approval_to_start to in_progress.

        Args:
            session: Database session
            execution_id: Execution ID

        Returns:
            Updated CheckpointExecution

        Raises:
            ValueError: If execution not found or in wrong state
        """
        execution = ExecutionService.get_execution(session, execution_id)
        if not execution:
            raise ValueError(f"Execution with ID '{execution_id}' not found")

        if execution.status != "waiting_approval_to_start":
            raise ValueError(
                f"Cannot approve start - execution is in status '{execution.status}', "
                f"expected 'waiting_approval_to_start'"
            )

        # Update execution status
        execution.status = "in_progress"
        execution.started_at = datetime.utcnow()

        # Record human interaction
        interaction = HumanInteraction(
            execution_id=execution_id,
            interaction_type="approval_to_start",
            user_input="approved",
            system_response="Checkpoint execution approved and started.",
        )
        session.add(interaction)
        session.flush()

        return execution

    @staticmethod
    def submit_form_data(
        session: Session,
        execution_id: str,
        form_data: dict
    ) -> tuple[CheckpointExecution, list[dict]]:
        """
        Submit form data for a human-only checkpoint.

        Saves form data to staging area and creates artifact if configured.

        Args:
            session: Database session
            execution_id: Execution ID
            form_data: Form field values

        Returns:
            Tuple of (updated CheckpointExecution, list of created artifacts)

        Raises:
            ValueError: If execution not found or not in in_progress state
        """
        execution = ExecutionService.get_execution(session, execution_id)
        if not execution:
            raise ValueError(f"Execution with ID '{execution_id}' not found")

        if execution.status != "in_progress":
            raise ValueError(
                f"Cannot submit form data - execution is in status '{execution.status}', "
                f"expected 'in_progress'"
            )

        # Get checkpoint definition
        checkpoint_def = session.execute(
            select(CheckpointDefinition).where(
                CheckpointDefinition.checkpoint_id == execution.checkpoint_id
            )
        ).scalar_one()

        # Get run for version info
        run = session.execute(
            select(PipelineRun).where(PipelineRun.run_id == execution.run_id)
        ).scalar_one()

        human_only_config = checkpoint_def.execution.get("human_only_config", {})
        artifacts_created = []

        # Save form data to staging
        temp_path = Path(execution.temp_workspace_path)
        staging_dir = temp_path / "artifacts_staging"
        staging_dir.mkdir(parents=True, exist_ok=True)

        # Store form data in human interaction
        interaction = HumanInteraction(
            execution_id=execution_id,
            interaction_type="script_input",  # Reuse for form submission
            user_input=json.dumps(form_data),
            system_response="Form data submitted successfully.",
        )
        session.add(interaction)

        # Save as artifact if configured
        if human_only_config.get("save_as_artifact", False):
            artifact_name = human_only_config.get("artifact_name", "form_data")
            artifact_format = human_only_config.get("artifact_format", "json")

            # During revisions, overwrite the existing artifact instead of creating new ones
            # Find existing artifact with same name for this execution
            existing_artifact = session.execute(
                select(Artifact).where(
                    Artifact.execution_id == execution_id,
                    Artifact.artifact_name == artifact_name
                )
            ).scalar_one_or_none()

            # Create artifact file
            if artifact_format == "json":
                content = json.dumps(form_data, indent=2)
            else:  # markdown
                content = "# Form Data\n\n"
                for key, value in form_data.items():
                    content += f"**{key}**: {value}\n\n"

            # Use existing artifact_id if revising, otherwise create new one
            if existing_artifact:
                artifact_id = existing_artifact.artifact_id
            else:
                artifact_id = str(uuid4())

            artifact_file = staging_dir / f"{artifact_name}_{artifact_id}.{artifact_format}"
            with open(artifact_file, 'w') as f:
                f.write(content)

            # Update existing artifact or create new one
            if existing_artifact:
                existing_artifact.file_path = str(artifact_file)
                existing_artifact.size_bytes = len(content.encode())
                existing_artifact.format = artifact_format
            else:
                artifact = Artifact(
                    execution_id=execution_id,
                    artifact_id=artifact_id,
                    artifact_name=artifact_name,
                    file_path=str(artifact_file),
                    format=artifact_format,
                    size_bytes=len(content.encode()),
                )
                session.add(artifact)
            session.flush()

            artifacts_created.append({
                "artifact_id": artifact_id,
                "artifact_name": artifact_name,
                "file_path": str(artifact_file),
                "format": artifact_format,
                "is_revision": bool(existing_artifact),
            })

        # Check if approval is required to complete
        requires_approval = checkpoint_def.human_interaction.get("requires_approval_to_complete", False)

        if requires_approval:
            execution.status = "waiting_approval_to_complete"
            session.flush()
            return execution, artifacts_created
        else:
            # Auto-complete - promote artifacts and move to next checkpoint
            session.flush()
            result = ExecutionService._complete_checkpoint_and_advance(
                session=session,
                execution=execution,
                promote_artifacts=True
            )
            return execution, artifacts_created

    @staticmethod
    def _complete_checkpoint_and_advance(
        session: Session,
        execution: CheckpointExecution,
        promote_artifacts: bool = True
    ) -> dict:
        """
        Internal helper to complete a checkpoint and advance to the next one.

        This handles the common logic for completing a checkpoint:
        - Promote artifacts from staging to permanent
        - Create next checkpoint execution if applicable
        - Update run status
        """
        # Get checkpoint definition and run
        checkpoint_def = session.execute(
            select(CheckpointDefinition).where(
                CheckpointDefinition.checkpoint_id == execution.checkpoint_id
            )
        ).scalar_one()

        run = session.execute(
            select(PipelineRun).where(PipelineRun.run_id == execution.run_id)
        ).scalar_one()

        # Get pipeline for checkpoint order
        pipeline = session.execute(
            select(Pipeline).where(Pipeline.pipeline_id == run.pipeline_id)
        ).scalar_one()

        # Promote artifacts if requested
        promoted_artifacts = []
        if promote_artifacts:
            fm = FileManager(run.pipeline_id)

            # Get all artifacts for this execution
            artifacts = session.execute(
                select(Artifact).where(Artifact.execution_id == execution.execution_id)
            ).scalars().all()

            for artifact in artifacts:
                # Parse file name to get components
                staging_path = Path(artifact.file_path)
                stem = staging_path.stem  # e.g., "form_data_abc123"
                # Split by last underscore to separate name from ID
                parts = stem.rsplit('_', 1)
                if len(parts) == 2:
                    name_part = parts[0]
                    id_part = parts[1]
                else:
                    name_part = stem
                    id_part = artifact.artifact_id

                artifact_format = staging_path.suffix.lstrip('.')

                try:
                    permanent_path = fm.promote_artifact_to_permanent(
                        execution_id=execution.execution_id,
                        run_version=run.run_version,
                        checkpoint_name=checkpoint_def.checkpoint_name,
                        checkpoint_position=execution.checkpoint_position,
                        artifact_name=name_part,
                        artifact_id=id_part,
                        artifact_format=artifact_format,
                    )

                    # Update artifact record
                    artifact.file_path = str(permanent_path)
                    artifact.promoted_to_permanent_at = datetime.utcnow()

                    promoted_artifacts.append({
                        "artifact_name": artifact.artifact_name,
                        "permanent_path": str(permanent_path),
                    })
                except FileNotFoundError:
                    # Artifact file doesn't exist, skip promotion
                    pass

        # Update execution status
        execution.status = "completed"
        execution.completed_at = datetime.utcnow()

        # Record human interaction
        interaction = HumanInteraction(
            execution_id=execution.execution_id,
            interaction_type="approval_to_complete",
            user_input="approved",
            system_response=f"Checkpoint completed. {len(promoted_artifacts)} artifacts promoted.",
        )
        session.add(interaction)

        # Check if there's a next checkpoint
        current_position = execution.checkpoint_position
        checkpoint_order = pipeline.checkpoint_order
        next_checkpoint_id = None
        next_execution = None

        if current_position + 1 < len(checkpoint_order):
            next_checkpoint_id = checkpoint_order[current_position + 1]

            # Get next checkpoint definition
            next_checkpoint_def = session.execute(
                select(CheckpointDefinition).where(
                    CheckpointDefinition.checkpoint_id == next_checkpoint_id
                )
            ).scalar_one_or_none()

            if next_checkpoint_def:
                # Clean up the PREVIOUS checkpoint's temp workspace before starting next
                # This is critical: temp should be deleted after next checkpoint starts
                fm = FileManager(run.pipeline_id)
                fm.delete_temp_execution_directory(execution.execution_id)

                # Create next checkpoint execution
                from src.services.run_service import RunService
                next_execution = RunService.create_checkpoint_execution(
                    session=session,
                    run=run,
                    checkpoint_def=next_checkpoint_def,
                    position=current_position + 1,
                    file_manager=fm,
                )

                # Update run's current checkpoint
                run.current_checkpoint_id = next_checkpoint_id
                run.current_checkpoint_position = current_position + 1

                # Check if pipeline has auto_advance enabled
                if pipeline.auto_advance:
                    human_interaction = next_checkpoint_def.human_interaction or {}
                    requires_approval = human_interaction.get("requires_approval_to_start", False)

                    if not requires_approval:
                        # Auto-start the next checkpoint
                        next_execution.status = "in_progress"
                        next_execution.started_at = datetime.utcnow()
                else:
                    # Require approval to start
                    next_execution.status = "waiting_approval_to_start"
        else:
            # No more checkpoints - complete the run
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            run.current_checkpoint_id = None
            run.current_checkpoint_position = None

            # Clean up temp workspace
            fm = FileManager(run.pipeline_id)
            fm.delete_temp_execution_directory(execution.execution_id)

            # Update run_info.json with final status
            fm.save_run_info(run.run_version, {
                "run_id": run.run_id,
                "pipeline_id": run.pipeline_id,
                "run_version": run.run_version,
                "status": run.status,
                "created_at": run.created_at.isoformat(),
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "previous_run_id": run.previous_run_id,
                "extends_from_run_version": run.extends_from_run_version,
            })

        session.flush()

        # Log checkpoint completion
        logger = get_logger(run.pipeline_id)
        logger.log_event(
            "checkpoint_completed",
            f"Checkpoint '{checkpoint_def.checkpoint_name}' (position {execution.checkpoint_position}) completed",
            {
                "execution_id": execution.execution_id,
                "checkpoint_position": execution.checkpoint_position,
                "artifacts_promoted": len(promoted_artifacts),
                "next_checkpoint_exists": next_checkpoint_id is not None,
            }
        )

        # Log pipeline completion if finished
        if run.status == "completed":
            logger.log_event(
                "pipeline_completed",
                f"Pipeline run v{run.run_version} completed successfully",
                {
                    "run_id": run.run_id,
                    "run_version": run.run_version,
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                }
            )

        return {
            "execution": execution,
            "promoted_artifacts": promoted_artifacts,
            "next_checkpoint_id": next_checkpoint_id,
            "next_execution_id": next_execution.execution_id if next_execution else None,
            "run_status": run.status,
        }

    @staticmethod
    def approve_complete(
        session: Session,
        execution_id: str,
        promote_artifacts: bool = True
    ) -> dict:
        """
        Approve the completion of a checkpoint execution.

        Promotes artifacts from staging to permanent storage and
        optionally starts the next checkpoint.

        Args:
            session: Database session
            execution_id: Execution ID
            promote_artifacts: Whether to promote artifacts to permanent storage

        Returns:
            Dictionary with execution data and next checkpoint info

        Raises:
            ValueError: If execution not found or in wrong state
        """
        execution = ExecutionService.get_execution(session, execution_id)
        if not execution:
            raise ValueError(f"Execution with ID '{execution_id}' not found")

        if execution.status != "waiting_approval_to_complete":
            raise ValueError(
                f"Cannot approve completion - execution is in status '{execution.status}', "
                f"expected 'waiting_approval_to_complete'"
            )

        # Use the helper function to complete and advance
        return ExecutionService._complete_checkpoint_and_advance(
            session=session,
            execution=execution,
            promote_artifacts=promote_artifacts
        )

    @staticmethod
    def request_revision(
        session: Session,
        execution_id: str,
        feedback: str
    ) -> CheckpointExecution:
        """
        Request a revision for a checkpoint execution.

        Increments revision_iteration and resets status to in_progress.
        Fails if max_revision_iterations is exceeded.

        Args:
            session: Database session
            execution_id: Execution ID
            feedback: Revision feedback from user

        Returns:
            Updated CheckpointExecution

        Raises:
            ValueError: If execution not found, max revisions exceeded, or wrong state
        """
        execution = ExecutionService.get_execution(session, execution_id)
        if not execution:
            raise ValueError(f"Execution with ID '{execution_id}' not found")

        if execution.status not in ("waiting_approval_to_complete",):
            raise ValueError(
                f"Cannot request revision - execution is in status '{execution.status}', "
                f"expected 'waiting_approval_to_complete'"
            )

        # Check revision limit
        if execution.revision_iteration >= execution.max_revision_iterations:
            execution.status = "failed"
            execution.failed_at = datetime.utcnow()

            # Record failure interaction
            interaction = HumanInteraction(
                execution_id=execution_id,
                interaction_type="revision_request",
                user_input=feedback,
                system_response=f"Max revision iterations ({execution.max_revision_iterations}) exceeded. Checkpoint failed.",
            )
            session.add(interaction)
            session.flush()

            raise ValueError(
                f"Max revision iterations ({execution.max_revision_iterations}) exceeded. "
                f"Checkpoint has been marked as failed."
            )

        # Increment revision and reset to in_progress
        execution.revision_iteration += 1
        execution.status = "in_progress"

        # Record revision request
        interaction = HumanInteraction(
            execution_id=execution_id,
            interaction_type="revision_request",
            user_input=feedback,
            system_response=f"Revision #{execution.revision_iteration} requested. Status reset to in_progress.",
        )
        session.add(interaction)
        session.flush()

        return execution

    @staticmethod
    def get_execution_form_fields(session: Session, execution_id: str) -> list[dict]:
        """
        Get the input fields for a human-only checkpoint execution.

        Args:
            session: Database session
            execution_id: Execution ID

        Returns:
            List of input field definitions
        """
        execution = ExecutionService.get_execution(session, execution_id)
        if not execution:
            raise ValueError(f"Execution with ID '{execution_id}' not found")

        checkpoint_def = session.execute(
            select(CheckpointDefinition).where(
                CheckpointDefinition.checkpoint_id == execution.checkpoint_id
            )
        ).scalar_one_or_none()

        if not checkpoint_def:
            return []

        human_only_config = checkpoint_def.execution.get("human_only_config", {})
        return human_only_config.get("input_fields", [])
