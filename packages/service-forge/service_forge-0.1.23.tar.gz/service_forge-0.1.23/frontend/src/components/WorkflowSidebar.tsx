import React, { useEffect, useState } from 'react';
import { ApiService } from '../services/api';
import type { Workflow } from '../services/api';

interface WorkflowSidebarProps {
  onWorkflowSelect: (workflow: Workflow) => void;
  selectedWorkflowId?: string;
}

export const WorkflowSidebar: React.FC<WorkflowSidebarProps> = ({
  onWorkflowSelect,
  selectedWorkflowId,
}) => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        setLoading(true);
        setError(null);
        const workflowsData = await ApiService.getWorkflows();
        setWorkflows(workflowsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch workflows');
        console.error('Error fetching workflows:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchWorkflows();
  }, []);

  const handleWorkflowClick = (workflow: Workflow) => {
    onWorkflowSelect(workflow);
  };

  if (error) {
    return (
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>Workflows</h2>
        </div>
        <div className="sidebar-content">
          <div className="error">Error: {error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>Workflows</h2>
        <div className="workflow-count">{workflows.length} workflows</div>
      </div>
      <div className="sidebar-content">
        <div className="workflow-list">
          {workflows.map((workflow) => (
            <div
              key={workflow.id}
              className={`workflow-item ${
                selectedWorkflowId === workflow.id ? 'selected' : ''
              }`}
              onClick={() => handleWorkflowClick(workflow)}
            >
              <div className="workflow-name">{workflow.name}</div>
              <div className="workflow-meta">
                {workflow.nodes.length} nodes, {workflow.edges.length} edges
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
