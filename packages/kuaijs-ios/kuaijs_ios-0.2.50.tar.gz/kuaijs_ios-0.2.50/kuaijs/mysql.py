from typing import Any, List, Dict, Optional, TypedDict


class MySQLConfig(TypedDict, total=False):
    """MySQL 连接配置"""

    host: str  # 主机名或 IP 地址
    port: Optional[int]  # 端口号（默认 3306）
    username: str  # 用户名
    password: str  # 密码
    database: str  # 数据库名
    charset: Optional[str]  # 字符集（默认 utf8mb4）


class MySQLResult(TypedDict):
    """MySQL 查询/执行结果"""

    rows: List[Dict[str, Any]]  # 查询结果行（字典列表）
    affectedRows: int  # 受影响的行数
    success: bool  # 是否成功执行
    insertId: Optional[int]  # 插入操作的自增 ID（如果有）
    error: Optional[str]  # 错误信息（如果有）


def connect(config: MySQLConfig) -> bool:
    """连接到数据库"""
    return True


def disconnect():
    """断开数据库连接"""
    pass


def isConnected() -> bool:
    """检查连接状态"""
    return False


def query(sql: str, params: List[Any] = []) -> MySQLResult:
    """执行查询（SELECT）"""
    return {
        "rows": [],
        "affectedRows": 0,
        "success": True,
        "insertId": None,
        "error": None,
    }


def execute(sql: str, params: List[Any] = []) -> MySQLResult:
    """执行更新（INSERT/UPDATE/DELETE）"""
    return {
        "rows": [],
        "affectedRows": 0,
        "success": True,
        "insertId": None,
        "error": None,
    }


def beginTransaction() -> bool:
    """开始事务"""
    return True


def commit() -> bool:
    """提交事务"""
    return True


def rollback() -> bool:
    """回滚事务"""
    return True
