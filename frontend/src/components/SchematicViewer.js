import React, { useEffect, useState, useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';

import ModuleSymbol from './ModuleSymbol';
import '../styles/SchematicViewer.css';

import { 
  createSmartRoutes, 
  buildEdgesFromSchematicData, 
  processEdgeClickData 
} from './schematic/routingUtils';
import { 
  buildNodesFromSchematicData, 
  buildNodesFromModuleDefinition, 
  createTestNodes 
} from './schematic/nodeBuilderUtils';
import { 
  SignalInfoPanel, 
  getReactFlowConfig, 
  getViewerContainerStyle, 
  createNodeTypes 
} from './schematic/uiComponentUtils';
import { 
  createEdgeClickHandler, 
  createPanelCloseHandler 
} from './schematic/eventHandlerUtils';

function SchematicViewer({ designData, currentModule, selectedNet, onNetSelect, onNavigate }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedEdgeInfo, setSelectedEdgeInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [layoutMode, setLayoutMode] = useState('layered'); // 'layered' | 'grid'

  // 优化：缓存事件处理器
  const handleEdgeClick = useCallback(
    createEdgeClickHandler(setSelectedEdgeInfo, onNetSelect), 
    [onNetSelect]
  );
  
  const handlePanelClose = useCallback(
    createPanelCloseHandler(setSelectedEdgeInfo), 
    []
  );

  // 优化：将构建逻辑提取为独立的effect
  useEffect(() => {
    if (!designData || !currentModule) {
      setNodes([]);
      setEdges([]);
      return;
    }

    setIsLoading(true);
    buildSchematicView();
    setIsLoading(false);
  }, [designData, currentModule]);

  // 优化：将网络选择更新逻辑分离
  useEffect(() => {
    if (selectedNet && edges.length > 0) {
      const updatedEdges = edges.map(edge => ({
        ...edge,
        data: { ...edge.data, isSelected: edge.data.netId === selectedNet },
        style: {
          ...edge.style,
          strokeWidth: edge.data.netId === selectedNet ? 4 : 2,
        }
      }));
      setEdges(updatedEdges);
    }
  }, [selectedNet]);

  const buildSchematicView = useCallback(() => {
    const schematicView = designData.schematic_views?.[currentModule];
    const moduleInfo = designData.module_library?.[currentModule];
    
    if (!moduleInfo) {
      const testNodes = createTestNodes();
      setNodes(testNodes);
      setEdges([]);
      return;
    }

    if (schematicView?.symbols?.length > 0) {
      buildFromSchematicData(schematicView, moduleInfo);
    } else {
      buildFromModuleDefinition(moduleInfo);
    }
  }, [designData, currentModule]);

  const buildFromSchematicData = useCallback((schematicView, moduleInfo) => {
    const reactFlowNodes = buildNodesFromSchematicData(schematicView, designData, onNavigate);
    const reactFlowEdges = buildEdgesFromSchematicData(schematicView, designData, selectedNet);
    
    setNodes(reactFlowNodes);
    setEdges(reactFlowEdges);
  }, [designData, onNavigate, selectedNet]);

  const buildFromModuleDefinition = useCallback((moduleInfo) => {
    const useLayeredLayout = layoutMode === 'layered';
    const defaultNodes = buildNodesFromModuleDefinition(moduleInfo, designData, onNavigate, useLayeredLayout);
    setNodes(defaultNodes);

    if (moduleInfo.internal_structure?.port_connections) {
      // 优化：使用Promise处理异步更新
      Promise.resolve().then(() => {
        const newEdges = createSmartRoutes(defaultNodes, moduleInfo.internal_structure.port_connections, selectedNet);
        setEdges(newEdges);
      });
    } else {
      setEdges([]);
    }
  }, [designData, onNavigate, selectedNet, layoutMode]);

  // 优化：缓存处理后的边数据
  const edgesWithClickHandler = useMemo(() => {
    return processEdgeClickData(edges, handleEdgeClick);
  }, [edges, handleEdgeClick]);

  const nodeTypes = useMemo(() => createNodeTypes(ModuleSymbol), []);
  const reactFlowConfig = useMemo(() => getReactFlowConfig(), []);

  if (isLoading) {
    return <div className="schematic-loading">Loading schematic...</div>;
  }

  return (
    <div className="schematic-viewer">
      <div className="viewer-content" style={getViewerContainerStyle()}>
        <ReactFlow
          nodes={nodes}
          edges={edgesWithClickHandler}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onEdgeClick={handleEdgeClick}
          nodeTypes={nodeTypes}
          {...reactFlowConfig}
        >
          <Background />
          <Controls />
          <MiniMap />
          
          {/* 添加布局模式切换控制 */}
          <Panel position="top-right">
            <div style={{ 
              background: 'white', 
              padding: '8px', 
              borderRadius: '4px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              <label style={{ fontSize: '12px', marginRight: '8px' }}>Layout:</label>
              <select 
                value={layoutMode} 
                onChange={(e) => setLayoutMode(e.target.value)}
                style={{ fontSize: '12px' }}
              >
                <option value="layered">Layered (Topology)</option>
                <option value="grid">Grid (Original)</option>
              </select>
            </div>
          </Panel>
          
          {selectedEdgeInfo && (
            <Panel position="bottom-right" className="signal-info-panel">
              <SignalInfoPanel 
                selectedEdgeInfo={selectedEdgeInfo}
                onClose={handlePanelClose}
              />
            </Panel>
          )}
        </ReactFlow>
      </div>
    </div>
  );
}

export default SchematicViewer;