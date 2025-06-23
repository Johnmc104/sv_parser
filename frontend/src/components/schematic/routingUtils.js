/**
 * 信号路由和连线处理工具 - 优化版本
 */

import { getSignalColor, calculateRouteOffset } from './moduleLayoutUtils';

// 优化：缓存和批量处理路由计算
export const createSmartRoutes = (nodes, connections, selectedNet) => {
  if (!connections || connections.length === 0) return [];

  const newEdges = [];
  const usedPaths = new Set();
  const nodeMap = new Map(nodes.map(node => [node.id, node]));

  // 优化：预处理连接数据
  const processedConnections = connections
    .filter(conn => conn.connections && conn.connections.length >= 2)
    .map(conn => ({
      ...conn,
      instancePorts: conn.connections.filter(c => c.type === 'instance_port')
    }))
    .filter(conn => conn.instancePorts.length >= 2);

  processedConnections.forEach((connection, connIndex) => {
    const { drivers, loads } = categorizePortsByDirection(connection.instancePorts, nodeMap);
    
    // 优化：使用扁平化的路由生成
    const routes = generateRoutes(drivers, loads, connection, nodeMap, usedPaths, newEdges.length, selectedNet);
    newEdges.push(...routes);
  });
  
  return newEdges;
};

// 优化：提取端口分类逻辑
const categorizePortsByDirection = (instancePorts, nodeMap) => {
  let drivers = [];
  let loads = [];
  
  instancePorts.forEach(port => {
    const nodeData = nodeMap.get(port.instance);
    if (!nodeData) return;
    
    const portInfo = nodeData.data.portPositions[port.port];
    if (!portInfo) return;
    
    if (portInfo.direction === 'output' || portInfo.side === 'right') {
      drivers.push(port);
    } else if (portInfo.direction === 'input' || portInfo.side === 'left') {
      loads.push(port);
    }
  });

  // 优化：更智能的默认分配
  if (drivers.length === 0 && instancePorts.length > 0) {
    drivers = [instancePorts[0]];
    loads = instancePorts.slice(1);
  } else if (loads.length === 0 && instancePorts.length > 1) {
    loads = instancePorts.slice(1);
  }

  return { drivers, loads };
};

// 优化：批量生成路由
const generateRoutes = (drivers, loads, connection, nodeMap, usedPaths, baseIndex, selectedNet) => {
  const routes = [];
  
  drivers.forEach(driver => {
    loads.forEach((load, loadIndex) => {
      const edge = createEdgeFromPorts(driver, load, connection, nodeMap, usedPaths, baseIndex + routes.length, selectedNet);
      if (edge) {
        routes.push(edge);
        usedPaths.add(`${driver.instance}-${load.instance}`);
      }
    });
  });
  
  return routes;
};

// 优化：提取边创建逻辑
const createEdgeFromPorts = (driver, load, connection, nodeMap, usedPaths, edgeIndex, selectedNet) => {
  const edgeId = `${connection.net}_${driver.instance}_${driver.port}_to_${load.instance}_${load.port}`;
  const routeOffset = calculateRouteOffset(driver, load, Array.from(nodeMap.values()), usedPaths, edgeIndex);
  
  const isClockSignal = connection.net.includes('clk');
  const isSelected = selectedNet === connection.net;
  
  return {
    id: edgeId,
    source: driver.instance,
    target: load.instance,
    sourceHandle: driver.port,
    targetHandle: load.port,
    type: 'smoothstep',
    animated: isClockSignal,
    data: {
      netId: connection.net,
      netName: connection.net,
      netWidth: 1,
      netType: isClockSignal ? 'clock' : 'data',
      isSelected,
    },
    style: {
      stroke: getSignalColor(connection.net),
      strokeWidth: isSelected ? 4 : 2,
      strokeDasharray: isClockSignal ? '5,5' : 'none',
      zIndex: 1000 + edgeIndex,
    },
    ...routeOffset
  };
};

// 从原理图数据构建边
export const buildEdgesFromSchematicData = (schematicView, designData, selectedNet) => {
  if (!schematicView.signal_routes) return [];
  
  return schematicView.signal_routes.flatMap(route => {
    const netInfo = designData.signal_netlist?.nets?.[route.net_id];
    
    return route.segments?.map((segment, segIndex) => ({
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
        zIndex: 1000,
      },
    })) || [];
  });
};

// 优化：使用更高效的边处理
export const processEdgeClickData = (edges, handleEdgeClick) => {
  return edges.map(edge => ({
    ...edge,
    data: {
      ...edge.data,
      onClick: (event) => handleEdgeClick(event, edge)
    }
  }));
};