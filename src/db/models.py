"""
Database Models

SQLAlchemy models for the Pipeline system database.
This is the source of truth for all pipeline state.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# =============================================================================
# Base Class
# =============================================================================

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# =============================================================================
# Pipeline Model
# =============================================================================

class Pipeline(Base):
    """
    Pipeline Definition (Configuration)

    Represents a pipeline configuration with checkpoints.
    """
    __tablename__ = "pipelines"

    pipeline_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    pipeline_name: Mapped[str] = mapped_column(String(255), nullable=False)
    pipeline_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pipeline_definition_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    checkpoint_order: Mapped[dict] = mapped_column(SQLiteJSON, nullable=False, default=list)
    auto_advance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    checkpoint_definitions = relationship(
        "CheckpointDefinition",
        back_populates="pipeline",
        cascade="all, delete-orphan",
        order_by="CheckpointDefinition.created_at"
    )
    pipeline_runs = relationship(
        "PipelineRun",
        back_populates="pipeline",
        cascade="all, delete-orphan",
        order_by="PipelineRun.run_version.desc()"
    )
    events = relationship(
        "Event",
        back_populates="pipeline",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Pipeline(pipeline_id={self.pipeline_id}, name={self.pipeline_name}, version={self.pipeline_definition_version})>"


# =============================================================================
# Checkpoint Definition Model
# =============================================================================

class CheckpointDefinition(Base):
    """
    Checkpoint Definition (Configuration)

    Defines a single checkpoint within a pipeline.
    """
    __tablename__ = "checkpoint_definitions"

    checkpoint_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    pipeline_id: Mapped[str] = mapped_column(String(36), ForeignKey("pipelines.pipeline_id", ondelete="CASCADE"), nullable=False)
    checkpoint_name: Mapped[str] = mapped_column(String(255), nullable=False)
    checkpoint_description: Mapped[str] = mapped_column(Text, nullable=False)
    dependencies: Mapped[dict] = mapped_column(SQLiteJSON, nullable=False, default=dict)
    inputs: Mapped[dict] = mapped_column(SQLiteJSON, nullable=False, default=dict)
    execution: Mapped[dict] = mapped_column(SQLiteJSON, nullable=False, default=dict)
    human_interaction: Mapped[dict] = mapped_column(SQLiteJSON, nullable=False, default=dict)
    output: Mapped[dict] = mapped_column(SQLiteJSON, nullable=False, default=dict)
    instructions: Mapped[dict] = mapped_column(SQLiteJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pipeline = relationship("Pipeline", back_populates="checkpoint_definitions")
    checkpoint_executions = relationship(
        "CheckpointExecution",
        back_populates="checkpoint_definition",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CheckpointDefinition(checkpoint_id={self.checkpoint_id}, name={self.checkpoint_name})>"


# =============================================================================
# Pipeline Run Model
# =============================================================================

class PipelineRun(Base):
    """
    Pipeline Run (Runtime State)

    Represents a single execution of a pipeline.
    """
    __tablename__ = "pipeline_runs"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    pipeline_id: Mapped[str] = mapped_column(String(36), ForeignKey("pipelines.pipeline_id", ondelete="CASCADE"), nullable=False)
    run_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("not_started", "in_progress", "paused", "completed", "failed", name="pipeline_run_status"),
        nullable=False,
        default="not_started"
    )
    current_checkpoint_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("checkpoint_definitions.checkpoint_id"), nullable=True)
    current_checkpoint_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    previous_run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("pipeline_runs.run_id"), nullable=True)
    extends_from_run_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_resumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    pipeline = relationship("Pipeline", back_populates="pipeline_runs")
    current_checkpoint = relationship("CheckpointDefinition", foreign_keys=[current_checkpoint_id])
    checkpoint_executions = relationship(
        "CheckpointExecution",
        back_populates="pipeline_run",
        cascade="all, delete-orphan",
        order_by="CheckpointExecution.checkpoint_position"
    )
    rollback_events = relationship(
        "RollbackEvent",
        back_populates="source_run",
        foreign_keys="RollbackEvent.source_run_id",
        cascade="all, delete-orphan"
    )
    events = relationship(
        "Event",
        back_populates="pipeline_run",
        cascade="all, delete-orphan"
    )

    # Self-referential relationship for previous_run_id
    previous_run = relationship("PipelineRun", foreign_keys=[previous_run_id], remote_side=[run_id])

    __table_args__ = (
        Index("idx_pipeline_run_version", "pipeline_id", "run_version"),
        Index("idx_pipeline_run_status", "pipeline_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<PipelineRun(run_id={self.run_id}, version=v{self.run_version}, status={self.status})>"


# =============================================================================
# Checkpoint Execution Model
# =============================================================================

class CheckpointExecution(Base):
    """
    Checkpoint Execution Instance (Runtime State)

    Represents a single execution of a checkpoint within a pipeline run.
    """
    __tablename__ = "checkpoint_executions"

    execution_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("pipeline_runs.run_id", ondelete="CASCADE"), nullable=False)
    checkpoint_id: Mapped[str] = mapped_column(String(36), ForeignKey("checkpoint_definitions.checkpoint_id"), nullable=False)
    checkpoint_position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "waiting_approval_to_start",
            "in_progress",
            "waiting_approval_to_complete",
            "completed",
            "failed",
            name="checkpoint_execution_status"
        ),
        nullable=False,
        default="pending"
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    revision_iteration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_revision_iterations: Mapped[int] = mapped_column(Integer, nullable=False)
    temp_workspace_path: Mapped[str] = mapped_column(String(500), nullable=False)
    permanent_output_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    pipeline_run = relationship("PipelineRun", back_populates="checkpoint_executions")
    checkpoint_definition = relationship("CheckpointDefinition", back_populates="checkpoint_executions")
    execution_logs = relationship(
        "ExecutionLog",
        back_populates="checkpoint_execution",
        cascade="all, delete-orphan",
        order_by="ExecutionLog.timestamp"
    )
    human_interactions = relationship(
        "HumanInteraction",
        back_populates="checkpoint_execution",
        cascade="all, delete-orphan",
        order_by="HumanInteraction.timestamp"
    )
    artifacts = relationship(
        "Artifact",
        back_populates="checkpoint_execution",
        cascade="all, delete-orphan"
    )
    events = relationship(
        "Event",
        back_populates="checkpoint_execution",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_execution_run_position", "run_id", "checkpoint_position"),
        Index("idx_execution_status", "run_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<CheckpointExecution(execution_id={self.execution_id}, position={self.checkpoint_position}, status={self.status})>"


# =============================================================================
# Execution Log Model
# =============================================================================

class ExecutionLog(Base):
    """
    Execution Log

    Stores log entries for checkpoint executions.
    """
    __tablename__ = "execution_logs"

    log_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("checkpoint_executions.execution_id", ondelete="CASCADE"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    level: Mapped[str] = mapped_column(Enum("info", "warning", "error", name="log_level"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(SQLiteJSON, nullable=True)

    # Relationships
    checkpoint_execution = relationship("CheckpointExecution", back_populates="execution_logs")

    __table_args__ = (
        Index("idx_log_execution_timestamp", "execution_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<ExecutionLog(log_id={self.log_id}, level={self.level}, message={self.message[:50]}...)"


# =============================================================================
# Human Interaction Model
# =============================================================================

class HumanInteraction(Base):
    """
    Human Interaction

    Records of human interactions during checkpoint execution.
    """
    __tablename__ = "human_interactions"

    interaction_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("checkpoint_executions.execution_id", ondelete="CASCADE"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    interaction_type: Mapped[str] = mapped_column(
        Enum(
            "approval_to_start",
            "approval_to_complete",
            "revision_request",
            "script_input",
            "validation_feedback",
            name="human_interaction_type"
        ),
        nullable=False
    )
    user_input: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    system_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    checkpoint_execution = relationship("CheckpointExecution", back_populates="human_interactions")

    __table_args__ = (
        Index("idx_interaction_execution_timestamp", "execution_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<HumanInteraction(interaction_id={self.interaction_id}, type={self.interaction_type})>"


# =============================================================================
# Artifact Model
# =============================================================================

class Artifact(Base):
    """
    Artifact

    Records of artifacts generated during checkpoint execution.
    """
    __tablename__ = "artifacts"

    artifact_record_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("checkpoint_executions.execution_id", ondelete="CASCADE"), nullable=False)
    artifact_id: Mapped[str] = mapped_column(String(36), nullable=False)
    artifact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    format: Mapped[str] = mapped_column(String(50), nullable=False)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    promoted_to_permanent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    checkpoint_execution = relationship("CheckpointExecution", back_populates="artifacts")

    __table_args__ = (
        Index("idx_artifact_execution", "execution_id"),
        Index("idx_artifact_id_name", "artifact_id", "artifact_name"),
    )

    def __repr__(self) -> str:
        return f"<Artifact(artifact_record_id={self.artifact_record_id}, name={self.artifact_name}, format={self.format})>"


# =============================================================================
# Rollback Event Model
# =============================================================================

class RollbackEvent(Base):
    """
    Rollback Event

    Records of rollback operations.
    """
    __tablename__ = "rollback_events"

    rollback_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("pipeline_runs.run_id", ondelete="CASCADE"), nullable=False)
    source_run_version: Mapped[int] = mapped_column(Integer, nullable=False)
    rollback_type: Mapped[str] = mapped_column(Enum("checkpoint_level", "run_level", name="rollback_type"), nullable=False)
    target_run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("pipeline_runs.run_id"), nullable=True)
    target_checkpoint_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("checkpoint_definitions.checkpoint_id"), nullable=True)
    target_checkpoint_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    archive_location: Mapped[str] = mapped_column(String(500), nullable=False)
    triggered_by: Mapped[str] = mapped_column(Enum("user_request", "checkpoint_failure", name="rollback_triggered_by"), nullable=False)
    user_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rolled_back_items: Mapped[dict] = mapped_column(SQLiteJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    source_run = relationship("PipelineRun", foreign_keys=[source_run_id], back_populates="rollback_events")
    target_run = relationship("PipelineRun", foreign_keys=[target_run_id])
    archived_items = relationship(
        "ArchivedItem",
        back_populates="rollback_event",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_rollback_source_run", "source_run_id"),
        Index("idx_rollback_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<RollbackEvent(rollback_id={self.rollback_id}, type={self.rollback_type})>"


# =============================================================================
# Archived Item Model
# =============================================================================

class ArchivedItem(Base):
    """
    Archived Item

    Records of items archived during rollback.
    """
    __tablename__ = "archived_items"

    archive_item_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    rollback_id: Mapped[str] = mapped_column(String(36), ForeignKey("rollback_events.rollback_id", ondelete="CASCADE"), nullable=False)
    item_type: Mapped[str] = mapped_column(Enum("run", "checkpoint_execution", "artifact", name="archived_item_type"), nullable=False)
    item_id: Mapped[str] = mapped_column(String(36), nullable=False)
    original_path: Mapped[str] = mapped_column(String(500), nullable=False)
    archived_path: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    rollback_event = relationship("RollbackEvent", back_populates="archived_items")

    __table_args__ = (
        Index("idx_archived_rollback", "rollback_id"),
        Index("idx_archived_item_type", "rollback_id", "item_type"),
    )

    def __repr__(self) -> str:
        return f"<ArchivedItem(archive_item_id={self.archive_item_id}, type={self.item_type})>"


# =============================================================================
# Event Model
# =============================================================================

class Event(Base):
    """
    Event

    General event logging for the pipeline system.
    """
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    pipeline_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("pipelines.pipeline_id", ondelete="CASCADE"), nullable=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("pipeline_runs.run_id", ondelete="CASCADE"), nullable=True)
    execution_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("checkpoint_executions.execution_id", ondelete="CASCADE"), nullable=True)
    checkpoint_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("checkpoint_definitions.checkpoint_id"), nullable=True)
    rollback_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("rollback_events.rollback_id"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_metadata: Mapped[Optional[dict]] = mapped_column("metadata", SQLiteJSON, nullable=True)

    # Relationships
    pipeline = relationship("Pipeline", back_populates="events")
    pipeline_run = relationship("PipelineRun", back_populates="events")
    checkpoint_execution = relationship("CheckpointExecution", back_populates="events")

    __table_args__ = (
        Index("idx_event_timestamp", "timestamp"),
        Index("idx_event_pipeline", "pipeline_id"),
        Index("idx_event_run", "run_id"),
        Index("idx_event_execution", "execution_id"),
    )

    def __repr__(self) -> str:
        return f"<Event(event_id={self.event_id}, type={self.event_type}, description={self.description[:50]}...)>"
