from dataclasses import dataclass
from typing import Dict, Any, Optional
from .base_types import (
    PortDirection, SignalType, 
    parse_signal_width, format_port_label, 
    validate_identifier, ValidationError
)

@dataclass
class PortInfo:
    """端口信息 - 专注于前端显示和连接"""
    name: str
    direction: PortDirection
    width: int = 1
    range_spec: Optional[str] = None
    
    def __post_init__(self):
        """数据验证和规范化"""
        if not validate_identifier(self.name):
            raise ValidationError(f"Invalid port name: {self.name}")
        
        # 确保方向是枚举类型
        if isinstance(self.direction, str):
            try:
                self.direction = PortDirection(self.direction.lower())
            except ValueError:
                raise ValidationError(f"Invalid port direction: {self.direction}")
        
        # 从 range_spec 重新计算 width（如果提供的话）
        if self.range_spec:
            self.width = parse_signal_width(self.range_spec)
        
        if self.width < 1:
            self.width = 1
    
    @property
    def is_bus(self) -> bool:
        """是否为总线信号"""
        return self.width > 1
    
    @property
    def display_label(self) -> str:
        """用于前端显示的标签"""
        return format_port_label(self.name, self.width)
    
    @property
    def handle_id(self) -> str:
        """React Flow Handle 的 ID"""
        return f"port-{self.name}"
    
    @property
    def handle_position(self) -> str:
        """React Flow Handle 的位置"""
        if self.direction == PortDirection.INPUT:
            return "left"
        elif self.direction == PortDirection.OUTPUT:
            return "right"
        else:  # INOUT
            return "top"
    
    @property
    def handle_type(self) -> str:
        """React Flow Handle 的类型"""
        if self.direction == PortDirection.INPUT:
            return "target"
        elif self.direction == PortDirection.OUTPUT:
            return "source"
        else:  # INOUT
            return "source"  # 双向端口默认作为 source
    
    @property
    def css_class(self) -> str:
        """用于前端样式的 CSS 类名"""
        base_class = f"port port-{self.direction.value}"
        if self.is_bus:
            base_class += " port-bus"
        return base_class
    
    def to_react_flow_handle(self) -> Dict[str, Any]:
        """转换为 React Flow Handle 配置"""
        return {
            'id': self.handle_id,
            'type': self.handle_type,
            'position': self.handle_position,
            'style': {
                'background': self._get_handle_color(),
                'border': '2px solid #555'
            }
        }
    
    def _get_handle_color(self) -> str:
        """根据端口方向返回 Handle 颜色"""
        color_map = {
            PortDirection.INPUT: '#4CAF50',   # 绿色
            PortDirection.OUTPUT: '#FF9800',  # 橙色
            PortDirection.INOUT: '#9C27B0'    # 紫色
        }
        return color_map.get(self.direction, '#666')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式 - 包含前端所需的所有信息"""
        return {
            'name': self.name,
            'direction': self.direction.value,
            'width': self.width,
            'range_spec': self.range_spec,
            'is_bus': self.is_bus,
            'display_label': self.display_label,
            'handle': self.to_react_flow_handle(),
            'css_class': self.css_class
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortInfo':
        """从字典创建 PortInfo 对象"""
        return cls(
            name=data['name'],
            direction=data['direction'],
            width=data.get('width', 1),
            range_spec=data.get('range_spec')
        )

class PortCollection:
    """端口集合 - 用于管理模块的所有端口"""
    
    def __init__(self):
        self._ports: Dict[str, PortInfo] = {}
    
    def add_port(self, port: PortInfo):
        """添加端口"""
        if port.name in self._ports:
            raise ValidationError(f"Port {port.name} already exists")
        self._ports[port.name] = port
    
    def get_port(self, name: str) -> Optional[PortInfo]:
        """获取端口"""
        return self._ports.get(name)
    
    def remove_port(self, name: str) -> bool:
        """移除端口"""
        if name in self._ports:
            del self._ports[name]
            return True
        return False
    
    @property
    def all_ports(self) -> list[PortInfo]:
        """获取所有端口"""
        return list(self._ports.values())
    
    @property
    def input_ports(self) -> list[PortInfo]:
        """获取输入端口"""
        return [p for p in self._ports.values() if p.direction == PortDirection.INPUT]
    
    @property
    def output_ports(self) -> list[PortInfo]:
        """获取输出端口"""
        return [p for p in self._ports.values() if p.direction == PortDirection.OUTPUT]
    
    @property
    def inout_ports(self) -> list[PortInfo]:
        """获取双向端口"""
        return [p for p in self._ports.values() if p.direction == PortDirection.INOUT]
    
    @property
    def port_count(self) -> Dict[str, int]:
        """端口统计"""
        return {
            'total': len(self._ports),
            'input': len(self.input_ports),
            'output': len(self.output_ports),
            'inout': len(self.inout_ports)
        }
    
    def to_react_flow_handles(self) -> list[Dict[str, Any]]:
        """转换为 React Flow Handles 列表"""
        return [port.to_react_flow_handle() for port in self._ports.values()]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'ports': {name: port.to_dict() for name, port in self._ports.items()},
            'stats': self.port_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortCollection':
        """从字典创建 PortCollection 对象"""
        collection = cls()
        for port_data in data.get('ports', {}).values():
            port = PortInfo.from_dict(port_data)
            collection.add_port(port)
        return collection

# 工具函数：快速创建端口
def create_input_port(name: str, width: int = 1, range_spec: Optional[str] = None) -> PortInfo:
    """创建输入端口"""
    return PortInfo(name=name, direction=PortDirection.INPUT, width=width, range_spec=range_spec)

def create_output_port(name: str, width: int = 1, range_spec: Optional[str] = None) -> PortInfo:
    """创建输出端口"""
    return PortInfo(name=name, direction=PortDirection.OUTPUT, width=width, range_spec=range_spec)

def create_inout_port(name: str, width: int = 1, range_spec: Optional[str] = None) -> PortInfo:
    """创建双向端口"""
    return PortInfo(name=name, direction=PortDirection.INOUT, width=width, range_spec=range_spec)

__all__ = [
    'PortInfo', 'PortCollection',
    'create_input_port', 'create_output_port', 'create_inout_port'
]