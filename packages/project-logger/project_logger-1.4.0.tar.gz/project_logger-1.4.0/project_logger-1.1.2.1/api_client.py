# project_logger-1.1.2.1/api_client.py
"""
API客户端模块 - 用于与project_logger_api服务通信
"""
import os
import json
import time
import hmac
import hashlib
import logging
import requests
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# 修复相对导入问题
try:
    from .exceptions import DatabaseConnectionException
except ImportError:
    from exceptions import DatabaseConnectionException

# 加载配置文件
try:
    from .config_template import load_config
    load_config()
except ImportError:
    try:
        from config_template import load_config
        load_config()
    except ImportError:
        # 手动加载.env文件作为备选方案
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()

logger = logging.getLogger("ProjectSecurityLogger")


class APIClient:
    """API客户端"""
    
    def __init__(self):
        # API服务配置
        self.base_url = os.getenv('API_BASE_URL', 'http://127.0.0.1:5000/api/v1')
        self.api_key = os.getenv('API_KEY', 'your-api-key-here')
        self.hmac_secret = os.getenv('HMAC_SECRET', 'your-hmac-secret-here')
        self.client_id = os.getenv('API_CLIENT_ID', 'project_logger_client')
        
        # 请求配置
        self.timeout = int(os.getenv('API_TIMEOUT', '30'))
        self.max_retries = int(os.getenv('API_MAX_RETRIES', '3'))
        
        # 缓存的访问令牌
        self._access_token = None
        self._token_expires_at = 0
        
        # 会话对象
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
            'User-Agent': 'ProjectLogger/1.1.2.1'
        })
    
    def _generate_hmac_signature(self, data: str, timestamp: str) -> str:
        """生成HMAC签名"""
        message = f"{data}:{timestamp}"
        signature = hmac.new(
            self.hmac_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_access_token(self) -> str:
        """获取访问令牌"""
        current_time = time.time()
        
        # 如果令牌未过期，直接返回
        if self._access_token and current_time < self._token_expires_at:
            return self._access_token
        
        # 请求新令牌
        try:
            response = self.session.post(
                f"{self.base_url}/auth/token",
                json={'client_id': self.client_id},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            if data['success']:
                token_data = data['data']
                self._access_token = token_data['access_token']
                # 提前5分钟过期，避免边界情况
                self._token_expires_at = current_time + token_data['expires_in'] - 300
                return self._access_token
            else:
                raise Exception(f"Token request failed: {data.get('error', {}).get('message', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise DatabaseConnectionException(f"API authentication failed: {e}")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发起API请求"""
        url = f"{self.base_url}{endpoint}"

        # 获取访问令牌
        access_token = self._get_access_token()

        # 准备请求数据
        if data is None:
            data = {}

        # 生成与服务端一致的JSON字符串
        json_data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        timestamp = str(int(time.time()))
        signature = self._generate_hmac_signature(json_data, timestamp)

        # 设置请求头
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Signature': signature,
            'X-Timestamp': timestamp,
            'Content-Type': 'application/json; charset=utf-8'
        }
        
        # 发起请求，支持重试
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, headers=headers, timeout=self.timeout)
                else:
                    # 使用UTF-8编码发送JSON数据
                    response = self.session.post(
                        url,
                        data=json_data.encode('utf-8'),
                        headers=headers,
                        timeout=self.timeout
                    )
                
                response.raise_for_status()
                result = response.json()
                
                if result['success']:
                    return result['data']
                else:
                    error_info = result.get('error', {})
                    raise Exception(f"API error: {error_info.get('message', 'Unknown error')}")
                    
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.warning(f"API request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API request failed after {self.max_retries} attempts: {e}")
            except Exception as e:
                logger.error(f"API request error: {e}")
                raise DatabaseConnectionException(f"API request failed: {e}")
        
        # 所有重试都失败
        raise DatabaseConnectionException(f"API request failed after {self.max_retries} attempts: {last_exception}")
    
    def check_project_security(self, host_id: str, project_uuid: str, max_allowed_hosts: int = 1) -> bool:
        """检查项目安全性"""
        try:
            data = {
                'host_id': host_id,
                'project_uuid': project_uuid,
                'max_allowed_hosts': max_allowed_hosts
            }
            result = self._make_request('POST', '/security/check', data)
            return result.get('allowed', False)
        except Exception as e:
            logger.error(f"Security check API error: {e}")
            # 安全检测失败时默认允许执行
            return True
    
    def has_host_changed(self, host_id: str, project_uuid: str) -> bool:
        """检查主机是否发生变化"""
        try:
            data = {
                'host_id': host_id,
                'project_uuid': project_uuid
            }
            result = self._make_request('POST', '/security/host-changed', data)
            return result.get('changed', True)
        except Exception as e:
            logger.error(f"Host change check API error: {e}")
            return True
    
    def check_activation_status(self, project_uuid: str) -> bool:
        """检查项目激活状态"""
        try:
            data = {'project_uuid': project_uuid}
            result = self._make_request('POST', '/activation/status', data)
            return result.get('activated', False)
        except Exception as e:
            logger.error(f"Activation status check API error: {e}")
            return False
    
    def validate_identifiers(self, host_id: str, project_uuid: str, current_project_path: str,
                           system_uuid_path: str, host_uuid_path: str,
                           system_uuid_content: str, host_uuid_content: str) -> bool:
        """验证标识符"""
        try:
            data = {
                'host_id': host_id,
                'project_uuid': project_uuid,
                'current_project_path': current_project_path,
                'system_uuid_path': system_uuid_path,
                'host_uuid_path': host_uuid_path,
                'system_uuid_content': system_uuid_content,
                'host_uuid_content': host_uuid_content
            }
            result = self._make_request('POST', '/identifiers/validate', data)
            return result.get('valid', False)
        except Exception as e:
            logger.error(f"Identifier validation API error: {e}")
            return False
    
    def register_activation(self, host_id: str, system_uuid_content: str, project_number_id: int) -> bool:
        """注册项目激活"""
        try:
            data = {
                'host_id': host_id,
                'system_uuid_content': system_uuid_content,
                'project_number_id': project_number_id
            }
            result = self._make_request('POST', '/activation/register', data)
            return result.get('registered', False)
        except Exception as e:
            logger.error(f"Activation registration API error: {e}")
            return False
    
    def parse_and_register_project_number(self, project_path: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """解析并注册项目编号"""
        try:
            data = {'project_path': project_path}
            result = self._make_request('POST', '/project/parse-number', data)
            return (
                result.get('project_number'),
                result.get('identifier_code'),
                result.get('project_number_id')
            )
        except Exception as e:
            logger.error(f"Project number parsing API error: {e}")
            return None, None, None
    
    def log_launch_to_db(self, host_id: str, project_uuid: str, project_path: str, uuid_file_path: str,
                         system_uuid_path: str, system_uuid_content: str,
                         host_uuid_path: str, host_uuid_content: str, host_info: Dict[str, str]) -> Tuple[bool, int, Optional[str], Optional[int]]:
        """记录启动日志"""
        try:
            data = {
                'host_id': host_id,
                'project_uuid': project_uuid,
                'project_path': project_path,
                'uuid_file_path': uuid_file_path,
                'system_uuid_path': system_uuid_path,
                'system_uuid_content': system_uuid_content,
                'host_uuid_path': host_uuid_path,
                'host_uuid_content': host_uuid_content,
                'host_info': host_info
            }
            result = self._make_request('POST', '/logs/launch', data)
            return (
                result.get('logged', False),
                result.get('is_activated', 0),
                result.get('identifier_code'),
                result.get('project_number_id')
            )
        except Exception as e:
            logger.error(f"Launch log API error: {e}")
            return False, 0, None, None


# 全局API客户端实例
api_client = APIClient()
