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
  const [debugInfo, setDebugInfo] = useState(''); // 添加调试信息

  // 添加调试函数
  const updateDebugInfo = (info) => {
    console.log('Debug:', info);
    setDebugInfo(info);
  };

  useEffect(() => {
    if (designData && currentModule) {
      updateDebugInfo(`Loading module: ${currentModule}`);
      buildSchematicView();
    } else {
      updateDebugInfo(`Missing data - designData: ${!!designData}, currentModule: ${currentModule}`);
    }
  }, [designData, currentModule]);

  const buildSchematicView = () => {
    const schematicView = designData.schematic_views?.[currentModule];
    const moduleInfo = designData.module_library?.[currentModule];
    
    updateDebugInfo(`Module: ${currentModule}, HasSchematic: ${!!schematicView}, HasModuleInfo: ${!!moduleInfo}`);

    if (!moduleInfo) {
      updateDebugInfo(`No module info found for: ${currentModule}`);
      // 创建一个简单的测试节点
      createTestNodes();
      return;
    }

    // 如果有完整的原理图数据，使用它
    if (schematicView && schematicView.symbols && schematicView.symbols.length > 0) {
      updateDebugInfo('Using schematic view data');
      buildFromSchematicData(schematicView, moduleInfo);
    } else {
      updateDebugInfo('Building from module definition');
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
    
    updateDebugInfo(`Created ${testNodes.length} test nodes`);
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
        console.log(`Processing route for net: ${route.net_id}`, netInfo);
        
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
              onClick: () => onNetSelect(route.net_id)
            },
            style: {
              stroke: getSignalColor(netInfo?.net_class || 'data'),
              strokeWidth: selectedNet === route.net_id ? 4 : 2,
              strokeDasharray: netInfo?.net_class === 'clock' ? '5,5' : 'none',
            },
            label: netInfo?.name || route.net_id,
            labelStyle: { 
              fontSize: 11, 
              fontWeight: selectedNet === route.net_id ? 'bold' : 'normal',
              backgroundColor: 'rgba(255,255,255,0.9)',
              padding: '2px 6px',
              borderRadius: '4px',
              border: '1px solid #ddd'
            }
          };
          reactFlowEdges.push(edge);
        });
      });
    }

    console.log('Generated nodes:', reactFlowNodes);
    console.log('Generated edges:', reactFlowEdges);
    
    setNodes(reactFlowNodes);
    setEdges(reactFlowEdges);
  };

  const buildFromModuleDefinition = (moduleInfo) => {
    console.log('Building from module definition:', moduleInfo);

    const defaultNodes = [];
    const defaultEdges = [];

    if (moduleInfo.internal_structure?.instances && moduleInfo.internal_structure.instances.length > 0) {
      const instances = moduleInfo.internal_structure.instances;
      
      const cols = Math.min(3, Math.ceil(Math.sqrt(instances.length)));
      const spacingX = 350;
      const spacingY = 280;
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

        const row = Math.floor(index / cols);
        const col = index % cols;
        const x = startX + col * spacingX;
        const y = startY + row * spacingY;

        // 确保创建的节点数据完整
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
          style: {
            width: moduleSize.width,
            height: moduleSize.height,
          }
        };

        console.log('Created node:', nodeData); // 调试信息
        defaultNodes.push(nodeData);
      });

      // 设置节点
      setNodes(defaultNodes);

      // 连线处理
      if (moduleInfo.internal_structure.port_connections) {
        setTimeout(() => {
          const newEdges = [];
          
          moduleInfo.internal_structure.port_connections.forEach((connection, connIndex) => {
            console.log('Processing connection:', connection);
            
            if (connection.connections && connection.connections.length >= 2) {
              const instancePorts = connection.connections.filter(conn => conn.type === 'instance_port');
              
              if (instancePorts.length >= 2) {
                let drivers = [];
                let loads = [];
                
                instancePorts.forEach(port => {
                  // 使用defaultNodes而不是未定义的nodes
                  const nodeData = defaultNodes.find(n => n.id === port.instance);
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
                        isSelected: selectedNet === connection.net,
                        onClick: () => onNetSelect(connection.net)
                      },
                      style: {
                        stroke: getSignalColor(connection.net),
                        strokeWidth: selectedNet === connection.net ? 4 : 2,
                        strokeDasharray: connection.net.includes('clk') ? '5,5' : 'none',
                      },
                      label: connection.net,
                      labelStyle: {
                        fontSize: 10,
                        fontWeight: selectedNet === connection.net ? 'bold' : 'normal',
                        backgroundColor: 'rgba(255,255,255,0.9)',
                        padding: '2px 4px',
                        borderRadius: '3px',
                        border: '1px solid #ddd'
                      }
                    };
                    
                    newEdges.push(edge);
                  });
                });
              }
            }
          });
          
          console.log('Created edges:', newEdges);
          setEdges(newEdges);
        }, 100);
      }
    } else {
      setNodes([]);
      setEdges([]);
    }
  };

  // 计算模块的动态尺寸
  const calculateModuleSize = (ports) => {
    const inputs = ports.filter(p => p.direction === 'input');
    const outputs = ports.filter(p => p.direction === 'output');
    const inouts = ports.filter(p => p.direction === 'inout');

    const portSpacing = 25;
    const headerHeight = 35;
    const marginTop = 10;
    const marginBottom = 15;
    const marginSide = 15;
    const minWidth = 160;
    const minHeight = 80;

    // 计算高度：基于左右两侧端口的最大数量
    const maxSidePorts = Math.max(inputs.length, outputs.length);
    const sidePortsHeight = maxSidePorts > 0 ? maxSidePorts * portSpacing : 0;
    const bottomPortsHeight = inouts.length > 0 ? 25 : 0; // 底部端口区域

    const calculatedHeight = Math.max(
      minHeight,
      headerHeight + marginTop + sidePortsHeight + bottomPortsHeight + marginBottom
    );

    // 计算宽度：基于端口名称长度和底部端口数量
    const maxPortNameLength = Math.max(
      ...ports.map(p => p.name.length),
      10 // 最小长度
    );
    const estimatedTextWidth = maxPortNameLength * 7; // 估算字符宽度
    const bottomPortsWidth = inouts.length > 0 ? inouts.length * 40 : 0;

    const calculatedWidth = Math.max(
      minWidth,
      estimatedTextWidth + 2 * marginSide,
      bottomPortsWidth + 2 * marginSide
    );

    return {
      width: calculatedWidth,
      height: calculatedHeight
    };
  };

  const createPortPositions = (ports, moduleSize) => {
    const positions = {};
    const inputs = ports.filter(p => p.direction === 'input');
    const outputs = ports.filter(p => p.direction === 'output');
    const inouts = ports.filter(p => p.direction === 'inout');

    const { width: symbolWidth, height: symbolHeight } = moduleSize;
    const marginTop = 35;
    const marginBottom = 15;
    const marginSide = 15;
    const availableHeight = symbolHeight - marginTop - marginBottom;
    const availableWidth = symbolWidth - 2 * marginSide;

    // 输入端口 - 左侧分布
    inputs.forEach((port, index) => {
      const totalInputs = inputs.length;
      const yOffset = marginTop + (totalInputs > 1 ? 
        (index * availableHeight) / (totalInputs - 1) : 
        availableHeight / 2);
      
      positions[port.name] = { 
        side: 'left', 
        offset: Math.min(yOffset, symbolHeight - 20),
        bus: port.width > 1,
        direction: 'input'
      };
    });

    // 输出端口 - 右侧分布  
    outputs.forEach((port, index) => {
      const totalOutputs = outputs.length;
      const yOffset = marginTop + (totalOutputs > 1 ? 
        (index * availableHeight) / (totalOutputs - 1) : 
        availableHeight / 2);
      
      positions[port.name] = { 
        side: 'right', 
        offset: Math.min(yOffset, symbolHeight - 20),
        bus: port.width > 1,
        direction: 'output'
      };
    });

    // 双向端口 - 底部分布
    inouts.forEach((port, index) => {
      const totalInouts = inouts.length;
      const xOffset = marginSide + (totalInouts > 1 ? 
        (index * availableWidth) / (totalInouts - 1) : 
        availableWidth / 2);
      
      positions[port.name] = { 
        side: 'bottom', 
        offset: Math.min(xOffset, symbolWidth - 20),
        bus: port.width > 1,
        direction: 'inout'
      };
    });

    return positions;
  };

  // 信号颜色分类
  const getSignalColor = (netName) => {
    if (netName.includes('clk')) return '#2196F3'; // 蓝色 - 时钟
    if (netName.includes('bus') || netName.includes('addr') || netName.includes('data')) return '#FF9800'; // 橙色 - 总线
    if (netName.includes('irq') || netName.includes('interrupt')) return '#9C27B0'; // 紫色 - 中断
    if (netName.includes('gpio')) return '#4CAF50'; // 绿色 - GPIO
    return '#666'; // 灰色 - 其他
  };

  // 添加调试useEffect
  useEffect(() => {
    console.log('Current edges:', edges);
    console.log('Current nodes:', nodes);
    
    // 验证连线的Handle是否存在
    edges.forEach(edge => {
      const sourceNode = nodes.find(n => n.id === edge.source);
      const targetNode = nodes.find(n => n.id === edge.target);
      
      if (!sourceNode) {
        console.error(`Source node not found for edge ${edge.id}: ${edge.source}`);
      }
      if (!targetNode) {
        console.error(`Target node not found for edge ${edge.id}: ${edge.target}`);
      }
      
      if (sourceNode && !sourceNode.data.portPositions[edge.sourceHandle]) {
        console.error(`Source handle not found: ${edge.source}#${edge.sourceHandle}`);
        console.log('Available source handles:', Object.keys(sourceNode.data.portPositions));
      }
      
      if (targetNode && !targetNode.data.portPositions[edge.targetHandle]) {
        console.error(`Target handle not found: ${edge.target}#${edge.targetHandle}`);
        console.log('Available target handles:', Object.keys(targetNode.data.portPositions));
      }
    });
  }, [nodes, edges]);

  // 确保nodeTypes正确定义
  const nodeTypes = useMemo(() => ({
    moduleSymbol: ModuleSymbol,
  }), []);

  return (
    <div className="schematic-viewer">
      {/* 在ReactFlow外部显示调试信息 */}
      <div style={{ 
        position: 'absolute',
        top: '10px',
        left: '10px',
        background: 'rgba(255,255,255,0.9)', 
        padding: '10px', 
        borderRadius: '4px',
        fontSize: '12px',
        maxWidth: '300px',
        zIndex: 1000
      }}>
        <strong>Debug Info:</strong><br/>
        {debugInfo}<br/>
        Nodes: {nodes.length}, Edges: {edges.length}
      </div>

      <div className="viewer-content" style={{ width: '100%', height: '100%' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
          style={{ width: '100%', height: '100%' }}
        >
          <Background />
          <Controls />
          <MiniMap />
          {/* 将Panel移动到ReactFlow内部 */}
          <Panel position="top-right" className="info-panel">
            <div style={{ 
              background: 'rgba(255,255,255,0.95)', 
              padding: '10px', 
              borderRadius: '6px',
              fontSize: '12px',
              minWidth: '200px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
            }}>
              <h4 style={{ margin: '0 0 8px 0' }}>Module: {currentModule}</h4>
              <div>Total Components: {nodes.length}</div>
              <div>Connections: {edges.length}</div>
            </div>
          </Panel>
        </ReactFlow>
      </div>
    </div>
  );
}

export default SchematicViewer;
