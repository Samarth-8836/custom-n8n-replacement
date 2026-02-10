"""
Checkpoint Service

Business logic for checkpoint CRUD operations.
"""

from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from src.core.file_manager import FileManager
from src.db.models import CheckpointDefinition, Event, Pipeline
from src.models.schemas import (
    CheckpointCreate,
    CheckpointUpdate,
    CheckpointResponse,
    CheckpointSummary,
    HumanInteractionResponse,
    HumanOnlyConfigResponse,
    HumanOnlyConfigUpdate,
    InputFieldResponse,
    OutputArtifactResponse,
)
from src.utils.logger import get_logger


class CheckpointService:
    """
    Service for managing checkpoint CRUD operations.
    """

    @staticmethod
    def create_checkpoint(
        session: Session,
        pipeline_id: str,
        data: CheckpointCreate,
    ) -> CheckpointResponse:
        """
        Create a new checkpoint for a pipeline.

        Args:
            session: Database session
            pipeline_id: Pipeline UUID
            data: Checkpoint creation data

        Returns:
            CheckpointResponse: Created checkpoint data

        Raises:
            ValueError: If pipeline not found
        """
        # Verify pipeline exists
        pipeline = session.execute(
            select(Pipeline).where(Pipeline.pipeline_id == pipeline_id)
        ).scalar_one_or_none()

        if not pipeline:
            raise ValueError(f"Pipeline with ID '{pipeline_id}' not found")

        # Generate checkpoint ID
        checkpoint_id = str(uuid4())

        # Generate IDs for input fields and output artifacts
        input_fields_with_ids = []
        for field in data.human_only_config.input_fields:
            input_fields_with_ids.append({
                "field_id": str(uuid4()),
                "name": field.name,
                "type": field.type,
                "label": field.label,
                "required": field.required,
                "default": field.default,
                "validation": field.validation,
            })

        output_artifacts_with_ids = []
        for artifact in data.output_artifacts:
            output_artifacts_with_ids.append({
                "artifact_id": str(uuid4()),
                "name": artifact.name,
                "format": artifact.format,
                "description": artifact.description,
                "schema": None,  # No schema in Slice 4
            })

        # Build the checkpoint definition JSON structure
        # For Slice 4, we only support human_only mode
        execution_config = {
            "mode": data.execution_mode,
            "human_only_config": {
                "instructions": data.human_only_config.instructions,
                "input_fields": input_fields_with_ids,
                "save_as_artifact": data.human_only_config.save_as_artifact,
                "artifact_name": data.human_only_config.artifact_name,
                "artifact_format": data.human_only_config.artifact_format,
            },
        }

        # Create checkpoint model
        checkpoint = CheckpointDefinition(
            checkpoint_id=checkpoint_id,
            pipeline_id=pipeline_id,
            checkpoint_name=data.checkpoint_name,
            checkpoint_description=data.checkpoint_description,
            dependencies={
                "required_checkpoint_ids": [],  # Empty for Slice 4
            },
            inputs={
                "include_previous_version": False,  # Default for Slice 4
                "include_checkpoint_outputs": [],  # Empty for Slice 4
            },
            execution=execution_config,
            human_interaction={
                "requires_approval_to_start": data.human_interaction.requires_approval_to_start,
                "requires_approval_to_complete": data.human_interaction.requires_approval_to_complete,
                "max_revision_iterations": data.human_interaction.max_revision_iterations,
            },
            output={
                "artifacts": output_artifacts_with_ids,
                "validation": {
                    "enabled": False,  # No validation in Slice 4
                },
            },
            instructions={
                "system_prompt": None,
                "task_prompt": None,
                "examples": [],
                "injection_points": {
                    "previous_version_context": "before_task_prompt",
                    "checkpoint_references": "before_task_prompt",
                },
                "injection_format": {
                    "include_file_paths": True,
                    "include_file_contents": True,
                    "content_format": "markdown",
                },
            },
        )

        session.add(checkpoint)
        session.flush()

        # Update pipeline's checkpoint_order
        checkpoint_order = pipeline.checkpoint_order or []
        if not isinstance(checkpoint_order, list):
            checkpoint_order = []
        checkpoint_order.append(checkpoint_id)
        pipeline.checkpoint_order = checkpoint_order
        flag_modified(pipeline, "checkpoint_order")  # Mark JSON column as modified

        # Save checkpoint definition to file system
        file_manager = FileManager(pipeline_id)
        file_manager.save_checkpoint_definition(checkpoint_id, checkpoint.to_dict())

        # Update pipeline definition file
        file_manager.save_pipeline_definition(pipeline.to_dict())

        # Log event
        event = Event(
            event_type="checkpoint_created",
            pipeline_id=pipeline_id,
            checkpoint_id=checkpoint_id,
            description=f"Checkpoint '{data.checkpoint_name}' created",
            event_metadata={
                "checkpoint_name": data.checkpoint_name,
                "execution_mode": data.execution_mode,
            }
        )
        session.add(event)

        session.commit()
        session.refresh(checkpoint)

        # Log to system.log
        logger = get_logger(pipeline_id)
        logger.log_event(
            "checkpoint_created",
            f"Checkpoint '{data.checkpoint_name}' created",
            {
                "checkpoint_id": checkpoint_id,
                "checkpoint_name": data.checkpoint_name,
                "execution_mode": data.execution_mode,
            }
        )

        # Build response
        return CheckpointService._build_checkpoint_response(checkpoint)

    @staticmethod
    def get_checkpoint(
        session: Session,
        checkpoint_id: str,
    ) -> Optional[CheckpointResponse]:
        """
        Get a checkpoint by ID.

        Args:
            session: Database session
            checkpoint_id: Checkpoint UUID

        Returns:
            CheckpointResponse: Checkpoint data or None if not found
        """
        checkpoint = session.execute(
            select(CheckpointDefinition).where(CheckpointDefinition.checkpoint_id == checkpoint_id)
        ).scalar_one_or_none()

        if not checkpoint:
            return None

        return CheckpointService._build_checkpoint_response(checkpoint)

    @staticmethod
    def get_checkpoints_for_pipeline(
        session: Session,
        pipeline_id: str,
    ) -> list[CheckpointSummary]:
        """
        Get all checkpoints for a pipeline.

        Args:
            session: Database session
            pipeline_id: Pipeline UUID

        Returns:
            list of checkpoint summaries
        """
        checkpoints = session.execute(
            select(CheckpointDefinition)
            .where(CheckpointDefinition.pipeline_id == pipeline_id)
            .order_by(CheckpointDefinition.created_at)
        ).scalars().all()

        return [
            CheckpointSummary(
                checkpoint_id=cp.checkpoint_id,
                checkpoint_name=cp.checkpoint_name,
                checkpoint_description=cp.checkpoint_description,
                execution_mode=cp.execution.get("mode", "unknown") if cp.execution else "unknown",
                created_at=cp.created_at,
                updated_at=cp.updated_at,
            )
            for cp in checkpoints
        ]

    @staticmethod
    def _build_checkpoint_response(checkpoint: CheckpointDefinition) -> CheckpointResponse:
        """
        Build a CheckpointResponse from a CheckpointDefinition model.

        Args:
            checkpoint: CheckpointDefinition model

        Returns:
            CheckpointResponse
        """
        execution = checkpoint.execution or {}
        human_only_config = execution.get("human_only_config", {})

        # Build input field responses
        input_fields = []
        for field in human_only_config.get("input_fields", []):
            input_fields.append(InputFieldResponse(
                field_id=field.get("field_id", str(uuid4())),
                name=field.get("name", ""),
                type=field.get("type", "text"),
                label=field.get("label", ""),
                required=field.get("required", True),
                default=field.get("default"),
                validation=field.get("validation"),
            ))

        # Build output artifact responses
        output_artifacts = []
        for artifact in (checkpoint.output or {}).get("artifacts", []):
            output_artifacts.append(OutputArtifactResponse(
                artifact_id=artifact.get("artifact_id", str(uuid4())),
                name=artifact.get("name", ""),
                format=artifact.get("format", "json"),
                description=artifact.get("description"),
            ))

        return CheckpointResponse(
            checkpoint_id=checkpoint.checkpoint_id,
            pipeline_id=checkpoint.pipeline_id,
            checkpoint_name=checkpoint.checkpoint_name,
            checkpoint_description=checkpoint.checkpoint_description,
            execution_mode=execution.get("mode", "human_only"),
            human_only_config=HumanOnlyConfigResponse(
                instructions=human_only_config.get("instructions", ""),
                input_fields=input_fields,
                save_as_artifact=human_only_config.get("save_as_artifact", False),
                artifact_name=human_only_config.get("artifact_name"),
                artifact_format=human_only_config.get("artifact_format", "json"),
            ),
            human_interaction=HumanInteractionResponse(
                requires_approval_to_start=(checkpoint.human_interaction or {}).get("requires_approval_to_start", False),
                requires_approval_to_complete=(checkpoint.human_interaction or {}).get("requires_approval_to_complete", False),
                max_revision_iterations=(checkpoint.human_interaction or {}).get("max_revision_iterations", 3),
            ),
            output_artifacts=output_artifacts,
            dependencies=checkpoint.dependencies or {},
            inputs=checkpoint.inputs or {},
            execution=checkpoint.execution or {},
            output=checkpoint.output or {},
            instructions=checkpoint.instructions or {},
            created_at=checkpoint.created_at,
            updated_at=checkpoint.updated_at,
        )

    @staticmethod
    def update_checkpoint(
        session: Session,
        checkpoint_id: str,
        data: CheckpointUpdate,
    ) -> Optional[CheckpointResponse]:
        """
        Update a checkpoint.

        Args:
            session: Database session
            checkpoint_id: Checkpoint UUID
            data: Checkpoint update data

        Returns:
            CheckpointResponse: Updated checkpoint data or None if not found

        Raises:
            ValueError: If checkpoint not found
        """
        checkpoint = session.execute(
            select(CheckpointDefinition).where(CheckpointDefinition.checkpoint_id == checkpoint_id)
        ).scalar_one_or_none()

        if not checkpoint:
            raise ValueError(f"Checkpoint with ID '{checkpoint_id}' not found")

        # Get pipeline_id for file manager
        pipeline_id = checkpoint.pipeline_id

        # Update basic fields if provided
        if data.checkpoint_name is not None:
            checkpoint.checkpoint_name = data.checkpoint_name
        if data.checkpoint_description is not None:
            checkpoint.checkpoint_description = data.checkpoint_description

        # Update human_only_config if provided
        if data.human_only_config is not None:
            execution = checkpoint.execution or {}
            existing_human_only_config = execution.get("human_only_config", {})

            # Merge with existing values, only updating fields that are explicitly provided
            if data.human_only_config.instructions is not None:
                existing_human_only_config["instructions"] = data.human_only_config.instructions
            if data.human_only_config.input_fields is not None:
                input_fields_with_ids = []
                for field in data.human_only_config.input_fields:
                    input_fields_with_ids.append({
                        "field_id": str(uuid4()),
                        "name": field.name,
                        "type": field.type,
                        "label": field.label,
                        "required": field.required,
                        "default": field.default,
                        "validation": field.validation,
                    })
                existing_human_only_config["input_fields"] = input_fields_with_ids
            if data.human_only_config.save_as_artifact is not None:
                existing_human_only_config["save_as_artifact"] = data.human_only_config.save_as_artifact
            if data.human_only_config.artifact_name is not None:
                existing_human_only_config["artifact_name"] = data.human_only_config.artifact_name
            if data.human_only_config.artifact_format is not None:
                existing_human_only_config["artifact_format"] = data.human_only_config.artifact_format

            execution["human_only_config"] = existing_human_only_config
            checkpoint.execution = execution

        # Update human_interaction if provided
        if data.human_interaction is not None:
            existing_interaction = checkpoint.human_interaction or {}
            if data.human_interaction.requires_approval_to_start is not None:
                existing_interaction["requires_approval_to_start"] = data.human_interaction.requires_approval_to_start
            if data.human_interaction.requires_approval_to_complete is not None:
                existing_interaction["requires_approval_to_complete"] = data.human_interaction.requires_approval_to_complete
            if data.human_interaction.max_revision_iterations is not None:
                existing_interaction["max_revision_iterations"] = data.human_interaction.max_revision_iterations
            checkpoint.human_interaction = existing_interaction

        # Update output_artifacts if provided
        if data.output_artifacts is not None:
            output = checkpoint.output or {"artifacts": [], "validation": {"enabled": False}}
            output_artifacts_with_ids = []
            for artifact in data.output_artifacts:
                output_artifacts_with_ids.append({
                    "artifact_id": str(uuid4()),
                    "name": artifact.name,
                    "format": artifact.format,
                    "description": artifact.description,
                    "schema": None,
                })
            output["artifacts"] = output_artifacts_with_ids
            checkpoint.output = output

        # Flag JSON columns as modified so SQLAlchemy detects the changes
        if data.human_only_config is not None:
            flag_modified(checkpoint, "execution")
        if data.human_interaction is not None:
            flag_modified(checkpoint, "human_interaction")
        if data.output_artifacts is not None:
            flag_modified(checkpoint, "output")

        # Save checkpoint definition to file system
        file_manager = FileManager(pipeline_id)
        file_manager.save_checkpoint_definition(checkpoint_id, checkpoint.to_dict())

        # Log event
        event = Event(
            event_type="checkpoint_updated",
            pipeline_id=pipeline_id,
            checkpoint_id=checkpoint_id,
            description=f"Checkpoint '{checkpoint.checkpoint_name}' updated",
            event_metadata={
                "checkpoint_name": checkpoint.checkpoint_name,
                "updated_fields": list(data.model_dump(exclude_unset=True).keys()),
            }
        )
        session.add(event)

        session.commit()
        session.refresh(checkpoint)

        return CheckpointService._build_checkpoint_response(checkpoint)

    @staticmethod
    def delete_checkpoint(
        session: Session,
        checkpoint_id: str,
    ) -> bool:
        """
        Delete a checkpoint.

        Args:
            session: Database session
            checkpoint_id: Checkpoint UUID

        Returns:
            bool: True if deleted, False if not found
        """
        checkpoint = session.execute(
            select(CheckpointDefinition).where(CheckpointDefinition.checkpoint_id == checkpoint_id)
        ).scalar_one_or_none()

        if not checkpoint:
            return False

        pipeline_id = checkpoint.pipeline_id
        checkpoint_name = checkpoint.checkpoint_name

        # Remove checkpoint_id from pipeline's checkpoint_order
        pipeline = session.execute(
            select(Pipeline).where(Pipeline.pipeline_id == pipeline_id)
        ).scalar_one_or_none()

        if pipeline:
            checkpoint_order = pipeline.checkpoint_order or []
            if checkpoint_id in checkpoint_order:
                checkpoint_order.remove(checkpoint_id)
                pipeline.checkpoint_order = checkpoint_order
                flag_modified(pipeline, "checkpoint_order")  # Mark JSON column as modified

                # Update pipeline definition file
                file_manager = FileManager(pipeline_id)
                file_manager.save_pipeline_definition(pipeline.to_dict())

        # Delete checkpoint file from file system
        file_manager = FileManager(pipeline_id)
        file_manager.delete_checkpoint_definition(checkpoint_id)

        # Delete checkpoint from database
        session.delete(checkpoint)

        # Log event
        event = Event(
            event_type="checkpoint_deleted",
            pipeline_id=pipeline_id,
            checkpoint_id=checkpoint_id,
            description=f"Checkpoint '{checkpoint_name}' deleted",
            event_metadata={"checkpoint_name": checkpoint_name}
        )
        session.add(event)

        session.commit()

        return True


# Add helper method to CheckpointDefinition model for dict conversion
def to_dict(self) -> dict:
    """Convert checkpoint definition model to dictionary."""
    return {
        "checkpoint_id": self.checkpoint_id,
        "pipeline_id": self.pipeline_id,
        "checkpoint_name": self.checkpoint_name,
        "checkpoint_description": self.checkpoint_description,
        "dependencies": self.dependencies,
        "inputs": self.inputs,
        "execution": self.execution,
        "human_interaction": self.human_interaction,
        "output": self.output,
        "instructions": self.instructions,
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }


# Monkey patch the to_dict method onto the CheckpointDefinition model
CheckpointDefinition.to_dict = to_dict
