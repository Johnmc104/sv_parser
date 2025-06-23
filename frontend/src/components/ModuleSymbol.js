import React, { memo, useEffect, useRef } from 'react';
import { Handle, Position } from 'reactflow';
import '../styles/ModuleSymbol.css';

const ModuleSymbol = memo(({ data, selected, id }) => {
  const nodeRef = useRef(null);

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

  if (!size) {
    console.error('ModuleSymbol: size is undefined');
    return <div>Error: No size data</div>;
  }

  // 强制DOM更新尺寸
  useEffect(() => {
    if (nodeRef.current && size) {
      nodeRef.current.style.width = `${size.width}px`;
      nodeRef.current.style.height = `${size.height}px`;
      console.log(`Forcing size update for ${instanceName}: ${size.width}x${size.height}`);
    }
  }, [size, instanceName]);

  const getHandlePosition = (side) => {
    switch (side) {
      case 'left': return Position.Left;
      case 'right': return Position.Right;
      case 'top': return Position.Top;
      case 'bottom': return Position.Bottom;
      default: return Position.Left;
    }
  };

  // 计算端口在边缘的精确位置和标签位置
  const getHandleStyle = (portName, portInfo) => {
    const baseSize = 8;
    const handleStyle = {
      width: `${baseSize}px`,
      height: `${baseSize}px`,
      border: `2px solid #333`,
      borderRadius: portInfo.bus ? '2px' : '50%',
      backgroundColor: portInfo.bus ? '#FF9800' : '#fff',
      zIndex: 10,
    };

    const offset = portInfo.offset || 0;
    
    switch (portInfo.side) {
      case 'left':
        handleStyle.left = `-${baseSize/2}px`;
        handleStyle.top = `${offset}px`;
        handleStyle.transform = 'translateY(-50%)';
        break;
      case 'right':
        handleStyle.right = `-${baseSize/2}px`;
        handleStyle.top = `${offset}px`;
        handleStyle.transform = 'translateY(-50%)';
        break;
      case 'bottom':
        handleStyle.bottom = `-${baseSize/2}px`;
        handleStyle.left = `${offset}px`;
        handleStyle.transform = 'translateX(-50%)';
        break;
    }

    return handleStyle;
  };

  // 计算端口标签位置 - 确保在矩形内部，使用与SchematicViewer一致的边距
  const getPortLabelStyle = (portName, portInfo) => {
    const offset = portInfo.offset || 0;
    let labelStyle = {
      position: 'absolute',
      fontSize: '9px',
      fontFamily: 'monospace',
      whiteSpace: 'nowrap',
      color: '#333',
      backgroundColor: 'rgba(255,255,255,0.9)',
      padding: '1px 4px',
      borderRadius: '2px',
      border: '1px solid #ccc',
      zIndex: 15,
      fontWeight: '500',
      maxWidth: '80px',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
    };

    switch (portInfo.side) {
      case 'left':
        labelStyle = {
          ...labelStyle,
          left: '8px', // 在矩形内部
          top: `${offset}px`,
          transform: 'translateY(-50%)',
          textAlign: 'left'
        };
        break;
      case 'right':
        labelStyle = {
          ...labelStyle,
          right: '8px', // 在矩形内部
          top: `${offset}px`,
          transform: 'translateY(-50%)',
          textAlign: 'right'
        };
        break;
      case 'bottom':
        labelStyle = {
          ...labelStyle,
          bottom: '25px', // 与SchematicViewer中的bottomMargin一致
          left: `${offset}px`,
          transform: 'translateX(-50%)',
          textAlign: 'center'
        };
        break;
    }

    return labelStyle;
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
    zIndex: 1,
    // 强制尺寸
    minWidth: `${size.width}px`,
    minHeight: `${size.height}px`,
    maxWidth: `${size.width}px`,
    maxHeight: `${size.height}px`,
  };

  // Debug信息：显示计算出的尺寸
  console.log(`Module ${instanceName}: calculated size = ${size.width}x${size.height}`);
  if (portPositions) {
    console.log(`Port positions for ${instanceName}:`, portPositions);
  }

  return (
    <div 
      ref={nodeRef}
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
      <div className="ports-area" style={{ position: 'relative', flex: 1 }}>
        {portPositions && Object.entries(portPositions).map(([portName, portInfo]) => {
          const handleStyle = getHandleStyle(portName, portInfo);
          const labelStyle = getPortLabelStyle(portName, portInfo);
          
          const handleType = portInfo.side === 'left' ? 'target' : 
                           portInfo.side === 'right' ? 'source' : 
                           'source';

          return (
            <div key={portName}>
              <Handle
                type={handleType}
                position={getHandlePosition(portInfo.side)}
                id={portName}
                style={handleStyle}
              />
              
              {/* 端口标签 - 现在在矩形内部 */}
              <div 
                className={`port-label port-${portInfo.side}`}
                style={labelStyle}
              >
                {portName}
                {portInfo.bus && <span className="bus-indicator">[]</span>}
              </div>
            </div>
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