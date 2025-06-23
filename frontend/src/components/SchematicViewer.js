import React, { useEffect, useState, useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Panel,
} from 'reactflow';

import ModuleSymbol from './ModuleSymbol';
import SignalWire from './SignalWire';
import 'reactflow/dist/style.css';

const nodeTypes = {
  moduleSymbol: ModuleSymbol,
};

const edgeTypes = {
  signalWire: SignalWire,
};

function SchematicViewer({ designData, currentModule, selectedNet, onNetSelect, onNavigate }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [schematicData, setSchematicData] = useState(null);
  const [viewMode, setViewMode] = useState('schematic'); // 'schematic' | 'block'

  useEffect(() => {
    if (designData && currentModule) {
      buildSchematicView();
    }
  }, [designData, currentModule]);

  const buildSchematicView = () => {
    const schematicView = designData.schematic_views[currentModule];
    const moduleInfo = designData.module_library[currentModule];
    
    if (!schematicView || !moduleInfo) {
      console.warn(`No schematic view found for module: ${currentModule}`);
      return;
    }

    setSchematicData(schematicView);

    // 构建节点（模块符号）
    const reactFlowNodes = schematicView.symbols.map(symbol => ({
      id: symbol.id,
      type: 'moduleSymbol',
      position: symbol.position,
      data: {
        instanceName: symbol.instance_name,
        moduleType: symbol.module_type,
        size: symbol.size,
        portPositions: symbol.port_positions,
        isSelected: false,
        onDoubleClick: () => {
          // 双击进入子模块
          if (designData.schematic_views[symbol.module_type]) {
            onNavigate(symbol.module_type);
          }
        }
      },
      style: {
        width: symbol.size.width,
        height: symbol.size.height,
      }
    }));

    // 构建边（信号线）
    const reactFlowEdges = schematicView.signal_routes.map(route => {
      const netInfo = designData.signal_netlist.nets[route.net_id];
      
      return route.segments.map((segment, segIndex) => ({
        id: `${route.net_id}_seg_${segIndex}`,
        type: 'signalWire',
        source: segment.from.symbol,
        target: segment.to.symbol,
        sourceHandle: segment.from.port,
        targetHandle: segment.to.port,
        data: {
          netId: route.net_id,
          netName: netInfo?.name || route.net_id,
          netWidth: netInfo?.width || 1,
          netType: netInfo?.net_class || 'data',
          routeType: route.route_type,
          style: route.style,
          waypoints: segment.waypoints,
          isSelected: selectedNet === route.net_id,
          onClick: () => onNetSelect(route.net_id)
        },
        style: {
          ...route.style,
          strokeWidth: selectedNet === route.net_id ? route.style.width * 2 : route.style.width,
        }
      }));
    }).flat();

    setNodes(reactFlowNodes);
    setEdges(reactFlowEdges);
  };

  const onNodeClick = useCallback((event, node) => {
    // 节点点击处理
    console.log('Node clicked:', node);
  }, []);

  const onEdgeClick = useCallback((event, edge) => {
    // 信号线点击处理
    if (edge.data?.onClick) {
      edge.data.onClick();
    }
  }, []);

  const highlightSignalPath = useCallback((netId) => {
    if (!netId || !designData) return;

    const netInfo = designData.signal_netlist.nets[netId];
    if (!netInfo) return;

    // 高亮相关的节点和边
    setNodes(nodes => nodes.map(node => ({
      ...node,
      data: {
        ...node.data,
        isHighlighted: isNodeConnectedToNet(node, netInfo)
      }
    })));

    setEdges(edges => edges.map(edge => ({
      ...edge,
      style: {
        ...edge.style,
        opacity: edge.data?.netId === netId ? 1 : 0.3
      }
    })));
  }, [designData]);

  const isNodeConnectedToNet = (node, netInfo) => {
    return netInfo.driver?.instance === node.data.instanceName ||
           netInfo.loads?.some(load => load.instance === node.data.instanceName);
  };

  useEffect(() => {
    if (selectedNet) {
      highlightSignalPath(selectedNet);
    } else {
      // 清除高亮
      setEdges(edges => edges.map(edge => ({
        ...edge,
        style: {
          ...edge.style,
          opacity: 1
        }
      })));
    }
  }, [selectedNet, highlightSignalPath]);

  const getNetStatistics = () => {
    if (!designData || !currentModule) return null;

    const nets = designData.signal_netlist.nets;
    const moduleNets = Object.values(nets).filter(net => 
      net.driver?.module === currentModule || 
      net.loads?.some(load => load.module === currentModule)
    );

    const stats = {
      total: moduleNets.length,
      clock: moduleNets.filter(net => net.net_class === 'clock').length,
      data: moduleNets.filter(net => net.net_class === 'data').length,
      bus: moduleNets.filter(net => net.net_class === 'bus').length,
      interrupt: moduleNets.filter(net => net.net_class === 'interrupt').length,
    };

    return stats;
  };

  const netStats = getNetStatistics();

  return (
    <div className="schematic-viewer">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        minZoom={0.1}
        maxZoom={2}
      >
        <Background 
          variant="dots" 
          gap={schematicData?.layout_info?.grid_size || 10} 
          size={1} 
          color="#e0e0e0"
        />
        
        <Controls showInteractive={false} />
        
        <MiniMap 
          nodeStrokeColor="#333"
          nodeColor="#fff"
          nodeBorderRadius={2}
          maskColor="rgba(0,0,0,0.1)"
        />
        
        <Panel position="top-left">
          <div className="schematic-info">
            <h3>{currentModule}</h3>
            <div className="view-controls">
              <button 
                className={viewMode === 'schematic' ? 'active' : ''}
                onClick={() => setViewMode('schematic')}
              >
                Schematic
              </button>
              <button 
                className={viewMode === 'block' ? 'active' : ''}
                onClick={() => setViewMode('block')}
              >
                Block
              </button>
            </div>
          </div>
        </Panel>

        <Panel position="top-right">
          <div className="net-controls">
            <div className="selected-net">
              {selectedNet ? (
                <div>
                  <strong>Selected Signal:</strong>
                  <div>{designData.signal_netlist.nets[selectedNet]?.name || selectedNet}</div>
                  <button onClick={() => onNetSelect(null)}>Clear</button>
                </div>
              ) : (
                <div>Click a signal to select</div>
              )}
            </div>
            
            {netStats && (
              <div className="net-statistics">
                <strong>Signal Statistics:</strong>
                <div>Total: {netStats.total}</div>
                <div>Clock: {netStats.clock}</div>
                <div>Data: {netStats.data}</div>
                <div>Bus: {netStats.bus}</div>
                <div>Interrupt: {netStats.interrupt}</div>
              </div>
            )}
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

export default SchematicViewer;