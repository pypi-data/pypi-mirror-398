# project_logger-1.1.2.1/config_template.py
"""
配置文件模板和自动生成工具
"""
import os
from pathlib import Path

# 默认配置模板
DEFAULT_CONFIG = """# Project Logger 客户端配置
# 自动生成的配置文件

# API服务连接配置
API_BASE_URL=http://127.0.0.1:5000/api/v1
API_KEY=test-api-key-12345
HMAC_SECRET=test-hmac-secret-67890
API_CLIENT_ID=project_logger_client

# API请求配置
API_TIMEOUT=30
API_MAX_RETRIES=3

# 项目安全配置
PROJECT_SECURITY_DISABLED=0
PROJECT_SECURITY_STRICT=0
"""

def create_config_file(config_path=None):
    """创建配置文件"""
    if config_path is None:
        config_path = Path(__file__).parent / '.env'
    
    # 如果配置文件已存在，不覆盖
    if config_path.exists():
        print(f"配置文件已存在: {config_path}")
        return config_path
    
    # 创建配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(DEFAULT_CONFIG)
    
    print(f"已创建配置文件: {config_path}")
    return config_path

def load_config():
    """加载配置文件，如果不存在则创建"""
    config_path = Path(__file__).parent / '.env'
    
    if not config_path.exists():
        create_config_file(config_path)
    
    # 加载环境变量
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

if __name__ == '__main__':
    create_config_file()
