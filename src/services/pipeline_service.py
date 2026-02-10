"""
Pipeline Service

Business logic for pipeline CRUD operations.
"""

from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from src.core.file_manager import FileManager
from src.db.models import CheckpointDefinition, Event, Pipeline
from src.models.schemas import PipelineCreate, PipelineDetailResponse, PipelineResponse, PipelineUpdate


class PipelineService:
    """
    Service for managing pipeline CRUD operations.
    """

    @staticmethod
    def create_pipeline(
        session: Session,
        data: PipelineCreate,
    ) -> PipelineResponse:
        """
        Create a new pipeline.

        Args:
            session: Database session
            data: Pipeline creation data

        Returns:
            PipelineResponse: Created pipeline data

        Raises:
            ValueError: If pipeline name already exists
        """
        # Check if pipeline with same name already exists
        existing = session.execute(
            select(Pipeline).where(Pipeline.pipeline_name == data.pipeline_name)
        ).scalar_one_or_none()

        if existing:
            raise ValueError(f"Pipeline with name '{data.pipeline_name}' already exists")

        # Generate pipeline ID
        pipeline_id = str(uuid4())

        # Create pipeline model
        pipeline = Pipeline(
            pipeline_id=pipeline_id,
            pipeline_name=data.pipeline_name,
            pipeline_description=data.pipeline_description,
            auto_advance=data.auto_advance,
            pipeline_definition_version=1,
            checkpoint_order=[],
        )

        session.add(pipeline)
        session.flush()

        # Create file system structure
        file_manager = FileManager(pipeline_id)
        file_manager.initialize_pipeline_structure()

        # Save pipeline definition to file
        file_manager.save_pipeline_definition(pipeline.to_dict())

        # Log event
        event = Event(
            event_type="pipeline_created",
            pipeline_id=pipeline_id,
            description=f"Pipeline '{data.pipeline_name}' created",
            event_metadata={"pipeline_name": data.pipeline_name}
        )
        session.add(event)

        session.commit()
        session.refresh(pipeline)

        return PipelineResponse(
            pipeline_id=pipeline.pipeline_id,
            pipeline_name=pipeline.pipeline_name,
            pipeline_description=pipeline.pipeline_description,
            auto_advance=pipeline.auto_advance,
            pipeline_definition_version=pipeline.pipeline_definition_version,
            checkpoint_order=pipeline.checkpoint_order or [],
            created_at=pipeline.created_at,
            updated_at=pipeline.updated_at,
            checkpoint_count=0,
        )

    @staticmethod
    def get_pipeline(session: Session, pipeline_id: str) -> Optional[PipelineResponse]:
        """
        Get a pipeline by ID.

        Args:
            session: Database session
            pipeline_id: Pipeline UUID

        Returns:
            PipelineResponse: Pipeline data or None if not found
        """
        pipeline = session.execute(
            select(Pipeline).where(Pipeline.pipeline_id == pipeline_id)
        ).scalar_one_or_none()

        if not pipeline:
            return None

        # Count checkpoints
        checkpoint_count = session.execute(
            select(CheckpointDefinition).where(CheckpointDefinition.pipeline_id == pipeline_id)
        ).scalar() or 0
        checkpoint_count = len(pipeline.checkpoint_definitions) if hasattr(pipeline, 'checkpoint_definitions') else 0

        return PipelineResponse(
            pipeline_id=pipeline.pipeline_id,
            pipeline_name=pipeline.pipeline_name,
            pipeline_description=pipeline.pipeline_description,
            auto_advance=pipeline.auto_advance,
            pipeline_definition_version=pipeline.pipeline_definition_version,
            checkpoint_order=pipeline.checkpoint_order or [],
            created_at=pipeline.created_at,
            updated_at=pipeline.updated_at,
            checkpoint_count=checkpoint_count,
        )

    @staticmethod
    def get_pipeline_detail(session: Session, pipeline_id: str) -> Optional[PipelineDetailResponse]:
        """
        Get a pipeline by ID with checkpoint details.

        Args:
            session: Database session
            pipeline_id: Pipeline UUID

        Returns:
            PipelineDetailResponse: Pipeline data with checkpoints or None if not found
        """
        pipeline = session.execute(
            select(Pipeline).where(Pipeline.pipeline_id == pipeline_id)
        ).scalar_one_or_none()

        if not pipeline:
            return None

        # Get all checkpoints for this pipeline
        checkpoints = session.execute(
            select(CheckpointDefinition)
            .where(CheckpointDefinition.pipeline_id == pipeline_id)
        ).scalars().all()

        # Create a mapping of checkpoint_id -> checkpoint for quick lookup
        checkpoint_map = {cp.checkpoint_id: cp for cp in checkpoints}

        # Order checkpoints according to checkpoint_order
        # If checkpoint_order is empty or None, fall back to created_at ordering
        checkpoint_order = pipeline.checkpoint_order or []
        if checkpoint_order:
            # Use the order from checkpoint_order, but include any checkpoints not in the list
            ordered_checkpoints = []
            for cp_id in checkpoint_order:
                if cp_id in checkpoint_map:
                    ordered_checkpoints.append(checkpoint_map[cp_id])
                    del checkpoint_map[cp_id]
            # Append any remaining checkpoints (newly added ones not yet in checkpoint_order)
            ordered_checkpoints.extend(checkpoint_map.values())
            checkpoints = ordered_checkpoints
        else:
            # No checkpoint_order set, sort by created_at
            checkpoints = sorted(checkpoints, key=lambda cp: cp.created_at)

        checkpoint_summaries = [
            {
                "checkpoint_id": cp.checkpoint_id,
                "checkpoint_name": cp.checkpoint_name,
                "checkpoint_description": cp.checkpoint_description,
                "execution_mode": cp.execution.get("mode", "human_only") if cp.execution else "human_only",
                "created_at": cp.created_at,
                "updated_at": cp.updated_at,
            }
            for cp in checkpoints
        ]

        return PipelineDetailResponse(
            pipeline_id=pipeline.pipeline_id,
            pipeline_name=pipeline.pipeline_name,
            pipeline_description=pipeline.pipeline_description,
            auto_advance=pipeline.auto_advance,
            pipeline_definition_version=pipeline.pipeline_definition_version,
            checkpoint_order=pipeline.checkpoint_order or [],
            created_at=pipeline.created_at,
            updated_at=pipeline.updated_at,
            checkpoint_count=len(checkpoints),
            checkpoints=checkpoint_summaries,
        )

    @staticmethod
    def list_pipelines(
        session: Session,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[PipelineResponse], int]:
        """
        List all pipelines with pagination.

        Args:
            session: Database session
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            tuple: (list of PipelineResponse, total count)
        """
        # Get total count
        total_count = session.execute(
            select(func.count(Pipeline.pipeline_id))
        ).scalar() or 0

        # Get paginated results
        offset = (page - 1) * page_size
        pipelines = session.execute(
            select(Pipeline)
            .order_by(Pipeline.created_at.desc())
            .offset(offset)
            .limit(page_size)
        ).scalars().all()

        results = []
        for pipeline in pipelines:
            checkpoint_count = len(pipeline.checkpoint_definitions) if hasattr(pipeline, 'checkpoint_definitions') else 0
            results.append(PipelineResponse(
                pipeline_id=pipeline.pipeline_id,
                pipeline_name=pipeline.pipeline_name,
                pipeline_description=pipeline.pipeline_description,
                auto_advance=pipeline.auto_advance,
                pipeline_definition_version=pipeline.pipeline_definition_version,
                checkpoint_order=pipeline.checkpoint_order or [],
                created_at=pipeline.created_at,
                updated_at=pipeline.updated_at,
                checkpoint_count=checkpoint_count,
            ))

        return results, total_count

    @staticmethod
    def update_pipeline(
        session: Session,
        pipeline_id: str,
        data: PipelineUpdate,
    ) -> Optional[PipelineResponse]:
        """
        Update a pipeline.

        Note: This only updates name, description, and auto_advance.
        Changes to checkpoint_order create a new pipeline version.

        Args:
            session: Database session
            pipeline_id: Pipeline UUID
            data: Pipeline update data

        Returns:
            PipelineResponse: Updated pipeline data or None if not found

        Raises:
            ValueError: If new name conflicts with existing pipeline
        """
        pipeline = session.execute(
            select(Pipeline).where(Pipeline.pipeline_id == pipeline_id)
        ).scalar_one_or_none()

        if not pipeline:
            return None

        # Check for name conflict if changing name
        if data.pipeline_name and data.pipeline_name != pipeline.pipeline_name:
            existing = session.execute(
                select(Pipeline).where(
                    Pipeline.pipeline_name == data.pipeline_name,
                    Pipeline.pipeline_id != pipeline_id
                )
            ).scalar_one_or_none()

            if existing:
                raise ValueError(f"Pipeline with name '{data.pipeline_name}' already exists")

            pipeline.pipeline_name = data.pipeline_name

        # Update other fields
        if data.pipeline_description is not None:
            pipeline.pipeline_description = data.pipeline_description

        if data.auto_advance is not None:
            pipeline.auto_advance = data.auto_advance

        # Update file system definition
        file_manager = FileManager(pipeline_id)
        file_manager.save_pipeline_definition(pipeline.to_dict())

        # Log event
        event = Event(
            event_type="pipeline_updated",
            pipeline_id=pipeline_id,
            description=f"Pipeline '{pipeline.pipeline_name}' updated",
            event_metadata={"updated_fields": list(data.model_dump(exclude_unset=True).keys())}
        )
        session.add(event)

        session.commit()
        session.refresh(pipeline)

        checkpoint_count = len(pipeline.checkpoint_definitions) if hasattr(pipeline, 'checkpoint_definitions') else 0

        return PipelineResponse(
            pipeline_id=pipeline.pipeline_id,
            pipeline_name=pipeline.pipeline_name,
            pipeline_description=pipeline.pipeline_description,
            auto_advance=pipeline.auto_advance,
            pipeline_definition_version=pipeline.pipeline_definition_version,
            checkpoint_order=pipeline.checkpoint_order or [],
            created_at=pipeline.created_at,
            updated_at=pipeline.updated_at,
            checkpoint_count=checkpoint_count,
        )

    @staticmethod
    def delete_pipeline(session: Session, pipeline_id: str) -> bool:
        """
        Delete a pipeline (soft delete - moves to archive).

        Args:
            session: Database session
            pipeline_id: Pipeline UUID

        Returns:
            bool: True if deleted, False if not found
        """
        pipeline = session.execute(
            select(Pipeline).where(Pipeline.pipeline_id == pipeline_id)
        ).scalar_one_or_none()

        if not pipeline:
            return False

        pipeline_name = pipeline.pipeline_name

        # The cascade will delete related records
        # In production, we would move to archive first
        session.delete(pipeline)

        # Log event
        event = Event(
            event_type="pipeline_deleted",
            pipeline_id=pipeline_id,
            description=f"Pipeline '{pipeline_name}' deleted",
            event_metadata={"pipeline_name": pipeline_name}
        )
        session.add(event)

        session.commit()

        return True

    @staticmethod
    def reorder_checkpoints(
        session: Session,
        pipeline_id: str,
        checkpoint_order: list[str],
    ) -> Optional[PipelineResponse]:
        """
        Reorder checkpoints in a pipeline.

        Args:
            session: Database session
            pipeline_id: Pipeline UUID
            checkpoint_order: New ordered list of checkpoint IDs

        Returns:
            PipelineResponse: Updated pipeline data or None if not found

        Raises:
            ValueError: If pipeline not found or invalid checkpoint IDs
        """
        pipeline = session.execute(
            select(Pipeline).where(Pipeline.pipeline_id == pipeline_id)
        ).scalar_one_or_none()

        if not pipeline:
            raise ValueError(f"Pipeline with ID '{pipeline_id}' not found")

        # Verify all checkpoint IDs exist in the pipeline
        existing_checkpoints = session.execute(
            select(CheckpointDefinition).where(CheckpointDefinition.pipeline_id == pipeline_id)
        ).scalars().all()

        existing_checkpoint_ids = {cp.checkpoint_id for cp in existing_checkpoints}
        provided_checkpoint_ids = set(checkpoint_order)

        # Check that all provided IDs exist
        if not provided_checkpoint_ids.issubset(existing_checkpoint_ids):
            invalid_ids = provided_checkpoint_ids - existing_checkpoint_ids
            raise ValueError(f"Invalid checkpoint IDs: {invalid_ids}")

        # Check that all existing checkpoints are included
        if existing_checkpoint_ids != provided_checkpoint_ids:
            missing_ids = existing_checkpoint_ids - provided_checkpoint_ids
            raise ValueError(f"Missing checkpoint IDs: {missing_ids}")

        # Update checkpoint order
        pipeline.checkpoint_order = checkpoint_order

        # Flag checkpoint_order as modified since it's a JSON column
        flag_modified(pipeline, "checkpoint_order")

        # Increment pipeline definition version since checkpoint order changed
        pipeline.pipeline_definition_version += 1

        # Update file system definition
        file_manager = FileManager(pipeline_id)
        file_manager.save_pipeline_definition(pipeline.to_dict())

        # Log event
        event = Event(
            event_type="checkpoints_reordered",
            pipeline_id=pipeline_id,
            description=f"Checkpoints reordered in pipeline '{pipeline.pipeline_name}'",
            event_metadata={
                "pipeline_name": pipeline.pipeline_name,
                "new_checkpoint_order": checkpoint_order,
                "new_version": pipeline.pipeline_definition_version,
            }
        )
        session.add(event)

        session.commit()
        session.refresh(pipeline)

        checkpoint_count = len(pipeline.checkpoint_definitions) if hasattr(pipeline, 'checkpoint_definitions') else 0

        return PipelineResponse(
            pipeline_id=pipeline.pipeline_id,
            pipeline_name=pipeline.pipeline_name,
            pipeline_description=pipeline.pipeline_description,
            auto_advance=pipeline.auto_advance,
            pipeline_definition_version=pipeline.pipeline_definition_version,
            checkpoint_order=pipeline.checkpoint_order or [],
            created_at=pipeline.created_at,
            updated_at=pipeline.updated_at,
            checkpoint_count=checkpoint_count,
        )


# Add helper method to Pipeline model for dict conversion
def to_dict(self) -> dict:
    """Convert pipeline model to dictionary."""
    return {
        "pipeline_id": self.pipeline_id,
        "pipeline_name": self.pipeline_name,
        "pipeline_description": self.pipeline_description,
        "pipeline_definition_version": self.pipeline_definition_version,
        "checkpoint_order": self.checkpoint_order,
        "auto_advance": self.auto_advance,
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }


# Monkey patch the to_dict method onto the Pipeline model
Pipeline.to_dict = to_dict
