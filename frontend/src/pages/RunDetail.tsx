/**
 * Pipeline Run Detail Page
 *
 * Displays the status and progress of a pipeline run.
 * Shows checkpoint executions and allows interaction for human-only checkpoints.
 */

import { useEffect, useState, useCallback } from 'react';
import type { PipelineRunDetail, CheckpointExecutionDetail, FormField } from '../types/pipeline';
import { api } from '../lib/api';

interface RunDetailProps {
  runId: string;
}

// Render a form input field based on its type
function FormInput({ field, value, onChange, error }: {
  field: FormField;
  value: string | number | boolean;
  onChange: (val: string | number | boolean) => void;
  error?: string;
}) {
  const inputId = `field-${field.name}`;

  switch (field.type) {
    case 'text':
      return (
        <input
          id={inputId}
          type="text"
          value={String(value || '')}
          onChange={(e) => onChange(e.target.value)}
          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            error ? 'border-red-300' : 'border-gray-300'
          }`}
          placeholder={field.default || ''}
        />
      );

    case 'multiline_text':
      return (
        <textarea
          id={inputId}
          value={String(value || '')}
          onChange={(e) => onChange(e.target.value)}
          rows={4}
          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            error ? 'border-red-300' : 'border-gray-300'
          }`}
          placeholder={field.default || ''}
        />
      );

    case 'number':
      return (
        <input
          id={inputId}
          type="number"
          value={value === '' ? '' : Number(value || 0)}
          onChange={(e) => onChange(e.target.value ? Number(e.target.value) : '')}
          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            error ? 'border-red-300' : 'border-gray-300'
          }`}
          placeholder={field.default || '0'}
        />
      );

    case 'boolean':
      return (
        <div className="flex items-center gap-2">
          <input
            id={inputId}
            type="checkbox"
            checked={Boolean(value)}
            onChange={(e) => onChange(e.target.checked)}
            className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
          />
          <label htmlFor={inputId} className="text-sm text-gray-700">
            {field.label}
          </label>
        </div>
      );

    case 'file':
      return (
        <input
          id={inputId}
          type="file"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              onChange(file.name);
            }
          }}
          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            error ? 'border-red-300' : 'border-gray-300'
          }`}
        />
      );

    default:
      return (
        <input
          id={inputId}
          type="text"
          value={String(value || '')}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
        />
      );
  }
}

// Render a checkpoint execution with its controls
function CheckpointExecutionCard({
  execution,
  onAction,
  loading
}: {
  execution: CheckpointExecutionDetail;
  onAction: (action: string, data?: unknown) => Promise<void>;
  loading: boolean;
}) {
  const [formData, setFormData] = useState<Record<string, string | number | boolean>>({});
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [revisionFeedback, setRevisionFeedback] = useState('');
  const [showRevisionInput, setShowRevisionInput] = useState(false);

  const inputFields = execution.human_only_config?.input_fields || [];
  const instructions = execution.human_only_config?.instructions || '';

  // Initialize form data with default values or previously submitted data (for revisions)
  useEffect(() => {
    const defaults: Record<string, string | number | boolean> = {};

    // If there's previously submitted form data and we're in a revision (in_progress after being submitted),
    // load the previous data for editing
    if (execution.form_data && execution.status === 'in_progress' && execution.revision_iteration > 0) {
      inputFields.forEach((field) => {
        defaults[field.name] = execution.form_data![field.name] as string | number | boolean || field.default || '';
      });
    } else {
      // Use field defaults for initial submission
      inputFields.forEach((field) => {
        if (field.default !== undefined) {
          defaults[field.name] = field.default;
        } else if (field.type === 'boolean') {
          defaults[field.name] = false;
        } else if (field.type === 'number') {
          defaults[field.name] = 0;
        } else {
          defaults[field.name] = '';
        }
      });
    }

    setFormData(defaults);
    setFormErrors({}); // Clear any previous errors
  }, [execution.execution_id, execution.status, execution.revision_iteration, execution.form_data, inputFields]);

  const handleFieldChange = (fieldName: string, value: string | number | boolean) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }));
    // Clear error when user starts typing
    if (formErrors[fieldName]) {
      setFormErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[fieldName];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};
    inputFields.forEach((field) => {
      if (field.required && !formData[field.name]) {
        errors[field.name] = `${field.label} is required`;
      }
    });
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleApproveStart = async () => {
    await onAction('approve-start');
  };

  const handleSubmitForm = async () => {
    if (!validateForm()) return;
    await onAction('submit', formData);
  };

  const handleApproveComplete = async () => {
    await onAction('approve-complete');
  };

  const handleRequestRevision = async () => {
    if (!revisionFeedback.trim()) {
      return;
    }
    await onAction('request-revision', { feedback: revisionFeedback });
    setRevisionFeedback('');
    setShowRevisionInput(false);
  };

  const statusColor = {
    pending: 'bg-gray-100 text-gray-800 border-gray-300',
    waiting_approval_to_start: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    in_progress: 'bg-blue-100 text-blue-800 border-blue-300',
    waiting_approval_to_complete: 'bg-green-100 text-green-800 border-green-300',
    completed: 'bg-green-100 text-green-800 border-green-300',
    failed: 'bg-red-100 text-red-800 border-red-300',
  }[execution.status] || 'bg-gray-100 text-gray-800 border-gray-300';

  return (
    <div className={`border rounded-lg p-6 ${statusColor}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-white/50 text-sm font-bold">
            {execution.checkpoint_position + 1}
          </span>
          <div>
            <h3 className="font-bold text-lg">
              {execution.checkpoint_name || `Checkpoint ${execution.checkpoint_position + 1}`}
            </h3>
            <p className="text-sm opacity-75 capitalize">
              Status: {execution.status.replace(/_/g, ' ')}
            </p>
          </div>
        </div>
        {execution.attempt_number > 1 && (
          <span className="text-sm px-2 py-1 bg-white/50 rounded">
            Attempt {execution.attempt_number}/{execution.max_attempts}
          </span>
        )}
      </div>

      {/* Instructions for human-only checkpoints */}
      {instructions && execution.status !== 'completed' && (
        <div className="mb-4 p-3 bg-white/50 rounded-lg">
          <p className="text-sm font-medium mb-1">Instructions:</p>
          <p className="text-sm whitespace-pre-wrap">{instructions}</p>
        </div>
      )}

      {/* Form for in_progress status */}
      {execution.status === 'in_progress' && inputFields.length > 0 && (
        <div className="mb-4 space-y-4">
          <h4 className="font-medium">Please fill out the form below:</h4>
          {inputFields.map((field) => (
            <div key={field.name}>
              <label htmlFor={`field-${field.name}`} className="block text-sm font-medium text-gray-700 mb-1">
                {field.label}
                {field.required && <span className="text-red-500 ml-1">*</span>}
              </label>
              <FormInput
                field={field}
                value={formData[field.name]}
                onChange={(val) => handleFieldChange(field.name, val)}
                error={formErrors[field.name]}
              />
              {formErrors[field.name] && (
                <p className="mt-1 text-sm text-red-600">{formErrors[field.name]}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3">
        {execution.status === 'waiting_approval_to_start' && (
          <button
            onClick={handleApproveStart}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Processing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Approve Start
              </>
            )}
          </button>
        )}

        {execution.status === 'in_progress' && inputFields.length > 0 && (
          <button
            onClick={handleSubmitForm}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Submitting...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Submit Form
              </>
            )}
          </button>
        )}

        {/* For checkpoints with no input fields, show a continue button */}
        {execution.status === 'in_progress' && inputFields.length === 0 && (
          <button
            onClick={handleSubmitForm}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Processing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Continue
              </>
            )}
          </button>
        )}

        {execution.status === 'waiting_approval_to_complete' && (
          <>
            <button
              onClick={handleApproveComplete}
              disabled={loading}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Processing...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Approve & Complete
                </>
              )}
            </button>
            {!showRevisionInput ? (
              <button
                onClick={() => setShowRevisionInput(true)}
                disabled={loading}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                </svg>
                Request Revision
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={revisionFeedback}
                  onChange={(e) => setRevisionFeedback(e.target.value)}
                  placeholder="Enter revision feedback..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                />
                <button
                  onClick={handleRequestRevision}
                  disabled={loading || !revisionFeedback.trim()}
                  className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  Submit
                </button>
                <button
                  onClick={() => {
                    setShowRevisionInput(false);
                    setRevisionFeedback('');
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            )}
            {execution.revision_iteration < execution.max_revision_iterations && (
              <p className="text-sm text-gray-600 ml-auto">
                Revisions: {execution.revision_iteration}/{execution.max_revision_iterations}
              </p>
            )}
          </>
        )}

        {execution.status === 'completed' && (
          <span className="px-4 py-2 bg-white/50 text-green-800 rounded-lg flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Completed
            {execution.completed_at && (
              <span className="text-sm">
                at {new Date(execution.completed_at).toLocaleTimeString()}
              </span>
            )}
          </span>
        )}

        {execution.status === 'failed' && (
          <span className="px-4 py-2 bg-white/50 text-red-800 rounded-lg flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            Failed
            {execution.failed_at && (
              <span className="text-sm">
                at {new Date(execution.failed_at).toLocaleTimeString()}
              </span>
            )}
          </span>
        )}
      </div>

      {/* Display submitted form data for waiting_approval_to_complete */}
      {execution.status === 'waiting_approval_to_complete' && execution.form_data && (
        <div className="mt-4 p-3 bg-white/50 rounded-lg">
          <p className="text-sm font-medium mb-2">Submitted Data:</p>
          <pre className="text-xs overflow-auto max-h-40">
            {JSON.stringify(execution.form_data, null, 2)}
          </pre>
        </div>
      )}

      {/* Display staged artifacts */}
      {execution.artifacts_staged.length > 0 && (
        <div className="mt-4 p-3 bg-white/50 rounded-lg">
          <p className="text-sm font-medium mb-2">Staged Artifacts:</p>
          <ul className="text-sm space-y-1">
            {execution.artifacts_staged.map((artifact, idx) => (
              <li key={idx} className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                </svg>
                {artifact.name} ({(artifact.size / 1024).toFixed(1)} KB)
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function RunDetail({ runId }: RunDetailProps) {
  const [run, setRun] = useState<PipelineRunDetail | null>(null);
  const [currentExecution, setCurrentExecution] = useState<CheckpointExecutionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!runId) return;

    try {
      setLoading(true);
      const data = await api.getRun(runId);
      setRun(data);
      setError(null);

      // Load current execution details if available
      if (data.current_checkpoint_id && data.checkpoint_executions.length > 0) {
        // Find the current pending/active execution
        const currentExec = data.checkpoint_executions.find(
          (e) => e.status !== 'completed' && e.status !== 'failed'
        );
        if (currentExec) {
          try {
            const execDetail = await api.getExecution(currentExec.execution_id);
            setCurrentExecution(execDetail);
          } catch {
            setCurrentExecution(null);
          }
        } else {
          setCurrentExecution(null);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load run');
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleExecutionAction = async (action: string, data?: unknown) => {
    if (!currentExecution) return;

    try {
      setActionLoading(true);
      setActionMessage(null);

      let result;
      switch (action) {
        case 'approve-start':
          result = await api.approveExecutionStart(currentExecution.execution_id);
          break;
        case 'submit':
          result = await api.submitFormData(currentExecution.execution_id, data as Record<string, unknown>);
          // Update execution state with returned form data immediately
          if (result.form_data && currentExecution) {
            setCurrentExecution({
              ...currentExecution,
              form_data: result.form_data,
              status: result.status || currentExecution.status
            });
          }
          // Check if pipeline was completed (auto-complete without approval)
          if (result.run_status === 'completed') {
            setActionMessage('Pipeline completed successfully! 🎉');
            // Clear current execution immediately when pipeline completes
            setCurrentExecution(null);
          }
          break;
        case 'approve-complete':
          result = await api.approveExecutionComplete(currentExecution.execution_id);
          // Check if pipeline is completed
          if (result.run_status === 'completed') {
            setActionMessage('Pipeline completed successfully! 🎉');
            // Clear current execution immediately when pipeline completes
            setCurrentExecution(null);
          } else {
            setActionMessage('Checkpoint completed. Moving to next checkpoint...');
          }
          // Refresh data after completion
          setTimeout(() => {
            fetchData();
          }, 1000);
          break;
        case 'request-revision':
          result = await api.requestRevision(
            currentExecution.execution_id,
            (data as { feedback: string }).feedback
          );
          setActionMessage(`Revision requested. Status: ${result.status}`);
          break;
        default:
          throw new Error(`Unknown action: ${action}`);
      }

      if (action !== 'approve-complete') {
        setActionMessage(result.message || 'Action completed successfully');
      }

      // Refresh execution data
      setTimeout(() => {
        fetchData();
      }, 500);

      setTimeout(() => setActionMessage(null), 3000);
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Action failed');
      setTimeout(() => setActionMessage(null), 5000);
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartRun = async () => {
    if (!runId) return;

    try {
      setActionLoading(true);
      setActionMessage(null);
      const data = await api.startRun(runId);
      setRun(data);
      setActionMessage('Run started successfully!');
      setTimeout(() => {
        fetchData();
        setActionMessage(null);
      }, 1000);
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Failed to start run');
      setTimeout(() => setActionMessage(null), 3000);
    } finally {
      setActionLoading(false);
    }
  };

  const handlePauseRun = async () => {
    if (!runId) return;

    try {
      setActionLoading(true);
      setActionMessage(null);
      const data = await api.pauseRun(runId);
      setRun(data);
      setActionMessage('Run paused successfully!');
      setTimeout(() => {
        fetchData();
        setActionMessage(null);
      }, 1000);
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Failed to pause run');
      setTimeout(() => setActionMessage(null), 3000);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResumeRun = async () => {
    if (!runId) return;

    try {
      setActionLoading(true);
      setActionMessage(null);
      const data = await api.resumeRun(runId);
      setRun(data);
      setActionMessage('Run resumed successfully!');
      setTimeout(() => {
        fetchData();
        setActionMessage(null);
      }, 1000);
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Failed to resume run');
      setTimeout(() => setActionMessage(null), 3000);
    } finally {
      setActionLoading(false);
    }
  };

  // Check if we can pause - allow pausing whenever run is in_progress
  // Pause should be available before starting a checkpoint or between checkpoints
  const canPause = run?.status === 'in_progress';

  // When paused, hide all checkpoint controls - user must resume first
  const isPaused = run?.status === 'paused';

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      case 'not_started':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading run details...</p>
        </div>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h1 className="text-xl font-semibold text-red-800 mb-2">Error</h1>
          <p className="text-red-600">{error || 'Run not found'}</p>
          <a
            href="/"
            className="mt-4 inline-block px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Go Back
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <a
            href={`/pipelines/${run.pipeline_id}`}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Go to pipeline"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </a>
          <h1 className="text-2xl font-bold text-gray-900">
            {run.pipeline_name || 'Pipeline'} - Run v{run.run_version}
          </h1>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(run.status)}`}>
            {run.status.replace('_', ' ')}
          </span>
        </div>

        {/* Pause/Resume Buttons in Header */}
        <div className="flex items-center gap-2">
          {canPause && (
            <button
              onClick={handlePauseRun}
              disabled={actionLoading}
              className="px-3 py-1.5 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 text-sm font-medium"
              title="Pause the pipeline"
            >
              {actionLoading ? (
                <>
                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                  Pausing...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  Pause
                </>
              )}
            </button>
          )}
          {isPaused && (
            <button
              onClick={handleResumeRun}
              disabled={actionLoading}
              className="px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 text-sm font-medium"
              title="Resume the pipeline"
            >
              {actionLoading ? (
                <>
                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                  Resuming...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                  </svg>
                  Resume
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Action Messages */}
      {actionMessage && (
        <div className={`mb-4 p-3 rounded-lg ${
          actionMessage.includes('success') || actionMessage.includes('completed') || actionMessage.includes('🎉')
            ? 'bg-green-50 text-green-800'
            : 'bg-red-50 text-red-800'
        }`}>
          {actionMessage}
        </div>
      )}

      {/* Run Info Card */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Run Information</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">Version</p>
            <p className="font-medium">v{run.run_version}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Status</p>
            <p className="font-medium capitalize">{run.status.replace('_', ' ')}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Progress</p>
            <p className="font-medium">{run.completed_checkpoints} / {run.checkpoint_count} checkpoints</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Created</p>
            <p className="font-medium">{new Date(run.created_at).toLocaleString()}</p>
          </div>
          {run.started_at && (
            <div>
              <p className="text-sm text-gray-500">Started</p>
              <p className="font-medium">{new Date(run.started_at).toLocaleString()}</p>
            </div>
          )}
          {run.completed_at && (
            <div>
              <p className="text-sm text-gray-500">Completed</p>
              <p className="font-medium">{new Date(run.completed_at).toLocaleString()}</p>
            </div>
          )}
          {run.previous_run_id && (
            <div>
              <p className="text-sm text-gray-500">Extends From</p>
              <p className="font-medium">v{run.extends_from_run_version}</p>
            </div>
          )}
          <div>
            <p className="text-sm text-gray-500">Run ID</p>
            <p className="font-medium text-xs font-mono">{run.run_id.slice(0, 8)}...</p>
          </div>
        </div>

        {/* Progress Bar */}
        {run.checkpoint_count > 0 && (
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Progress</span>
              <span>{Math.round((run.completed_checkpoints / run.checkpoint_count) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${(run.completed_checkpoints / run.checkpoint_count) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Start Run Button */}
        {run.status === 'not_started' && (
          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={handleStartRun}
              disabled={actionLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {actionLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Starting...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Start Pipeline Run
                </>
              )}
            </button>
            <p className="text-sm text-gray-500">
              This will create the first checkpoint execution and begin the pipeline.
            </p>
          </div>
        )}
      </div>

      {/* Current Execution (if active) - Hide when paused */}
      {!isPaused && currentExecution && currentExecution.status !== 'completed' && currentExecution.status !== 'failed' && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-4">Current Checkpoint</h2>
          <CheckpointExecutionCard
            execution={currentExecution}
            onAction={handleExecutionAction}
            loading={actionLoading}
          />
        </div>
      )}

      {/* Paused State Message - Show instead of current execution when paused */}
      {isPaused && (
        <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <svg className="w-12 h-12 text-yellow-600 mx-auto mb-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <h3 className="text-lg font-semibold text-yellow-900 mb-2">Pipeline is Paused</h3>
          <p className="text-sm text-yellow-800 mb-4">
            Resume the pipeline to continue with the next checkpoint.
          </p>
          {currentExecution && (
            <p className="text-xs text-yellow-700">
              Current checkpoint: {currentExecution.checkpoint_name || `Checkpoint ${currentExecution.checkpoint_position + 1}`}
            </p>
          )}
        </div>
      )}

      {/* Checkpoint Executions */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Checkpoint Executions</h2>

        {run.checkpoint_executions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No checkpoint executions yet.</p>
            {run.status === 'not_started' && (
              <p className="mt-2">Start the run to begin executing checkpoints.</p>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {run.checkpoint_executions.map((execution) => {
              // If this is the current active execution, don't render it here
              if (currentExecution && currentExecution.execution_id === execution.execution_id &&
                  currentExecution.status !== 'completed' && currentExecution.status !== 'failed') {
                return null;
              }

              const statusColor = {
                completed: 'bg-green-100 text-green-800 border-green-300',
                in_progress: 'bg-blue-100 text-blue-800 border-blue-300',
                failed: 'bg-red-100 text-red-800 border-red-300',
                waiting_approval_to_start:
                'bg-yellow-100 text-yellow-800 border-yellow-300',
                waiting_approval_to_complete:
                'bg-green-50 text-green-700 border-green-200',
                pending: 'bg-gray-100 text-gray-800 border-gray-300',
              }[execution.status] || 'bg-gray-100 text-gray-800 border-gray-300';

              return (
                <div
                  key={execution.execution_id}
                  className={`border rounded-lg p-4 ${statusColor}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-white/50 text-sm font-medium">
                        {execution.checkpoint_position + 1}
                      </span>
                      <div>
                        <h3 className="font-medium">
                          {execution.checkpoint_name || `Checkpoint ${execution.checkpoint_position + 1}`}
                        </h3>
                        <p className="text-sm opacity-75 capitalize">
                          Status: {execution.status.replace(/_/g, ' ')}
                        </p>
                      </div>
                    </div>
                    <div className="text-right text-sm">
                      {execution.attempt_number > 1 && (
                        <p className="opacity-75">Attempt {execution.attempt_number}</p>
                      )}
                      {execution.completed_at && (
                        <p className="opacity-75">
                          {new Date(execution.completed_at).toLocaleTimeString()}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Info Box for Slice 7 */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">ℹ️ Slice 7 & 8 Features</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Approve checkpoint start (for checkpoints requiring approval)</li>
          <li>• Fill out forms for human-only checkpoints</li>
          <li>• Approve checkpoint completion with artifact promotion</li>
          <li>• Request revisions with feedback</li>
          <li>• Automatic progression to next checkpoint</li>
          <li>• Pause pipeline between checkpoints (Slice 8)</li>
          <li>• Resume paused pipeline (Slice 8)</li>
        </ul>
      </div>
    </div>
  );
}
