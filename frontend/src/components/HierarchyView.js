import React, { useState, useEffect } from 'react';

function HierarchyView({ data }) {
  const [hierarchy, setHierarchy] = useState(null);
  const [selectedModule, setSelectedModule] = useState(null);
  const [expandedNodes, setExpandedNodes] = useState(new Set());

  useEffect(() => {
    if (data) {
      const hierarchyData = data.hierarchy || data.data?.hierarchy;
      setHierarchy(hierarchyData);
      
      // 默认展开顶层模块
      if (hierarchyData) {
        setExpandedNodes(new Set([hierarchyData.name]));
      }
    }
  }, [data]);

  const toggleNode = (nodeName) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeName)) {
      newExpanded.delete(nodeName);
    } else {
      newExpanded.add(nodeName);
    }
    setExpandedNodes(newExpanded);
  };

  const renderHierarchyNode = (node, level = 0) => {
    if (!node) return null;

    const isExpanded = expandedNodes.has(node.name);
    const hasChildren = node.children && node.children.length > 0;
    const isSelected = selectedModule === node.name;

    return (
      <div key={node.name} className="hierarchy-node">
        <div 
          className={`hierarchy-item level-${level} ${isSelected ? 'selected' : ''}`}
          style={{ paddingLeft: `${level * 20}px` }}
          onClick={() => setSelectedModule(node.name)}
        >
          {hasChildren && (
            <span 
              className={`expand-icon ${isExpanded ? 'expanded' : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                toggleNode(node.name);
              }}
            >
              {isExpanded ? '▼' : '▶'}
            </span>
          )}
          <span className="node-name">{node.name}</span>
          {node.instance_count > 0 && (
            <span className="instance-count">({node.instance_count})</span>
          )}
        </div>
        
        {isExpanded && hasChildren && (
          <div className="hierarchy-children">
            {node.children.map(child => renderHierarchyNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const getModuleDetails = () => {
    if (!selectedModule || !data.designInfo) return null;
    
    const modules = data.designInfo.modules || data.data?.design_info?.modules;
    const module = modules?.[selectedModule];
    
    if (!module) return null;

    return (
      <div className="module-details">
        <h4>Module: {selectedModule}</h4>
        <div className="detail-section">
          <h5>Ports ({module.ports?.length || 0})</h5>
          {module.ports?.map((port, index) => (
            <div key={index} className={`port-item ${port.direction}`}>
              <span className="port-direction">{port.direction}</span>
              <span className="port-name">{port.name}</span>
              {port.width > 1 && (
                <span className="port-width">[{port.width-1}:0]</span>
              )}
            </div>
          ))}
        </div>
        
        {module.instances && module.instances.length > 0 && (
          <div className="detail-section">
            <h5>Instances ({module.instances.length})</h5>
            {module.instances.map((instance, index) => (
              <div key={index} className="instance-item">
                <span className="instance-name">{instance.name}</span>
                <span className="instance-type">({instance.module_type})</span>
              </div>
            ))}
          </div>
        )}
        
        {module.parameters && module.parameters.length > 0 && (
          <div className="detail-section">
            <h5>Parameters ({module.parameters.length})</h5>
            {module.parameters.map((param, index) => (
              <div key={index} className="parameter-item">
                <span className="param-name">{param.name}</span>
                <span className="param-value">= {param.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  if (!hierarchy) {
    return (
      <div className="hierarchy-view">
        <div className="no-data">No hierarchy data available</div>
      </div>
    );
  }

  return (
    <div className="hierarchy-view">
      <div className="hierarchy-panel">
        <h3>Module Hierarchy</h3>
        <div className="hierarchy-tree">
          {renderHierarchyNode(hierarchy)}
        </div>
      </div>
      
      <div className="details-panel">
        {selectedModule ? getModuleDetails() : (
          <div className="no-selection">
            <p>Select a module to view details</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default HierarchyView;