from flask import Flask, jsonify
from flask_cors import CORS
import os
from datetime import datetime

# 导入 API 蓝图
from api.routes import api_bp

def create_app(config=None):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 配置 CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:8080", "http://127.0.0.1:8080"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 基本配置
    app.config.update({
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB 最大文件大小
        'UPLOAD_FOLDER': '/tmp/verilog_uploads',
        'JSON_SORT_KEYS': False,
        'JSONIFY_PRETTYPRINT_REGULAR': True
    })
    
    # 应用自定义配置
    if config:
        app.config.update(config)
    
    # 注册 API 蓝图
    app.register_blueprint(api_bp)
    
    # 注册全局错误处理器
    register_error_handlers(app)
    
    # 注册中间件
    register_middleware(app)
    
    return app

def register_error_handlers(app):
    """注册全局错误处理器"""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'The requested endpoint was not found',
            'timestamp': datetime.now().isoformat()
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 'Method Not Allowed',
            'message': 'The request method is not allowed for this endpoint',
            'timestamp': datetime.now().isoformat()
        }), 405
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            'success': False,
            'error': 'File Too Large',
            'message': 'The uploaded file is too large (max 16MB)',
            'timestamp': datetime.now().isoformat()
        }), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'timestamp': datetime.now().isoformat()
        }), 500

def register_middleware(app):
    """注册中间件"""
    
    @app.before_request
    def before_request():
        """请求前处理"""
        # 这里可以添加日志记录、认证等
        pass
    
    @app.after_request
    def after_request(response):
        """请求后处理"""
        # 添加响应头
        response.headers['X-API-Version'] = '1.0.0'
        response.headers['X-Timestamp'] = datetime.now().isoformat()
        return response

# 创建应用实例
app = create_app()

# 根路径
@app.route('/')
def index():
    """API 根路径"""
    return jsonify({
        'name': 'Verilog Parser API',
        'version': '1.0.0',
        'description': 'Backend API for Verilog file parsing and visualization',
        'endpoints': {
            'health': '/api/health',
            'parse': '/api/parse-verilog',
            'design': '/api/design',
            'modules': '/api/modules',
            'hierarchy': '/api/hierarchy',
            'flow_data': '/api/flow-data'
        },
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # 开发环境配置
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    port = 8080  # 默认端口
    host = os.getenv('HOST', '0.0.0.0')
    
    print(f"Starting Verilog Parser API...")
    print(f"Debug mode: {debug_mode}")
    print(f"Server: http://{host}:{port}")
    print(f"API endpoints: http://{host}:{port}/api/")
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        threaded=True
    )