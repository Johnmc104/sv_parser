/**
 * 信号路由和连线处理工具 - 从 SchematicViewer.js 拆分
 */

import { getSignalColor, calculateRouteOffset } from './moduleLayoutUtils';

// 智能路由算法 - 避免信号重叠
export const createSmartRoutes = (nodes, connections, selectedNet) => {
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

// 从原理图数据构建边
export const buildEdgesFromSchematicData = (schematicView, designData, selectedNet) => {
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
  
  return reactFlowEdges;
};

// 处理边点击的数据封装
export const processEdgeClickData = (edges, handleEdgeClick) => {
  return edges.map(edge => ({
    ...edge,
    data: {
      ...edge.data,
      onClick: (event) => handleEdgeClick(event, edge)
    }
  }));
};