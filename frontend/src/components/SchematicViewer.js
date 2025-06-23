import React, { useEffect, useState, useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Panel,
  ConnectionLineType,
} from 'reactflow';
import 'reactflow/dist/style.css';

import ModuleSymbol from './ModuleSymbol';
import '../styles/SchematicViewer.css';

import { createSmartRoutes, buildEdgesFromSchematicData, processEdgeClickData } from '../utils/routingUtils';
import { buildNodesFromSchematicData, buildNodesFromModuleDefinition, createTestNodes } from '../utils/nodeBuilderUtils';

function SchematicViewer({ designData, currentModule, selectedNet, onNetSelect, onNavigate }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [schematicData, setSchematicData] = useState(null);
  const [viewMode, setViewMode] = useState('schematic');
  const [selectedEdgeInfo, setSelectedEdgeInfo] = useState(null);

  useEffect(() => {
    if (designData && currentModule) {
      buildSchematicView();
    }
  }, [designData, currentModule]);

  const buildSchematicView = () => {
    const schematicView = designData.schematic_views?.[currentModule];
    const moduleInfo = designData.module_library?.[currentModule];
    
    if (!moduleInfo) {
      const testNodes = createTestNodes();
      setNodes(testNodes);
      setEdges([]);
      return;
    }

    // 如果有完整的原理图数据，使用它
    if (schematicView && schematicView.symbols && schematicView.symbols.length > 0) {
      buildFromSchematicData(schematicView, moduleInfo);
    } else {
      buildFromModuleDefinition(moduleInfo);
    }
  };

  const buildFromSchematicData = (schematicView, moduleInfo) => {
    console.log('Building from schematic data');
    setSchematicData(schematicView);

    // 构建节点
    const reactFlowNodes = buildNodesFromSchematicData(schematicView, designData, onNavigate);
    
    // 构建边 - 从信号网表和路由信息
    const reactFlowEdges = buildEdgesFromSchematicData(schematicView, designData, selectedNet);
    
    setNodes(reactFlowNodes);
    setEdges(reactFlowEdges);
  };

  const buildFromModuleDefinition = (moduleInfo) => {
    console.log('Building from module definition:', moduleInfo);

    // 构建节点
    const defaultNodes = buildNodesFromModuleDefinition(moduleInfo, designData, onNavigate);

    // 确保节点状态完全重置
    setNodes([]); // 先清空
    setTimeout(() => {
      setNodes(defaultNodes); // 然后设置新节点
    }, 10);

    // 连线处理 - 使用智能路由避免重叠
    if (moduleInfo.internal_structure?.port_connections) {
      setTimeout(() => {
        const newEdges = createSmartRoutes(defaultNodes, moduleInfo.internal_structure.port_connections, selectedNet);
        setEdges(newEdges);
      }, 100);
    } else {
      setEdges([]);
    }
  };

  // 处理边点击事件
  const handleEdgeClick = useCallback((event, edge) => {
    event.stopPropagation();
    setSelectedEdgeInfo(edge.data);
    onNetSelect(edge.data.netId);
  }, [onNetSelect]);

  // 修改边的onClick处理
  const edgesWithClickHandler = useMemo(() => {
    return processEdgeClickData(edges, handleEdgeClick);
  }, [edges, handleEdgeClick]);

  const nodeTypes = useMemo(() => ({
    moduleSymbol: ModuleSymbol,
  }), []);

  return (
    <div className="schematic-viewer">
      <div className="viewer-content" style={{ width: '100%', height: '100%' }}>
        <ReactFlow
          nodes={nodes}
          edges={edgesWithClickHandler}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onEdgeClick={handleEdgeClick}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
          style={{ width: '100%', height: '100%' }}
          defaultEdgeOptions={{
            style: { zIndex: 1000 },
          }}
        >
          <Background />
          <Controls />
          <MiniMap />
          
          {/* 信号信息面板 */}
          {selectedEdgeInfo && (
            <Panel position="bottom-right" className="signal-info-panel">
              <div style={{ 
                background: 'rgba(255,255,255,0.95)', 
                padding: '12px', 
                borderRadius: '6px',
                fontSize: '12px',
                minWidth: '200px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                border: '1px solid #ddd'
              }}>
                <h4 style={{ margin: '0 0 8px 0', color: '#333' }}>Signal Information</h4>
                <div style={{ marginBottom: '4px' }}>
                  <strong>Name:</strong> {selectedEdgeInfo.netName}
                </div>
                <div style={{ marginBottom: '4px' }}>
                  <strong>Type:</strong> {selectedEdgeInfo.netType}
                </div>
                <div style={{ marginBottom: '4px' }}>
                  <strong>Width:</strong> {selectedEdgeInfo.netWidth} bit{selectedEdgeInfo.netWidth > 1 ? 's' : ''}
                </div>
                <button 
                  onClick={() => setSelectedEdgeInfo(null)}
                  style={{
                    marginTop: '8px',
                    padding: '4px 8px',
                    background: '#f44336',
                    color: 'white',
                    border: 'none',
                    borderRadius: '3px',
                    cursor: 'pointer',
                    fontSize: '11px'
                  }}
                >
                  Close
                </button>
              </div>
            </Panel>
          )}
        </ReactFlow>
      </div>
    </div>
  );
}

export default SchematicViewer;