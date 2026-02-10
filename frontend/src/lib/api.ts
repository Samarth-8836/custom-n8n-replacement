/**
 * API Client
 *
 * Handles all HTTP requests to the backend API
 */

import type {
  Pipeline,
  PipelineCreate,
  PipelineDetail,
  PipelineListResponse,
  PipelineUpdate,
  Checkpoint,
  CheckpointCreate,
  CheckpointUpdate,
  CheckpointSummary,
  PipelineRun,
  PipelineRunDetail,
  PipelineRunListResponse,
  PipelineRunCreate,
  CheckpointExecutionDetail,
  FormField,
} from '../types/pipeline';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || error.detail || `HTTP ${response.status}`);
  }
  // Handle 204 No Content responses (empty body)
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  // =============================================================================
  // Pipeline APIs
  // =============================================================================

  /**
   * Get all pipelines with pagination
   */
  async getPipelines(page = 1, pageSize = 50): Promise<PipelineListResponse> {
    const response = await fetch(
      `${API_BASE_URL}/pipelines?page=${page}&page_size=${pageSize}`
    );
    return handleResponse<PipelineListResponse>(response);
  },

  /**
   * Get a single pipeline by ID
   */
  async getPipeline(pipelineId: string): Promise<PipelineDetail> {
    const response = await fetch(`${API_BASE_URL}/pipelines/${pipelineId}`);
    return handleResponse<PipelineDetail>(response);
  },

  /**
   * Create a new pipeline
   */
  async createPipeline(data: PipelineCreate): Promise<Pipeline> {
    const response = await fetch(`${API_BASE_URL}/pipelines`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<Pipeline>(response);
  },

  /**
   * Update a pipeline
   */
  async updatePipeline(pipelineId: string, data: PipelineUpdate): Promise<Pipeline> {
    const response = await fetch(`${API_BASE_URL}/pipelines/${pipelineId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<Pipeline>(response);
  },

  /**
   * Delete a pipeline
   */
  async deletePipeline(pipelineId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/pipelines/${pipelineId}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(response);
  },

  // =============================================================================
  // Checkpoint APIs
  // =============================================================================

  /**
   * Create a new checkpoint for a pipeline
   */
  async createCheckpoint(pipelineId: string, data: Omit<CheckpointCreate, 'pipeline_id'>): Promise<Checkpoint> {
    const response = await fetch(
      `${API_BASE_URL}/checkpoints?pipeline_id=${encodeURIComponent(pipelineId)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return handleResponse<Checkpoint>(response);
  },

  /**
   * Get a checkpoint by ID
   */
  async getCheckpoint(checkpointId: string): Promise<Checkpoint> {
    const response = await fetch(`${API_BASE_URL}/checkpoints/${checkpointId}`);
    return handleResponse<Checkpoint>(response);
  },

  /**
   * List all checkpoints for a pipeline
   */
  async listCheckpoints(pipelineId: string): Promise<CheckpointSummary[]> {
    const response = await fetch(
      `${API_BASE_URL}/checkpoints?pipeline_id=${encodeURIComponent(pipelineId)}`
    );
    return handleResponse<CheckpointSummary[]>(response);
  },

  /**
   * Update a checkpoint
   */
  async updateCheckpoint(checkpointId: string, data: CheckpointUpdate): Promise<Checkpoint> {
    const response = await fetch(`${API_BASE_URL}/checkpoints/${checkpointId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<Checkpoint>(response);
  },

  /**
   * Delete a checkpoint
   */
  async deleteCheckpoint(checkpointId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/checkpoints/${checkpointId}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(response);
  },

  /**
   * Reorder checkpoints in a pipeline
   */
  async reorderCheckpoints(pipelineId: string, checkpointOrder: string[]): Promise<Pipeline> {
    const response = await fetch(`${API_BASE_URL}/pipelines/${pipelineId}/checkpoint-order`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(checkpointOrder),
    });
    return handleResponse<Pipeline>(response);
  },

  // =============================================================================
  // Pipeline Run APIs (Slice 6)
  // =============================================================================

  /**
   * Create a new pipeline run
   */
  async createRun(pipelineId: string, data?: PipelineRunCreate): Promise<PipelineRun> {
    const queryParams = new URLSearchParams({ pipeline_id: pipelineId });
    const response = await fetch(`${API_BASE_URL}/runs?${queryParams}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : JSON.stringify({}),
    });
    return handleResponse<PipelineRun>(response);
  },

  /**
   * Start a pipeline run (creates first checkpoint execution)
   */
  async startRun(runId: string): Promise<PipelineRunDetail> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    return handleResponse<PipelineRunDetail>(response);
  },

  /**
   * Get a pipeline run by ID
   */
  async getRun(runId: string): Promise<PipelineRunDetail> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}`);
    return handleResponse<PipelineRunDetail>(response);
  },

  /**
   * List runs for a pipeline
   */
  async listRuns(pipelineId: string, page = 1, pageSize = 50): Promise<PipelineRunListResponse> {
    const response = await fetch(
      `${API_BASE_URL}/runs?pipeline_id=${encodeURIComponent(pipelineId)}&page=${page}&page_size=${pageSize}`
    );
    return handleResponse<PipelineRunListResponse>(response);
  },

  // =============================================================================
  // Checkpoint Execution APIs (Slice 7)
  // =============================================================================

  /**
   * Get checkpoint execution details
   */
  async getExecution(executionId: string): Promise<CheckpointExecutionDetail> {
    const response = await fetch(`${API_BASE_URL}/executions/${executionId}`);
    return handleResponse<CheckpointExecutionDetail>(response);
  },

  /**
   * Get form fields for a checkpoint execution
   */
  async getExecutionFormFields(executionId: string): Promise<{ form_fields: FormField[] }> {
    const response = await fetch(`${API_BASE_URL}/executions/${executionId}/form-fields`);
    return handleResponse<{ form_fields: FormField[] }>(response);
  },

  /**
   * Approve checkpoint start
   */
  async approveExecutionStart(executionId: string): Promise<{
    execution_id: string;
    status: string;
    started_at: string | null;
    message: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/executions/${executionId}/approve-start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    return handleResponse<{ execution_id: string; status: string; started_at: string | null; message: string }>(response);
  },

  /**
   * Submit form data for a checkpoint execution
   */
  async submitFormData(executionId: string, formData: Record<string, unknown>): Promise<{
    execution_id: string;
    status: string;
    artifacts_created: Array<{ artifact_id: string; artifact_name: string; file_path: string; format: string }>;
    run_status?: string;
    next_checkpoint_id?: string;
    message: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/executions/${executionId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ form_data: formData }),
    });
    return handleResponse<{
      execution_id: string;
      status: string;
      artifacts_created: Array<{ artifact_id: string; artifact_name: string; file_path: string; format: string }>;
      run_status?: string;
      next_checkpoint_id?: string;
      message: string;
    }>(response);
  },

  /**
   * Approve checkpoint completion
   */
  async approveExecutionComplete(executionId: string, promoteArtifacts = true): Promise<{
    execution_id: string;
    status: string;
    completed_at: string | null;
    promoted_artifacts: Array<{ artifact_name: string; permanent_path: string }>;
    run_status: string;
    next_checkpoint_id: string | null;
    next_execution_id: string | null;
    message: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/executions/${executionId}/approve-complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ promote_artifacts: promoteArtifacts }),
    });
    return handleResponse<{
      execution_id: string;
      status: string;
      completed_at: string | null;
      promoted_artifacts: Array<{ artifact_name: string; permanent_path: string }>;
      run_status: string;
      next_checkpoint_id: string | null;
      next_execution_id: string | null;
      message: string;
    }>(response);
  },

  /**
   * Request a revision for a checkpoint execution
   */
  async requestRevision(executionId: string, feedback: string): Promise<{
    execution_id: string;
    status: string;
    revision_iteration: number;
    max_revision_iterations: number;
    message: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/executions/${executionId}/request-revision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback }),
    });
    return handleResponse<{
      execution_id: string;
      status: string;
      revision_iteration: number;
      max_revision_iterations: number;
      message: string;
    }>(response);
  },
};
