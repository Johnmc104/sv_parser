/**
 * 事件处理工具 - 从 SchematicViewer.js 拆分
 */

// 创建边点击处理器
export const createEdgeClickHandler = (setSelectedEdgeInfo, onNetSelect) => {
  return (event, edge) => {
    event.stopPropagation();
    setSelectedEdgeInfo(edge.data);
    onNetSelect(edge.data.netId);
  };
};

// 创建信息面板关闭处理器
export const createPanelCloseHandler = (setSelectedEdgeInfo) => {
  return () => setSelectedEdgeInfo(null);
};

// 创建节点状态更新处理器
export const createNodeStateUpdater = (setNodes, setEdges) => {
  return {
    clearNodes: () => setNodes([]),
    updateNodes: (nodes) => {
      setTimeout(() => setNodes(nodes), 10);
    },
    updateEdges: (edges) => {
      setTimeout(() => setEdges(edges), 100);
    },
    clearEdges: () => setEdges([])
  };
};