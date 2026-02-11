/**
 * Artifact Preview Component
 *
 * Displays artifact content with appropriate formatting:
 * - JSON: Syntax highlighted and formatted
 * - Markdown: Rendered with basic formatting
 * - Other text formats: Plain text with monospace font
 */

import { useState, useEffect } from 'react';
import type { ArtifactSummary } from '../types/pipeline';
import { api } from '../lib/api';

interface ArtifactPreviewProps {
  artifact: ArtifactSummary;
}

export function ArtifactPreview({ artifact }: ArtifactPreviewProps) {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  const loadContent = async () => {
    // If content is already loaded, just show the preview
    if (content !== null) {
      setShowPreview(true);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await api.getArtifactContent(artifact.artifact_id);

      if (data.error) {
        setError(data.error);
      } else if (data.content !== null) {
        setContent(data.content);
      }
      setShowPreview(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load artifact content');
      setShowPreview(true);
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return 'Unknown size';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'json':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      case 'md':
      case 'mmd':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        );
      case 'txt':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        );
      case 'py':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
        );
      case 'csv':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
    }
  };

  const handleDownload = async () => {
    try {
      const filename = `${artifact.artifact_name}.${artifact.format}`;
      await api.downloadArtifact(artifact.artifact_id, filename);
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  const handleTogglePreview = async () => {
    if (showPreview) {
      // Just hide the preview
      setShowPreview(false);
    } else {
      // Show preview and load content if not already loaded
      await loadContent();
    }
  };

  // Render JSON with syntax highlighting
  const renderJson = () => {
    if (!content) return null;
    try {
      const parsed = JSON.parse(content);
      return (
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto text-sm">
          <code>{JSON.stringify(parsed, null, 2)}</code>
        </pre>
      );
    } catch {
      return (
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto text-sm">
          <code>{content}</code>
        </pre>
      );
    }
  };

  // Render Markdown with basic formatting
  const renderMarkdown = () => {
    if (!content) return null;

    // Simple markdown to HTML conversion
    const html = content
      // Headers
      .replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>')
      .replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold mt-4 mb-2">$1</h2>')
      .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mt-4 mb-2">$1</h1>')
      // Bold
      .replace(/\*\*(.*?)\*\*/gim, '<strong class="font-semibold">$1</strong>')
      // Italic
      .replace(/\*(.*?)\*/gim, '<em class="italic">$1</em>')
      // Code blocks
      .replace(/```([\s\S]*?)```/gim, '<pre class="bg-gray-100 p-2 rounded my-2 overflow-auto"><code>$1</code></pre>')
      // Inline code
      .replace(/`([^`]+)`/gim, '<code class="bg-gray-100 px-1 rounded text-sm">$1</code>')
      // Lists
      .replace(/^\* (.*$)/gim, '<li class="ml-4">$1</li>')
      // Line breaks
      .replace(/\n$/gim, '<br />');

    return (
      <div className="prose prose-sm max-w-none bg-white p-4 rounded-lg border border-gray-200">
        <div dangerouslySetInnerHTML={{ __html: html }} />
      </div>
    );
  };

  // Render plain text
  const renderPlainText = () => {
    if (!content) return null;
    return (
      <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto text-sm whitespace-pre-wrap">
        <code>{content}</code>
      </pre>
    );
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          <p className="font-medium">Failed to load artifact content</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      );
    }

    switch (artifact.format) {
      case 'json':
        return renderJson();
      case 'md':
      case 'mmd':
        return renderMarkdown();
      default:
        return renderPlainText();
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 px-4 py-3 flex items-center justify-between border-b border-gray-200">
        <div className="flex items-center gap-2">
          <span className="text-gray-500">{getFormatIcon(artifact.format)}</span>
          <span className="font-medium text-gray-900">{artifact.artifact_name}</span>
          <span className="text-xs px-2 py-0.5 bg-gray-200 text-gray-700 rounded">
            {artifact.format.toUpperCase()}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">{formatFileSize(artifact.size_bytes)}</span>
          <button
            onClick={handleDownload}
            className="p-1.5 hover:bg-gray-200 rounded-lg transition-colors"
            title="Download artifact"
          >
            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>
          <button
            onClick={handleTogglePreview}
            className="p-1.5 hover:bg-gray-200 rounded-lg transition-colors"
            title={showPreview ? 'Hide preview' : 'Show preview'}
          >
            {showPreview ? (
              <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            ) : (
              <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Preview */}
      {showPreview && (
        <div className="max-h-96 overflow-auto">
          {renderContent()}
        </div>
      )}
    </div>
  );
}
