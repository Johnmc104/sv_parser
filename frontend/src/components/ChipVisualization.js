// filepath: /home/zhhe/work/sv_parser/frontend/src/components/ChipVisualization.js
import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';

import ModuleNode from './ModuleNode';

const nodeTypes = {
  moduleNode: ModuleNode,
};

function ChipVisualization({ data }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [stats, setStats] = useState(null);
  const [validation, setValidation] = useState(null);

  useEffect(() => {
    if (data) {
      // 支持多种数据格式
      const flowData = data.flowData || data.flow_data || data.data?.flow_data;
      const statsData = data.stats || data.data?.stats;
      const validationData = data.validation || data.data?.validation;
      
      if (flowData) {
        setNodes(flowData.nodes || []);
        setEdges(flowData.edges || []);
      }
      
      setStats(statsData);
      setValidation(validationData);
    }
  }, [data, setNodes, setEdges]);

  const onConnect = useCallback((params) => {
    setEdges((eds) => addEdge(params, eds));
  }, [setEdges]);

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
  }, []);

  const onLayoutNodes = useCallback(() => {
    // 改进的自动布局算法
    const layoutNodes = nodes.map((node, index) => {
      const isTopLevel = node.data?.isTop || node.data?.label?.includes('top');
      return {
        ...node,
        position: {
          x: isTopLevel ? 300 : (index % 4) * 250 + 50,
          y: isTopLevel ? 50 : Math.floor(index / 4) * 180 + 200,
        },
      };
    });
    setNodes(layoutNodes);
  }, [nodes, setNodes]);

  const getModuleTypeColor = (moduleType) => {
    const colors = {
      'gpio': '#4CAF50',
      'clk': '#2196F3',
      'bridge': '#FF9800',
      'interrupt': '#9C27B0',
      'led': '#F44336',
      'top': '#1A192B'
    };
    
    for (const [type, color] of Object.entries(colors)) {
      if (moduleType?.toLowerCase().includes(type)) {
        return color;
      }
    }
    return '#607D8B';
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
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
        <Controls />
        <MiniMap 
          nodeStrokeColor={(n) => getModuleTypeColor(n.data?.label)}
          nodeColor={(n) => getModuleTypeColor(n.data?.label)}
        />
        <Background variant="dots" gap={12} size={1} />
        
        <Panel position="top-right">
          <div className="panel-content">
            <button onClick={onLayoutNodes} className="layout-btn">
              Auto Layout
            </button>
            
            {stats && (
              <div className="design-stats">
                <h4>Design Statistics</h4>
                <p>Modules: {stats.modules?.total || 0}</p>
                <p>Instances: {stats.instances?.total || 0}</p>
                <p>Ports: {stats.ports?.total || 0}</p>
                <p>Hierarchy Depth: {stats.hierarchy?.max_depth || 0}</p>
                {stats.modules?.top_module && (
                  <p>Top Module: {stats.modules.top_module}</p>
                )}
              </div>
            )}
            
            {validation && (
              <div className="validation-info">
                <h4>Validation</h4>
                <p className={validation.error_count > 0 ? 'error' : 'success'}>
                  Errors: {validation.error_count || 0}
                </p>
                <p className={validation.warning_count > 0 ? 'warning' : 'success'}>
                  Warnings: {validation.warning_count || 0}
                </p>
              </div>
            )}
            
            {selectedNode && (
              <div className="selected-node-info">
                <h4>Selected: {selectedNode.data.label}</h4>
                <p>Type: {selectedNode.type}</p>
                <p>Ports: {selectedNode.data.ports?.length || 0}</p>
                {selectedNode.data.instances && (
                  <p>Instances: {selectedNode.data.instances.length}</p>
                )}
              </div>
            )}
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

export default ChipVisualization;