import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

const ModuleNode = ({ data, selected }) => {
  const inputPorts = data.ports?.filter(p => p.direction === 'input') || [];
  const outputPorts = data.ports?.filter(p => p.direction === 'output') || [];

  return (
    <div className={`module-node ${selected ? 'selected' : ''}`}>
      <div className="module-header">
        <strong>{data.label}</strong>
      </div>
      
      <div className="module-body">
        <div className="ports-container">
          <div className="input-ports">
            {inputPorts.map((port, index) => (
              <div key={`input-${index}`} className="port input-port">
                <Handle
                  type="target"
                  position={Position.Left}
                  id={`${data.label}-${port.name}`}
                  style={{ background: '#4CAF50' }}
                />
                <span className="port-label">
                  {port.name}
                  {port.width > 1 && <span className="port-width">[{port.width-1}:0]</span>}
                </span>
              </div>
            ))}
          </div>
          
          <div className="output-ports">
            {outputPorts.map((port, index) => (
              <div key={`output-${index}`} className="port output-port">
                <span className="port-label">
                  {port.name}
                  {port.width > 1 && <span className="port-width">[{port.width-1}:0]</span>}
                </span>
                <Handle
                  type="source"
                  position={Position.Right}
                  id={`${data.label}-${port.name}`}
                  style={{ background: '#FF9800' }}
                />
              </div>
            ))}
          </div>
        </div>
        
        {data.instances && data.instances.length > 0 && (
          <div className="instances">
            <div className="instances-header">Instances:</div>
            {data.instances.map((instance, index) => (
              <div key={index} className="instance-item">
                {instance}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default memo(ModuleNode);