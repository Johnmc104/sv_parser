import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

const ModuleSymbol = memo(({ data, selected }) => {
  const { 
    instanceName, 
    moduleType, 
    size, 
    portPositions, 
    isSelected,
    isHighlighted,
    onDoubleClick 
  } = data;

  const getHandlePosition = (side) => {
    switch (side) {
      case 'left': return Position.Left;
      case 'right': return Position.Right;
      case 'top': return Position.Top;
      case 'bottom': return Position.Bottom;
      default: return Position.Left;
    }
  };

  const getPortStyle = (port, info) => {
    const baseStyle = {
      position: 'absolute',
      width: '12px',
      height: '12px',
      border: '2px solid',
      borderRadius: info.bus ? '2px' : '50%',
      backgroundColor: '#fff',
    };

    // 根据端口类型设置颜色
    const typeColors = {
      clock: '#2196F3',
      reset: '#f44336',
      data: '#4CAF50',
      address: '#FF9800',
      control: '#9C27B0',
      interrupt: '#E91E63',
      gpio: '#607D8B',
    };

    // 从设计数据中获取端口类型
    let portType = 'data'; // 默认类型
    if (data.moduleInfo?.ports) {
      const portInfo = data.moduleInfo.ports.find(p => p.name === port);
      if (portInfo) {
        portType = portInfo.type;
      }
    }

    baseStyle.borderColor = typeColors[portType] || typeColors.data;

    // 根据side定位
    switch (info.side) {
      case 'left':
        baseStyle.left = '-6px';
        baseStyle.top = `${info.offset}px`;
        break;
      case 'right':
        baseStyle.right = '-6px';
        baseStyle.top = `${info.offset}px`;
        break;
      case 'top':
        baseStyle.top = '-6px';
        baseStyle.left = `${info.offset}px`;
        break;
      case 'bottom':
        baseStyle.bottom = '-6px';
        baseStyle.left = `${info.offset}px`;
        break;
    }

    return baseStyle;
  };

  const symbolStyle = {
    width: `${size.width}px`,
    height: `${size.height}px`,
    border: `2px solid ${isSelected ? '#2196F3' : '#333'}`,
    borderRadius: '4px',
    backgroundColor: isHighlighted ? '#e3f2fd' : '#fff',
    boxShadow: selected ? '0 0 0 3px rgba(33, 150, 243, 0.3)' : 'none',
    position: 'relative',
    cursor: 'pointer',
  };

  return (
    <div 
      className="module-symbol" 
      style={symbolStyle}
      onDoubleClick={onDoubleClick}
    >
      {/* 模块标题 */}
      <div className="symbol-header">
        <div className="instance-name">{instanceName}</div>
        <div className="module-type">({moduleType})</div>
      </div>

      {/* 端口句柄 */}
      {portPositions && Object.entries(portPositions).map(([portName, portInfo]) => (
        <Handle
          key={portName}
          type="source"
          position={getHandlePosition(portInfo.side)}
          id={portName}
          style={getPortStyle(portName, portInfo)}
        >
          {/* 端口标签 */}
          <div 
            className={`port-label port-${portInfo.side}`}
            style={{
              position: 'absolute',
              fontSize: '10px',
              fontFamily: 'monospace',
              whiteSpace: 'nowrap',
              ...(portInfo.side === 'left' && { right: '15px', top: '-5px' }),
              ...(portInfo.side === 'right' && { left: '15px', top: '-5px' }),
              ...(portInfo.side === 'top' && { top: '15px', left: '-10px' }),
              ...(portInfo.side === 'bottom' && { bottom: '15px', left: '-10px' }),
            }}
          >
            {portName}
            {portInfo.bus && <span className="bus-indicator">[ ]</span>}
          </div>
        </Handle>
      ))}
    </div>
  );
});

ModuleSymbol.displayName = 'ModuleSymbol';

export default ModuleSymbol;