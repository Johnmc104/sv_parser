import React, { memo, useEffect, useRef } from 'react';
import { Handle } from 'reactflow';
import '../styles/ModuleSymbol.css';

import { 
  getHandlePosition,
  getHandleStyle,
  getPortLabelStyle,
  getHandleType,
  getSymbolStyle,
  logModuleDebugInfo
} from '../utils/portRenderUtils';

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

  const symbolStyle = getSymbolStyle(size, isSelected, isHighlighted, selected);

  // Debug信息：显示计算出的尺寸
  logModuleDebugInfo(instanceName, size, portPositions);

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
          const handleType = getHandleType(portInfo);

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