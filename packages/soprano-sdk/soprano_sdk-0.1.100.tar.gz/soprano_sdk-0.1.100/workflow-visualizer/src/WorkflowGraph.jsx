import React, { useCallback, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
  ReactFlowProvider,
  useReactFlow,
  Panel
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import CustomNode from './CustomNode';
import { Info } from 'lucide-react';

const nodeWidth = 240;
const nodeHeight = 140;

const nodeTypes = {
  custom: CustomNode,
};

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 80,
    ranksep: 100
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = isHorizontal ? 'left' : 'top';
    node.sourcePosition = isHorizontal ? 'right' : 'bottom';

    node.position = {
      x: nodeWithPosition.x - nodeWidth / 2,
      y: nodeWithPosition.y - nodeHeight / 2,
    };

    return node;
  });

  return { nodes, edges };
};

const LayoutFlow = ({ workflowData, onNodeClick, onInfoClick }) => {
  const { fitView } = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (!workflowData) return;

    const newNodes = [];
    const newEdges = [];

    // Process Steps
    if (workflowData.steps) {
      workflowData.steps.forEach((step) => {
        newNodes.push({
          id: step.id,
          data: { label: step.id, ...step, isOutcome: false },
          position: { x: 0, y: 0 },
          type: 'custom',
        });

        // Handle transitions array
        if (step.transitions && Array.isArray(step.transitions)) {
          step.transitions.forEach((transition, index) => {
            // Determine label based on transition type
            let label = '';
            if (transition.pattern) {
              label = transition.pattern.replace(/:/g, '');
            } else if (transition.condition !== undefined) {
              // Handle both boolean and string conditions
              if (typeof transition.condition === 'boolean') {
              label = transition.condition === true ? 'true' : 'false';
              } else {
                label = String(transition.condition);
              }
            }

            newEdges.push({
              id: `${step.id}-${transition.next}-${index}`,
              source: step.id,
              target: transition.next,
              label: label,
              type: 'default',
              markerEnd: {
                type: MarkerType.ArrowClosed,
                color: '#718096',
              },
              style: { stroke: '#718096', strokeWidth: 2 },
              labelStyle: {
                fill: '#fff',
                fontWeight: 700,
                fontSize: 13,
                fontFamily: '"Inter", sans-serif'
              },
              labelBgStyle: {
                fill: '#1e1e1e',
                fillOpacity: 0.95,
              },
              labelBgPadding: [8, 4],
              labelBgBorderRadius: 4,
              animated: transition.pattern ? true : false,
            });
          });
        }

        // Handle direct 'next' field
        if (step.next) {
          newEdges.push({
            id: `${step.id}-${step.next}-direct`,
            source: step.id,
            target: step.next,
            type: 'default',
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: '#718096',
            },
            style: { stroke: '#718096', strokeWidth: 2 },
          });
        }
      });
    }

    // Process Outcomes
    if (workflowData.outcomes) {
      workflowData.outcomes.forEach((outcome) => {
        newNodes.push({
          id: outcome.id,
          data: { label: outcome.id, ...outcome, isOutcome: true },
          position: { x: 0, y: 0 },
          type: 'custom',
        });
      });
    }

    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      newNodes,
      newEdges
    );

    setNodes(layoutedNodes);
    setEdges(layoutedEdges);

    setTimeout(() => {
      fitView({ padding: 0.2, duration: 800 });
    }, 100);
  }, [workflowData, setNodes, setEdges, fitView]);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div style={{ width: '100%', height: '100%', flex: 1 }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
      >
        <Controls
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}
          showInteractive={false}
        />
        <Panel position="top-right" style={{ margin: 10 }}>
          <button
            onClick={onInfoClick}
            title="Workflow Info"
            style={{
              width: '32px',
              height: '32px',
              backgroundColor: '#1e1e1e',
              border: '1px solid #444',
              borderRadius: '4px',
              cursor: 'pointer',
              padding: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#90caf9"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ display: 'block' }}
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4" />
              <path d="M12 8h.01" />
            </svg>
          </button>
        </Panel>
        <MiniMap />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>

      {/* Custom styles for Controls */}
      <style>{`
        .react-flow__controls {
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
          background: #1e1e1e;
          border: 1px solid #444;
          border-radius: 8px;
          padding: 4px;
        }
        .react-flow__controls button {
          background: transparent;
          border: none;
          border-bottom: 1px solid #333;
          margin: 0;
          padding: 8px;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: background 0.2s;
        }
        .react-flow__controls button:last-child {
          border-bottom: none;
        }
        .react-flow__controls button:hover {
          background: #2d2d2d;
        }
        .react-flow__controls button path {
          fill: #90caf9;
        }
        .react-flow__minimap {
          background: #1e1e1e;
          border: 1px solid #444;
        }
        .react-flow__minimap-mask {
          fill: #90caf9;
          fill-opacity: 0.2;
        }
      `}</style>
    </div>
  );
};

const WorkflowGraph = ({ onInfoClick, ...props }) => (
  <div style={{ width: '100%', height: '100%', display: 'flex', flex: 1 }}>
    <ReactFlowProvider>
      <LayoutFlow {...props} onInfoClick={onInfoClick} />
    </ReactFlowProvider>
  </div>
);

export default WorkflowGraph;
