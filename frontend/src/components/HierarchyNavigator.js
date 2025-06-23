import React, { useState, useEffect } from 'react';
import '../styles/HierarchyNavigator.css';

function HierarchyNavigator({ designData, currentView, onNavigate }) {
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [hierarchyTree, setHierarchyTree] = useState(null);

  useEffect(() => {
    if (designData) {
      const tree = buildHierarchyTree(designData);
      setHierarchyTree(tree);
      // 默认展开顶层模块
      setExpandedNodes(new Set([designData.design_metadata.top_module]));
    }
  }, [designData]);

  const buildHierarchyTree = (data) => {
    const moduleLib = data.module_library;
    const topModule = data.design_metadata.top_module;
    
    const buildNode = (moduleName, instanceName = null) => {
      const moduleInfo = moduleLib[moduleName];
      if (!moduleInfo) return null;

      const children = [];
      if (moduleInfo.internal_structure?.instances) {
        moduleInfo.internal_structure.instances.forEach(instance => {
          const childNode = buildNode(instance.module_type, instance.name);
          if (childNode) {
            children.push(childNode);
          }
        });
      }

      // 判断是否有原理图：如果模块本身存在于module_library中，就认为有原理图
      const hasSchematic = !!moduleInfo;

      return {
        name: instanceName || moduleName,
        module_type: moduleName,
        display_name: instanceName ? `${instanceName} (${moduleName})` : moduleName,
        children,
        is_top: moduleName === topModule,
        has_schematic: hasSchematic, // 修改判断逻辑
        instance_count: moduleInfo.internal_structure?.instances?.length || 0,
        port_count: moduleInfo.ports?.length || 0
      };
    };

    return buildNode(topModule);
  };

  const toggleNode = (nodeName) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeName)) {
      newExpanded.delete(nodeName);
    } else {
      newExpanded.add(nodeName);
    }
    setExpandedNodes(newExpanded);
  };

  const handleNodeClick = (node) => {
    console.log('Hierarchy node clicked:', node);
    if (node.has_schematic) {
      onNavigate(node.module_type);
    }
  };

  const renderNode = (node, level = 0) => {
    if (!node) return null;

    const isExpanded = expandedNodes.has(node.name);
    const hasChildren = node.children && node.children.length > 0;
    const isSelected = currentView === node.module_type;
    const isClickable = node.has_schematic;

    return (
      <div key={node.name} className="hierarchy-node">
        <div 
          className={`hierarchy-item level-${level} ${isSelected ? 'selected' : ''} ${isClickable ? 'clickable' : 'disabled'}`}
          style={{ paddingLeft: `${level * 20 + 10}px` }}
          onClick={() => handleNodeClick(node)}
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
          
          <span className="node-icon">
            {node.is_top ? '🏠' : hasChildren ? '📦' : '⚙️'}
          </span>
          
          <span className="node-name">{node.display_name}</span>
          
          <span className="node-info">
            {node.instance_count > 0 && (
              <span className="instance-badge">{node.instance_count}</span>
            )}
          </span>
        </div>
        
        {isExpanded && hasChildren && (
          <div className="hierarchy-children">
            {node.children.map(child => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const getCurrentModuleInfo = () => {
    if (!designData || !currentView) return null;
    
    const moduleInfo = designData.module_library[currentView];
    if (!moduleInfo) return null;

    const netlist = designData.signal_netlist?.nets || {};
    const relatedNets = Object.values(netlist).filter(net => 
      net.driver?.module === currentView || 
      net.loads?.some(load => load.module === currentView)
    );

    return {
      ...moduleInfo,
      related_nets: relatedNets
    };
  };

  const moduleInfo = getCurrentModuleInfo();

  return (
    <div className="hierarchy-navigator">
      <div className="navigator-section">
        <h3>📊 Design Hierarchy</h3>
        <div className="hierarchy-tree">
          {hierarchyTree ? renderNode(hierarchyTree) : (
            <div className="loading">Building hierarchy...</div>
          )}
        </div>
      </div>

      {moduleInfo && (
        <div className="navigator-section">
          <h3>📋 Module Details</h3>
          <div className="module-info">
            <div className="info-item">
              <label>Module:</label>
              <span>{currentView}</span>
            </div>
            <div className="info-item">
              <label>Type:</label>
              <span>{moduleInfo.module_type}</span>
            </div>
            <div className="info-item">
              <label>Ports:</label>
              <span>{moduleInfo.ports?.length || 0}</span>
            </div>
            <div className="info-item">
              <label>Instances:</label>
              <span>{moduleInfo.internal_structure?.instances?.length || 0}</span>
            </div>
            <div className="info-item">
              <label>Signals:</label>
              <span>{moduleInfo.related_nets?.length || 0}</span>
            </div>
          </div>

          <div className="ports-list">
            <h4>Ports</h4>
            <div className="ports-container">
              {moduleInfo.ports?.map((port, index) => (
                <div key={index} className={`port-item ${port.direction}`}>
                  <span className="port-direction">{port.direction}</span>
                  <span className="port-name">{port.name}</span>
                  {port.width > 1 && (
                    <span className="port-width">[{port.width-1}:0]</span>
                  )}
                  <span className="port-type">{port.type}</span>
                </div>
              )) || <div className="no-ports">No ports defined</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default HierarchyNavigator;