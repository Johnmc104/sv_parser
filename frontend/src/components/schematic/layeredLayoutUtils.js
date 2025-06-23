/**
 * 分层布局算法 - 基于拓扑关系的模块布局
 * 优化模块排列以减少连线转弯，但保持端口固定位置（输入左侧，输出右侧）
 */

import { calculateModuleSize } from './moduleLayoutUtils';
import { buildModuleDependencyGraph, generateTopologicalLayers } from './topologyUtils';

export const generateLayeredLayout = (moduleInfo, designData) => {
  const { graph, inDegree, outDegree } = buildModuleDependencyGraph(moduleInfo);
  const layers = generateTopologicalLayers(graph, inDegree, outDegree);
  
  // 分析连接模式以优化排列
  const connectionPatterns = analyzeConnectionPatterns(moduleInfo, layers);
  
  return calculateLayeredPositions(layers, moduleInfo, designData, connectionPatterns);
};

// 分析连接模式 - 重点关注模块间的连接密度和方向
const analyzeConnectionPatterns = (moduleInfo, layers) => {
  const patterns = new Map();
  const connections = moduleInfo.internal_structure.port_connections || [];
  
  // 初始化连接模式表
  layers.forEach(layer => {
    layer.forEach(instance => {
      patterns.set(instance, {
        upstreamConnections: new Map(), // 来自上游的连接
        downstreamConnections: new Map(), // 到下游的连接
        connectionCount: 0
      });
    });
  });
  
  // 分析连接模式
  connections.forEach(connection => {
    const instancePorts = connection.connections?.filter(c => c.type === 'instance_port') || [];
    
    if (instancePorts.length >= 2) {
      // 分析驱动端和负载端
      const { drivers, loads } = categorizeConnections(instancePorts);
      
      drivers.forEach(driver => {
        loads.forEach(load => {
          if (driver.instance !== load.instance) {
            // 记录连接关系
            const driverPattern = patterns.get(driver.instance);
            const loadPattern = patterns.get(load.instance);
            
            if (driverPattern && loadPattern) {
              // 更新下游连接
              const currentDownstream = driverPattern.downstreamConnections.get(load.instance) || 0;
              driverPattern.downstreamConnections.set(load.instance, currentDownstream + 1);
              driverPattern.connectionCount++;
              
              // 更新上游连接
              const currentUpstream = loadPattern.upstreamConnections.get(driver.instance) || 0;
              loadPattern.upstreamConnections.set(driver.instance, currentUpstream + 1);
              loadPattern.connectionCount++;
            }
          }
        });
      });
    }
  });
  
  return patterns;
};

// 简化的连接分类
const categorizeConnections = (instancePorts) => {
  // 简化处理：假设第一个为驱动端，其余为负载端
  // 实际应用中可以根据端口方向进行更精确分类
  const drivers = instancePorts.slice(0, 1);
  const loads = instancePorts.slice(1);
  return { drivers, loads };
};

const calculateLayeredPositions = (layers, moduleInfo, designData, connectionPatterns) => {
  const layerSpacing = 400; // 层间垂直距离
  const baseModuleSpacing = 300; // 基础模块间距离
  const startX = 150;
  const startY = 100;
  
  const positions = new Map();
  
  // 计算所有模块的尺寸
  const moduleSizes = new Map();
  layers.forEach(layer => {
    layer.forEach(instanceName => {
      const instance = moduleInfo.internal_structure.instances.find(i => i.name === instanceName);
      if (instance) {
        const subModuleInfo = designData.module_library[instance.module_type];
        if (subModuleInfo) {
          const moduleSize = calculateModuleSize(subModuleInfo.ports || []);
          moduleSizes.set(instanceName, moduleSize);
        }
      }
    });
  });
  
  // 优化层内排列以减少连线长度和交叉
  const optimizedLayers = optimizeForDirectConnections(layers, connectionPatterns, moduleSizes);
  
  // 计算最终位置
  optimizedLayers.forEach((layer, layerIndex) => {
    const layerY = startY + layerIndex * layerSpacing;
    
    // 动态调整模块间距以适应连接密度
    const moduleSpacing = calculateDynamicSpacing(layer, connectionPatterns, moduleSizes, baseModuleSpacing);
    
    // 计算层的总宽度用于居中
    const totalWidth = layer.reduce((sum, instanceName, index) => {
      const size = moduleSizes.get(instanceName) || { width: 200 };
      return sum + size.width + (index > 0 ? moduleSpacing : 0);
    }, 0);
    
    // 居中对齐
    const layerStartX = startX + Math.max(0, (1400 - totalWidth) / 2);
    
    let currentX = layerStartX;
    
    layer.forEach((instanceName) => {
      const instance = moduleInfo.internal_structure.instances.find(i => i.name === instanceName);
      if (!instance) return;
      
      const moduleType = instance.module_type;
      const subModuleInfo = designData.module_library[moduleType];
      
      if (subModuleInfo) {
        const moduleSize = moduleSizes.get(instanceName);
        
        positions.set(instanceName, {
          x: currentX,
          y: layerY,
          layer: layerIndex,
          moduleSize,
          moduleInfo: subModuleInfo
        });
        
        currentX += moduleSize.width + moduleSpacing;
      }
    });
  });
  
  return { positions, layers: optimizedLayers, totalLayers: optimizedLayers.length };
};

// 优化模块排列以支持更多直连
const optimizeForDirectConnections = (layers, connectionPatterns, moduleSizes) => {
  const optimizedLayers = layers.map(layer => [...layer]);
  
  // 多轮优化
  for (let iteration = 0; iteration < 3; iteration++) {
    for (let layerIndex = 0; layerIndex < optimizedLayers.length; layerIndex++) {
      const currentLayer = optimizedLayers[layerIndex];
      
      if (currentLayer.length <= 1) continue;
      
      // 基于连接强度计算每个模块的理想位置
      const idealPositions = calculateIdealPositions(
        currentLayer,
        layerIndex,
        optimizedLayers,
        connectionPatterns
      );
      
      // 根据理想位置排序
      currentLayer.sort((a, b) => {
        const posA = idealPositions.get(a) || 0;
        const posB = idealPositions.get(b) || 0;
        return posA - posB;
      });
    }
  }
  
  return optimizedLayers;
};

// 计算模块的理想位置
const calculateIdealPositions = (currentLayer, layerIndex, allLayers, connectionPatterns) => {
  const idealPositions = new Map();
  
  currentLayer.forEach(instanceName => {
    let weightedSum = 0;
    let totalWeight = 0;
    
    const pattern = connectionPatterns.get(instanceName);
    if (!pattern) {
      idealPositions.set(instanceName, currentLayer.indexOf(instanceName));
      return;
    }
    
    // 考虑与上一层的连接
    if (layerIndex > 0) {
      const prevLayer = allLayers[layerIndex - 1];
      pattern.upstreamConnections.forEach((weight, sourceInstance) => {
        const sourceIndex = prevLayer.indexOf(sourceInstance);
        if (sourceIndex >= 0) {
          weightedSum += sourceIndex * weight;
          totalWeight += weight;
        }
      });
    }
    
    // 考虑与下一层的连接
    if (layerIndex < allLayers.length - 1) {
      const nextLayer = allLayers[layerIndex + 1];
      pattern.downstreamConnections.forEach((weight, targetInstance) => {
        const targetIndex = nextLayer.indexOf(targetInstance);
        if (targetIndex >= 0) {
          weightedSum += targetIndex * weight;
          totalWeight += weight;
        }
      });
    }
    
    // 计算理想位置
    const idealPos = totalWeight > 0 ? weightedSum / totalWeight : currentLayer.indexOf(instanceName);
    idealPositions.set(instanceName, idealPos);
  });
  
  return idealPositions;
};

// 计算动态间距
const calculateDynamicSpacing = (layer, connectionPatterns, moduleSizes, baseSpacing) => {
  if (layer.length <= 1) return baseSpacing;
  
  // 计算层内连接密度
  let totalConnections = 0;
  layer.forEach(instance => {
    const pattern = connectionPatterns.get(instance);
    if (pattern) {
      totalConnections += pattern.connectionCount;
    }
  });
  
  // 根据连接密度调整间距
  const avgConnections = totalConnections / layer.length;
  const spacingMultiplier = Math.max(0.8, Math.min(1.5, 1 + avgConnections * 0.1));
  
  return Math.round(baseSpacing * spacingMultiplier);
};

// 优化层内排列：减少连线交叉
export const optimizeLayerArrangement = (positions, connections, layers) => {
  // 保持位置不变，只返回原始位置
  // 主要优化已经在 optimizeForDirectConnections 中完成
  return positions;
};