/**
 * 节点构建工具 - 从 SchematicViewer.js 拆分
 */

import { calculateModuleSize, calculatePortPositions } from './moduleLayoutUtils';
import { generateLayeredLayout, optimizeLayerArrangement } from './layeredLayoutUtils';

// 从原理图数据构建节点
export const buildNodesFromSchematicData = (schematicView, designData, onNavigate) => {
  const reactFlowNodes = schematicView.symbols.map(symbol => ({
    id: symbol.id,
    type: 'moduleSymbol',
    position: symbol.position,
    data: {
      instanceName: symbol.instance_name,
      moduleType: symbol.module_type,
      size: symbol.size,
      portPositions: symbol.port_positions,
      moduleInfo: designData.module_library[symbol.module_type],
      isSelected: false,
      isHighlighted: false,
      onDoubleClick: () => {
        console.log(`Attempting to navigate to: ${symbol.module_type}`);
        if (designData.module_library[symbol.module_type]) {
          onNavigate(symbol.module_type);
        }
      }
    },
    style: {
      width: symbol.size.width,
      height: symbol.size.height,
    }
  }));

  return reactFlowNodes;
};

// 从模块定义构建节点
export const buildNodesFromModuleDefinition = (moduleInfo, designData, onNavigate, useLayeredLayout = true) => {
  const defaultNodes = [];

  if (moduleInfo.internal_structure?.instances && moduleInfo.internal_structure.instances.length > 0) {
    if (useLayeredLayout) {
      // 使用新的分层布局
      return buildLayeredNodes(moduleInfo, designData, onNavigate);
    } else {
      // 保持原有的网格布局作为备选
      return buildGridNodes(moduleInfo, designData, onNavigate);
    }
  }

  return defaultNodes;
};

const buildLayeredNodes = (moduleInfo, designData, onNavigate) => {
  const { positions, layers } = generateLayeredLayout(moduleInfo, designData);
  const connections = moduleInfo.internal_structure.port_connections || [];
  
  // 应用连线优化
  const optimizedPositions = optimizeLayerArrangement(positions, connections, layers);
  const nodes = [];
  
  optimizedPositions.forEach((posData, instanceName) => {
    const instance = moduleInfo.internal_structure.instances.find(i => i.name === instanceName);
    if (!instance) return;
    
    // 使用标准端口位置计算，保持输入左侧，输出右侧
    const portPositions = calculatePortPositions(
      posData.moduleInfo.ports || [], 
      posData.moduleSize
    );
    
    const nodeData = {
      id: instanceName,
      type: 'moduleSymbol',
      position: { x: posData.x, y: posData.y },
      data: {
        instanceName: instance.name,
        moduleType: instance.module_type,
        size: posData.moduleSize,
        portPositions: portPositions,
        moduleInfo: posData.moduleInfo,
        layer: posData.layer,
        isSelected: false,
        isHighlighted: false,
        onDoubleClick: () => {
          console.log(`Double clicked on ${instance.name}, navigating to ${instance.module_type}`);
          onNavigate(instance.module_type);
        }
      },
      style: {
        width: posData.moduleSize.width,
        height: posData.moduleSize.height,
      }
    };
    
    nodes.push(nodeData);
  });
  
  return nodes;
};

const buildGridNodes = (moduleInfo, designData, onNavigate) => {
  const defaultNodes = [];

  if (moduleInfo.internal_structure?.instances && moduleInfo.internal_structure.instances.length > 0) {
    const instances = moduleInfo.internal_structure.instances;
    
    // 改进布局算法 - 增加间距避免重叠
    const cols = Math.min(3, Math.ceil(Math.sqrt(instances.length)));
    const spacingX = 450; // 增加水平间距
    const spacingY = 350; // 增加垂直间距
    const startX = 150;
    const startY = 100;

    instances.forEach((instance, index) => {
      const subModuleInfo = designData.module_library[instance.module_type];
      if (!subModuleInfo) {
        console.warn(`No module info for: ${instance.module_type}`);
        return;
      }

      const moduleSize = calculateModuleSize(subModuleInfo.ports || []);
      const portPositions = calculatePortPositions(subModuleInfo.ports || [], moduleSize);

      // Debug输出
      console.log(`Instance ${instance.name}:`, {
        moduleType: instance.module_type,
        ports: subModuleInfo.ports || [],
        calculatedSize: moduleSize,
        portPositions: portPositions
      });

      const row = Math.floor(index / cols);
      const col = index % cols;
      const x = startX + col * spacingX;
      const y = startY + row * spacingY;

      const nodeData = {
        id: instance.name,
        type: 'moduleSymbol',
        position: { x, y },
        data: {
          instanceName: instance.name,
          moduleType: instance.module_type,
          size: moduleSize,
          portPositions: portPositions,
          moduleInfo: subModuleInfo,
          isSelected: false,
          isHighlighted: false,
          onDoubleClick: () => {
            console.log(`Double clicked on ${instance.name}, navigating to ${instance.module_type}`);
            onNavigate(instance.module_type);
          }
        },
        // 强制ReactFlow使用我们的尺寸 - 移除 style，让组件自己控制
        width: moduleSize.width,
        height: moduleSize.height,
        style: {
          width: moduleSize.width,
          height: moduleSize.height,
        }
      };

      defaultNodes.push(nodeData);
    });
  }

  return defaultNodes;
};

// 创建测试节点
export const createTestNodes = () => {
  const testNodes = [
    {
      id: 'test-1',
      type: 'moduleSymbol',
      position: { x: 100, y: 100 },
      data: {
        instanceName: 'test_instance',
        moduleType: 'test_module',
        size: { width: 200, height: 120 },
        portPositions: {
          clk: { side: 'left', offset: 30, direction: 'input' },
          data_out: { side: 'right', offset: 30, direction: 'output' }
        },
        moduleInfo: { ports: [] },
        isSelected: false,
        isHighlighted: false,
        onDoubleClick: () => console.log('Test node clicked')
      },
      style: { width: 200, height: 120 }
    }
  ];
  
  return testNodes;
};