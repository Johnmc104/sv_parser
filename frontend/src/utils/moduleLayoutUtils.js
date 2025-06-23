/**
 * 模块布局和尺寸计算工具 - 从原始SchematicViewer.js拆分
 */

// 计算模块的动态尺寸 - 修正计算逻辑
export const calculateModuleSize = (ports) => {
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

export const createPortPositions = (ports, moduleSize) => {
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
export const getSignalColor = (netName) => {
  if (typeof netName !== 'string') return '#666';
  
  if (netName.includes('clk')) return '#2196F3';
  if (netName.includes('bus') || netName.includes('addr') || netName.includes('data')) return '#FF9800';
  if (netName.includes('irq') || netName.includes('interrupt')) return '#9C27B0';
  if (netName.includes('gpio')) return '#4CAF50';
  if (netName.includes('rst') || netName.includes('reset')) return '#f44336';
  return '#666';
};

// 计算路由偏移
export const calculateRouteOffset = (driver, load, nodes, usedPaths, edgeIndex) => {
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