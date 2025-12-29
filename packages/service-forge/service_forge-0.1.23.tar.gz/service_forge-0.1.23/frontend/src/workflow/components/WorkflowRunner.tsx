import React, { useState } from 'react';
import { ApiService, type Workflow } from '../../services/api';

interface WorkflowRunnerProps {
  workflow?: Workflow;
}

export const WorkflowRunner: React.FC<WorkflowRunnerProps> = ({ workflow }) => {
  const [output, setOutput] = useState<string>('');
  const [isRunning, setIsRunning] = useState<boolean>(false);

  const handleRunWorkflow = async () => {
    if (!workflow?.id) {
      setOutput('Error: No workflow selected');
      return;
    }

    setIsRunning(true);
    setOutput('Running workflow...\n');

    try {
      const result = await ApiService.runWorkflow(workflow.id);
      setOutput(prev => prev + `\nWorkflow completed successfully!\nResult:\n${result.message}\n`);
    } catch (error) {
      setOutput(prev => prev + `\nError running workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsRunning(false);
    }
  };

  const clearOutput = () => {
    setOutput('');
  };

  return (
    <div style={{
      width: '100%',
      padding: '20px',
      borderTop: '1px solid #e0e0e0',
      backgroundColor: '#f9f9f9'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        marginBottom: '15px'
      }}>
        <button
          onClick={handleRunWorkflow}
          disabled={!workflow?.id || isRunning}
          style={{
            padding: '10px 20px',
            backgroundColor: workflow?.id && !isRunning ? '#007bff' : '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: workflow?.id && !isRunning ? 'pointer' : 'not-allowed',
            fontSize: '14px',
            fontWeight: '500'
          }}
        >
          {isRunning ? 'RUNNING...' : 'RUN'}
        </button>
        
        <button
          onClick={clearOutput}
          style={{
            padding: '8px 16px',
            backgroundColor: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          Clear
        </button>
      </div>

      <div style={{
        width: '100%',
        height: '300px',
        border: '1px solid #ccc',
        borderRadius: '4px',
        backgroundColor: 'white',
        padding: '10px',
        fontFamily: 'monospace',
        fontSize: '12px',
        overflow: 'auto',
        whiteSpace: 'pre-wrap'
      }}>
        {output || 'Output will appear here when you run a workflow...'}
      </div>
    </div>
  );
};
