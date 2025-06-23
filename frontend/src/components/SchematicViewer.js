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
  calculateModuleSize, 
  createPortPositions, 
  getSignalColor, 
  calculateRouteOffset 
} from '../utils/moduleLayoutUtils';

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
      createTestNodes();
      return;
    }

    // 如果有完整的原理图数据，使用它
    if (schematicView && schematicView.symbols && schematicView.symbols.length > 0) {
      buildFromSchematicData(schematicView, moduleInfo);
    } else {
      buildFromModuleDefinition(moduleInfo);
    }
  };

  // 添加测试节点创建函数
  const createTestNodes = () => {
    const testNodes = [
      {
        id: 'test-1',
        type: 'moduleSymbol',
        position: { x: 100, y: 100 },
        data: {
          instanceName: 'test_instance',
          moduleType: 'test_module',
          size: { width: 200, height: 120 },
          portPositions: {
            clk: { side: 'left', offset: 30, direction: 'input' },
            data_out: { side: 'right', offset: 30, direction: 'output' }
          },
          moduleInfo: { ports: [] },
          isSelected: false,
          isHighlighted: false,
          onDoubleClick: () => console.log('Test node clicked')
        },
        style: { width: 200, height: 120 }
      }
    ];
    
    setNodes(testNodes);
    setEdges([]);
  };

  const buildFromSchematicData = (schematicView, moduleInfo) => {
    console.log('Building from schematic data');
    setSchematicData(schematicView);

    // 构建节点
    const reactFlowNodes = schematicView.symbols.map(symbol => ({
      id: symbol.id,
      type: 'moduleSymbol',
      position: symbol.position,
      data: {
        instanceName: symbol.instance_name,
        moduleType: symbol.module_type,
        size: symbol.size,
        portPositions: symbol.port_positions,
        moduleInfo: designData.module_library[symbol.module_type],
        isSelected: false,
        isHighlighted: false,
        onDoubleClick: () => {
          console.log(`Attempting to navigate to: ${symbol.module_type}`);
          if (designData.module_library[symbol.module_type]) {
            onNavigate(symbol.module_type);
          }
        }
      },
      style: {
        width: symbol.size.width,
        height: symbol.size.height,
      }
    }));

    // 构建边 - 从信号网表和路由信息
    const reactFlowEdges = [];
    
    if (schematicView.signal_routes) {
      schematicView.signal_routes.forEach(route => {
        const netInfo = designData.signal_netlist?.nets?.[route.net_id];
        
        route.segments?.forEach((segment, segIndex) => {
          const edge = {
            id: `${route.net_id}_seg_${segIndex}`,
            source: segment.from.symbol,
            target: segment.to.symbol,
            sourceHandle: segment.from.port,
            targetHandle: segment.to.port,
            type: 'smoothstep',
            animated: route.route_type === 'clock_tree',
            data: {
              netId: route.net_id,
              netName: netInfo?.name || route.net_id,
              netWidth: netInfo?.width || 1,
              netType: netInfo?.net_class || 'data',
              isSelected: selectedNet === route.net_id,
            },
            style: {
              stroke: getSignalColor(netInfo?.net_class || 'data'),
              strokeWidth: selectedNet === route.net_id ? 4 : 2,
              strokeDasharray: netInfo?.net_class === 'clock' ? '5,5' : 'none',
              zIndex: 1000, // 确保信号线在模块之上
            },
          };
          reactFlowEdges.push(edge);
        });
      });
    }
    
    setNodes(reactFlowNodes);
    setEdges(reactFlowEdges);
  };

   const buildFromModuleDefinition = (moduleInfo) => {
    console.log('Building from module definition:', moduleInfo);

    const defaultNodes = [];
    const defaultEdges = [];

    if (moduleInfo.internal_structure?.instances && moduleInfo.internal_structure.instances.length > 0) {
      const instances = moduleInfo.internal_structure.instances;
      
      // 改进布局算法 - 增加间距避免重叠
      const cols = Math.min(3, Math.ceil(Math.sqrt(instances.length)));
      const spacingX = 450; // 增加水平间距
      const spacingY = 350; // 增加垂直间距
      const startX = 150;
      const startY = 100;

      instances.forEach((instance, index) => {
        const subModuleInfo = designData.module_library[instance.module_type];
        if (!subModuleInfo) {
          console.warn(`No module info for: ${instance.module_type}`);
          return;
        }

        const moduleSize = calculateModuleSize(subModuleInfo.ports || []);
        const portPositions = createPortPositions(subModuleInfo.ports || [], moduleSize);

        // Debug输出
        console.log(`Instance ${instance.name}:`, {
          moduleType: instance.module_type,
          ports: subModuleInfo.ports || [],
          calculatedSize: moduleSize,
          portPositions: portPositions
        });

        const row = Math.floor(index / cols);
        const col = index % cols;
        const x = startX + col * spacingX;
        const y = startY + row * spacingY;

        const nodeData = {
          id: instance.name,
          type: 'moduleSymbol',
          position: { x, y },
          data: {
            instanceName: instance.name,
            moduleType: instance.module_type,
            size: moduleSize,
            portPositions: portPositions,
            moduleInfo: subModuleInfo,
            isSelected: false,
            isHighlighted: false,
            onDoubleClick: () => {
              console.log(`Double clicked on ${instance.name}, navigating to ${instance.module_type}`);
              onNavigate(instance.module_type);
            }
          },
          // 强制ReactFlow使用我们的尺寸 - 移除 style，让组件自己控制
          width: moduleSize.width,
          height: moduleSize.height,
          style: {
            width: moduleSize.width,
            height: moduleSize.height,
          }
        };

        defaultNodes.push(nodeData);
      });

      // 确保节点状态完全重置
      setNodes([]); // 先清空
      setTimeout(() => {
        setNodes(defaultNodes); // 然后设置新节点
      }, 10);

      // 连线处理 - 使用智能路由避免重叠
      if (moduleInfo.internal_structure.port_connections) {
        setTimeout(() => {
          const newEdges = createSmartRoutes(defaultNodes, moduleInfo.internal_structure.port_connections);
          setEdges(newEdges);
        }, 100);
      }
    } else {
      setNodes([]);
      setEdges([]);
    }
  };

  // 智能路由算法 - 避免信号重叠
  const createSmartRoutes = (nodes, connections) => {
    const newEdges = [];
    const usedPaths = new Set(); // 记录已使用的路径

    connections.forEach((connection, connIndex) => {
      if (connection.connections && connection.connections.length >= 2) {
        const instancePorts = connection.connections.filter(conn => conn.type === 'instance_port');
        
        if (instancePorts.length >= 2) {
          let drivers = [];
          let loads = [];
          
          instancePorts.forEach(port => {
            const nodeData = nodes.find(n => n.id === port.instance);
            if (nodeData) {
              const portInfo = nodeData.data.portPositions[port.port];
              if (portInfo) {
                if (portInfo.direction === 'output' || portInfo.side === 'right') {
                  drivers.push(port);
                } else if (portInfo.direction === 'input' || portInfo.side === 'left') {
                  loads.push(port);
                }
              }
            }
          });

          if (drivers.length === 0 && instancePorts.length > 0) {
            drivers = [instancePorts[0]];
            loads = instancePorts.slice(1);
          } else if (loads.length === 0 && instancePorts.length > 1) {
            loads = instancePorts.slice(1);
          }

          drivers.forEach(driver => {
            loads.forEach((load, loadIndex) => {
              const edgeId = `${connection.net}_${driver.instance}_${driver.port}_to_${load.instance}_${load.port}`;
              
              // 计算路由偏移以避免重叠
              const routeOffset = calculateRouteOffset(driver, load, nodes, usedPaths, newEdges.length);
              
              const edge = {
                id: edgeId,
                source: driver.instance,
                target: load.instance,
                sourceHandle: driver.port,
                targetHandle: load.port,
                type: 'smoothstep',
                animated: connection.net.includes('clk'),
                data: {
                  netId: connection.net,
                  netName: connection.net,
                  netWidth: 1,
                  netType: connection.net.includes('clk') ? 'clock' : 'data',
                  isSelected: selectedNet === connection.net,
                },
                style: {
                  stroke: getSignalColor(connection.net),
                  strokeWidth: selectedNet === connection.net ? 4 : 2,
                  strokeDasharray: connection.net.includes('clk') ? '5,5' : 'none',
                  zIndex: 1000 + newEdges.length, // 每条线都有不同的z-index
                },
                ...routeOffset
              };
              
              newEdges.push(edge);
              
              // 记录路径
              const pathKey = `${driver.instance}-${load.instance}`;
              usedPaths.add(pathKey);
            });
          });
        }
      }
    });
    
    return newEdges;
  };

  // 处理边点击事件
  const handleEdgeClick = useCallback((event, edge) => {
    event.stopPropagation();
    setSelectedEdgeInfo(edge.data);
    onNetSelect(edge.data.netId);
  }, [onNetSelect]);

  // 修改边的onClick处理
  const edgesWithClickHandler = useMemo(() => {
    return edges.map(edge => ({
      ...edge,
      data: {
        ...edge.data,
        onClick: (event) => handleEdgeClick(event, edge)
      }
    }));
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