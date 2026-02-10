/**
 * Main App Component
 */

import { Header } from './components/Header';
import { PipelineList } from './pages/PipelineList';
import { CreatePipeline } from './pages/CreatePipeline';
import { EditPipeline } from './pages/EditPipeline';
import { PipelineDetail } from './pages/PipelineDetail';
import { CreateCheckpoint } from './pages/CreateCheckpoint';
import { EditCheckpoint } from './pages/EditCheckpoint';
import { RunDetail } from './pages/RunDetail';

// Simple router based on current path
function getCurrentRoute() {
  const path = window.location.pathname;

  // Run detail page (must check before other routes)
  const runDetailMatch = path.match(/^\/runs\/([a-f0-9-]+)$/i);
  if (runDetailMatch) {
    const runId = runDetailMatch[1];
    return <RunDetail runId={runId} />;
  }

  // Edit checkpoint page (must check before create/detail routes)
  const editCheckpointMatch = path.match(/^\/pipelines\/([a-f0-9-]+)\/checkpoints\/([a-f0-9-]+)\/edit$/i);
  if (editCheckpointMatch) {
    const pipelineId = editCheckpointMatch[1];
    const checkpointId = editCheckpointMatch[2];
    return <EditCheckpoint pipelineId={pipelineId} checkpointId={checkpointId} />;
  }

  // Create checkpoint page (must check before edit/detail routes)
  const createCheckpointMatch = path.match(/^\/pipelines\/([a-f0-9-]+)\/checkpoints\/new$/i);
  if (createCheckpointMatch) {
    const pipelineId = createCheckpointMatch[1];
    return <CreateCheckpoint pipelineId={pipelineId} />;
  }

  // Pipeline edit page (must check before detail route)
  const pipelineEditMatch = path.match(/^\/pipelines\/([a-f0-9-]+)\/edit$/i);
  if (pipelineEditMatch) {
    const pipelineId = pipelineEditMatch[1];
    return <EditPipeline pipelineId={pipelineId} />;
  }

  // Pipeline detail page (must check before /pipelines)
  const pipelineDetailMatch = path.match(/^\/pipelines\/([a-f0-9-]+)$/i);
  if (pipelineDetailMatch) {
    const pipelineId = pipelineDetailMatch[1];
    return <PipelineDetail pipelineId={pipelineId} />;
  }

  // Pipeline list page
  if (path === '/' || path === '/pipelines') {
    return <PipelineList />;
  }

  // Create pipeline page
  if (path === '/pipelines/new') {
    return <CreatePipeline />;
  }

  // Default to pipeline list for unknown routes
  return <PipelineList />;
}

export function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main>{getCurrentRoute()}</main>
    </div>
  );
}
