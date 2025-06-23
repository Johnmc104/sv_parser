/**
 * 事件处理工具 - 优化版本
 */

// 优化：添加防抖处理
export const createEdgeClickHandler = (setSelectedEdgeInfo, onNetSelect) => {
  let timeoutId = null;
  
  return (event, edge) => {
    event.stopPropagation();
    
    // 清除之前的超时
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    
    // 防抖处理
    timeoutId = setTimeout(() => {
      setSelectedEdgeInfo(edge.data);
      onNetSelect(edge.data.netId);
    }, 50);
  };
};

// 优化：添加状态清理
export const createPanelCloseHandler = (setSelectedEdgeInfo, onNetSelect) => {
  return () => {
    setSelectedEdgeInfo(null);
    onNetSelect?.(null); // 可选的网络清除
  };
};

// 优化：移除不必要的节点状态更新器（直接使用React hooks）
export const createBatchUpdater = () => {
  const updates = [];
  let isScheduled = false;
  
  const scheduleUpdate = (updateFn) => {
    updates.push(updateFn);
    
    if (!isScheduled) {
      isScheduled = true;
      requestAnimationFrame(() => {
        updates.forEach(fn => fn());
        updates.length = 0;
        isScheduled = false;
      });
    }
  };
  
  return { scheduleUpdate };
};