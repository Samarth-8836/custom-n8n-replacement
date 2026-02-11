"""
Artifact Service

Business logic for artifact management.
Handles retrieving artifact metadata, content, and file paths for download/preview.
"""

import json
import os
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.file_manager import FileManager
from src.db.models import Artifact, CheckpointExecution, CheckpointDefinition, PipelineRun


class ArtifactService:
    """
    Service for managing artifacts.

    Handles retrieving artifacts for download and preview,
    including reading file contents for text-based formats.
    """

    @staticmethod
    def get_artifact(session: Session, artifact_id: str) -> Optional[Artifact]:
        """
        Get an artifact by its ID.

        Args:
            session: Database session
            artifact_id: Artifact ID

        Returns:
            Artifact record or None if not found
        """
        return session.execute(
            select(Artifact).where(Artifact.artifact_id == artifact_id)
        ).scalar_one_or_none()

    @staticmethod
    def get_artifact_metadata(session: Session, artifact_id: str) -> Optional[dict]:
        """
        Get artifact metadata including file information.

        Args:
            session: Database session
            artifact_id: Artifact ID

        Returns:
            Dictionary with artifact metadata or None
        """
        artifact = ArtifactService.get_artifact(session, artifact_id)
        if not artifact:
            return None

        # Get checkpoint execution for additional context
        execution = session.execute(
            select(CheckpointExecution).where(
                CheckpointExecution.execution_id == artifact.execution_id
            )
        ).scalar_one_or_none()

        # Get file size from actual file if exists
        file_size = artifact.size_bytes
        file_exists = False
        if artifact.file_path:
            file_path = Path(artifact.file_path)
            if file_path.exists():
                file_exists = True
                # Update file size from actual file
                file_size = file_path.stat().st_size

        return {
            "artifact_id": artifact.artifact_id,
            "artifact_record_id": artifact.artifact_record_id,
            "artifact_name": artifact.artifact_name,
            "format": artifact.format,
            "file_path": artifact.file_path,
            "size_bytes": file_size,
            "checksum": artifact.checksum,
            "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
            "promoted_to_permanent_at": artifact.promoted_to_permanent_at.isoformat() if artifact.promoted_to_permanent_at else None,
            "execution_id": artifact.execution_id,
            "file_exists": file_exists,
            # Additional context
            "checkpoint_position": execution.checkpoint_position if execution else None,
            "is_promoted": artifact.promoted_to_permanent_at is not None,
        }

    @staticmethod
    def get_artifact_content(session: Session, artifact_id: str) -> Optional[dict]:
        """
        Get artifact file content for preview.

        Only returns content for text-based formats (json, md, txt, py, html, csv, mmd).
        Binary files will return metadata but not content.

        Args:
            session: Database session
            artifact_id: Artifact ID

        Returns:
            Dictionary with content and metadata, or None if not found
        """
        artifact = ArtifactService.get_artifact(session, artifact_id)
        if not artifact:
            return None

        file_path = Path(artifact.file_path)

        # Check if file exists
        if not file_path.exists():
            return {
                "artifact_id": artifact.artifact_id,
                "artifact_name": artifact.artifact_name,
                "format": artifact.format,
                "error": "File not found",
                "file_path": str(file_path),
            }

        # Binary formats - don't return content
        binary_formats = []  # For now, treat all as text-based for preview

        # Check file size limit for preview (1MB)
        file_size = file_path.stat().st_size
        max_preview_size = 1024 * 1024  # 1MB

        if file_size > max_preview_size:
            return {
                "artifact_id": artifact.artifact_id,
                "artifact_name": artifact.artifact_name,
                "format": artifact.format,
                "size_bytes": file_size,
                "error": "File too large for preview",
                "file_path": str(file_path),
                "content_type": "text" if artifact.format in ["json", "md", "txt", "py", "html", "csv", "mmd"] else "binary",
            }

        # Read file content for text formats
        text_formats = ["json", "md", "txt", "py", "html", "csv", "mmd"]

        if artifact.format in text_formats:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                return {
                    "artifact_id": artifact.artifact_id,
                    "artifact_name": artifact.artifact_name,
                    "format": artifact.format,
                    "size_bytes": file_size,
                    "content": content,
                    "file_path": str(file_path),
                    "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
                }
            except UnicodeDecodeError:
                return {
                    "artifact_id": artifact.artifact_id,
                    "artifact_name": artifact.artifact_name,
                    "format": artifact.format,
                    "error": "File is binary or has encoding issues",
                    "file_path": str(file_path),
                }
        else:
            # Unknown format - return metadata only
            return {
                "artifact_id": artifact.artifact_id,
                "artifact_name": artifact.artifact_name,
                "format": artifact.format,
                "size_bytes": file_size,
                "error": "Unsupported format for preview",
                "file_path": str(file_path),
            }

    @staticmethod
    def list_artifacts_for_execution(session: Session, execution_id: str) -> list[dict]:
        """
        List all artifacts for a checkpoint execution.

        Args:
            session: Database session
            execution_id: Execution ID

        Returns:
            List of artifact metadata dictionaries
        """
        artifacts = session.execute(
            select(Artifact).where(
                Artifact.execution_id == execution_id
            ).order_by(Artifact.created_at)
        ).scalars().all()

        return [
            {
                "artifact_id": art.artifact_id,
                "artifact_name": art.artifact_name,
                "format": art.format,
                "size_bytes": art.size_bytes,
                "created_at": art.created_at.isoformat() if art.created_at else None,
                "promoted_to_permanent_at": art.promoted_to_permanent_at.isoformat() if art.promoted_to_permanent_at else None,
                "is_promoted": art.promoted_to_permanent_at is not None,
            }
            for art in artifacts
        ]

    @staticmethod
    def get_artifact_file_path(session: Session, artifact_id: str) -> Optional[str]:
        """
        Get the file path for an artifact.

        Args:
            session: Database session
            artifact_id: Artifact ID

        Returns:
            File path string or None if not found
        """
        artifact = ArtifactService.get_artifact(session, artifact_id)
        if not artifact:
            return None

        return artifact.file_path

    @staticmethod
    def get_previous_version_artifacts(
        session: Session,
        execution_id: str,
        checkpoint_position: int,
        previous_run_id: str
    ) -> list[dict]:
        """
        Get artifacts from the same checkpoint in the previous run version.

        This enables version extension where v2 can reference v1's outputs.

        Args:
            session: Database session
            execution_id: Current execution ID (for context)
            checkpoint_position: Current checkpoint position
            previous_run_id: The previous run's ID to get artifacts from

        Returns:
            List of artifact dictionaries from previous version, or empty list if not found
        """
        if not previous_run_id:
            return []

        # Get the previous run
        previous_run = session.execute(
            select(PipelineRun).where(PipelineRun.run_id == previous_run_id)
        ).scalar_one_or_none()

        if not previous_run:
            return []

        # Get the checkpoint execution from the previous run at the same position
        previous_execution = session.execute(
            select(CheckpointExecution)
            .where(
                CheckpointExecution.run_id == previous_run_id,
                CheckpointExecution.checkpoint_position == checkpoint_position
            )
        ).scalar_one_or_none()

        if not previous_execution:
            return []

        # Get all artifacts for that execution
        artifacts = session.execute(
            select(Artifact).where(
                Artifact.execution_id == previous_execution.execution_id
            )
        ).scalars().all()

        # Filter to only promoted artifacts (permanent storage)
        result = []
        for art in artifacts:
            if not art.promoted_to_permanent_at:
                continue  # Skip non-promoted artifacts

            file_path = Path(art.file_path)
            if not file_path.exists():
                continue  # Skip missing files

            # Try to read content for text-based formats (for UI display)
            content = None
            text_formats = ["json", "md", "txt", "py", "html", "csv", "mmd"]
            if art.format in text_formats:
                try:
                    # Only read small files for context display
                    if file_path.stat().st_size <= 10000:  # 10KB limit for inline display
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                except Exception:
                    pass  # Content not critical, metadata is enough

            result.append({
                "artifact_id": art.artifact_id,
                "artifact_name": art.artifact_name,
                "format": art.format,
                "file_path": str(file_path),
                "size_bytes": art.size_bytes,
                "created_at": art.created_at.isoformat() if art.created_at else None,
                "content": content,
                "is_from_previous": True,
                "previous_run_version": previous_run.run_version,
            })

        return result
