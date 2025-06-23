import React, { memo } from 'react';
import { getBezierPath, getMarkerEnd } from 'reactflow';

const SignalWire = memo(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  style = {},
  markerEnd,
}) => {
  const {
    netName,
    netWidth,
    netType,
    routeType,
    isSelected,
    onClick,
    waypoints = []
  } = data;

  // 根据信号类型确定样式
  const getWireStyle = () => {
    const baseStyle = {
      strokeWidth: netWidth > 1 ? 3 : 2,
      stroke: '#333',
      fill: 'none',
      ...style,
    };

    // 信号类型颜色
    const typeColors = {
      clock: '#2196F3',
      reset: '#f44336', 
      data: '#4CAF50',
      bus: '#FF9800',
      interrupt: '#9C27B0',
      control: '#607D8B',
    };

    baseStyle.stroke = typeColors[netType] || typeColors.data;

    // 选中状态
    if (isSelected) {
      baseStyle.strokeWidth = baseStyle.strokeWidth * 1.5;
      baseStyle.filter = 'drop-shadow(0 0 6px rgba(33, 150, 243, 0.6))';
    }

    // 时钟信号特殊样式
    if (netType === 'clock') {
      baseStyle.strokeDasharray = '5,5';
    }

    return baseStyle;
  };

  // 计算路径
  const getPath = () => {
    if (waypoints && waypoints.length > 0) {
      // 使用waypoints创建曼哈顿路由
      let pathData = `M ${sourceX} ${sourceY}`;
      
      waypoints.forEach(point => {
        pathData += ` L ${point.x} ${point.y}`;
      });
      
      pathData += ` L ${targetX} ${targetY}`;
      return pathData;
    } else {
      // 使用默认贝塞尔曲线
      const [edgePath] = getBezierPath({
        sourceX,
        sourceY,
        sourcePosition,
        targetX,
        targetY,
        targetPosition,
      });
      return edgePath;
    }
  };

  const wireStyle = getWireStyle();
  const pathData = getPath();

  return (
    <g onClick={onClick} style={{ cursor: 'pointer' }}>
      {/* 主信号线 */}
      <path
        id={id}
        d={pathData}
        style={wireStyle}
        markerEnd={markerEnd}
      />
      
      {/* 总线指示器 */}
      {netWidth > 1 && (
        <g>
          {/* 总线斜线标记 */}
          <path
            d={`M ${sourceX + 10} ${sourceY - 5} L ${sourceX + 20} ${sourceY + 5}`}
            stroke={wireStyle.stroke}
            strokeWidth="2"
            fill="none"
          />
          {/* 位宽标签 */}
          <text
            x={sourceX + 25}
            y={sourceY + 3}
            fontSize="10"
            fontFamily="monospace"
            fill={wireStyle.stroke}
          >
            [{netWidth-1}:0]
          </text>
        </g>
      )}
      
      {/* 信号名称标签 */}
      <text
        x={(sourceX + targetX) / 2}
        y={(sourceY + targetY) / 2 - 8}
        fontSize="11"
        fontFamily="Arial, sans-serif"
        textAnchor="middle"
        fill={wireStyle.stroke}
        style={{
          fontWeight: isSelected ? 'bold' : 'normal',
          filter: 'drop-shadow(1px 1px 1px rgba(255,255,255,0.8))',
        }}
      >
        {netName}
      </text>
      
      {/* 选中时的外层高亮 */}
      {isSelected && (
        <path
          d={pathData}
          stroke="rgba(33, 150, 243, 0.3)"
          strokeWidth={wireStyle.strokeWidth + 4}
          fill="none"
          pointerEvents="none"
        />
      )}
    </g>
  );
});

SignalWire.displayName = 'SignalWire';

export default SignalWire;