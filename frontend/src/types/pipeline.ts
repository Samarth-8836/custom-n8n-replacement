/**
 * Pipeline Types
 *
 * TypeScript types matching the backend Pydantic schemas
 */

// =============================================================================
// Pipeline Types
// =============================================================================

export interface Pipeline {
  pipeline_id: string;
  pipeline_name: string;
  pipeline_description: string | null;
  pipeline_definition_version: number;
  checkpoint_order: string[];
  auto_advance: boolean;
  created_at: string;
  updated_at: string;
  checkpoint_count: number;
}

export interface PipelineDetail extends Pipeline {
  checkpoints: CheckpointSummary[];
}

export interface PipelineCreate {
  pipeline_name: string;
  pipeline_description?: string;
  auto_advance?: boolean;
}

export interface PipelineUpdate {
  pipeline_name?: string;
  pipeline_description?: string;
  auto_advance?: boolean;
}

export interface PipelineListResponse {
  pipelines: Pipeline[];
  total_count: number;
  page: number;
  page_size: number;
}

// =============================================================================
// Checkpoint Types
// =============================================================================

export type ExecutionMode = 'human_only' | 'agentic' | 'script';
export type InputFieldType = 'text' | 'number' | 'boolean' | 'file' | 'multiline_text';
export type ArtifactFormat = 'json' | 'md' | 'mmd' | 'txt' | 'py' | 'html' | 'csv';
export type ArtifactFormatSimple = 'json' | 'md';

export interface CheckpointSummary {
  checkpoint_id: string;
  checkpoint_name: string;
  checkpoint_description: string;
  execution_mode: string;
  created_at: string;
  updated_at: string;
}

export interface InputField {
  field_id?: string;
  name: string;
  type: InputFieldType;
  label: string;
  required: boolean;
  default?: string;
  validation?: string;
}

export interface InputFieldCreate extends Omit<InputField, 'field_id'> {}

export interface OutputArtifact {
  artifact_id?: string;
  name: string;
  format: ArtifactFormat;
  description?: string;
}

export interface OutputArtifactCreate extends Omit<OutputArtifact, 'artifact_id'> {}

export interface HumanOnlyConfig {
  instructions: string;
  input_fields: InputField[];
  save_as_artifact: boolean;
  artifact_name?: string;
  artifact_format: ArtifactFormatSimple;
}

export interface HumanOnlyConfigCreate extends HumanOnlyConfig {
  input_fields: InputFieldCreate[];
}

export interface HumanInteraction {
  requires_approval_to_start: boolean;
  requires_approval_to_complete: boolean;
  max_revision_iterations: number;
}

export interface Checkpoint {
  checkpoint_id: string;
  pipeline_id: string;
  checkpoint_name: string;
  checkpoint_description: string;
  execution_mode: ExecutionMode;
  human_only_config: HumanOnlyConfig;
  human_interaction: HumanInteraction;
  output_artifacts: OutputArtifact[];
  dependencies: Record<string, unknown>;
  inputs: Record<string, unknown>;
  execution: Record<string, unknown>;
  output: Record<string, unknown>;
  instructions: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CheckpointCreate {
  pipeline_id: string;
  checkpoint_name: string;
  checkpoint_description: string;
  execution_mode: 'human_only';
  human_only_config: HumanOnlyConfigCreate;
  human_interaction: HumanInteraction;
  output_artifacts: OutputArtifactCreate[];
}

export interface CheckpointUpdate {
  checkpoint_name?: string;
  checkpoint_description?: string;
  human_only_config?: HumanOnlyConfigCreate;
  human_interaction?: HumanInteraction;
  output_artifacts?: OutputArtifactCreate[];
}

// =============================================================================
// Error Types
// =============================================================================

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

// =============================================================================
// Pipeline Run Types (Slice 6)
// =============================================================================

export type PipelineRunStatus = 'not_started' | 'in_progress' | 'paused' | 'completed' | 'failed';
export type CheckpointExecutionStatus = 'pending' | 'waiting_approval_to_start' | 'in_progress' | 'waiting_approval_to_complete' | 'completed' | 'failed';

export interface PipelineRunSummary {
  run_id: string;
  run_version: number;
  status: PipelineRunStatus;
  created_at: string | null;
  completed_at: string | null;
}

export interface PipelineRunCreate {
  extends_from_run_id?: string;
}

export interface PipelineRun {
  run_id: string;
  pipeline_id: string;
  pipeline_name: string | null;
  run_version: number;
  status: PipelineRunStatus;
  current_checkpoint_id: string | null;
  current_checkpoint_position: number | null;
  previous_run_id: string | null;
  extends_from_run_version: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  paused_at: string | null;
  last_resumed_at: string | null;
  checkpoint_count: number;
  completed_checkpoints: number;
}

export interface CheckpointExecutionSummary {
  execution_id: string;
  checkpoint_id: string;
  checkpoint_name: string | null;
  checkpoint_position: number;
  status: CheckpointExecutionStatus;
  attempt_number: number;
  revision_iteration: number;
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface PipelineRunDetail extends PipelineRun {
  checkpoint_executions: CheckpointExecutionSummary[];
}

export interface PipelineRunListResponse {
  runs: PipelineRunSummary[];
  total_count: number;
}

// =============================================================================
// Checkpoint Execution Detail Types (Slice 7)
// =============================================================================

export interface CheckpointExecutionDetail extends CheckpointExecutionSummary {
  run_id: string;
  temp_workspace_path: string;
  permanent_output_path: string;
  max_attempts: number;
  max_revision_iterations: number;
  failed_at: string | null;
  execution_mode: string | null;
  checkpoint_description: string | null;
  human_only_config: HumanOnlyConfig | null;
  human_interaction_settings: HumanInteraction | null;
  form_data: Record<string, unknown> | null;
  artifacts_staged: Array<{ name: string; size: number }>;
  run_version: number | null;
}

// Re-export InputField as FormField for use in execution context
export type FormField = InputField;
