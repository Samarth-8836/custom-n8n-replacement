/**
 * Edit Checkpoint Page
 */

import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import type {
  InputFieldCreate,
  OutputArtifactCreate,
  HumanInteraction,
  HumanOnlyConfigCreate,
  Checkpoint,
  InputFieldType,
  ArtifactFormat,
} from '../types/pipeline';

interface EditCheckpointProps {
  pipelineId: string;
  checkpointId: string;
}

export function EditCheckpoint({ pipelineId, checkpointId }: EditCheckpointProps) {
  const [pipelineName, setPipelineName] = useState<string>('');
  const [checkpoint, setCheckpoint] = useState<Checkpoint | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Basic info
  const [checkpointName, setCheckpointName] = useState('');
  const [checkpointDescription, setCheckpointDescription] = useState('');
  const [nameError, setNameError] = useState('');
  const [descriptionError, setDescriptionError] = useState('');

  // Human-only config
  const [instructions, setInstructions] = useState('');
  const [inputFields, setInputFields] = useState<InputFieldCreate[]>([]);
  const [saveAsArtifact, setSaveAsArtifact] = useState(false);
  const [artifactName, setArtifactName] = useState('');
  const [artifactFormat, setArtifactFormat] = useState<'json' | 'md'>('json');

  // Human interaction
  const [requiresApprovalToStart, setRequiresApprovalToStart] = useState(false);
  const [requiresApprovalToComplete, setRequiresApprovalToComplete] = useState(false);
  const [maxRevisionIterations, setMaxRevisionIterations] = useState(3);

  // Output artifacts
  const [outputArtifacts, setOutputArtifacts] = useState<OutputArtifactCreate[]>([]);

  // New input field form
  const [newFieldName, setNewFieldName] = useState('');
  const [newFieldType, setNewFieldType] = useState<InputFieldType>('text');
  const [newFieldLabel, setNewFieldLabel] = useState('');
  const [newFieldRequired, setNewFieldRequired] = useState(true);
  const [newFieldDefault, setNewFieldDefault] = useState('');

  // New output artifact form
  const [newArtifactName, setNewArtifactName] = useState('');
  const [newArtifactFormat, setNewArtifactFormat] = useState<ArtifactFormat>('json');
  const [newArtifactDescription, setNewArtifactDescription] = useState('');

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Load pipeline and checkpoint in parallel
        const [pipelineData, checkpointData] = await Promise.all([
          api.getPipeline(pipelineId),
          api.getCheckpoint(checkpointId),
        ]);

        setPipelineName(pipelineData.pipeline_name);
        setCheckpoint(checkpointData);

        // Pre-fill form with checkpoint data
        setCheckpointName(checkpointData.checkpoint_name);
        setCheckpointDescription(checkpointData.checkpoint_description);

        // Human-only config
        const humanOnlyConfig = checkpointData.human_only_config;
        setInstructions(humanOnlyConfig.instructions);
        setInputFields(humanOnlyConfig.input_fields.map((f) => ({
          name: f.name,
          type: f.type,
          label: f.label,
          required: f.required,
          default: f.default,
        })));
        setSaveAsArtifact(humanOnlyConfig.save_as_artifact);
        setArtifactName(humanOnlyConfig.artifact_name || '');
        setArtifactFormat(humanOnlyConfig.artifact_format);

        // Human interaction
        setRequiresApprovalToStart(checkpointData.human_interaction.requires_approval_to_start);
        setRequiresApprovalToComplete(checkpointData.human_interaction.requires_approval_to_complete);
        setMaxRevisionIterations(checkpointData.human_interaction.max_revision_iterations);

        // Output artifacts
        setOutputArtifacts(checkpointData.output_artifacts.map((a) => ({
          name: a.name,
          format: a.format,
          description: a.description,
        })));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load checkpoint data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [pipelineId, checkpointId]);

  const handleAddInputField = () => {
    if (!newFieldName.trim() || !newFieldLabel.trim()) {
      alert('Please provide both name and label for the input field');
      return;
    }

    const newField: InputFieldCreate = {
      name: newFieldName.trim(),
      type: newFieldType,
      label: newFieldLabel.trim(),
      required: newFieldRequired,
      default: newFieldDefault.trim() || undefined,
    };

    setInputFields([...inputFields, newField]);

    // Reset form
    setNewFieldName('');
    setNewFieldLabel('');
    setNewFieldDefault('');
    setNewFieldRequired(true);
  };

  const handleRemoveInputField = (index: number) => {
    setInputFields(inputFields.filter((_, i) => i !== index));
  };

  const handleAddOutputArtifact = () => {
    if (!newArtifactName.trim()) {
      alert('Please provide a name for the output artifact');
      return;
    }

    const newArtifact: OutputArtifactCreate = {
      name: newArtifactName.trim(),
      format: newArtifactFormat,
      description: newArtifactDescription.trim() || undefined,
    };

    setOutputArtifacts([...outputArtifacts, newArtifact]);

    // Reset form
    setNewArtifactName('');
    setNewArtifactDescription('');
  };

  const handleRemoveOutputArtifact = (index: number) => {
    setOutputArtifacts(outputArtifacts.filter((_, i) => i !== index));
  };

  const validateForm = (): boolean => {
    let isValid = true;

    if (!checkpointName.trim()) {
      setNameError('Checkpoint name is required');
      isValid = false;
    } else if (checkpointName.length > 255) {
      setNameError('Checkpoint name must be 255 characters or less');
      isValid = false;
    } else {
      setNameError('');
    }

    if (!checkpointDescription.trim()) {
      setDescriptionError('Checkpoint description is required');
      isValid = false;
    } else if (checkpointDescription.length > 5000) {
      setDescriptionError('Description must be 5000 characters or less');
      isValid = false;
    } else {
      setDescriptionError('');
    }

    if (!instructions.trim()) {
      alert('Please provide instructions for the human-only checkpoint');
      return false;
    }

    if (saveAsArtifact && !artifactName.trim()) {
      alert('Please provide an artifact name when "Save as Artifact" is enabled');
      return false;
    }

    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const humanOnlyConfig: HumanOnlyConfigCreate = {
        instructions: instructions.trim(),
        input_fields: inputFields,
        save_as_artifact: saveAsArtifact,
        artifact_name: artifactName.trim() || undefined,
        artifact_format: artifactFormat,
      };

      const humanInteraction: HumanInteraction = {
        requires_approval_to_start: requiresApprovalToStart,
        requires_approval_to_complete: requiresApprovalToComplete,
        max_revision_iterations: maxRevisionIterations,
      };

      await api.updateCheckpoint(checkpointId, {
        checkpoint_name: checkpointName.trim(),
        checkpoint_description: checkpointDescription.trim(),
        human_only_config: humanOnlyConfig,
        human_interaction: humanInteraction,
        output_artifacts: outputArtifacts,
      });

      // Redirect to pipeline detail page
      window.location.href = `/pipelines/${pipelineId}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update checkpoint');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-sm text-gray-600">Loading checkpoint...</p>
        </div>
      </div>
    );
  }

  if (error && !checkpoint) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-800">{error}</p>
          <a
            href={`/pipelines/${pipelineId}`}
            className="mt-2 inline-block text-sm text-red-700 underline hover:text-red-900"
          >
            Back to Pipeline
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <a
          href={`/pipelines/${pipelineId}`}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          ← Back to Pipeline
        </a>
      </div>

      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Edit Checkpoint</h1>
            <p className="text-sm text-gray-500 mt-1">
              For pipeline: <span className="font-medium text-gray-700">{pipelineName}</span>
            </p>
          </div>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'Saving...' : 'Save Changes'}
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Basic Information */}
          <section>
            <h2 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h2>

            <div className="space-y-4">
              <div>
                <label htmlFor="checkpointName" className="block text-sm font-medium text-gray-700">
                  Checkpoint Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="checkpointName"
                  value={checkpointName}
                  onChange={(e) => setCheckpointName(e.target.value)}
                  maxLength={255}
                  className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                    nameError
                      ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                      : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
                  }`}
                  placeholder="e.g., Gather Requirements"
                />
                {nameError && <p className="mt-1 text-sm text-red-600">{nameError}</p>}
              </div>

              <div>
                <label htmlFor="checkpointDescription" className="block text-sm font-medium text-gray-700">
                  Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="checkpointDescription"
                  value={checkpointDescription}
                  onChange={(e) => setCheckpointDescription(e.target.value)}
                  rows={3}
                  maxLength={5000}
                  className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                    descriptionError
                      ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                      : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
                  }`}
                  placeholder="Describe what this checkpoint does..."
                />
                {descriptionError && <p className="mt-1 text-sm text-red-600">{descriptionError}</p>}
              </div>
            </div>
          </section>

          <hr />

          {/* Human-Only Configuration */}
          <section>
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Human-Only Configuration
            </h2>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
              <p className="text-sm text-blue-800">
                <strong>Human-only mode</strong> collects input from users through a form.
                This is the simplest checkpoint type - agentic and script modes will be added in future updates.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label htmlFor="instructions" className="block text-sm font-medium text-gray-700">
                  Instructions <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="instructions"
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  rows={4}
                  maxLength={5000}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  placeholder="Provide instructions for the user completing this checkpoint..."
                />
                <p className="mt-1 text-xs text-gray-500">
                  These instructions will be shown to the user when they complete this checkpoint.
                </p>
              </div>

              {/* Input Fields */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Input Fields
                  </label>
                  <span className="text-xs text-gray-500">
                    {inputFields.length} field{inputFields.length !== 1 ? 's' : ''} added
                  </span>
                </div>

                {/* Add Input Field Form */}
                <div className="bg-gray-50 rounded-md p-4 mb-3 space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label htmlFor="newFieldName" className="block text-xs font-medium text-gray-700">
                        Field Name
                      </label>
                      <input
                        type="text"
                        id="newFieldName"
                        value={newFieldName}
                        onChange={(e) => setNewFieldName(e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        placeholder="e.g., user_email"
                      />
                    </div>
                    <div>
                      <label htmlFor="newFieldType" className="block text-xs font-medium text-gray-700">
                        Field Type
                      </label>
                      <select
                        id="newFieldType"
                        value={newFieldType}
                        onChange={(e) => setNewFieldType(e.target.value as InputFieldType)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      >
                        <option value="text">Text</option>
                        <option value="multiline_text">Multiline Text</option>
                        <option value="number">Number</option>
                        <option value="boolean">Boolean</option>
                        <option value="file">File Upload</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label htmlFor="newFieldLabel" className="block text-xs font-medium text-gray-700">
                      Label <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      id="newFieldLabel"
                      value={newFieldLabel}
                      onChange={(e) => setNewFieldLabel(e.target.value)}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      placeholder="e.g., User Email"
                    />
                  </div>
                  <div className="flex items-center gap-4">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={newFieldRequired}
                        onChange={(e) => setNewFieldRequired(e.target.checked)}
                        className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="text-sm text-gray-700">Required</span>
                    </label>
                    <div className="flex-1">
                      <input
                        type="text"
                        value={newFieldDefault}
                        onChange={(e) => setNewFieldDefault(e.target.value)}
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        placeholder="Default value (optional)"
                      />
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleAddInputField}
                    className="w-full py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    + Add Input Field
                  </button>
                </div>

                {/* List of Input Fields */}
                {inputFields.length > 0 && (
                  <ul className="divide-y divide-gray-200 border border-gray-200 rounded-md">
                    {inputFields.map((field, index) => (
                      <li key={index} className="px-4 py-3 flex items-center justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            {field.label}
                            <span className="ml-2 text-xs font-normal text-gray-500">
                              ({field.type})
                            </span>
                          </p>
                          <p className="text-xs text-gray-500">
                            Field: <code className="bg-gray-100 px-1 rounded">{field.name}</code>
                            {field.required && ' • Required'}
                            {field.default && ` • Default: "${field.default}"`}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveInputField(index)}
                          className="ml-3 text-red-600 hover:text-red-800 text-sm"
                        >
                          Remove
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Save as Artifact */}
              <div className="border border-gray-200 rounded-md p-4">
                <div className="flex items-start">
                  <input
                    type="checkbox"
                    id="saveAsArtifact"
                    checked={saveAsArtifact}
                    onChange={(e) => setSaveAsArtifact(e.target.checked)}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div className="ml-3 flex-1">
                    <label htmlFor="saveAsArtifact" className="block text-sm font-medium text-gray-700">
                      Save form data as artifact
                    </label>
                    <p className="text-xs text-gray-500 mt-1">
                      Save the submitted form data as an output artifact for this checkpoint.
                    </p>
                  </div>
                </div>

                {saveAsArtifact && (
                  <div className="mt-4 grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="artifactName" className="block text-sm font-medium text-gray-700">
                        Artifact Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        id="artifactName"
                        value={artifactName}
                        onChange={(e) => setArtifactName(e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        placeholder="e.g., user_input_data"
                      />
                    </div>
                    <div>
                      <label htmlFor="artifactFormat" className="block text-sm font-medium text-gray-700">
                        Artifact Format
                      </label>
                      <select
                        id="artifactFormat"
                        value={artifactFormat}
                        onChange={(e) => setArtifactFormat(e.target.value as 'json' | 'md')}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      >
                        <option value="json">JSON</option>
                        <option value="md">Markdown</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>

          <hr />

          {/* Human Interaction Settings */}
          <section>
            <h2 className="text-lg font-medium text-gray-900 mb-4">Human Interaction Settings</h2>

            <div className="space-y-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={requiresApprovalToStart}
                  onChange={(e) => setRequiresApprovalToStart(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Require approval to start this checkpoint
                </span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={requiresApprovalToComplete}
                  onChange={(e) => setRequiresApprovalToComplete(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Require approval to complete this checkpoint
                </span>
              </label>

              <div>
                <label htmlFor="maxRevisions" className="block text-sm font-medium text-gray-700">
                  Max Revision Iterations
                </label>
                <input
                  type="number"
                  id="maxRevisions"
                  value={maxRevisionIterations}
                  onChange={(e) => setMaxRevisionIterations(parseInt(e.target.value) || 0)}
                  min={0}
                  max={10}
                  className="mt-1 block w-32 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Number of times the user can request revisions before the checkpoint fails.
                </p>
              </div>
            </div>
          </section>

          <hr />

          {/* Output Artifacts */}
          <section>
            <h2 className="text-lg font-medium text-gray-900 mb-4">Expected Output Artifacts</h2>

            <div className="bg-gray-50 rounded-md p-4 mb-4">
              <p className="text-sm text-gray-600">
                Define what outputs this checkpoint should produce. This helps track and validate results.
              </p>
            </div>

            {/* Add Output Artifact Form */}
            <div className="bg-gray-50 rounded-md p-4 mb-3 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="newArtifactName" className="block text-xs font-medium text-gray-700">
                    Artifact Name
                  </label>
                  <input
                    type="text"
                    id="newArtifactName"
                    value={newArtifactName}
                    onChange={(e) => setNewArtifactName(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="e.g., requirements_doc"
                  />
                </div>
                <div>
                  <label htmlFor="newArtifactFormat" className="block text-xs font-medium text-gray-700">
                    Format
                  </label>
                  <select
                    id="newArtifactFormat"
                    value={newArtifactFormat}
                    onChange={(e) => setNewArtifactFormat(e.target.value as ArtifactFormat)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  >
                    <option value="json">JSON</option>
                    <option value="md">Markdown</option>
                    <option value="txt">Plain Text</option>
                    <option value="mmd">Mermaid Diagram</option>
                    <option value="py">Python Script</option>
                    <option value="html">HTML</option>
                    <option value="csv">CSV</option>
                  </select>
                </div>
              </div>
              <div>
                <label htmlFor="newArtifactDescription" className="block text-xs font-medium text-gray-700">
                  Description (optional)
                </label>
                <input
                  type="text"
                  id="newArtifactDescription"
                  value={newArtifactDescription}
                  onChange={(e) => setNewArtifactDescription(e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  placeholder="e.g., User requirements document"
                />
              </div>
              <button
                type="button"
                onClick={handleAddOutputArtifact}
                className="w-full py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                + Add Output Artifact
              </button>
            </div>

            {/* List of Output Artifacts */}
            {outputArtifacts.length > 0 && (
              <ul className="divide-y divide-gray-200 border border-gray-200 rounded-md">
                {outputArtifacts.map((artifact, index) => (
                  <li key={index} className="px-4 py-3 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {artifact.name}
                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          {artifact.format}
                        </span>
                      </p>
                      {artifact.description && (
                        <p className="text-xs text-gray-500">{artifact.description}</p>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveOutputArtifact(index)}
                      className="ml-3 text-red-600 hover:text-red-800 text-sm"
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <hr />

          {/* Submit - Fixed at bottom for visibility */}
          <div className="sticky bottom-0 bg-white border-t border-gray-200 py-4 px-6 -mx-6 mt-6">
            <div className="flex justify-end space-x-3">
              <a
                href={`/pipelines/${pipelineId}`}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </a>
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
