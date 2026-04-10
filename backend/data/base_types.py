from enum import Enum
from typing import Any, Optional, Union
import re

class PortDirection(Enum):
    """端口方向枚举"""
    INPUT = "input"
    OUTPUT = "output" 
    INOUT = "inout"

class SignalType(Enum):
    """信号类型枚举"""
    WIRE = "wire"
    REG = "reg"
    LOGIC = "logic"

# 前端显示相关的枚举
class NodeType(Enum):
    """React Flow 节点类型"""
    MODULE = "moduleNode"
    TOP_MODULE = "topModuleNode"

class EdgeType(Enum):
    """React Flow 边类型"""
    INSTANTIATION = "instantiation"  # 实例化关系
    CONNECTION = "connection"        # 信号连接

# 常量定义 - 专注于前端显示需要的
DEFAULT_SIGNAL_WIDTH = 1
NODE_WIDTH = 200
NODE_HEIGHT = 150
GRID_SPACING = 300

def parse_signal_width(range_spec: Optional[str]) -> int:
    """解析信号宽度 - 简化版本，专注于显示需要"""
    if not range_spec:
        return DEFAULT_SIGNAL_WIDTH
    
    try:
        # 移除空格和括号
        clean_range = range_spec.strip().strip('[]')
        
        if ':' in clean_range:
            # [high:low] 格式
            high, low = clean_range.split(':')
            return abs(int(high.strip()) - int(low.strip())) + 1
        else:
            # [n] 格式，表示 [n:0]
            return int(clean_range.strip()) + 1
    except:
        return DEFAULT_SIGNAL_WIDTH

def format_port_label(name: str, width: int) -> str:
    """格式化端口标签用于前端显示"""
    if width > 1:
        return f"{name}[{width-1}:0]"
    return name

def validate_identifier(name: str) -> bool:
    """简单的标识符验证"""
    if not name or not isinstance(name, str):
        return False
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))

# 前端布局相关的工具函数
def calculate_node_position(index: int, nodes_per_row: int = 3) -> dict:
    """计算节点在画布上的位置"""
    row = index // nodes_per_row
    col = index % nodes_per_row
    return {
        'x': col * GRID_SPACING,
        'y': row * GRID_SPACING
    }

# 异常类
class ValidationError(Exception):
    """数据验证错误"""
    pass

__all__ = [
    'PortDirection', 'SignalType', 'NodeType', 'EdgeType',
    'DEFAULT_SIGNAL_WIDTH', 'NODE_WIDTH', 'NODE_HEIGHT', 'GRID_SPACING',
    'parse_signal_width', 'format_port_label', 'validate_identifier',
    'calculate_node_position', 'ValidationError'
]