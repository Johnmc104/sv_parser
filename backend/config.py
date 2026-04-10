import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent

class Config:
    """基础配置类"""
    
    # Flask 配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/verilog_uploads')
    ALLOWED_EXTENSIONS = {'.v', '.sv', '.vh', '.svh'}
    
    # API 配置
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # CORS 配置
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000'
    ]
    
    # 解析器配置
    MAX_HIERARCHY_DEPTH = 20
    MAX_MODULES_PER_DESIGN = 1000
    ENABLE_CACHE = True
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', None)

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    
    # 开发环境特定配置
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:5173'  # Vite 默认端口
    ]

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    
    # 生产环境安全配置
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")
    
    # 生产环境 CORS 配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')

class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    
    # 测试数据库
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB for testing

# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env_name=None):
    """获取配置对象"""
    if env_name is None:
        env_name = os.getenv('FLASK_ENV', 'default')
    
    return config_map.get(env_name, DevelopmentConfig)