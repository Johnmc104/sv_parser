from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from .base_types import (
    NodeType, calculate_node_position, 
    validate_identifier, ValidationError,
    NODE_WIDTH, NODE_HEIGHT
)
from .port_models import PortInfo, PortCollection
from .connection_models import (
    InstanceInfo, InstanceCollection, 
    ParameterInfo, WireInfo
)

@dataclass
class ModuleInfo:
    """模块信息 - 核心的模块数据结构"""
    name: str
    ports: PortCollection = field(default_factory=PortCollection)
    instances: InstanceCollection = field(default_factory=InstanceCollection)
    parameters: List[ParameterInfo] = field(default_factory=list)
    wires: List[WireInfo] = field(default_factory=list)
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    is_top_module: bool = False
    
    def __post_init__(self):
        """数据验证"""
        if not validate_identifier(self.name):
            raise ValidationError(f"Invalid module name: {self.name}")
    
    # === 端口操作 ===
    def add_port(self, port: PortInfo):
        """添加端口"""
        self.ports.add_port(port)
    
    def get_port(self, name: str) -> Optional[PortInfo]:
        """获取端口"""
        return self.ports.get_port(name)
    
    # === 实例操作 ===
    def add_instance(self, instance: InstanceInfo):
        """添加实例"""
        self.instances.add_instance(instance)
    
    def get_instance(self, name: str) -> Optional[InstanceInfo]:
        """获取实例"""
        return self.instances.get_instance(name)
    
    # === 参数操作 ===
    def add_parameter(self, parameter: ParameterInfo):
        """添加参数"""
        # 检查参数名是否重复
        for existing in self.parameters:
            if existing.name == parameter.name:
                raise ValidationError(f"Parameter {parameter.name} already exists")
        self.parameters.append(parameter)
    
    def get_parameter(self, name: str) -> Optional[ParameterInfo]:
        """获取参数"""
        for param in self.parameters:
            if param.name == name:
                return param
        return None
    
    # === 线网操作 ===
    def add_wire(self, wire: WireInfo):
        """添加线网"""
        # 检查线网名是否重复
        for existing in self.wires:
            if existing.name == wire.name:
                raise ValidationError(f"Wire {wire.name} already exists")
        self.wires.append(wire)
    
    def get_wire(self, name: str) -> Optional[WireInfo]:
        """获取线网"""
        for wire in self.wires:
            if wire.name == name:
                return wire
        return None
    
    # === 依赖关系分析 ===
    @property
    def instantiated_modules(self) -> Set[str]:
        """获取此模块实例化的所有模块类型"""
        return set(inst.module_type for inst in self.instances.all_instances)
    
    @property
    def has_instances(self) -> bool:
        """是否包含实例"""
        return self.instances.instance_count > 0
    
    @property
    def complexity_score(self) -> int:
        """模块复杂度评分（用于布局优化）"""
        return (
            len(self.ports.all_ports) * 2 +           # 端口权重
            self.instances.instance_count * 5 +        # 实例权重
            len(self.parameters) * 1 +                 # 参数权重
            len(self.wires) * 1                        # 线网权重
        )
    
    # === 统计信息 ===
    @property
    def stats(self) -> Dict[str, Any]:
        """模块统计信息"""
        return {
            'name': self.name,
            'ports': self.ports.port_count,
            'instances': {
                'total': self.instances.instance_count,
                'types': len(self.instances.module_types),
                'module_types': self.instances.module_types
            },
            'parameters': len(self.parameters),
            'wires': len(self.wires),
            'complexity_score': self.complexity_score,
            'is_top_module': self.is_top_module,
            'instantiated_modules': list(self.instantiated_modules)
        }
    
    # === React Flow 数据生成 ===
    def to_react_flow_node(self, position_index: int = 0) -> Dict[str, Any]:
        """转换为 React Flow 节点数据"""
        position = calculate_node_position(position_index)
        
        node_type = NodeType.TOP_MODULE.value if self.is_top_module else NodeType.MODULE.value
        
        # 为前端准备的端口数据
        port_groups = {
            'input': [port.to_dict() for port in self.ports.input_ports],
            'output': [port.to_dict() for port in self.ports.output_ports],
            'inout': [port.to_dict() for port in self.ports.inout_ports]
        }
        
        # 实例信息（用于节点内部显示）
        instance_summary = []
        for inst in self.instances.all_instances[:5]:  # 最多显示5个实例
            instance_summary.append({
                'name': inst.instance_name,
                'type': inst.module_type,
                'has_params': inst.has_parameters
            })
        
        return {
            'id': self.name,
            'type': node_type,
            'position': position,
            'data': {
                'label': self.name,
                'module_name': self.name,
                'is_top': self.is_top_module,
                'ports': port_groups,
                'port_handles': self.ports.to_react_flow_handles(),
                'instances': instance_summary,
                'instance_count': self.instances.instance_count,
                'parameters': [param.to_dict() for param in self.parameters],
                'stats': self.stats,
                'complexity': self.complexity_score
            },
            'style': {
                'width': NODE_WIDTH,
                'height': NODE_HEIGHT,
                'border': '2px solid' + (' #FF5722' if self.is_top_module else ' #2196F3'),
                'borderRadius': 8,
                'backgroundColor': '#ffffff',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
            }
        }
    
    def to_react_flow_edges(self) -> List[Dict[str, Any]]:
        """生成此模块的所有实例化边"""
        return self.instances.to_react_flow_edges(self.name)
    
    # === 序列化 ===
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'ports': self.ports.to_dict(),
            'instances': self.instances.to_dict(),
            'parameters': [param.to_dict() for param in self.parameters],
            'wires': [wire.to_dict() for wire in self.wires],
            'file_path': self.file_path,
            'line_number': self.line_number,
            'is_top_module': self.is_top_module,
            'stats': self.stats
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModuleInfo':
        """从字典创建 ModuleInfo 对象"""
        # 创建基本模块
        module = cls(
            name=data['name'],
            file_path=data.get('file_path'),
            line_number=data.get('line_number'),
            is_top_module=data.get('is_top_module', False)
        )
        
        # 恢复端口
        if 'ports' in data:
            module.ports = PortCollection.from_dict(data['ports'])
        
        # 恢复实例
        if 'instances' in data:
            for inst_data in data['instances'].get('instances', {}).values():
                instance = InstanceInfo.from_dict(inst_data)
                module.add_instance(instance)
        
        # 恢复参数
        for param_data in data.get('parameters', []):
            param = ParameterInfo(
                name=param_data['name'],
                value=param_data['value'],
                param_type=param_data.get('param_type', 'integer')
            )
            module.add_parameter(param)
        
        # 恢复线网
        for wire_data in data.get('wires', []):
            wire = WireInfo(
                name=wire_data['name'],
                width=wire_data.get('width', 1),
                range_spec=wire_data.get('range_spec')
            )
            module.add_wire(wire)
        
        return module

class ModuleCollection:
    """模块集合 - 管理整个设计中的所有模块"""
    
    def __init__(self):
        self._modules: Dict[str, ModuleInfo] = {}
        self._top_module: Optional[str] = None
    
    def add_module(self, module: ModuleInfo):
        """添加模块"""
        if module.name in self._modules:
            raise ValidationError(f"Module {module.name} already exists")
        self._modules[module.name] = module
        
        # 如果是顶层模块，设置标记
        if module.is_top_module:
            self._top_module = module.name
    
    def get_module(self, name: str) -> Optional[ModuleInfo]:
        """获取模块"""
        return self._modules.get(name)
    
    def remove_module(self, name: str) -> bool:
        """移除模块"""
        if name in self._modules:
            if self._top_module == name:
                self._top_module = None
            del self._modules[name]
            return True
        return False
    
    @property
    def all_modules(self) -> List[ModuleInfo]:
        """获取所有模块"""
        return list(self._modules.values())
    
    @property
    def module_names(self) -> List[str]:
        """获取所有模块名称"""
        return list(self._modules.keys())
    
    @property
    def module_count(self) -> int:
        """模块数量"""
        return len(self._modules)
    
    @property
    def top_module(self) -> Optional[ModuleInfo]:
        """获取顶层模块"""
        if self._top_module:
            return self._modules.get(self._top_module)
        return None
    
    def find_top_module(self) -> Optional[ModuleInfo]:
        """自动查找顶层模块"""
        if self._top_module and self._top_module in self._modules:
            return self._modules[self._top_module]
        
        # 查找没有被实例化的模块
        instantiated_modules = set()
        for module in self._modules.values():
            instantiated_modules.update(module.instantiated_modules)
        
        top_candidates = set(self._modules.keys()) - instantiated_modules
        
        if len(top_candidates) == 1:
            top_name = list(top_candidates)[0]
            self._top_module = top_name
            self._modules[top_name].is_top_module = True
            return self._modules[top_name]
        elif len(top_candidates) > 1:
            # 选择复杂度最高的作为顶层
            max_complexity = 0
            top_candidate = None
            for candidate in top_candidates:
                complexity = self._modules[candidate].complexity_score
                if complexity > max_complexity:
                    max_complexity = complexity
                    top_candidate = candidate
            
            if top_candidate:
                self._top_module = top_candidate
                self._modules[top_candidate].is_top_module = True
                return self._modules[top_candidate]
        
        return None
    
    def get_instantiation_relationships(self) -> List[Dict[str, Any]]:
        """获取所有实例化关系"""
        relationships = []
        for module in self._modules.values():
            for instance in module.instances.all_instances:
                relationships.append({
                    'parent_module': module.name,
                    'child_module': instance.module_type,
                    'instance_name': instance.instance_name,
                    'has_parameters': instance.has_parameters,
                    'connection_count': instance.connection_count
                })
        return relationships
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'modules': {name: module.to_dict() for name, module in self._modules.items()},
            'top_module': self._top_module,
            'stats': {
                'total_modules': self.module_count,
                'module_names': self.module_names,
                'instantiation_count': len(self.get_instantiation_relationships())
            }
        }

# 工具函数
def create_module(name: str, is_top: bool = False) -> ModuleInfo:
    """快速创建模块"""
    return ModuleInfo(name=name, is_top_module=is_top)

__all__ = [
    'ModuleInfo', 'ModuleCollection', 'create_module'
]