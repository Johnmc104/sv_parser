from flask import Blueprint
from .handlers import (
    parse_verilog_files,
    get_design_info,
    get_module_details,
    get_hierarchy_info,
    get_flow_data,
    health_check,
    clear_design,
    set_top_module,
    validate_design,
    export_design
)

# 创建 API 蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

# === 核心解析接口 ===
@api_bp.route('/parse-verilog', methods=['POST'])
def route_parse_verilog():
    """解析 Verilog 文件"""
    return parse_verilog_files()

@api_bp.route('/clear', methods=['POST'])
def route_clear_design():
    """清除当前设计数据"""
    return clear_design()

# === 设计信息接口 ===
@api_bp.route('/design', methods=['GET'])
def route_get_design():
    """获取完整设计信息"""
    return get_design_info()

@api_bp.route('/design/stats', methods=['GET'])
def route_get_design_stats():
    """获取设计统计信息"""
    return get_design_info(stats_only=True)

@api_bp.route('/design/validate', methods=['GET'])
def route_validate_design():
    """验证设计完整性"""
    return validate_design()

@api_bp.route('/design/export', methods=['POST'])
def route_export_design():
    """导出设计数据"""
    return export_design()

# === 模块信息接口 ===
@api_bp.route('/modules', methods=['GET'])
def route_get_modules():
    """获取所有模块列表"""
    return get_design_info(modules_only=True)

@api_bp.route('/modules/<module_name>', methods=['GET'])
def route_get_module(module_name):
    """获取特定模块详情"""
    return get_module_details(module_name)

@api_bp.route('/modules/<module_name>/set-top', methods=['POST'])
def route_set_top_module(module_name):
    """设置顶层模块"""
    return set_top_module(module_name)

# === 层次结构接口 ===
@api_bp.route('/hierarchy', methods=['GET'])
def route_get_hierarchy():
    """获取模块层次结构"""
    return get_hierarchy_info()

@api_bp.route('/hierarchy/rebuild', methods=['POST'])
def route_rebuild_hierarchy():
    """重新构建层次结构"""
    return get_hierarchy_info(force_rebuild=True)

# === React Flow 数据接口 ===
@api_bp.route('/flow-data', methods=['GET'])
def route_get_flow_data():
    """获取 React Flow 可视化数据"""
    return get_flow_data()

@api_bp.route('/flow-data/rebuild', methods=['POST'])
def route_rebuild_flow_data():
    """重新生成 Flow 数据"""
    return get_flow_data(force_rebuild=True)

# === 系统接口 ===
@api_bp.route('/health', methods=['GET'])
def route_health():
    """健康检查"""
    return health_check()

@api_bp.route('/version', methods=['GET'])
def route_version():
    """获取版本信息"""
    return health_check(include_version=True)

# 注册错误处理器
@api_bp.errorhandler(400)
def bad_request(error):
    """400 错误处理"""
    return {
        'success': False,
        'error': 'Bad Request',
        'message': str(error.description)
    }, 400

@api_bp.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return {
        'success': False,
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }, 404

@api_bp.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    return {
        'success': False,
        'error': 'Internal Server Error',
        'message': 'An internal server error occurred'
    }, 500