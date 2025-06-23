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

  // 计算路由偏移
  const calculateRouteOffset = (driver, load, nodes, usedPaths, edgeIndex) => {
    const pathKey = `${driver.instance}-${load.instance}`;
    const reversePathKey = `${load.instance}-${driver.instance}`;
    
    // 如果路径已被使用，添加偏移
    if (usedPaths.has(pathKey) || usedPaths.has(reversePathKey)) {
      const offset = (edgeIndex % 3 - 1) * 20; // -20, 0, 20 的偏移
      return {
        style: {
          strokeWidth: 2,
        },
        pathOptions: {
          offset: offset,
          borderRadius: 10
        }
      };
    }
    
    return {};
  };

// 计算模块的动态尺寸 - 修正计算逻辑
  const calculateModuleSize = (ports) => {
    const inputs = ports.filter(p => p.direction === 'input');
    const outputs = ports.filter(p => p.direction === 'output');
    const inouts = ports.filter(p => p.direction === 'inout');

    const portSpacing = 25; // 增加端口间距
    const headerHeight = 40;
    const topMargin = 10; // 头部下方的间距
    const bottomMargin = 100; // 底部预留空间
    const sideMargin = 15;
    const minWidth = 180;
    const minHeight = 100;

    // 计算实际需要的高度：基于左右两侧端口的最大数量
    const maxSidePorts = Math.max(inputs.length, outputs.length);
    
    // 计算侧边端口所需的实际高度
    let sidePortsHeight = 0;
    if (maxSidePorts > 0) {
      // 第一个端口在topMargin位置，最后一个端口要预留bottomMargin
      // 端口之间的间距为portSpacing
      sidePortsHeight = topMargin + (maxSidePorts - 1) * portSpacing + bottomMargin;
    } else {
      sidePortsHeight = topMargin + bottomMargin;
    }
    
    // 如果有inout端口，需要额外的底部空间
    const bottomPortsHeight = inouts.length > 0 ? 40 : 0;

    // 计算总高度
    const calculatedHeight = Math.max(
      minHeight,
      headerHeight + sidePortsHeight + bottomPortsHeight
    );

    // 计算宽度：基于端口名称长度和底部端口数量
    const maxPortNameLength = Math.max(
      ...ports.map(p => p.name.length),
      8 // 最小长度
    );
    
    // 估算文本宽度 + 端口标签空间
    const estimatedTextWidth = maxPortNameLength * 9; // 每字符约9px
    const labelPadding = 80; // 左右标签的padding空间
    
    // 底部端口所需宽度
    const bottomPortsWidth = inouts.length > 0 ? 
      Math.max(inouts.length * 80, 200) : 0; // 每个底部端口至少80px宽

    const calculatedWidth = Math.max(
      minWidth,
      estimatedTextWidth + labelPadding,
      bottomPortsWidth + 2 * sideMargin
    );

    // Debug输出
    console.log(`Module size calculation:`, {
      ports: ports.length,
      inputs: inputs.length,
      outputs: outputs.length,
      inouts: inouts.length,
      maxSidePorts,
      sidePortsHeight,
      calculatedHeight,
      calculatedWidth
    });

    return {
      width: Math.round(calculatedWidth),
      height: Math.round(calculatedHeight)
    };
  };

  const createPortPositions = (ports, moduleSize) => {
    const positions = {};
    const inputs = ports.filter(p => p.direction === 'input');
    const outputs = ports.filter(p => p.direction === 'output');
    const inouts = ports.filter(p => p.direction === 'inout');

    const { width: symbolWidth, height: symbolHeight } = moduleSize;
    const headerHeight = 40;
    const topMargin = 20;
    const bottomMargin = 30;
    const sideMargin = 15;
    const portSpacing = 25;
    
    // 输入端口 - 左侧均匀分布
    if (inputs.length > 0) {
      inputs.forEach((port, index) => {
        // 从topMargin开始，按照portSpacing间距分布
        const yOffset = headerHeight + topMargin + (index * portSpacing);
        
        positions[port.name] = { 
          side: 'left', 
          offset: yOffset,
          bus: port.width > 1,
          direction: 'input'
        };
      });
    }

    // 输出端口 - 右侧均匀分布
    if (outputs.length > 0) {
      outputs.forEach((port, index) => {
        // 从topMargin开始，按照portSpacing间距分布
        const yOffset = headerHeight + topMargin + (index * portSpacing);
        
        positions[port.name] = { 
          side: 'right', 
          offset: yOffset,
          bus: port.width > 1,
          direction: 'output'
        };
      });
    }

    // 双向端口 - 底部均匀分布
    if (inouts.length > 0) {
      const availableWidth = symbolWidth - 2 * sideMargin;
      
      inouts.forEach((port, index) => {
        let xOffset;
        if (inouts.length === 1) {
          // 单个端口居中
          xOffset = symbolWidth / 2;
        } else {
          // 多个端口均匀分布
          const spacing = availableWidth / (inouts.length - 1);
          xOffset = sideMargin + (spacing * index);
        }
        
        positions[port.name] = { 
          side: 'bottom', 
          offset: xOffset,
          bus: port.width > 1,
          direction: 'inout'
        };
      });
    }

    // Debug输出端口位置
    console.log(`Port positions for module (${symbolWidth}x${symbolHeight}):`, positions);

    return positions;
  };

  // 信号颜色分类
  const getSignalColor = (netName) => {
    if (typeof netName !== 'string') return '#666';
    
    if (netName.includes('clk')) return '#2196F3';
    if (netName.includes('bus') || netName.includes('addr') || netName.includes('data')) return '#FF9800';
    if (netName.includes('irq') || netName.includes('interrupt')) return '#9C27B0';
    if (netName.includes('gpio')) return '#4CAF50';
    if (netName.includes('rst') || netName.includes('reset')) return '#f44336';
    return '#666';
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