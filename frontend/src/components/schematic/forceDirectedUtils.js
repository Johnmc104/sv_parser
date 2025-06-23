/**
 * 力导向优化工具 - 参考Unity算法优化模块布局
 * 在分层布局基础上应用力导向微调，减少连线长度和交叉
 */

export const applyForceDirectedOptimization = (positions, connections, layers, iterations = 50) => {
  const optimizedPositions = new Map(positions);
  
  // 构建距离矩阵
  const distanceMatrix = buildDistanceMatrix(layers, connections);
  
  // 应用力导向优化
  for (let iter = 0; iter < iterations; iter++) {
    const forces = calculateForces(optimizedPositions, distanceMatrix, layers);
    
    // 应用约束条件：保持分层结构
    applyConstrainedMovement(optimizedPositions, forces, layers);
    
    // 检查收敛
    if (isConverged(forces)) break;
  }
  
  return optimizedPositions;
};

// 构建距离矩阵（类似Unity代码中的Floyd-Warshall算法）
const buildDistanceMatrix = (layers, connections) => {
  const allNodes = [];
  layers.forEach(layer => allNodes.push(...layer));
  
  const nodeCount = allNodes.length;
  const nodeIndex = new Map();
  allNodes.forEach((node, index) => nodeIndex.set(node, index));
  
  // 初始化距离矩阵
  const distance = Array(nodeCount).fill(null).map(() => 
    Array(nodeCount).fill(5.0) // 默认距离
  );
  
  // 对角线设为极小值
  for (let i = 0; i < nodeCount; i++) {
    distance[i][i] = 0.001;
  }
  
  // 根据实际连接设置距离
  connections.forEach(connection => {
    const instancePorts = connection.connections?.filter(c => c.type === 'instance_port') || [];
    
    if (instancePorts.length >= 2) {
      for (let i = 0; i < instancePorts.length; i++) {
        for (let j = i + 1; j < instancePorts.length; j++) {
          const node1 = instancePorts[i].instance;
          const node2 = instancePorts[j].instance;
          
          const idx1 = nodeIndex.get(node1);
          const idx2 = nodeIndex.get(node2);
          
          if (idx1 !== undefined && idx2 !== undefined) {
            // 连接的节点距离设为1
            distance[idx1][idx2] = 1.0;
            distance[idx2][idx1] = 1.0;
          }
        }
      }
    }
  });
  
  // Floyd-Warshall算法计算最短路径
  for (let k = 0; k < nodeCount; k++) {
    for (let i = 0; i < nodeCount; i++) {
      for (let j = 0; j < nodeCount; j++) {
        if (distance[i][k] + distance[k][j] < distance[i][j]) {
          distance[i][j] = distance[i][k] + distance[k][j];
        }
      }
    }
  }
  
  return { distance, nodeIndex, allNodes };
};

// 计算作用力（类似Unity代码中的梯度计算）
const calculateForces = (positions, distanceMatrix, layers) => {
  const { distance, nodeIndex, allNodes } = distanceMatrix;
  const forces = new Map();
  
  // 力的参数
  const L0 = 200; // 基础长度
  const K = 1.0;  // 弹簧常数
  
  // 计算理想长度和弹簧常数矩阵
  const maxDistance = Math.max(...distance.flat());
  const L = L0 / maxDistance;
  
  allNodes.forEach(nodeA => {
    let forceX = 0;
    let forceY = 0;
    
    const posA = positions.get(nodeA);
    if (!posA) return;
    
    const idxA = nodeIndex.get(nodeA);
    
    allNodes.forEach(nodeB => {
      if (nodeA === nodeB) return;
      
      const posB = positions.get(nodeB);
      if (!posB) return;
      
      const idxB = nodeIndex.get(nodeB);
      
      // 计算当前距离
      const dx = posA.x - posB.x;
      const dy = posA.y - posB.y;
      const currentDist = Math.sqrt(dx * dx + dy * dy);
      
      if (currentDist < 0.001) return; // 避免除零
      
      // 理想距离和弹簧常数
      const idealDist = L * distance[idxA][idxB];
      const springK = K / (distance[idxA][idxB] * distance[idxA][idxB]);
      
      // 计算弹簧力
      const force = springK * (currentDist - idealDist);
      const forceUnitX = dx / currentDist;
      const forceUnitY = dy / currentDist;
      
      forceX += force * forceUnitX;
      forceY += force * forceUnitY;
    });
    
    forces.set(nodeA, { x: forceX, y: forceY });
  });
  
  return forces;
};

// 应用约束移动（保持分层结构）
const applyConstrainedMovement = (positions, forces, layers) => {
  const stepSize = 0.1; // 移动步长
  const maxMovement = 20; // 最大移动距离
  
  forces.forEach((force, nodeName) => {
    const pos = positions.get(nodeName);
    if (!pos) return;
    
    // 限制移动幅度
    const forcemagnitude = Math.sqrt(force.x * force.x + force.y * force.y);
    if (forcemagnitude < 0.01) return;
    
    const movement = Math.min(maxMovement, stepSize * forcemagnitude);
    const moveX = (force.x / forcemagnitude) * movement;
    const moveY = (force.y / forcemagnitude) * movement;
    
    // 应用移动，但限制垂直移动（保持分层）
    pos.x += moveX;
    pos.y += moveY * 0.2; // 限制垂直移动，保持分层结构
    
    // 确保不会移动到负坐标
    pos.x = Math.max(50, pos.x);
    pos.y = Math.max(50, pos.y);
  });
};

// 检查收敛
const isConverged = (forces, threshold = 0.5) => {
  let totalForce = 0;
  let count = 0;
  
  forces.forEach(force => {
    totalForce += Math.sqrt(force.x * force.x + force.y * force.y);
    count++;
  });
  
  const averageForce = count > 0 ? totalForce / count : 0;
  return averageForce < threshold;
};