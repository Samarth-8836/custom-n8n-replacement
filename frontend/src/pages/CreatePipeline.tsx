/**
 * Create Pipeline Page
 */

import { useState } from 'react';
import { api } from '../lib/api';
import type { PipelineCreate } from '../types/pipeline';

export function CreatePipeline() {
  const [formData, setFormData] = useState<PipelineCreate>({
    pipeline_name: '',
    pipeline_description: '',
    auto_advance: false,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.pipeline_name.trim()) {
      newErrors.pipeline_name = 'Pipeline name is required';
    } else if (formData.pipeline_name.length > 255) {
      newErrors.pipeline_name = 'Pipeline name must be 255 characters or less';
    }

    if (formData.pipeline_description && formData.pipeline_description.length > 5000) {
      newErrors.pipeline_description = 'Description must be 5000 characters or less';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const pipeline = await api.createPipeline(formData);

      // Redirect to the pipeline detail page
      window.location.href = `/pipelines/${pipeline.pipeline_id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create pipeline');
      setSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        type === 'checkbox'
          ? (e.target as HTMLInputElement).checked
          : value,
    }));

    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <a
          href="/"
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          ← Back to Pipelines
        </a>
      </div>

      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Create New Pipeline
          </h2>
          <p className="mt-1 text-sm text-gray-600">
            Define a new pipeline with checkpoints for automated execution.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <div>
            <label htmlFor="pipeline_name" className="block text-sm font-medium text-gray-700">
              Pipeline Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="pipeline_name"
              name="pipeline_name"
              value={formData.pipeline_name}
              onChange={handleChange}
              className={`mt-1 block w-full rounded-md shadow-sm py-2 px-3 border ${
                errors.pipeline_name
                  ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                  : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
              } focus:outline-none focus:ring-1 sm:text-sm`}
              placeholder="My Awesome Pipeline"
            />
            {errors.pipeline_name && (
              <p className="mt-1 text-sm text-red-600">{errors.pipeline_name}</p>
            )}
          </div>

          <div>
            <label htmlFor="pipeline_description" className="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="pipeline_description"
              name="pipeline_description"
              value={formData.pipeline_description}
              onChange={handleChange}
              rows={4}
              className={`mt-1 block w-full rounded-md shadow-sm py-2 px-3 border ${
                errors.pipeline_description
                  ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                  : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
              } focus:outline-none focus:ring-1 sm:text-sm`}
              placeholder="Describe what this pipeline does..."
            />
            {errors.pipeline_description && (
              <p className="mt-1 text-sm text-red-600">{errors.pipeline_description}</p>
            )}
          </div>

          <div className="flex items-start">
            <div className="flex items-center h-5">
              <input
                id="auto_advance"
                name="auto_advance"
                type="checkbox"
                checked={formData.auto_advance}
                onChange={handleChange}
                className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
              />
            </div>
            <div className="ml-3 text-sm">
              <label htmlFor="auto_advance" className="font-medium text-gray-700">
                Auto-advance
              </label>
              <p className="text-gray-500">
                Automatically start the next checkpoint after the current one completes.
              </p>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <a
              href="/"
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </a>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Creating...' : 'Create Pipeline'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
