from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Tuple
import json
from .base_types import ValidationError, EdgeType
from .module_models import ModuleInfo, ModuleCollection

@dataclass
class HierarchyNode:
    """层次结构节点"""
    module_name: str
    instance_name: Optional[str] = None  # 如果是实例化节点
    depth: int = 0
    children: List['HierarchyNode'] = field(default_factory=list)
    is_missing: bool = False  # 模块定义缺失
    is_circular: bool = False  # 循环引用
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        if self.instance_name:
            return f"{self.instance_name} ({self.module_name})"
        return self.module_name
    
    @property
    def node_type(self) -> str:
        """节点类型"""
        if self.is_missing:
            return "missing"
        elif self.is_circular:
            return "circular"
        elif self.depth == 0:
            return "top"
        else:
            return "normal"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'module_name': self.module_name,
            'instance_name': self.instance_name,
            'display_name': self.display_name,
            'depth': self.depth,
            'node_type': self.node_type,
            'children': [child.to_dict() for child in self.children],
            'child_count': len(self.children)
        }

class DesignInfo:
    """设计信息容器 - 整个Verilog设计的顶层数据结构"""
    
    def __init__(self):
        self.modules = ModuleCollection()
        self.file_list: List[str] = []
        self.parse_errors: List[str] = []
        self.parse_warnings: List[str] = []
        self._hierarchy_cache: Optional[HierarchyNode] = None
        self._flow_data_cache: Optional[Dict[str, Any]] = None
    
    # === 模块管理 ===
    def add_module(self, module: ModuleInfo):
        """添加模块"""
        self.modules.add_module(module)
        self._invalidate_cache()
    
    def get_module(self, name: str) -> Optional[ModuleInfo]:
        """获取模块"""
        return self.modules.get_module(name)
    
    def remove_module(self, name: str) -> bool:
        """移除模块"""
        result = self.modules.remove_module(name)
        if result:
            self._invalidate_cache()
        return result
    
    # === 文件管理 ===
    def add_file(self, file_path: str):
        """添加源文件"""
        if file_path not in self.file_list:
            self.file_list.append(file_path)
    
    # === 错误和警告管理 ===
    def add_error(self, error: str):
        """添加解析错误"""
        self.parse_errors.append(error)
    
    def add_warning(self, warning: str):
        """添加解析警告"""
        self.parse_warnings.append(warning)
    
    # === 顶层模块管理 ===
    @property
    def top_module(self) -> Optional[ModuleInfo]:
        """获取顶层模块"""
        return self.modules.find_top_module()
    
    def set_top_module(self, module_name: str) -> bool:
        """手动设置顶层模块"""
        module = self.get_module(module_name)
        if module:
            # 清除其他模块的顶层标记
            for mod in self.modules.all_modules:
                mod.is_top_module = False
            
            # 设置新的顶层模块
            module.is_top_module = True
            self.modules._top_module = module_name
            self._invalidate_cache()
            return True
        return False
    
    # === 层次结构分析 ===
    def build_hierarchy(self, force_rebuild: bool = False) -> HierarchyNode:
        """构建模块层次结构"""
        if self._hierarchy_cache and not force_rebuild:
            return self._hierarchy_cache
        
        top_module = self.top_module
        if not top_module:
            # 没有顶层模块，创建虚拟根节点
            root = HierarchyNode(
                module_name="<No Top Module>",
                depth=0,
                is_missing=True
            )
            self._hierarchy_cache = root
            return root
        
        def build_tree(module_name: str, instance_name: Optional[str], 
                      depth: int, visited: Set[str]) -> HierarchyNode:
            # 检查循环引用
            if module_name in visited:
                return HierarchyNode(
                    module_name=module_name,
                    instance_name=instance_name,
                    depth=depth,
                    is_circular=True
                )
            
            # 检查模块是否存在
            module = self.get_module(module_name)
            if not module:
                return HierarchyNode(
                    module_name=module_name,
                    instance_name=instance_name,
                    depth=depth,
                    is_missing=True
                )
            
            # 创建节点
            node = HierarchyNode(
                module_name=module_name,
                instance_name=instance_name,
                depth=depth
            )
            
            # 递归构建子节点
            new_visited = visited | {module_name}
            for instance in module.instances.all_instances:
                child = build_tree(
                    instance.module_type,
                    instance.instance_name,
                    depth + 1,
                    new_visited
                )
                node.children.append(child)
            
            return node
        
        self._hierarchy_cache = build_tree(top_module.name, None, 0, set())
        return self._hierarchy_cache
    
    def get_hierarchy_stats(self) -> Dict[str, Any]:
        """获取层次结构统计"""
        hierarchy = self.build_hierarchy()
        
        def collect_stats(node: HierarchyNode, stats: Dict[str, Any]):
            stats['total_nodes'] += 1
            stats['max_depth'] = max(stats['max_depth'], node.depth)
            
            if node.is_missing:
                stats['missing_modules'] += 1
                stats['missing_list'].append(node.module_name)
            elif node.is_circular:
                stats['circular_refs'] += 1
            
            for child in node.children:
                collect_stats(child, stats)
        
        stats = {
            'total_nodes': 0,
            'max_depth': 0,
            'missing_modules': 0,
            'circular_refs': 0,
            'missing_list': []
        }
        
        collect_stats(hierarchy, stats)
        return stats
    
    # === React Flow 数据生成 ===
    def generate_flow_data(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """生成 React Flow 可视化数据"""
        if self._flow_data_cache and not force_rebuild:
            return self._flow_data_cache
        
        nodes = []
        edges = []
        
        # 生成节点
        for i, module in enumerate(self.modules.all_modules):
            node = module.to_react_flow_node(position_index=i)
            nodes.append(node)
        
        # 生成边（实例化关系）
        for module in self.modules.all_modules:
            module_edges = module.to_react_flow_edges()
            edges.extend(module_edges)
        
        # 添加边的样式和动画
        for edge in edges:
            edge['type'] = EdgeType.INSTANTIATION.value
            if not edge.get('animated'):
                edge['animated'] = True
        
        self._flow_data_cache = {
            'nodes': nodes,
            'edges': edges,
            'viewport': {
                'x': 0,
                'y': 0,
                'zoom': 1
            }
        }
        
        return self._flow_data_cache
    
    # === 验证和检查 ===
    def validate_design(self) -> Dict[str, Any]:
        """验证设计完整性"""
        issues = {
            'errors': [],
            'warnings': [],
            'missing_modules': [],
            'unused_modules': [],
            'circular_dependencies': []
        }
        
        # 检查缺失的模块
        all_referenced = set()
        for module in self.modules.all_modules:
            all_referenced.update(module.instantiated_modules)
        
        for ref_module in all_referenced:
            if ref_module not in self.modules.module_names:
                issues['missing_modules'].append(ref_module)
        
        # 检查未使用的模块
        instantiated = set()
        for module in self.modules.all_modules:
            instantiated.update(module.instantiated_modules)
        
        for module_name in self.modules.module_names:
            module = self.get_module(module_name)
            if module and module_name not in instantiated and not module.is_top_module:
                issues['unused_modules'].append(module_name)
        
        # 检查循环依赖
        hierarchy = self.build_hierarchy()
        def find_circular(node: HierarchyNode, path: List[str]):
            if node.is_circular:
                issues['circular_dependencies'].append(path + [node.module_name])
            for child in node.children:
                find_circular(child, path + [node.module_name])
        
        find_circular(hierarchy, [])
        
        # 添加错误和警告
        if issues['missing_modules']:
            issues['errors'].append(f"Missing module definitions: {', '.join(issues['missing_modules'])}")
        
        if issues['circular_dependencies']:
            issues['warnings'].append(f"Circular dependencies detected: {len(issues['circular_dependencies'])} cases")
        
        if not self.top_module:
            issues['warnings'].append("No top module identified")
        
        return issues
    
    # === 统计信息 ===
    @property
    def stats(self) -> Dict[str, Any]:
        """设计统计信息"""
        hierarchy_stats = self.get_hierarchy_stats()
        validation = self.validate_design()
        
        total_instances = sum(
            module.instances.instance_count 
            for module in self.modules.all_modules
        )
        
        total_ports = sum(
            len(module.ports.all_ports)
            for module in self.modules.all_modules
        )
        
        return {
            'modules': {
                'total': self.modules.module_count,
                'top_module': self.modules._top_module,
                'with_instances': len([m for m in self.modules.all_modules if m.has_instances])
            },
            'instances': {
                'total': total_instances,
                'unique_types': len(set().union(*[m.instantiated_modules for m in self.modules.all_modules]))
            },
            'ports': {
                'total': total_ports
            },
            'hierarchy': hierarchy_stats,
            'files': {
                'count': len(self.file_list),
                'list': self.file_list
            },
            'validation': {
                'error_count': len(validation['errors']),
                'warning_count': len(validation['warnings']),
                'missing_modules': len(validation['missing_modules']),
                'unused_modules': len(validation['unused_modules'])
            },
            'parse_status': {
                'errors': len(self.parse_errors),
                'warnings': len(self.parse_warnings)
            }
        }
    
    # === 序列化 ===
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'modules': self.modules.to_dict(),
            'hierarchy': self.build_hierarchy().to_dict(),
            'flow_data': self.generate_flow_data(),
            'stats': self.stats,
            'files': self.file_list,
            'errors': self.parse_errors,
            'warnings': self.parse_warnings,
            'validation': self.validate_design()
        }
    
    def export_json(self, file_path: str, include_flow_data: bool = True):
        """导出为 JSON 文件"""
        data = self.to_dict()
        if not include_flow_data:
            data.pop('flow_data', None)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DesignInfo':
        """从字典创建 DesignInfo 对象"""
        design = cls()
        
        # 恢复模块数据
        modules_data = data.get('modules', {})
        for module_data in modules_data.get('modules', {}).values():
            module = ModuleInfo.from_dict(module_data)
            design.add_module(module)
        
        # 恢复其他数据
        design.file_list = data.get('files', [])
        design.parse_errors = data.get('errors', [])
        design.parse_warnings = data.get('warnings', [])
        
        # 设置顶层模块
        top_module = modules_data.get('top_module')
        if top_module:
            design.set_top_module(top_module)
        
        return design
    
    def _invalidate_cache(self):
        """清除缓存"""
        self._hierarchy_cache = None
        self._flow_data_cache = None

# 工具函数
def create_design() -> DesignInfo:
    """创建新的设计对象"""
    return DesignInfo()

def load_design_from_json(file_path: str) -> DesignInfo:
    """从 JSON 文件加载设计"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return DesignInfo.from_dict(data)

__all__ = [
    'HierarchyNode', 'DesignInfo', 
    'create_design', 'load_design_from_json'
]