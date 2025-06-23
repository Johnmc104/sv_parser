/**
 * 模块布局和尺寸计算工具 - 从原始SchematicViewer.js拆分
 */

// 优化：缓存计算结果
const sizeCache = new Map();

export const calculateModuleSize = (ports) => {
  const cacheKey = JSON.stringify(ports.map(p => ({ name: p.name, direction: p.direction })));
  
  if (sizeCache.has(cacheKey)) {
    return sizeCache.get(cacheKey);
  }

  const inputs = ports.filter(p => p.direction === 'input');
  const outputs = ports.filter(p => p.direction === 'output');
  const inouts = ports.filter(p => p.direction === 'inout');

  const portSpacing = 30; // 增加端口间距
  const headerHeight = 40;
  const topMargin = 10;
  const bottomMargin = 50;
  const sideMargin = 15;
  const minWidth = 160;
  const minHeight = 100;

  const maxSidePorts = Math.max(inputs.length, outputs.length);
  
  let sidePortsHeight = 0;
  if (maxSidePorts > 0) {
    sidePortsHeight = topMargin + (maxSidePorts - 1) * portSpacing + bottomMargin;
  } else {
    sidePortsHeight = topMargin + bottomMargin;
  }
  
  const bottomPortsHeight = inouts.length > 0 ? 40 : 0;
  const calculatedHeight = Math.max(minHeight, headerHeight + sidePortsHeight + bottomPortsHeight);

  const maxPortNameLength = Math.max(...ports.map(p => p.name.length), 8);
  const estimatedTextWidth = maxPortNameLength * 9;
  const labelPadding = 80;
  const bottomPortsWidth = inouts.length > 0 ? Math.max(inouts.length * 80, 200) : 0;
  const calculatedWidth = Math.max(minWidth, estimatedTextWidth + labelPadding, bottomPortsWidth + 2 * sideMargin);

  const result = {
    width: Math.round(calculatedWidth),
    height: Math.round(calculatedHeight)
  };
  
  // 缓存结果
  sizeCache.set(cacheKey, result);
  
  return result;
};

// 优化：位置计算函数 - 修复端口位置堆积问题
export const calculatePortPositions = (ports, moduleSize) => {
  const positions = {};
  const inputs = ports.filter(p => p.direction === 'input');
  const outputs = ports.filter(p => p.direction === 'output');
  const inouts = ports.filter(p => p.direction === 'inout');
  
  const headerHeight = 10; // 模块标题高度
  const portStartY = headerHeight + 15; // 端口开始位置，避开标题区域
  const portEndY = moduleSize.height - 80; // 端口结束位置，避开底部区域
  
  // 计算可用的端口分布空间
  const availableHeight = portEndY - portStartY;
  
  // 输入端口（左侧）
  inputs.forEach((port, index) => {
    let yPosition;
    if (inputs.length === 1) {
      // 单个端口居中
      yPosition = portStartY + availableHeight / 2;
    } else {
      // 多个端口均匀分布
      yPosition = portStartY + (availableHeight / (inputs.length - 1)) * index;
    }
    
    positions[port.name] = {
      x: 0,
      y: Math.round(yPosition),
      side: 'left',
      direction: 'input',
      offset: Math.round(yPosition) // 相对于模块顶部的偏移
    };
  });
  
  // 输出端口（右侧）
  outputs.forEach((port, index) => {
    let yPosition;
    if (outputs.length === 1) {
      // 单个端口居中
      yPosition = portStartY + availableHeight / 2;
    } else {
      // 多个端口均匀分布
      yPosition = portStartY + (availableHeight / (outputs.length - 1)) * index;
    }
    
    positions[port.name] = {
      x: moduleSize.width,
      y: Math.round(yPosition),
      side: 'right',
      direction: 'output',
      offset: Math.round(yPosition) // 相对于模块顶部的偏移
    };
  });
  
  // 双向端口（底部）
  inouts.forEach((port, index) => {
    let xPosition;
    if (inouts.length === 1) {
      // 单个端口居中
      xPosition = moduleSize.width / 2;
    } else {
      // 多个端口均匀分布
      const spacing = moduleSize.width / (inouts.length + 1);
      xPosition = spacing * (index + 1);
    }
    
    positions[port.name] = {
      x: Math.round(xPosition),
      y: moduleSize.height,
      side: 'bottom',
      direction: 'inout',
      offset: Math.round(xPosition) // 相对于模块左边的偏移
    };
  });
  
  return positions;
};

// 优化：缓存路由偏移计算
const routeOffsetCache = new Map();

export const calculateRouteOffset = (driver, load, allNodes, usedPaths, routeIndex) => {
  const cacheKey = `${driver.instance}-${driver.port}-${load.instance}-${load.port}-${routeIndex}`;
  
  if (routeOffsetCache.has(cacheKey)) {
    return routeOffsetCache.get(cacheKey);
  }

  const baseOffset = 20;
  const routeSpacing = 15;
  const verticalOffset = routeIndex * routeSpacing;
  
  const result = {
    pathOptions: {
      offset: baseOffset + verticalOffset,
      borderRadius: 8
    }
  };
  
  // 缓存结果
  routeOffsetCache.set(cacheKey, result);
  
  return result;
};

// 信号颜色映射
const SIGNAL_COLORS = {
  clock: '#ff6b6b',
  reset: '#4ecdc4', 
  data: '#45b7d1',
  control: '#96ceb4',
  power: '#feca57',
  default: '#74b9ff'
};

export const getSignalColor = (signalType) => {
  return SIGNAL_COLORS[signalType] || SIGNAL_COLORS.default;
};

// 清理缓存的工具函数
export const clearLayoutCache = () => {
  sizeCache.clear();
  routeOffsetCache.clear();
};

// 辅助函数：调试端口位置
export const debugPortPositions = (ports, moduleSize) => {
  const positions = calculatePortPositions(ports, moduleSize);
  console.log('Port positions debug:', {
    moduleSize,
    ports: ports.map(p => ({ name: p.name, direction: p.direction })),
    positions
  });
  return positions;
};

// 增强端口位置计算，考虑连接方向
export const calculateOptimizedPortPositions = (ports, moduleSize, connections, instanceName, allPositions) => {
  const portPositions = {};
  
  if (!ports || ports.length === 0) {
    return portPositions;
  }

  // 基础端口位置计算
  const basePositions = calculatePortPositions(ports, moduleSize);
  
  // 分析连接方向，优化端口位置
  const connectionAnalysis = analyzePortConnections(ports, connections, instanceName, allPositions);
  
  ports.forEach(port => {
    const basePos = basePositions[port.name];
    if (!basePos) return;
    
    const connectionInfo = connectionAnalysis[port.name];
    
    if (connectionInfo && connectionInfo.preferredSide) {
      // 根据连接分析调整端口位置
      portPositions[port.name] = {
        ...basePos,
        side: connectionInfo.preferredSide,
        offset: calculateOptimalOffset(port, connectionInfo.targetPositions, moduleSize)
      };
    } else {
      portPositions[port.name] = basePos;
    }
  });

  return portPositions;
};

// 分析端口连接以确定最优位置
const analyzePortConnections = (ports, connections, instanceName, allPositions) => {
  const analysis = {};
  
  if (!connections || !allPositions) return analysis;
  
  connections.forEach(connection => {
    const instancePorts = connection.connections?.filter(c => c.type === 'instance_port') || [];
    
    // 找到当前实例的端口
    const currentInstancePorts = instancePorts.filter(p => p.instance === instanceName);
    const otherInstancePorts = instancePorts.filter(p => p.instance !== instanceName);
    
    currentInstancePorts.forEach(currentPort => {
      const portName = currentPort.port;
      
      if (!analysis[portName]) {
        analysis[portName] = {
          targetPositions: [],
          preferredSide: null
        };
      }
      
      // 收集连接目标的位置信息
      otherInstancePorts.forEach(otherPort => {
        const targetPosition = allPositions.get(otherPort.instance);
        if (targetPosition) {
          analysis[portName].targetPositions.push({
            x: targetPosition.x,
            y: targetPosition.y,
            instance: otherPort.instance,
            port: otherPort.port
          });
        }
      });
      
      // 根据目标位置确定最优端口侧面
      if (analysis[portName].targetPositions.length > 0) {
        analysis[portName].preferredSide = determineOptimalSide(
          allPositions.get(instanceName),
          analysis[portName].targetPositions
        );
      }
    });
  });
  
  return analysis;
};

// 确定最优端口侧面
const determineOptimalSide = (modulePosition, targetPositions) => {
  if (!modulePosition || targetPositions.length === 0) return null;
  
  // 计算目标位置的重心
  const avgX = targetPositions.reduce((sum, pos) => sum + pos.x, 0) / targetPositions.length;
  const avgY = targetPositions.reduce((sum, pos) => sum + pos.y, 0) / targetPositions.length;
  
  const deltaX = avgX - modulePosition.x;
  const deltaY = avgY - modulePosition.y;
  
  // 根据相对位置确定最优侧面
  if (Math.abs(deltaX) > Math.abs(deltaY)) {
    return deltaX > 0 ? 'right' : 'left';
  } else {
    return deltaY > 0 ? 'bottom' : 'top';
  }
};

// 计算最优端口偏移量
const calculateOptimalOffset = (port, targetPositions, moduleSize) => {
  if (!targetPositions || targetPositions.length === 0) {
    // 使用默认偏移量
    return moduleSize.height / 4;
  }
  
  // 计算目标的Y坐标重心，用于确定端口的垂直位置
  const avgTargetY = targetPositions.reduce((sum, pos) => sum + pos.y, 0) / targetPositions.length;
  
  // 将目标重心映射到模块内的偏移量
  const relativeOffset = Math.max(20, Math.min(moduleSize.height - 20, moduleSize.height / 3));
  
  return relativeOffset;
};