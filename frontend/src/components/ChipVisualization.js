import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
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

function ChipVisualization({ data, selectedModule, onModuleSelect }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [stats, setStats] = useState(null);
  const [validation, setValidation] = useState(null);
  const [filteredView, setFilteredView] = useState(false);

  useEffect(() => {
    if (data) {
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

  // 根据选中的模块过滤显示
  useEffect(() => {
    if (selectedModule && data) {
      const flowData = data.flowData || data.flow_data || data.data?.flow_data;
      if (flowData && filteredView) {
        // 显示与选中模块相关的连接
        const relatedEdges = flowData.edges.filter(edge => 
          edge.source === selectedModule || edge.target === selectedModule
        );
        
        const relatedNodeIds = new Set([selectedModule]);
        relatedEdges.forEach(edge => {
          relatedNodeIds.add(edge.source);
          relatedNodeIds.add(edge.target);
        });
        
        const relatedNodes = flowData.nodes.filter(node => 
          relatedNodeIds.has(node.id)
        );
        
        setNodes(relatedNodes);
        setEdges(relatedEdges);
      }
    }
  }, [selectedModule, data, filteredView, setNodes, setEdges]);

  const onNodeClick = useCallback((event, node) => {
    onModuleSelect(node.id);
  }, [onModuleSelect]);

  const onLayoutNodes = useCallback(() => {
    const layoutNodes = nodes.map((node, index) => {
      const isSelected = node.id === selectedModule;
      const isTopLevel = node.data?.isTop || node.data?.label?.includes('top');
      
      return {
        ...node,
        position: {
          x: isTopLevel ? 400 : isSelected ? 200 : (index % 4) * 250 + 50,
          y: isTopLevel ? 50 : isSelected ? 150 : Math.floor(index / 4) * 180 + 250,
        },
        style: {
          ...node.style,
          border: isSelected ? '3px solid #2196F3' : node.style?.border,
          boxShadow: isSelected ? '0 0 0 3px rgba(33, 150, 243, 0.3)' : node.style?.boxShadow,
        }
      };
    });
    setNodes(layoutNodes);
  }, [nodes, selectedModule, setNodes]);

  const toggleFilteredView = useCallback(() => {
    setFilteredView(!filteredView);
    if (!filteredView && data) {
      // 重新加载所有节点和边
      const flowData = data.flowData || data.flow_data || data.data?.flow_data;
      if (flowData) {
        setNodes(flowData.nodes || []);
        setEdges(flowData.edges || []);
      }
    }
  }, [filteredView, data, setNodes, setEdges]);

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

  // 高亮显示与选中模块相关的节点和边
  const highlightedNodes = nodes.map(node => ({
    ...node,
    style: {
      ...node.style,
      opacity: !selectedModule || node.id === selectedModule || 
               edges.some(edge => 
                 (edge.source === selectedModule && edge.target === node.id) ||
                 (edge.target === selectedModule && edge.source === node.id)
               ) ? 1 : 0.3,
      border: node.id === selectedModule ? '3px solid #2196F3' : node.style?.border,
    }
  }));

  const highlightedEdges = edges.map(edge => ({
    ...edge,
    style: {
      ...edge.style,
      opacity: !selectedModule || edge.source === selectedModule || edge.target === selectedModule ? 1 : 0.2,
      strokeWidth: edge.source === selectedModule || edge.target === selectedModule ? 3 : 2,
    }
  }));

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <ReactFlow
        nodes={highlightedNodes}
        edges={highlightedEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
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
            
            <button 
              onClick={toggleFilteredView} 
              className={`filter-btn ${filteredView ? 'active' : ''}`}
            >
              {filteredView ? 'Show All' : 'Filter View'}
            </button>
            
            {selectedModule && (
              <div className="selected-module-info">
                <h4>Selected: {selectedModule}</h4>
                <p>Connected modules: {
                  edges.filter(edge => 
                    edge.source === selectedModule || edge.target === selectedModule
                  ).length
                }</p>
              </div>
            )}
            
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
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

export default ChipVisualization;