from flask import request, jsonify, current_app
import tempfile
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime

# 导入核心模块
from ..data import (
    DesignInfo, ValidationError, create_design
)

# 全局设计数据存储
current_design: Optional[DesignInfo] = None

def get_current_design() -> DesignInfo:
    """获取当前设计对象，如果不存在则创建新的"""
    global current_design
    if current_design is None:
        current_design = create_design()
    return current_design

def clear_current_design():
    """清除当前设计数据"""
    global current_design
    current_design = None

# === 解析相关处理器 ===
def parse_verilog_files():
    """解析上传的 Verilog 文件"""
    try:
        # 检查文件上传
        files = request.files.getlist('verilog_files')
        top_module = request.form.get('top_module', '').strip()
        
        if not files:
            return jsonify({
                'success': False,
                'error': 'No files uploaded'
            }), 400
        
        # 验证文件类型
        valid_files = []
        for file in files:
            if file.filename and file.filename.endswith(('.v', '.sv')):
                valid_files.append(file)
        
        if not valid_files:
            return jsonify({
                'success': False,
                'error': 'No valid Verilog files found (.v or .sv)'
            }), 400
        
        # 创建临时目录保存文件
        with tempfile.TemporaryDirectory() as temp_dir:
            saved_files = []
            parse_logs = []
            
            # 保存文件
            for file in valid_files:
                file_path = os.path.join(temp_dir, file.filename)
                file.save(file_path)
                saved_files.append(file_path)
                parse_logs.append(f"Saved file: {file.filename}")
            
            # 这里应该调用实际的解析器
            # 暂时使用模拟数据演示
            design = _parse_files_mock(saved_files, top_module)
            
            # 更新全局设计对象
            global current_design
            current_design = design
            
            # 添加文件列表到设计对象
            for file_path in saved_files:
                design.add_file(os.path.basename(file_path))
            
            parse_logs.append(f"Successfully parsed {design.modules.module_count} modules")
            
            return jsonify({
                'success': True,
                'message': 'Files parsed successfully',
                'stats': design.stats,
                'flow_data': design.generate_flow_data(),
                'hierarchy': design.build_hierarchy().to_dict(),
                'logs': parse_logs,
                'timestamp': datetime.now().isoformat()
            })
    
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation Error',
            'message': str(e)
        }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': str(e)
        }), 500

def clear_design():
    """清除当前设计数据"""
    try:
        clear_current_design()
        return jsonify({
            'success': True,
            'message': 'Design data cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# === 设计信息处理器 ===
def get_design_info(stats_only: bool = False, modules_only: bool = False):
    """获取设计信息"""
    try:
        design = get_current_design()
        
        if not design.modules.module_count:
            return jsonify({
                'success': False,
                'error': 'No design data available',
                'message': 'Please parse Verilog files first'
            }), 404
        
        if stats_only:
            return jsonify({
                'success': True,
                'stats': design.stats
            })
        
        if modules_only:
            modules_info = []
            for module in design.modules.all_modules:
                modules_info.append({
                    'name': module.name,
                    'is_top': module.is_top_module,
                    'port_count': len(module.ports.all_ports),
                    'instance_count': module.instances.instance_count,
                    'complexity': module.complexity_score
                })
            
            return jsonify({
                'success': True,
                'modules': modules_info,
                'total_count': len(modules_info)
            })
        
        # 返回完整设计信息
        return jsonify({
            'success': True,
            'design': design.to_dict()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_module_details(module_name: str):
    """获取特定模块的详细信息"""
    try:
        design = get_current_design()
        module = design.get_module(module_name)
        
        if not module:
            return jsonify({
                'success': False,
                'error': f'Module "{module_name}" not found'
            }), 404
        
        return jsonify({
            'success': True,
            'module': module.to_dict()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def set_top_module(module_name: str):
    """设置顶层模块"""
    try:
        design = get_current_design()
        
        if design.set_top_module(module_name):
            return jsonify({
                'success': True,
                'message': f'Top module set to "{module_name}"',
                'flow_data': design.generate_flow_data(force_rebuild=True)
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Module "{module_name}" not found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# === 层次结构处理器 ===
def get_hierarchy_info(force_rebuild: bool = False):
    """获取模块层次结构"""
    try:
        design = get_current_design()
        
        if not design.modules.module_count:
            return jsonify({
                'success': False,
                'error': 'No design data available'
            }), 404
        
        hierarchy = design.build_hierarchy(force_rebuild=force_rebuild)
        hierarchy_stats = design.get_hierarchy_stats()
        
        return jsonify({
            'success': True,
            'hierarchy': hierarchy.to_dict(),
            'stats': hierarchy_stats
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# === React Flow 数据处理器 ===
def get_flow_data(force_rebuild: bool = False):
    """获取 React Flow 可视化数据"""
    try:
        design = get_current_design()
        
        if not design.modules.module_count:
            return jsonify({
                'success': False,
                'error': 'No design data available'
            }), 404
        
        flow_data = design.generate_flow_data(force_rebuild=force_rebuild)
        
        return jsonify({
            'success': True,
            'flow_data': flow_data,
            'stats': {
                'node_count': len(flow_data['nodes']),
                'edge_count': len(flow_data['edges']),
                'top_module': design.modules._top_module
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# === 验证处理器 ===
def validate_design():
    """验证设计完整性"""
    try:
        design = get_current_design()
        
        if not design.modules.module_count:
            return jsonify({
                'success': False,
                'error': 'No design data available'
            }), 404
        
        validation_result = design.validate_design()
        
        return jsonify({
            'success': True,
            'validation': validation_result,
            'is_valid': len(validation_result['errors']) == 0
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# === 导出处理器 ===
def export_design():
    """导出设计数据"""
    try:
        design = get_current_design()
        
        if not design.modules.module_count:
            return jsonify({
                'success': False,
                'error': 'No design data available'
            }), 404
        
        # 获取导出选项
        data = request.get_json() or {}
        include_flow_data = data.get('include_flow_data', True)
        format_type = data.get('format', 'json')  # 目前只支持 json
        
        if format_type != 'json':
            return jsonify({
                'success': False,
                'error': f'Unsupported format: {format_type}'
            }), 400
        
        # 生成导出数据
        export_data = design.to_dict()
        if not include_flow_data:
            export_data.pop('flow_data', None)
        
        return jsonify({
            'success': True,
            'data': export_data,
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'format': format_type,
                'includes_flow_data': include_flow_data,
                'module_count': design.modules.module_count
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# === 系统处理器 ===
def health_check(include_version: bool = False):
    """健康检查"""
    try:
        design = get_current_design()
        
        health_info = {
            'status': 'ok',
            'message': 'Verilog Parser API is running',
            'timestamp': datetime.now().isoformat(),
            'has_design_data': design.modules.module_count > 0
        }
        
        if include_version:
            from ..data import __version__
            health_info['version'] = __version__
            health_info['api_version'] = '1.0.0'
        
        if design.modules.module_count > 0:
            health_info['design_stats'] = {
                'module_count': design.modules.module_count,
                'top_module': design.modules._top_module,
                'file_count': len(design.file_list)
            }
        
        return jsonify(health_info)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# === 辅助函数 ===
def _parse_files_mock(file_paths: list, top_module: str) -> DesignInfo:
    """模拟解析器 - 生成测试数据"""
    from ..data import (
        create_design, create_module, 
        create_input_port, create_output_port, create_instance
    )
    
    design = create_design()
    
    # 创建模拟的模块
    # CPU 模块
    cpu_module = create_module("cpu_core", is_top=bool(top_module == "cpu_core" or not top_module))
    cpu_module.add_port(create_input_port("clk"))
    cpu_module.add_port(create_input_port("rst_n"))
    cpu_module.add_port(create_output_port("mem_addr", 32))
    cpu_module.add_port(create_output_port("mem_data", 32))
    
    # 添加实例
    alu_inst = create_instance("alu_inst", "alu")
    cpu_module.add_instance(alu_inst)
    
    regfile_inst = create_instance("regfile_inst", "register_file")
    cpu_module.add_instance(regfile_inst)
    
    design.add_module(cpu_module)
    
    # ALU 模块
    alu_module = create_module("alu")
    alu_module.add_port(create_input_port("a", 32))
    alu_module.add_port(create_input_port("b", 32))
    alu_module.add_port(create_input_port("op", 4))
    alu_module.add_port(create_output_port("result", 32))
    alu_module.add_port(create_output_port("zero"))
    
    design.add_module(alu_module)
    
    # 寄存器文件模块
    regfile_module = create_module("register_file")
    regfile_module.add_port(create_input_port("clk"))
    regfile_module.add_port(create_input_port("we"))
    regfile_module.add_port(create_input_port("addr", 5))
    regfile_module.add_port(create_input_port("data_in", 32))
    regfile_module.add_port(create_output_port("data_out", 32))
    
    design.add_module(regfile_module)
    
    # 内存模块
    memory_module = create_module("memory")
    memory_module.add_port(create_input_port("clk"))
    memory_module.add_port(create_input_port("addr", 32))
    memory_module.add_port(create_input_port("data_in", 32))
    memory_module.add_port(create_input_port("we"))
    memory_module.add_port(create_output_port("data_out", 32))
    
    design.add_module(memory_module)
    
    # 如果指定了顶层模块
    if top_module and design.get_module(top_module):
        design.set_top_module(top_module)
    
    return design