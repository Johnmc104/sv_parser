import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import '../styles/ModuleSymbol.css';

const ModuleSymbol = memo(({ data, selected, id }) => {
  // 添加安全检查
  if (!data) {
    console.error('ModuleSymbol: data is undefined');
    return <div>Error: No data</div>;
  }

  const { 
    instanceName, 
    moduleType, 
    size, 
    portPositions, 
    moduleInfo,
    isSelected,
    isHighlighted,
    onDoubleClick 
  } = data;

  // 添加更多安全检查
  if (!size) {
    console.error('ModuleSymbol: size is undefined');
    return <div>Error: No size data</div>;
  }

  const getHandlePosition = (side) => {
    switch (side) {
      case 'left': return Position.Left;
      case 'right': return Position.Right;
      case 'top': return Position.Top;
      case 'bottom': return Position.Bottom;
      default: return Position.Left;
    }
  };

  // 计算端口在边缘的精确位置
  const getHandleStyle = (portName, portInfo) => {
    const baseSize = 10; // 减小handle尺寸
    const handleStyle = {
      width: `${baseSize}px`,
      height: `${baseSize}px`,
      border: `2px solid #333`,
      borderRadius: portInfo.bus ? '2px' : '50%',
      backgroundColor: portInfo.bus ? '#FF9800' : '#fff',
    };

    // 根据端口位置设置具体坐标
    const offset = portInfo.offset || 0;
    
    switch (portInfo.side) {
      case 'left':
        handleStyle.left = `-${baseSize/2}px`;
        handleStyle.top = `${offset}px`;
        break;
      case 'right':
        handleStyle.right = `-${baseSize/2}px`;
        handleStyle.top = `${offset}px`;
        break;
      case 'bottom':
        handleStyle.bottom = `-${baseSize/2}px`;
        handleStyle.left = `${offset}px`;
        break;
    }

    return handleStyle;
  };

  const symbolStyle = {
    width: `${size.width}px`,
    height: `${size.height}px`,
    border: `2px solid ${isSelected ? '#2196F3' : '#333'}`,
    borderRadius: '6px',
    backgroundColor: isHighlighted ? '#e3f2fd' : '#fff',
    boxShadow: selected ? '0 0 0 3px rgba(33, 150, 243, 0.3)' : '0 2px 4px rgba(0,0,0,0.1)',
    position: 'relative',
    cursor: 'pointer',
    overflow: 'visible',
  };

  console.log(`Rendering ${instanceName} with ports:`, portPositions);

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

      {/* 端口区域 */}
      <div className="ports-area">
        {portPositions && Object.entries(portPositions).map(([portName, portInfo]) => {
          const handleStyle = getHandleStyle(portName, portInfo);
          
          // 根据端口方向确定Handle类型
          const handleType = portInfo.side === 'left' ? 'target' : 
                           portInfo.side === 'right' ? 'source' : 
                           'source'; // 双向端口默认为source

          return (
            <Handle
              key={portName}
              type={handleType}
              position={getHandlePosition(portInfo.side)}
              id={portName}
              style={handleStyle}
            >
              {/* 端口标签 */}
              <div 
                className={`port-label port-${portInfo.side}`}
                style={{
                  position: 'absolute',
                  fontSize: '9px',
                  fontFamily: 'monospace',
                  whiteSpace: 'nowrap',
                  color: '#333',
                  backgroundColor: 'rgba(255,255,255,0.95)',
                  padding: '1px 3px',
                  borderRadius: '2px',
                  border: '1px solid #ccc',
                  zIndex: 1000,
                  fontWeight: '500',
                  ...(portInfo.side === 'left' && { 
                    right: '12px', 
                    top: '50%', 
                    transform: 'translateY(-50%)' 
                  }),
                  ...(portInfo.side === 'right' && { 
                    left: '12px', 
                    top: '50%', 
                    transform: 'translateY(-50%)' 
                  }),
                  ...(portInfo.side === 'bottom' && { 
                    bottom: '12px', 
                    left: '50%', 
                    transform: 'translateX(-50%)' 
                  }),
                }}
              >
                {portName}
                {portInfo.bus && <span className="bus-indicator">[]</span>}
              </div>
            </Handle>
          );
        })}
      </div>

      {/* 模块信息 */}
      <div className="symbol-content">
        {moduleInfo?.ports && (
          <div className="port-count">
            {moduleInfo.ports.length} ports
          </div>
        )}
      </div>
    </div>
  );
});

ModuleSymbol.displayName = 'ModuleSymbol';

export default ModuleSymbol;