# security.py
"""
安全检测与执行控制模块
"""
import logging
import os
import sys
import threading

from .db import (
    check_project_security,
    log_launch_to_db,
    has_host_changed,
    validate_identifiers
)
from .exceptions import SecurityViolationException
from .utils import (
    get_host_id,
    get_project_uuid,
    get_lock_file_path,
    should_log,
    create_lock_file,
    detect_framework,
    create_system_uuid_file,
    create_host_uuid_file
)

# 配置日志
logger = logging.getLogger("ProjectSecurityLogger")

# 锁文件有效期（小时）
LOCK_FILE_VALID_HOURS = 24


def block_application():
    """阻止应用程序继续运行并立即退出"""
    framework = detect_framework()
    os._exit(1)


def print_activation_prompt(project_uuid):
    """显示项目编号缺失提示"""
    print("\n" + "=" * 60)
    print(f"项目未配置有效的项目编号，请检查README.md文件")
    print("操作步骤：")
    print("1. 在项目根目录创建README.md文件")
    print("2. 文件中包含 '项目编号：XXXX' 格式的内容")
    print("3. XXXX 为项目的唯一编号")
    print("4. 保存文件后重新启动项目")
    print("=" * 60 + "\n")


def perform_security_check():
    """执行完整的安全检查和日志记录"""
    if os.getenv('PROJECT_SECURITY_DISABLED', '0') == '1':
        logger.warning("Security check is disabled")
        return

    # 使用线程锁防止重复执行
    init_lock = threading.Lock()

    with init_lock:
        if hasattr(sys, '_project_security_checked'):
            return
        sys._project_security_checked = True

        try:
            # 获取项目UUID和文件路径
            project_uuid, uuid_file_path = get_project_uuid()
            host_id = get_host_id()
            project_path = os.getcwd()

            # 创建系统唯一标识文件
            system_uuid_path, system_uuid_content = create_system_uuid_file(project_path)

            # 创建主机唯一标识文件
            host_uuid_path, host_uuid_content = create_host_uuid_file()

            # 记录日志到数据库
            log_success, is_activated, identifier_code, project_number_id = log_launch_to_db(
                host_id,
                project_uuid,
                project_path,
                uuid_file_path,
                system_uuid_path,
                system_uuid_content,
                host_uuid_path,
                host_uuid_content
            )

            # 验证标识文件
            if not validate_identifiers(host_id, project_uuid, project_path, system_uuid_path, host_uuid_path):
                print_activation_prompt(project_uuid)
                logger.error("Identifier validation failed!")
                block_application()
                return

            # 检查激活状态
            if not is_activated:
                print_activation_prompt(project_uuid)
                block_application()
                return

            # 执行安全检测
            security_check_result = check_project_security(host_id, project_uuid)

            if not security_check_result:
                block_application()
                return

            # 创建项目唯一锁文件名
            lock_file = get_lock_file_path(project_uuid, project_path)

            # 检查主机特征是否有变化
            host_changed = has_host_changed(host_id, project_uuid)

            # 是否需要记录日志
            should_log_condition = should_log(lock_file, LOCK_FILE_VALID_HOURS) or host_changed

            if should_log_condition:
                log_launch_to_db(
                    host_id,
                    project_uuid,
                    project_path,
                    uuid_file_path,
                    system_uuid_path,
                    system_uuid_content,
                    host_uuid_path,
                    host_uuid_content
                )

                if log_success:
                    create_lock_file(lock_file)

        except Exception as e:
            logger.error(f"Security check failed: {e}", exc_info=True)
            if os.getenv('PROJECT_SECURITY_STRICT', '0') == '1':
                sys.exit(1)