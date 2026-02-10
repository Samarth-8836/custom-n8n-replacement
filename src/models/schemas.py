"""
Pydantic Schemas for Request/Response Validation

Defines all Pydantic models for API request/response validation.
"""

from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Pipeline Schemas
# =============================================================================


class PipelineBase(BaseModel):
    """Base schema for Pipeline data."""
    pipeline_name: str = Field(..., min_length=1, max_length=255, description="Name of the pipeline")
    pipeline_description: Optional[str] = Field(None, max_length=5000, description="Description of the pipeline")
    auto_advance: bool = Field(False, description="Auto-start next checkpoint after completion")


class PipelineCreate(PipelineBase):
    """Schema for creating a new pipeline."""
    pass


class PipelineUpdate(BaseModel):
    """Schema for updating a pipeline."""
    pipeline_name: Optional[str] = Field(None, min_length=1, max_length=255)
    pipeline_description: Optional[str] = Field(None, max_length=5000)
    auto_advance: Optional[bool] = None


class PipelineResponse(PipelineBase):
    """Schema for pipeline response."""
    pipeline_id: str = Field(..., description="Unique pipeline identifier")
    pipeline_definition_version: int = Field(..., description="Version of the pipeline definition")
    checkpoint_order: list[str] = Field(default_factory=list, description="Ordered list of checkpoint IDs")
    created_at: datetime = Field(..., description="Timestamp when pipeline was created")
    updated_at: datetime = Field(..., description="Timestamp when pipeline was last updated")

    # Computed fields
    checkpoint_count: int = Field(0, description="Number of checkpoints in the pipeline")

    model_config = {"from_attributes": True}


class PipelineListResponse(BaseModel):
    """Schema for pipeline list response."""
    pipelines: list[PipelineResponse]
    total_count: int
    page: int = 1
    page_size: int = 50


class PipelineDetailResponse(PipelineResponse):
    """Schema for detailed pipeline response including checkpoints."""
    checkpoints: list["CheckpointSummary"] = Field(default_factory=list)


# =============================================================================
# Input Field Schemas (for human_only checkpoints)
# =============================================================================


class InputFieldBase(BaseModel):
    """Base schema for input field."""
    name: str = Field(..., min_length=1, max_length=100, description="Field name")
    type: Literal["text", "number", "boolean", "file", "multiline_text"] = Field(
        ..., description="Field type"
    )
    label: str = Field(..., min_length=1, max_length=255, description="Field label")
    required: bool = Field(True, description="Whether field is required")
    default: Optional[str] = Field(None, description="Default value")
    validation: Optional[str] = Field(None, max_length=500, description="Validation regex or rule")


class InputFieldCreate(InputFieldBase):
    """Schema for creating an input field."""
    pass


class InputFieldResponse(InputFieldBase):
    """Schema for input field response."""
    field_id: str = Field(..., description="Unique field identifier")

    model_config = {"from_attributes": True}


# =============================================================================
# Output Artifact Schemas
# =============================================================================


class OutputArtifactBase(BaseModel):
    """Base schema for output artifact definition."""
    name: str = Field(..., min_length=1, max_length=255, description="Artifact name")
    format: Literal["json", "md", "mmd", "txt", "py", "html", "csv"] = Field(
        ..., description="Artifact format"
    )
    description: Optional[str] = Field(None, max_length=1000, description="Artifact description")


class OutputArtifactCreate(OutputArtifactBase):
    """Schema for creating an output artifact."""
    pass


class OutputArtifactResponse(OutputArtifactBase):
    """Schema for output artifact response."""
    artifact_id: str = Field(..., description="Unique artifact identifier")

    model_config = {"from_attributes": True}


# =============================================================================
# Human-Only Config Schemas
# =============================================================================


class HumanOnlyConfigBase(BaseModel):
    """Base schema for human-only checkpoint configuration."""
    instructions: str = Field(..., min_length=1, max_length=5000, description="Instructions for the user")
    input_fields: list[InputFieldCreate] = Field(
        default_factory=list, description="Form fields to collect from user"
    )
    save_as_artifact: bool = Field(False, description="Whether to save form data as artifact")
    artifact_name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Name for saved artifact"
    )
    artifact_format: Literal["json", "md"] = Field(
        "json", description="Format for saved artifact"
    )


class HumanOnlyConfigCreate(HumanOnlyConfigBase):
    """Schema for creating human-only config."""
    @field_validator("artifact_name")
    @classmethod
    def validate_artifact_name(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that artifact_name is provided if save_as_artifact is True."""
        if info.data.get("save_as_artifact", False) and not v:
            raise ValueError("artifact_name is required when save_as_artifact is True")
        return v


class HumanOnlyConfigResponse(HumanOnlyConfigBase):
    """Schema for human-only config response."""
    input_fields: list[InputFieldResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# =============================================================================
# Human Interaction Schemas
# =============================================================================


class HumanInteractionBase(BaseModel):
    """Base schema for human interaction settings."""
    requires_approval_to_start: bool = Field(
        False, description="Whether user must approve checkpoint start"
    )
    requires_approval_to_complete: bool = Field(
        False, description="Whether user must approve checkpoint completion"
    )
    max_revision_iterations: int = Field(
        3, ge=0, le=10, description="Max revision iterations before failure"
    )


class HumanInteractionCreate(HumanInteractionBase):
    """Schema for creating human interaction settings."""
    pass


class HumanInteractionResponse(HumanInteractionBase):
    """Schema for human interaction response."""
    model_config = {"from_attributes": True}


# =============================================================================
# Checkpoint Schemas (Slice 4 - Human-Only Mode)
# =============================================================================


class CheckpointBase(BaseModel):
    """Base schema for Checkpoint data."""
    checkpoint_name: str = Field(..., min_length=1, max_length=255)
    checkpoint_description: str = Field(..., min_length=1, max_length=5000)


class CheckpointSummary(CheckpointBase):
    """Summary schema for checkpoint in list view."""
    checkpoint_id: str
    execution_mode: str = Field(..., description="Execution mode (human_only, agentic, script)")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CheckpointCreate(CheckpointBase):
    """Schema for creating a checkpoint (human_only mode only for Slice 4)."""
    execution_mode: Literal["human_only"] = Field(
        "human_only", description="Execution mode - only human_only in Slice 4"
    )
    human_only_config: HumanOnlyConfigCreate = Field(
        ..., description="Configuration for human-only checkpoints"
    )
    human_interaction: HumanInteractionCreate = Field(
        default_factory=HumanInteractionCreate,
        description="Human interaction settings"
    )
    output_artifacts: list[OutputArtifactCreate] = Field(
        default_factory=list,
        description="Expected output artifacts from this checkpoint"
    )


class CheckpointUpdate(BaseModel):
    """Schema for updating a checkpoint."""
    checkpoint_name: Optional[str] = Field(None, min_length=1, max_length=255)
    checkpoint_description: Optional[str] = Field(None, min_length=1, max_length=5000)
    human_only_config: Optional["HumanOnlyConfigUpdate"] = None
    human_interaction: Optional[HumanInteractionCreate] = None
    output_artifacts: Optional[list[OutputArtifactCreate]] = None


class HumanOnlyConfigUpdate(BaseModel):
    """Schema for updating human-only config (without strict validation)."""
    instructions: Optional[str] = Field(None, min_length=1, max_length=5000)
    input_fields: Optional[list[InputFieldCreate]] = Field(None)  # Changed from default_factory=list
    save_as_artifact: Optional[bool] = None
    artifact_name: Optional[str] = Field(None, min_length=1, max_length=255)
    artifact_format: Optional[Literal["json", "md"]] = None  # Changed from "json" default

    model_config = {"extra": "ignore"}


class CheckpointResponse(CheckpointBase):
    """Schema for checkpoint response."""
    checkpoint_id: str
    pipeline_id: str
    execution_mode: str
    human_only_config: HumanOnlyConfigResponse
    human_interaction: HumanInteractionResponse
    output_artifacts: list[OutputArtifactResponse]
    dependencies: dict = Field(default_factory=dict)
    inputs: dict = Field(default_factory=dict)
    execution: dict = Field(default_factory=dict)
    output: dict = Field(default_factory=dict)
    instructions: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Pipeline Run Schemas (Slice 6)
# =============================================================================


class PipelineRunSummary(BaseModel):
    """Summary schema for pipeline run."""
    run_id: str
    run_version: int
    status: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PipelineRunCreate(BaseModel):
    """Schema for creating a new pipeline run."""
    extends_from_run_id: Optional[str] = Field(
        None,
        description="Optional run ID to extend from. If not provided, uses the latest valid run."
    )


class PipelineRunResponse(BaseModel):
    """Schema for pipeline run response."""
    run_id: str
    pipeline_id: str
    run_version: int
    status: str
    current_checkpoint_id: Optional[str] = None
    current_checkpoint_position: Optional[int] = None
    previous_run_id: Optional[str] = None
    extends_from_run_version: Optional[int] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    last_resumed_at: Optional[datetime] = None

    # Computed fields
    pipeline_name: Optional[str] = None
    checkpoint_count: int = 0
    completed_checkpoints: int = 0

    model_config = {"from_attributes": True}


class PipelineRunListResponse(BaseModel):
    """Schema for pipeline run list response."""
    runs: list[PipelineRunSummary]
    total_count: int


class PipelineRunDetailResponse(PipelineRunResponse):
    """Schema for detailed pipeline run response including checkpoint executions."""
    checkpoint_executions: list["CheckpointExecutionSummary"] = Field(default_factory=list)


# =============================================================================
# Checkpoint Execution Schemas (Slice 6)
# =============================================================================


class CheckpointExecutionSummary(BaseModel):
    """Summary schema for checkpoint execution."""
    execution_id: str
    checkpoint_id: str
    checkpoint_name: Optional[str] = None
    checkpoint_position: int
    status: str
    attempt_number: int
    revision_iteration: int
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CheckpointExecutionResponse(CheckpointExecutionSummary):
    """Detailed schema for checkpoint execution response."""
    run_id: str
    temp_workspace_path: str
    permanent_output_path: str
    max_attempts: int
    max_revision_iterations: int
    failed_at: Optional[datetime] = None

    # Checkpoint definition details
    execution_mode: Optional[str] = None
    checkpoint_description: Optional[str] = None

    model_config = {"from_attributes": True}


# =============================================================================
# Checkpoint Execution Control Schemas (Slice 7)
# =============================================================================


class ApproveStartRequest(BaseModel):
    """Schema for approving checkpoint start."""
    pass


class SubmitFormDataRequest(BaseModel):
    """Schema for submitting human form data."""
    form_data: dict = Field(..., description="Form field values submitted by user")


class ApproveCompleteRequest(BaseModel):
    """Schema for approving checkpoint completion."""
    promote_artifacts: bool = Field(
        True, description="Whether to promote artifacts to permanent storage"
    )


class RequestRevisionRequest(BaseModel):
    """Schema for requesting a revision."""
    feedback: str = Field(..., min_length=1, max_length=5000, description="Revision feedback")


class CheckpointExecutionDetailResponse(CheckpointExecutionResponse):
    """Extended schema for checkpoint execution with form details."""
    # Checkpoint definition for human-only mode
    human_only_config: Optional[dict] = Field(None, description="Human-only checkpoint config")
    human_interaction_settings: Optional[dict] = Field(None, description="Human interaction settings")

    # Current state
    form_data: Optional[dict] = Field(None, description="Submitted form data")
    artifacts_staged: list[dict] = Field(default_factory=list, description="Artifacts in staging")

    model_config = {"from_attributes": True}


# =============================================================================
# Error Response Schemas
# =============================================================================


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses."""
    error: str = Field(default="validation_error", description="Error type")
    message: str = Field(default="Request validation failed", description="Error message")
    details: list[dict] = Field(default_factory=list, description="Validation error details")


# =============================================================================
# Health Check Schema
# =============================================================================


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field("healthy", description="Service health status")
    service: str = Field("Pipeline n8n Alternative", description="Service name")
    version: str = Field("1.0.0", description="Service version")
    database_connected: Optional[bool] = Field(None, description="Database connection status")


# =============================================================================
# Re-export forward references
# =============================================================================

# Update forward references after all classes are defined
PipelineDetailResponse.model_rebuild()
CheckpointResponse.model_rebuild()
PipelineRunDetailResponse.model_rebuild()
CheckpointExecutionDetailResponse.model_rebuild()
