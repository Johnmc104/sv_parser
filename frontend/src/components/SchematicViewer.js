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
  createPanelCloseHandler, 
  createNodeStateUpdater 
} from './schematic/eventHandlerUtils';

function SchematicViewer({ designData, currentModule, selectedNet, onNetSelect, onNavigate }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [schematicData, setSchematicData] = useState(null);
  const [selectedEdgeInfo, setSelectedEdgeInfo] = useState(null);

  // 事件处理器
  const handleEdgeClick = useCallback(
    createEdgeClickHandler(setSelectedEdgeInfo, onNetSelect), 
    [onNetSelect]
  );
  
  const handlePanelClose = useCallback(
    createPanelCloseHandler(setSelectedEdgeInfo), 
    []
  );

  const nodeStateUpdater = useMemo(
    () => createNodeStateUpdater(setNodes, setEdges),
    [setNodes, setEdges]
  );

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

    if (schematicView && schematicView.symbols && schematicView.symbols.length > 0) {
      buildFromSchematicData(schematicView, moduleInfo);
    } else {
      buildFromModuleDefinition(moduleInfo);
    }
  };

  const buildFromSchematicData = (schematicView, moduleInfo) => {
    console.log('Building from schematic data');
    setSchematicData(schematicView);

    const reactFlowNodes = buildNodesFromSchematicData(schematicView, designData, onNavigate);
    const reactFlowEdges = buildEdgesFromSchematicData(schematicView, designData, selectedNet);
    
    setNodes(reactFlowNodes);
    setEdges(reactFlowEdges);
  };

  const buildFromModuleDefinition = (moduleInfo) => {
    console.log('Building from module definition:', moduleInfo);

    const defaultNodes = buildNodesFromModuleDefinition(moduleInfo, designData, onNavigate);

    nodeStateUpdater.clearNodes();
    nodeStateUpdater.updateNodes(defaultNodes);

    if (moduleInfo.internal_structure?.port_connections) {
      const newEdges = createSmartRoutes(defaultNodes, moduleInfo.internal_structure.port_connections, selectedNet);
      nodeStateUpdater.updateEdges(newEdges);
    } else {
      nodeStateUpdater.clearEdges();
    }
  };

  const edgesWithClickHandler = useMemo(() => {
    return processEdgeClickData(edges, handleEdgeClick);
  }, [edges, handleEdgeClick]);

  const nodeTypes = useMemo(() => createNodeTypes(ModuleSymbol), []);
  const reactFlowConfig = getReactFlowConfig();
  const containerStyle = getViewerContainerStyle();

  return (
    <div className="schematic-viewer">
      <div className="viewer-content" style={containerStyle}>
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