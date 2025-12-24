"""健康检查工具"""

from typing import Any

from fastmcp import FastMCP

from paperlib_mcp.db import check_connection
from paperlib_mcp.storage import check_bucket


def register_health_tools(mcp: FastMCP) -> None:
    """注册健康检查工具"""

    @mcp.tool()
    def health_check() -> dict[str, Any]:
        """检查系统健康状态
        
        验证数据库连接、S3/MinIO 存储桶访问以及必要的数据库扩展是否正常。
        
        Returns:
            健康状态信息，包含：
            - ok: 整体状态是否正常
            - db: 数据库连接状态
            - s3: S3/MinIO 存储状态
        """
        # 检查数据库
        db_status = check_connection()
        
        # 检查 S3
        s3_status = check_bucket()
        
        # 综合判断
        ok = (
            db_status.get("connected", False) 
            and db_status.get("vector_enabled", False)
            and s3_status.get("accessible", False)
        )
        
        return {
            "ok": ok,
            "db": db_status,
            "s3": s3_status,
        }
