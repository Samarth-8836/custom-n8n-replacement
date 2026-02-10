/**
 * Pipeline Detail Page
 */

import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { PipelineDetail } from '../types/pipeline';
import type { PipelineRunSummary, PipelineRun } from '../types/pipeline';

interface PipelineDetailProps {
  pipelineId: string;
}

export function PipelineDetail({ pipelineId }: PipelineDetailProps) {
  const [pipeline, setPipeline] = useState<PipelineDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reordering, setReordering] = useState(false);

  // Run-related state
  const [runs, setRuns] = useState<PipelineRunSummary[]>([]);
  const [runsLoading, setRunsLoading] = useState(false);
  const [createRunLoading, setCreateRunLoading] = useState(false);
  const [runMessage, setRunMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    const loadPipeline = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getPipeline(pipelineId);
        setPipeline(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load pipeline');
      } finally {
        setLoading(false);
      }
    };

    loadPipeline();
  }, [pipelineId]);

  // Load runs for this pipeline
  useEffect(() => {
    const loadRuns = async () => {
      try {
        setRunsLoading(true);
        const data = await api.listRuns(pipelineId, 1, 5);
        setRuns(data.runs);
      } catch (err) {
        console.error('Failed to load runs:', err);
      } finally {
        setRunsLoading(false);
      }
    };

    loadRuns();
  }, [pipelineId]);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this pipeline?')) {
      return;
    }

    try {
      await api.deletePipeline(pipelineId);
      window.location.href = '/';
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete pipeline');
    }
  };

  const handleDeleteCheckpoint = async (checkpointId: string, checkpointName: string) => {
    if (!confirm(`Are you sure you want to delete checkpoint "${checkpointName}"?`)) {
      return;
    }

    try {
      await api.deleteCheckpoint(checkpointId);
      // Reload pipeline data to update the list
      const data = await api.getPipeline(pipelineId);
      setPipeline(data);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete checkpoint');
    }
  };

  const handleMoveCheckpoint = async (checkpointId: string, direction: 'up' | 'down') => {
    if (!pipeline || pipeline.checkpoints.length < 2) return;

    const currentIndex = pipeline.checkpoints.findIndex(cp => cp.checkpoint_id === checkpointId);
    if (currentIndex === -1) return;

    const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    if (newIndex < 0 || newIndex >= pipeline.checkpoints.length) return;

    try {
      setReordering(true);

      // Create new checkpoint order
      const newOrder = [...pipeline.checkpoints];
      [newOrder[currentIndex], newOrder[newIndex]] = [newOrder[newIndex], newOrder[currentIndex]];

      const checkpointOrderIds = newOrder.map(cp => cp.checkpoint_id);

      await api.reorderCheckpoints(pipelineId, checkpointOrderIds);

      // Reload pipeline data
      const data = await api.getPipeline(pipelineId);
      setPipeline(data);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to reorder checkpoints');
    } finally {
      setReordering(false);
    }
  };

  const handleCreateRun = async () => {
    if (!pipeline || pipeline.checkpoint_count === 0) {
      setRunMessage({ type: 'error', text: 'Pipeline must have at least one checkpoint before running.' });
      return;
    }

    try {
      setCreateRunLoading(true);
      setRunMessage(null);

      const newRun = await api.createRun(pipelineId);

      // Reload runs list
      const data = await api.listRuns(pipelineId, 1, 5);
      setRuns(data.runs);

      setRunMessage({ type: 'success', text: `Run v${newRun.run_version} created!` });

      // Navigate to run detail after a short delay
      setTimeout(() => {
        window.location.href = `/runs/${newRun.run_id}`;
      }, 1000);
    } catch (err) {
      setRunMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to create run' });
    } finally {
      setCreateRunLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getExecutionModeLabel = (mode: string) => {
    switch (mode) {
      case 'human_only':
        return 'Human Only';
      case 'agentic':
        return 'Agentic';
      case 'script':
        return 'Script';
      default:
        return mode;
    }
  };

  const getExecutionModeColor = (mode: string) => {
    switch (mode) {
      case 'human_only':
        return 'bg-green-100 text-green-800';
      case 'agentic':
        return 'bg-purple-100 text-purple-800';
      case 'script':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-sm text-gray-600">Loading pipeline...</p>
        </div>
      </div>
    );
  }

  if (error || !pipeline) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-800">{error || 'Pipeline not found'}</p>
          <a
            href="/"
            className="mt-2 inline-block text-sm text-red-700 underline hover:text-red-900"
          >
            Back to Pipelines
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <a
          href="/"
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          ← Back to Pipelines
        </a>
      </div>

      {/* Header */}
      <div className="bg-white shadow-sm rounded-lg border border-gray-200 mb-6">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">
                {pipeline.pipeline_name}
              </h1>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                v{pipeline.pipeline_definition_version}
              </span>
            </div>
            {pipeline.pipeline_description && (
              <p className="mt-2 text-gray-600">{pipeline.pipeline_description}</p>
            )}
          </div>
          <div className="flex space-x-2">
            {/* Start Pipeline Run button */}
            <button
              onClick={handleCreateRun}
              disabled={createRunLoading || pipeline.checkpoint_count === 0}
              className="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {createRunLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Creating...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Start Run
                </>
              )}
            </button>
            <a
              href={`/pipelines/${pipelineId}/checkpoints/new`}
              className="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              + Add Checkpoint
            </a>
            <a
              href={`/pipelines/${pipelineId}/edit`}
              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Edit
            </a>
            <button
              onClick={handleDelete}
              className="inline-flex items-center px-3 py-2 border border-red-300 rounded-md shadow-sm text-sm font-medium text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              Delete
            </button>
          </div>
        </div>

        {/* Metadata */}
        <div className="px-6 py-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Pipeline ID</span>
            <p className="text-gray-900 font-mono text-xs truncate" title={pipeline.pipeline_id}>
              {pipeline.pipeline_id}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Checkpoints</span>
            <p className="text-gray-900 font-medium">{pipeline.checkpoint_count}</p>
          </div>
          <div>
            <span className="text-gray-500">Created</span>
            <p className="text-gray-900">{formatDate(pipeline.created_at)}</p>
          </div>
          <div>
            <span className="text-gray-500">Last Updated</span>
            <p className="text-gray-900">{formatDate(pipeline.updated_at)}</p>
          </div>
        </div>

        {pipeline.auto_advance && (
          <div className="px-6 pb-4">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
              Auto-advance enabled
            </span>
          </div>
        )}
      </div>

      {/* Checkpoints Section */}
      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Checkpoints</h2>
            <p className="text-sm text-gray-500">
              Execution steps in this pipeline
            </p>
          </div>
          <a
            href={`/pipelines/${pipelineId}/checkpoints/new`}
            className="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            + Add Checkpoint
          </a>
        </div>

        {pipeline.checkpoints.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No checkpoints</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by adding a checkpoint to this pipeline.
            </p>
            <div className="mt-6">
              <a
                href={`/pipelines/${pipelineId}/checkpoints/new`}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                + Add Your First Checkpoint
              </a>
            </div>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {pipeline.checkpoints.map((checkpoint, index) => (
              <li key={checkpoint.checkpoint_id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center flex-1">
                    <div className="flex items-center gap-2">
                      {/* Reorder buttons */}
                      {pipeline.checkpoints.length > 1 && (
                        <div className="flex flex-col gap-1">
                          <button
                            onClick={() => handleMoveCheckpoint(checkpoint.checkpoint_id, 'up')}
                            disabled={reordering || index === 0}
                            className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
                            title="Move up"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7-7" />
                            </svg>
                          </button>
                          <button
                            onClick={() => handleMoveCheckpoint(checkpoint.checkpoint_id, 'down')}
                            disabled={reordering || index === pipeline.checkpoints.length - 1}
                            className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
                            title="Move down"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </button>
                        </div>
                      )}
                      <div className="flex-shrink-0 h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                        <span className="text-sm font-medium text-blue-600">{index + 1}</span>
                      </div>
                    </div>
                    <div className="ml-3 flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-medium text-gray-900">
                          {checkpoint.checkpoint_name}
                        </h4>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getExecutionModeColor(checkpoint.execution_mode)}`}>
                          {getExecutionModeLabel(checkpoint.execution_mode)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">{checkpoint.checkpoint_description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <a
                      href={`/pipelines/${pipelineId}/checkpoints/${checkpoint.checkpoint_id}/edit`}
                      className="inline-flex items-center px-2.5 py-1.5 border border-gray-300 rounded-md shadow-sm text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Edit
                    </a>
                    <button
                      onClick={() => handleDeleteCheckpoint(checkpoint.checkpoint_id, checkpoint.checkpoint_name)}
                      className="inline-flex items-center px-2.5 py-1.5 border border-red-300 rounded-md shadow-sm text-xs font-medium text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Run creation message */}
      {runMessage && (
        <div className={`mt-4 p-4 rounded-md ${runMessage.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <p className={`text-sm ${runMessage.type === 'success' ? 'text-green-800' : 'text-red-800'}`}>
            {runMessage.text}
          </p>
        </div>
      )}

      {/* Pipeline Runs Section */}
      <div className="mt-6 bg-white shadow-sm rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Pipeline Runs</h2>
            <p className="text-sm text-gray-500">
              Execution history for this pipeline
            </p>
          </div>
          <button
            onClick={handleCreateRun}
            disabled={createRunLoading || !pipeline || pipeline.checkpoint_count === 0}
            className="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {createRunLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Creating...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Run
              </>
            )}
          </button>
        </div>

        {runsLoading ? (
          <div className="px-6 py-8 text-center text-sm text-gray-500">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mb-2"></div>
            <p>Loading runs...</p>
          </div>
        ) : runs.length === 0 ? (
          <div className="px-6 py-8 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No runs yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              {!pipeline || pipeline.checkpoint_count === 0
                ? 'Add at least one checkpoint to this pipeline before running.'
                : 'Start your first pipeline run to see execution history.'}
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {runs.map((run) => (
              <li key={run.run_id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex-shrink-0 h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                      <span className="text-sm font-bold text-indigo-600">v{run.run_version}</span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          run.status === 'completed' ? 'bg-green-100 text-green-800' :
                          run.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                          run.status === 'failed' ? 'bg-red-100 text-red-800' :
                          run.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {run.status.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">
                        {run.created_at ? new Date(run.created_at).toLocaleString() : 'Unknown date'}
                      </p>
                    </div>
                  </div>
                  <a
                    href={`/runs/${run.run_id}`}
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md shadow-sm text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    View Details
                  </a>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Info Box */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-blue-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3 flex-1">
            <h3 className="text-sm font-medium text-blue-800">Slice 6 Complete!</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>
                Pipeline run management features are now available:
              </p>
              <ul className="list-disc list-inside mt-1 space-y-1">
                <li>✓ Create new pipeline runs (v1, v2, v3...)</li>
                <li>✓ Start runs (creates first checkpoint execution)</li>
                <li>✓ View run history and status</li>
                <li>✓ Run detail page with checkpoint execution tracking</li>
              </ul>
              <p className="mt-2 text-xs">
                <strong>Coming in Slice 7:</strong> Execute human-only checkpoints (approve start, submit form data, approve complete)
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
