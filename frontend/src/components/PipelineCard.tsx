/**
 * Pipeline Card Component
 */

import type { Pipeline } from '../types/pipeline';

interface PipelineCardProps {
  pipeline: Pipeline;
  onDelete?: (id: string) => void;
}

export function PipelineCard({ pipeline, onDelete }: PipelineCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">
            {pipeline.pipeline_name}
          </h3>
          {pipeline.pipeline_description && (
            <p className="mt-1 text-sm text-gray-600 line-clamp-2">
              {pipeline.pipeline_description}
            </p>
          )}
        </div>
        <div className="ml-4 flex space-x-2">
          <a
            href={`/pipelines/${pipeline.pipeline_id}`}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            View
          </a>
          {onDelete && (
            <button
              onClick={() => onDelete(pipeline.pipeline_id)}
              className="text-red-600 hover:text-red-800 text-sm font-medium"
            >
              Delete
            </button>
          )}
        </div>
      </div>

      <div className="mt-4 flex items-center text-sm text-gray-500">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          v{pipeline.pipeline_definition_version}
        </span>
        <span className="mx-2">•</span>
        <span>{pipeline.checkpoint_count} checkpoints</span>
        <span className="mx-2">•</span>
        <span>Created {formatDate(pipeline.created_at)}</span>
      </div>

      {pipeline.auto_advance && (
        <div className="mt-2">
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
            Auto-advance enabled
          </span>
        </div>
      )}
    </div>
  );
}
