from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from .base_types import validate_identifier, ValidationError

@dataclass
class ParameterInfo:
    """参数信息 - 用于模块参数化和前端显示"""
    name: str
    value: Any
    param_type: str = "integer"  # integer, string, real, localparam
    
    def __post_init__(self):
        """数据验证"""
        if not validate_identifier(self.name):
            raise ValidationError(f"Invalid parameter name: {self.name}")
    
    @property
    def display_value(self) -> str:
        """用于前端显示的值"""
        if isinstance(self.value, str):
            return f'"{self.value}"' if self.param_type == "string" else self.value
        return str(self.value)
    
    @property
    def is_overridable(self) -> bool:
        """是否可以被重写（非 localparam）"""
        return self.param_type != "localparam"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'value': self.value,
            'param_type': self.param_type,
            'display_value': self.display_value,
            'is_overridable': self.is_overridable
        }

@dataclass
class ConnectionInfo:
    """端口连接信息 - 描述实例化时的端口连接"""
    port_name: str          # 被实例化模块的端口名
    signal_name: str        # 连接的信号名
    is_constant: bool = False
    constant_value: Optional[str] = None
    
    def __post_init__(self):
        """数据验证"""
        if not self.port_name:
            raise ValidationError("Port name cannot be empty")
        if not self.signal_name and not self.is_constant:
            raise ValidationError("Signal name cannot be empty for non-constant connection")
    
    @property
    def connection_label(self) -> str:
        """用于前端显示的连接标签"""
        if self.is_constant:
            return f"{self.port_name} = {self.constant_value or 'const'}"
        return f"{self.port_name} ← {self.signal_name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'port_name': self.port_name,
            'signal_name': self.signal_name,
            'is_constant': self.is_constant,
            'constant_value': self.constant_value,
            'connection_label': self.connection_label
        }

@dataclass 
class InstanceInfo:
    """模块实例化信息 - 核心的实例化关系数据"""
    instance_name: str                              # 实例名称
    module_type: str                               # 被实例化的模块类型
    connections: List[ConnectionInfo] = field(default_factory=list)  # 端口连接
    parameters: Dict[str, Any] = field(default_factory=dict)         # 参数重写
    position: Optional[Dict[str, int]] = None       # 前端布局位置
    
    def __post_init__(self):
        """数据验证"""
        if not validate_identifier(self.instance_name):
            raise ValidationError(f"Invalid instance name: {self.instance_name}")
        if not validate_identifier(self.module_type):
            raise ValidationError(f"Invalid module type: {self.module_type}")
    
    def add_connection(self, port_name: str, signal_name: str = "", 
                      is_constant: bool = False, constant_value: Optional[str] = None):
        """添加端口连接"""
        connection = ConnectionInfo(
            port_name=port_name,
            signal_name=signal_name,
            is_constant=is_constant,
            constant_value=constant_value
        )
        self.connections.append(connection)
    
    def get_connection(self, port_name: str) -> Optional[ConnectionInfo]:
        """获取指定端口的连接"""
        for conn in self.connections:
            if conn.port_name == port_name:
                return conn
        return None
    
    def set_parameter(self, param_name: str, value: Any):
        """设置参数值"""
        self.parameters[param_name] = value
    
    @property
    def display_name(self) -> str:
        """用于前端显示的名称"""
        if self.parameters:
            param_str = ", ".join([f"{k}={v}" for k, v in list(self.parameters.items())[:2]])
            if len(self.parameters) > 2:
                param_str += "..."
            return f"{self.instance_name}\n({param_str})"
        return self.instance_name
    
    @property
    def edge_label(self) -> str:
        """用于 React Flow 边的标签"""
        return f"{self.instance_name} : {self.module_type}"
    
    @property
    def has_parameters(self) -> bool:
        """是否有参数重写"""
        return bool(self.parameters)
    
    @property
    def connection_count(self) -> int:
        """连接数量"""
        return len(self.connections)
    
    def to_react_flow_edge(self, parent_module: str) -> Dict[str, Any]:
        """转换为 React Flow 边数据 - 表示实例化关系"""
        return {
            'id': f"{parent_module}-{self.instance_name}",
            'source': parent_module,
            'target': self.module_type,
            'label': self.edge_label,
            'type': 'smoothstep',
            'animated': True,
            'style': {
                'stroke': '#2196F3',
                'strokeWidth': 2,
            },
            'labelStyle': {
                'fontSize': 10,
                'fontWeight': 'bold'
            },
            'data': {
                'instance_name': self.instance_name,
                'module_type': self.module_type,
                'has_parameters': self.has_parameters,
                'connection_count': self.connection_count
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'instance_name': self.instance_name,
            'module_type': self.module_type,
            'connections': [conn.to_dict() for conn in self.connections],
            'parameters': self.parameters,
            'position': self.position,
            'display_name': self.display_name,
            'edge_label': self.edge_label,
            'has_parameters': self.has_parameters,
            'connection_count': self.connection_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InstanceInfo':
        """从字典创建 InstanceInfo 对象"""
        connections = [
            ConnectionInfo(
                port_name=conn['port_name'],
                signal_name=conn['signal_name'],
                is_constant=conn.get('is_constant', False),
                constant_value=conn.get('constant_value')
            )
            for conn in data.get('connections', [])
        ]
        
        return cls(
            instance_name=data['instance_name'],
            module_type=data['module_type'],
            connections=connections,
            parameters=data.get('parameters', {}),
            position=data.get('position')
        )

@dataclass
class WireInfo:
    """线网信息 - 用于模块内部信号声明"""
    name: str
    width: int = 1
    range_spec: Optional[str] = None
    
    def __post_init__(self):
        """数据验证"""
        if not validate_identifier(self.name):
            raise ValidationError(f"Invalid wire name: {self.name}")
        if self.width < 1:
            self.width = 1
    
    @property
    def is_bus(self) -> bool:
        """是否为总线"""
        return self.width > 1
    
    @property
    def display_name(self) -> str:
        """用于前端显示的名称"""
        if self.is_bus:
            range_str = self.range_spec or f"[{self.width-1}:0]"
            return f"{self.name} {range_str}"
        return self.name
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'width': self.width,
            'range_spec': self.range_spec,
            'is_bus': self.is_bus,
            'display_name': self.display_name
        }

class InstanceCollection:
    """实例集合 - 管理模块内的所有实例"""
    
    def __init__(self):
        self._instances: Dict[str, InstanceInfo] = {}
    
    def add_instance(self, instance: InstanceInfo):
        """添加实例"""
        if instance.instance_name in self._instances:
            raise ValidationError(f"Instance {instance.instance_name} already exists")
        self._instances[instance.instance_name] = instance
    
    def get_instance(self, name: str) -> Optional[InstanceInfo]:
        """获取实例"""
        return self._instances.get(name)
    
    def remove_instance(self, name: str) -> bool:
        """移除实例"""
        if name in self._instances:
            del self._instances[name]
            return True
        return False
    
    @property
    def all_instances(self) -> List[InstanceInfo]:
        """获取所有实例"""
        return list(self._instances.values())
    
    @property
    def instance_count(self) -> int:
        """实例数量"""
        return len(self._instances)
    
    @property
    def module_types(self) -> List[str]:
        """获取所有被实例化的模块类型"""
        return list(set(inst.module_type for inst in self._instances.values()))
    
    def get_instances_by_type(self, module_type: str) -> List[InstanceInfo]:
        """根据模块类型获取实例"""
        return [inst for inst in self._instances.values() if inst.module_type == module_type]
    
    def to_react_flow_edges(self, parent_module: str) -> List[Dict[str, Any]]:
        """转换为 React Flow 边列表"""
        return [inst.to_react_flow_edge(parent_module) for inst in self._instances.values()]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'instances': {name: inst.to_dict() for name, inst in self._instances.items()},
            'stats': {
                'total_instances': self.instance_count,
                'module_types': self.module_types,
                'type_count': len(self.module_types)
            }
        }

# 工具函数：快速创建实例和连接
def create_instance(instance_name: str, module_type: str, 
                   parameters: Optional[Dict[str, Any]] = None) -> InstanceInfo:
    """快速创建实例"""
    return InstanceInfo(
        instance_name=instance_name,
        module_type=module_type,
        parameters=parameters or {}
    )

def create_parameter(name: str, value: Any, param_type: str = "integer") -> ParameterInfo:
    """快速创建参数"""
    return ParameterInfo(name=name, value=value, param_type=param_type)

__all__ = [
    'ParameterInfo', 'ConnectionInfo', 'InstanceInfo', 'WireInfo', 'InstanceCollection',
    'create_instance', 'create_parameter'
]