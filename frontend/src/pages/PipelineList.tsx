/**
 * Pipeline List Page
 */

import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { Pipeline } from '../types/pipeline';
import { PipelineCard } from '../components/PipelineCard';

export function PipelineList() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPipelines = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getPipelines();
      setPipelines(response.pipelines);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pipelines');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this pipeline?')) {
      return;
    }

    try {
      await api.deletePipeline(id);
      setPipelines((prev) => prev.filter((p) => p.pipeline_id !== id));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete pipeline');
    }
  };

  useEffect(() => {
    loadPipelines();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Pipelines</h2>
        <a
          href="/pipelines/new"
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Create Pipeline
        </a>
      </div>

      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-sm text-gray-600">Loading pipelines...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <p className="text-sm text-red-800">{error}</p>
          <button
            onClick={loadPipelines}
            className="mt-2 text-sm text-red-700 underline hover:text-red-900"
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && pipelines.length === 0 && (
        <div className="text-center py-12">
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
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No pipelines</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating a new pipeline.
          </p>
          <div className="mt-6">
            <a
              href="/pipelines/new"
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              Create Pipeline
            </a>
          </div>
        </div>
      )}

      {!loading && !error && pipelines.length > 0 && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {pipelines.map((pipeline) => (
            <PipelineCard
              key={pipeline.pipeline_id}
              pipeline={pipeline}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
