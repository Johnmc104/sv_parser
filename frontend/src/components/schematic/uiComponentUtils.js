/**
 * UI组件工具 - 从 SchematicViewer.js 拆分
 */

import React from 'react';

// 信号信息面板组件
export const SignalInfoPanel = ({ selectedEdgeInfo, onClose }) => {
  if (!selectedEdgeInfo) return null;

  return (
    <div style={{ 
      background: 'rgba(255,255,255,0.95)', 
      padding: '12px', 
      borderRadius: '6px',
      fontSize: '12px',
      minWidth: '200px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      border: '1px solid #ddd'
    }}>
      <h4 style={{ margin: '0 0 8px 0', color: '#333' }}>Signal Information</h4>
      <div style={{ marginBottom: '4px' }}>
        <strong>Name:</strong> {selectedEdgeInfo.netName}
      </div>
      <div style={{ marginBottom: '4px' }}>
        <strong>Type:</strong> {selectedEdgeInfo.netType}
      </div>
      <div style={{ marginBottom: '4px' }}>
        <strong>Width:</strong> {selectedEdgeInfo.netWidth} bit{selectedEdgeInfo.netWidth > 1 ? 's' : ''}
      </div>
      <button 
        onClick={onClose}
        style={{
          marginTop: '8px',
          padding: '4px 8px',
          background: '#f44336',
          color: 'white',
          border: 'none',
          borderRadius: '3px',
          cursor: 'pointer',
          fontSize: '11px'
        }}
      >
        Close
      </button>
    </div>
  );
};

// 获取ReactFlow的默认配置
export const getReactFlowConfig = () => ({
  fitView: true,
  attributionPosition: "bottom-left",
  style: { width: '100%', height: '100%' },
  defaultEdgeOptions: {
    style: { zIndex: 1000 },
  }
});

// 获取查看器容器样式
export const getViewerContainerStyle = () => ({
  width: '100%', 
  height: '100%'
});

// 节点类型配置
export const createNodeTypes = (ModuleSymbol) => ({
  moduleSymbol: ModuleSymbol,
});