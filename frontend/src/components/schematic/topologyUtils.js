/**
 * 拓扑分析工具 - 分析模块间的上下游关系
 */

// 构建模块依赖图
export const buildModuleDependencyGraph = (moduleInfo) => {
  const graph = new Map();
  const inDegree = new Map();
  const outDegree = new Map();
  
  if (!moduleInfo.internal_structure?.instances) {
    return { graph, inDegree, outDegree, layers: [] };
  }

  const instances = moduleInfo.internal_structure.instances;
  const connections = moduleInfo.internal_structure.port_connections || [];

  // 初始化所有实例
  instances.forEach(instance => {
    graph.set(instance.name, { inputs: new Set(), outputs: new Set() });
    inDegree.set(instance.name, 0);
    outDegree.set(instance.name, 0);
  });

  // 分析连接关系
  connections.forEach(connection => {
    const instancePorts = connection.connections?.filter(c => c.type === 'instance_port') || [];
    
    if (instancePorts.length >= 2) {
      const { drivers, loads } = categorizePortConnections(instancePorts, instances);
      
      drivers.forEach(driver => {
        loads.forEach(load => {
          if (driver.instance !== load.instance) {
            // 添加依赖关系：driver -> load
            graph.get(driver.instance).outputs.add(load.instance);
            graph.get(load.instance).inputs.add(driver.instance);
            
            inDegree.set(load.instance, inDegree.get(load.instance) + 1);
            outDegree.set(driver.instance, outDegree.get(driver.instance) + 1);
          }
        });
      });
    }
  });

  return { graph, inDegree, outDegree };
};

// 拓扑排序生成层级
export const generateTopologicalLayers = (graph, inDegree, outDegree) => {
  const layers = [];
  const visited = new Set();
  const remaining = new Map(inDegree);
  
  while (visited.size < graph.size) {
    // 找到当前层：入度为0的节点
    const currentLayer = [];
    
    for (const [instance, degree] of remaining.entries()) {
      if (degree === 0 && !visited.has(instance)) {
        currentLayer.push(instance);
      }
    }
    
    if (currentLayer.length === 0) {
      // 处理循环依赖：选择剩余节点中入度最小的
      const minDegree = Math.min(...Array.from(remaining.values()).filter(d => d > 0));
      const candidates = Array.from(remaining.entries())
        .filter(([inst, deg]) => deg === minDegree && !visited.has(inst))
        .map(([inst]) => inst);
      
      if (candidates.length > 0) {
        currentLayer.push(candidates[0]);
      } else {
        break;
      }
    }
    
    layers.push(currentLayer);
    
    // 更新剩余节点的入度
    currentLayer.forEach(instance => {
      visited.add(instance);
      remaining.delete(instance);
      
      // 减少后续节点的入度
      if (graph.has(instance)) {
        graph.get(instance).outputs.forEach(target => {
          if (!visited.has(target)) {
            remaining.set(target, Math.max(0, remaining.get(target) - 1));
          }
        });
      }
    });
  }
  
  return layers;
};

const categorizePortConnections = (instancePorts, instances) => {
  // 简化的端口分类：假设第一个为driver，其余为loads
  // 实际实现中需要根据端口方向进行更精确的分类
  const drivers = instancePorts.slice(0, 1);
  const loads = instancePorts.slice(1);
  
  return { drivers, loads };
};