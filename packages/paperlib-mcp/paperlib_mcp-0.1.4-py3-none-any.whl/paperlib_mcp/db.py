"""PostgreSQL 数据库封装"""

from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row

from paperlib_mcp.settings import get_settings


def get_connection() -> psycopg.Connection:
    """获取数据库连接"""
    settings = get_settings()
    return psycopg.connect(settings.pg_dsn, row_factory=dict_row)


@contextmanager
def get_db():
    """数据库连接上下文管理器"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_one(sql: str, params: tuple | dict | None = None) -> dict[str, Any] | None:
    """查询单条记录
    
    Args:
        sql: SQL 查询语句
        params: 查询参数（元组或字典）
        
    Returns:
        单条记录的字典，如果没有结果则返回 None
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def query_all(sql: str, params: tuple | dict | None = None) -> list[dict[str, Any]]:
    """查询多条记录
    
    Args:
        sql: SQL 查询语句
        params: 查询参数（元组或字典）
        
    Returns:
        记录列表，每条记录为字典
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def execute(sql: str, params: tuple | dict | None = None) -> int:
    """执行 SQL 语句（INSERT/UPDATE/DELETE）
    
    Args:
        sql: SQL 语句
        params: 查询参数（元组或字典）
        
    Returns:
        受影响的行数
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount


def execute_returning(sql: str, params: tuple | dict | None = None) -> dict[str, Any] | None:
    """执行 SQL 语句并返回结果（用于 INSERT ... RETURNING）
    
    Args:
        sql: SQL 语句（应包含 RETURNING 子句）
        params: 查询参数（元组或字典）
        
    Returns:
        返回的记录字典，如果没有结果则返回 None
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def execute_many_returning(sql: str, params_list: list[tuple | dict]) -> list[dict[str, Any]]:
    """批量执行 SQL 语句并返回所有结果
    
    Args:
        sql: SQL 语句（应包含 RETURNING 子句）
        params_list: 参数列表
        
    Returns:
        返回的记录列表
    """
    results = []
    with get_db() as conn:
        with conn.cursor() as cur:
            for params in params_list:
                cur.execute(sql, params)
                row = cur.fetchone()
                if row:
                    results.append(row)
    return results


def check_connection() -> dict[str, Any]:
    """检查数据库连接状态
    
    Returns:
        连接状态信息，包括：
        - connected: 是否连接成功
        - extensions: 已安装的扩展列表
        - error: 错误信息（如果连接失败）
    """
    try:
        # 测试基本连接
        result = query_one("SELECT 1 as test")
        if not result or result.get("test") != 1:
            return {"connected": False, "error": "Connection test failed"}
        
        # 检查必要的扩展
        extensions = query_all(
            "SELECT extname FROM pg_extension WHERE extname IN ('vector')"
        )
        ext_names = [ext["extname"] for ext in extensions]
        
        return {
            "connected": True,
            "extensions": ext_names,
            "vector_enabled": "vector" in ext_names,
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}
