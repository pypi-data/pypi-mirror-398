"""
自定义异常类
"""

class SecurityViolationException(Exception):
    """安全违规异常"""
    pass

class DatabaseConnectionException(Exception):
    """数据库连接异常"""
    pass