"""
Verilog 数据模型包

提供完整的 Verilog 设计数据结构，专门为前端 React Flow 可视化优化。

主要组件：
- base_types: 基础类型和枚举
- port_models: 端口数据模型
- connection_models: 连接和参数数据模型  
- module_models: 模块数据模型
- design_models: 设计容器数据模型
"""

# 导入所有公共接口
from .base_types import (
    PortDirection, SignalType, NodeType, EdgeType,
    DEFAULT_SIGNAL_WIDTH, NODE_WIDTH, NODE_HEIGHT, GRID_SPACING,
    parse_signal_width, format_port_label, validate_identifier,
    calculate_node_position, ValidationError
)

from .port_models import (
    PortInfo, PortCollection,
    create_input_port, create_output_port, create_inout_port
)

from .connection_models import (
    ParameterInfo, ConnectionInfo, InstanceInfo, WireInfo, InstanceCollection,
    create_instance, create_parameter
)

from .module_models import (
    ModuleInfo, ModuleCollection, create_module
)

from .design_models import (
    HierarchyNode, DesignInfo,
    create_design, load_design_from_json
)

# 版本信息
__version__ = "1.0.0"

# 快速创建函数（便于测试和使用）
def create_simple_design(name: str = "test_design") -> DesignInfo:
    """创建一个简单的测试设计"""
    design = create_design()
    
    # 创建一个简单的顶层模块
    top_module = create_module("top", is_top=True)
    top_module.add_port(create_input_port("clk"))
    top_module.add_port(create_input_port("rst_n"))
    top_module.add_port(create_output_port("led", 8))
    
    design.add_module(top_module)
    return design

__all__ = [
    # 基础类型
    'PortDirection', 'SignalType', 'NodeType', 'EdgeType', 'ValidationError',
    
    # 数据模型类
    'PortInfo', 'PortCollection',
    'ParameterInfo', 'ConnectionInfo', 'InstanceInfo', 'WireInfo', 'InstanceCollection',
    'ModuleInfo', 'ModuleCollection',
    'HierarchyNode', 'DesignInfo',
    
    # 工具函数
    'parse_signal_width', 'format_port_label', 'validate_identifier', 'calculate_node_position',
    'create_input_port', 'create_output_port', 'create_inout_port',
    'create_instance', 'create_parameter', 'create_module',
    'create_design', 'load_design_from_json', 'create_simple_design',
    
    # 常量
    'DEFAULT_SIGNAL_WIDTH', 'NODE_WIDTH', 'NODE_HEIGHT', 'GRID_SPACING',
    
    # 版本
    '__version__'
]