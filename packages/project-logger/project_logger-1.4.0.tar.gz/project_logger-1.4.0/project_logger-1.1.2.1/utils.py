# utils.py
"""
实用工具函数
"""
import os
import sys
import hashlib
import socket
import getpass
import uuid
import time
import platform
import subprocess
import logging
import stat
import re
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProjectSecurityLogger")

# 常量配置
UUID_FILE = ".project_uuid"
PENDING_UUID_FILE = ".pending_uuid"
LOCK_FILE_PREFIX = ".project_lock_"
HOST_IDENTIFIER_PREFIX = "host_identifier_"
SYSTEM_IDENTIFIER_DIR = "security"
SYSTEM_IDENTIFIER_FILE = "system_identifier.js"
HOST_IDENTIFIER_DIR = "~/.project_security"
HOST_IDENTIFIER_FILE = "host_identifier.dat"

LOCK_FILE_VALID_HOURS = 24


def parse_project_number_from_readme(project_path):
    """从README.md解析项目编号和名称"""
    readme_path = Path(project_path) / "README.md"
    if not readme_path.exists():
        return None, None

    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()

        pattern = r'项目编号\s*[:：]\s*(\w+)'
        match = re.search(pattern, content)
        if match:
            project_number = match.group(1)
            name_pattern = r'项目名称\s*[:：]\s*([^\n]+)'
            name_match = re.search(name_pattern, content)
            project_name = name_match.group(1) if name_match else "Unnamed Project"
            return project_number, project_name
    except Exception as e:
        logger.error(f"Error parsing README.md: {e}")
    return None, None


def generate_identifier_code(project_number, project_path):
    """生成项目标识符代码（项目编号+主机信息+项目路径的哈希）"""
    host_info = get_host_info()
    combined = f"{project_number}-{host_info['hostname']}-{host_info['mac_address']}-{project_path}"
    return hashlib.sha256(combined.encode()).hexdigest()


def set_file_hidden(file_path):
    """将文件属性设置为隐藏"""
    try:
        if platform.system() == "Windows":
            import ctypes
            FILE_ATTRIBUTE_SYSTEM = 0x04
            FILE_ATTRIBUTE_HIDDEN = 0x02
            attributes = FILE_ATTRIBUTE_SYSTEM | FILE_ATTRIBUTE_HIDDEN
            ctypes.windll.kernel32.SetFileAttributesW(file_path, attributes)
            return True

        file = Path(file_path)
        file.chmod(stat.S_IRUSR | stat.S_IWUSR)
        return True
    except Exception as e:
        logger.error(f"Failed to set hidden attribute: {e}")
        return False


def get_project_parent_dir():
    """获取项目父目录"""
    project_dir = Path.cwd()
    for depth in range(3):
        parent_candidate = project_dir.parent
        if depth > 0:
            if (parent_candidate / ".git").exists() or (parent_candidate / ".vscode").exists():
                return parent_candidate
        project_dir = parent_candidate
    return Path.cwd().parent


def generate_host_based_id():
    """基于主机特征生成固定ID"""
    hostname = socket.gethostname()
    mac = get_mac_address()
    cpu_id = get_cpu_id()
    timestamp = str(time.time_ns())
    unique_str = f"{hostname}-{mac}-{cpu_id}-{timestamp}"
    return hashlib.sha256(unique_str.encode()).hexdigest()


def get_mac_address():
    """获取MAC地址"""
    try:
        return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                         for elements in range(0, 8 * 6, 8)][::-1])
    except:
        return str(uuid.getnode())


def ensure_project_uuid():
    """
    确保项目UUID存在
    """
    parent_dir = get_project_parent_dir()
    uuid_file = parent_dir / UUID_FILE
    pending_uuid_file = parent_dir / PENDING_UUID_FILE

    # 检查正式UUID文件
    if uuid_file.exists():
        try:
            with open(uuid_file, 'r') as f:
                project_uuid = f.read().strip()
                if len(project_uuid) == 64:
                    return project_uuid, str(uuid_file.resolve())
        except Exception as e:
            logger.error(f"Error reading UUID file: {e}")

    # 检查临时UUID文件
    if pending_uuid_file.exists():
        try:
            with open(pending_uuid_file, 'r') as f:
                project_uuid = f.read().strip()
                if len(project_uuid) == 64:
                    return project_uuid, None
        except Exception as e:
            logger.error(f"Error reading pending UUID file: {e}")

    # 生成新的UUID
    project_uuid = generate_host_based_id()
    try:
        parent_dir.mkdir(parents=True, exist_ok=True)
        with open(pending_uuid_file, 'w') as f:
            f.write(project_uuid)
        set_file_hidden(str(pending_uuid_file))
        return project_uuid, None
    except Exception as e:
        logger.error(f"Failed to create pending UUID")
        return project_uuid, None


def get_host_id():
    """生成基于主机特征的唯一ID"""
    hostname = socket.gethostname()
    username = getpass.getuser()
    mac = get_mac_address()
    cpu_id = get_cpu_id()
    unique_str = f"{hostname}-{username}-{mac}-{cpu_id}"
    return hashlib.sha256(unique_str.encode()).hexdigest()


def get_cpu_id():
    """获取CPU ID"""
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(
                'wmic cpu get ProcessorId',
                shell=True,
                stderr=subprocess.DEVNULL,
                text=True
            )
            lines = [line.strip() for line in result.split('\n') if line.strip()]
            return lines[1] if len(lines) > 1 else "unknown"

        elif platform.system() == "Darwin":
            return subprocess.check_output(
                "sysctl -n machdep.cpu.brand_string",
                shell=True,
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()

        elif platform.system() == "Linux":
            result = subprocess.check_output(
                "cat /proc/cpuinfo | grep 'serial' | awk '{print \\\\$3}'",
                shell=True,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return result.split()[0] if result.strip() else "unknown"

    except Exception as e:
        return "unknown"
    return "unsupported_os"


def get_project_uuid():
    """获取项目UUID"""
    return ensure_project_uuid()


def get_lock_file_path(project_uuid, project_path):
    """
    生成唯一的锁文件路径
    """
    parent_dir = get_project_parent_dir()
    combined = f"{project_uuid}_{project_path}"
    hash_id = hashlib.sha256(combined.encode()).hexdigest()
    lock_file_name = f"{LOCK_FILE_PREFIX}{hash_id[:16]}.lock"
    return str(parent_dir / lock_file_name)


def should_log(lock_file, valid_hours=LOCK_FILE_VALID_HOURS):
    """
    检查是否需要记录日志
    """
    lock_path = Path(lock_file)
    if not lock_path.exists():
        return True

    try:
        mod_time = lock_path.stat().st_mtime
        current_time = time.time()
        hours_diff = (current_time - mod_time) / 3600
        return hours_diff > valid_hours
    except Exception as e:
        logger.error(f"Error checking lock file: {e}")
        return True


def create_lock_file(lock_file):
    """创建或更新锁文件"""
    try:
        lock_path = Path(lock_file)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_file, 'w') as f:
            f.write(str(time.time()))
        set_file_hidden(lock_file)
        return True
    except Exception as e:
        return False


def detect_framework():
    """检测框架类型"""
    frameworks = {
        "django": "django",
        "flask": "flask",
        "fastapi": "fastapi",
        "pyramid": "pyramid",
        "tornado": "tornado",
        "bottle": "bottle",
        "cherrypy": "cherrypy",
        "sanic": "sanic"
    }

    # 检查已加载的模块
    for module_name in frameworks:
        if module_name in sys.modules:
            return frameworks[module_name]

    # 检查安装的包
    try:
        import pkg_resources
        installed_packages = [pkg.key for pkg in pkg_resources.working_set]
        for pkg_name in frameworks.values():
            if pkg_name in installed_packages:
                return pkg_name
    except:
        pass

    return "unknown"


def get_host_info():
    """收集主机信息"""
    try:
        cpu_id = get_cpu_id()
        mac = get_mac_address()
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        os_info = f"{platform.system()} {platform.release()} {platform.version()}"
        return {
            "hostname": socket.gethostname(),
            "username": getpass.getuser(),
            "mac_address": mac,
            "cpu_id": cpu_id,
            "python_version": python_version,
            "project_path": str(Path.cwd()),
            "os_info": os_info
        }
    except Exception as e:
        logger.error(f"Failed to get host info: {e}")
        return {
            "hostname": "unknown",
            "username": "unknown",
            "mac_address": "unknown",
            "cpu_id": "unknown",
            "python_version": "unknown",
            "project_path": "unknown",
            "os_info": "unknown"
        }


def create_system_uuid_file(project_path, existing_path=None):
    """
    在项目最深目录创建系统唯一标识文件
    """
    if existing_path and Path(existing_path).exists():
        try:
            content = read_file_content(existing_path)
            if content:
                return existing_path, content
        except Exception as e:
            logger.warning(f"Failed to reuse system identifier: {e}")

    deepest_dir = find_deepest_directory(project_path)
    identifier_file = deepest_dir / SYSTEM_IDENTIFIER_FILE

    if identifier_file.exists():
        content = read_file_content(str(identifier_file))
        return str(identifier_file.resolve()), content

    # 生成随机内容
    content = generate_encrypted_string()
    try:
        with open(identifier_file, 'w') as f:
            f.write(content)
        set_file_hidden(str(identifier_file))
    except Exception as e:
        logger.error(f"Failed to create system identifier: {e}")

    relative_path = os.path.relpath(str(identifier_file.resolve()), project_path)
    return relative_path, content


def create_host_uuid_file(project_uuid=None, existing_path=None):
    """
    创建用户主机唯一标识文件
    """
    if existing_path and Path(existing_path).exists():
        try:
            content = read_file_content(existing_path)
            if content:
                return existing_path, content
        except Exception as e:
            logger.warning(f"Failed to reuse host identifier: {e}")

    host_dir = Path(HOST_IDENTIFIER_DIR).expanduser()
    host_dir.mkdir(exist_ok=True, parents=True)
    random_suffix = str(uuid.uuid4())[:8]
    file_name = f"{HOST_IDENTIFIER_PREFIX}{random_suffix}.dat"
    identifier_file = host_dir / file_name

    if identifier_file.exists():
        content = read_file_content(str(identifier_file))
        return str(identifier_file.resolve()), content

    if project_uuid:
        content = hashlib.sha256(project_uuid.encode()).hexdigest()
    else:
        content = generate_encrypted_string()

    try:
        with open(identifier_file, 'w') as f:
            f.write(content)
        set_file_hidden(str(identifier_file))
    except Exception as e:
        logger.error(f"Failed to create host identifier: {e}")

    return str(identifier_file.resolve()), content


def find_deepest_directory(start_path):
    """
    查找项目中最深的目录
    """
    start_path = Path(start_path)
    deepest_dir = start_path
    max_depth = 0
    exclude_patterns = [SYSTEM_IDENTIFIER_DIR, "env", "venv", "__pycache__", "node_modules", ".idea"]

    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if d not in exclude_patterns]
        current_depth = len(Path(root).parts) - len(start_path.parts)
        if current_depth > max_depth:
            max_depth = current_depth
            deepest_dir = Path(root)

    return deepest_dir


def generate_encrypted_string(length=128):
    """生成随机加密字符串"""
    import string
    import random
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))


def read_file_content(file_path):
    """读取文件内容"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return f.read()
        return ""
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return ""