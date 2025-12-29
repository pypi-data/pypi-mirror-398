import '@xyflow/react/dist/style.css';

import { jsonDecode } from '@del-wang/utils';
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
} from '@xyflow/react';
import { useEffect, useId, useState } from 'react';

import { ControlPanel } from './workflow/components/ControlPanel';
import { kEdgeTypes } from './workflow/components/Edges';
import { kNodeTypes } from './workflow/components/Nodes';
import { ReactflowInstance } from './workflow/components/ReactflowInstance';
import { workflow2reactflow } from './workflow/data/convert';
import {
  kDefaultLayoutConfig,
  type ReactflowLayoutConfig,
} from './workflow/layout/node';
import { useAutoLayout } from './workflow/layout/useAutoLayout';
import { WorkflowSidebar } from './components/WorkflowSidebar';
import { WorkflowRunner } from './workflow/components/WorkflowRunner';
import type { Workflow } from './services/api';
import './components/WorkflowSidebar.css';

interface EditWorkFlowProps {
  workflow?: Workflow;
}

const EditWorkFlow: React.FC<EditWorkFlowProps> = ({ workflow }) => {
  const [nodes, _setNodes, onNodesChange] = useNodesState([]);
  const [edges, _setEdges, onEdgesChange] = useEdgesState([]);
  const [currentWorkflow, setCurrentWorkflow] = useState(workflow || undefined);

  const { layout, isDirty } = useAutoLayout();

  const layoutReactflow = async (
    props: ReactflowLayoutConfig & {
      workflow: string;
    },
  ) => {
    if (isDirty) {
      return;
    }
    const input = props.workflow;
    const data = jsonDecode(input);
    if (!data) {
      alert('Invalid workflow JSON data');
      return;
    }
    const workflow = workflow2reactflow(data);
    layout({ ...workflow, ...props });
  };
  
  useEffect(() => {
    if (workflow) {
      const workflowData = {
        nodes: workflow.nodes,
        edges: workflow.edges,
      };
      layoutReactflow({ workflow: JSON.stringify(workflowData), ...kDefaultLayoutConfig });
    }
  }, [workflow]);

  useEffect(() => {
    if (workflow && (nodes.length > 0 || edges.length > 0)) {
      const updatedWorkflow = {
        ...workflow,
        nodes: nodes.map((node: any) => ({
          id: node.id,
          type: node.type as 'base' | 'start',
          data: node.data,
          position: node.position,
        })),
        edges: edges.map((edge: any) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          sourceHandle: edge.sourceHandle,
          targetHandle: edge.targetHandle,
        })),
      };
      setCurrentWorkflow(updatedWorkflow);
    }
  }, [nodes, edges, workflow]);

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      <ReactFlow
        edges={edges}
        edgeTypes={kEdgeTypes}
        nodes={nodes}
        nodeTypes={kNodeTypes}
        onEdgesChange={onEdgesChange}
        onNodesChange={onNodesChange}
      >
        <Background
          color="#ccc"
          id={useId()}
          variant={BackgroundVariant.Dots}
        />
        <ReactflowInstance />
        <Controls />
        <MiniMap pannable zoomable />
        <ControlPanel layoutReactflow={layoutReactflow} workflow={currentWorkflow || workflow} />
      </ReactFlow>
    </div>
  );
};

export const WorkFlowViewer = () => {
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | undefined>();

  const handleWorkflowSelect = (workflow: Workflow) => {
    setSelectedWorkflow(workflow);
  };


  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        width: '100vw',
      }}
    >
      <WorkflowSidebar
        onWorkflowSelect={handleWorkflowSelect}
        selectedWorkflowId={selectedWorkflow?.id}
      />
      <div
        style={{
          flex: 1,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div style={{ flex: 1 }}>
          <ReactFlowProvider>
            <EditWorkFlow workflow={selectedWorkflow} />
          </ReactFlowProvider>
        </div>
        <WorkflowRunner workflow={selectedWorkflow} />
      </div>
    </div>
  );
};
