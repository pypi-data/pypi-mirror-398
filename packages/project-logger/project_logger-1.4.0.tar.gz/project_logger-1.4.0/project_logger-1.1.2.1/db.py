# db.py
"""
数据库接口模块 - 通过API调用替代直接数据库访问
注意：此模块已重构为API客户端模式，不再直接访问数据库
"""
import os
import logging
from .api_client import api_client
from .utils import get_host_info, read_file_content
from .exceptions import DatabaseConnectionException

# 配置日志
logger = logging.getLogger("ProjectSecurityLogger")

# 允许的最大主机数量
from .constants import MAX_ALLOWED_HOSTS


def initialize_db_pool():
    """
    初始化数据库连接池 - 已废弃
    注意：此函数已重构为API模式，不再需要数据库连接池
    """
    logger.info("Database connection pool initialization skipped - using API mode")
    return None


def get_db_connection():
    """
    获取数据库连接 - 已废弃
    注意：此函数已重构为API模式，不再直接连接数据库
    """
    logger.info("Database connection skipped - using API mode")
    return None


def check_project_security(host_id, project_uuid):
    """
    增强的安全策略：
    1. 检查项目是否已启动
    2. 如果项目未启动或当前主机是最早的两台设备之一，允许运行
    3. 否则阻止执行

    注意：此函数已重构为API调用模式
    """
    try:
        return api_client.check_project_security(host_id, project_uuid, MAX_ALLOWED_HOSTS)
    except Exception as e:
        logger.error(f"Security check API error: {e}", exc_info=True)
        # 安全检测失败时默认允许执行
        return True


def register_activation(host_id, system_uuid_content, project_number_id):
    """
    注册或更新项目激活关系
    注意：此函数已重构为API调用模式
    """
    try:
        return api_client.register_activation(host_id, system_uuid_content, project_number_id)
    except Exception as e:
        logger.error(f"激活注册API失败: {e}", exc_info=True)
        return False


def log_launch_to_db(host_id, project_uuid, project_path, uuid_file_path,
                     system_uuid_path, system_uuid_content,
                     host_uuid_path, host_uuid_content):
    """
    记录启动日志到数据库，优先更新相同主机ID和系统标识内容的记录
    注意：此函数已重构为API调用模式
    """
    try:
        # 获取主机信息
        host_info = get_host_info()

        return api_client.log_launch_to_db(
            host_id, project_uuid, project_path, uuid_file_path,
            system_uuid_path, system_uuid_content,
            host_uuid_path, host_uuid_content, host_info
        )
    except Exception as e:
        logger.error(f"日志记录API错误: {e}", exc_info=True)
        return False, 0, None, None


def parse_and_register_project_number(project_path):
    """
    解析并验证项目编号
    注意：此函数已重构为API调用模式
    """
    try:
        return api_client.parse_and_register_project_number(project_path)
    except Exception as e:
        logger.error(f"项目编号解析API错误: {e}", exc_info=True)
        return None, None, None


def validate_identifiers(host_id, project_uuid, current_project_path, system_uuid_path, host_uuid_path):
    """
    验证系统标识和主机标识是否匹配数据库记录
    注意：此函数已重构为API调用模式
    """
    try:
        # 读取本地文件内容
        system_uuid_content = read_file_content(system_uuid_path)
        host_uuid_content = read_file_content(host_uuid_path)

        return api_client.validate_identifiers(
            host_id, project_uuid, current_project_path,
            system_uuid_path, host_uuid_path,
            system_uuid_content, host_uuid_content
        )
    except Exception as e:
        logger.error(f"标识符验证API错误: {e}")
        return False


def check_activation_status(project_uuid):
    """
    检查项目是否已激活
    注意：此函数已重构为API调用模式
    """
    try:
        return api_client.check_activation_status(project_uuid)
    except Exception as e:
        logger.error(f"激活状态检查API错误: {e}")
        return False


def has_host_changed(host_id, project_uuid):
    """
    检查主机特征是否有变化：
    1. 项目首次运行：默认为有变化
    2. 数据库中不存在相同主机ID：有变化
    3. 存在相同主机ID但特征不同：有变化

    注意：此函数已重构为API调用模式
    """
    try:
        return api_client.has_host_changed(host_id, project_uuid)
    except Exception as e:
        logger.error(f"主机变化检查API错误: {e}")
        return True

