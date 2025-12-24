"""MinIO/S3 客户端封装"""

from pathlib import Path
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from paperlib_mcp.settings import get_settings


def get_s3_client():
    """获取 S3 客户端（兼容 MinIO）"""
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",  # MinIO 需要一个 region
    )


def upload_file(file_path: str | Path, key: str, bucket: str | None = None) -> dict[str, Any]:
    """上传文件到 S3/MinIO
    
    Args:
        file_path: 本地文件路径
        key: S3 对象键（路径）
        bucket: 存储桶名称，默认使用配置中的 bucket
        
    Returns:
        上传结果信息
    """
    settings = get_settings()
    bucket = bucket or settings.s3_bucket
    client = get_s3_client()
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    client.upload_file(str(file_path), bucket, key)
    
    return {
        "bucket": bucket,
        "key": key,
        "size": file_path.stat().st_size,
    }


def head_object(key: str, bucket: str | None = None) -> dict[str, Any] | None:
    """检查对象是否存在并获取元数据
    
    Args:
        key: S3 对象键
        bucket: 存储桶名称
        
    Returns:
        对象元数据，如果不存在则返回 None
    """
    settings = get_settings()
    bucket = bucket or settings.s3_bucket
    client = get_s3_client()
    
    try:
        response = client.head_object(Bucket=bucket, Key=key)
        return {
            "exists": True,
            "size": response.get("ContentLength"),
            "last_modified": response.get("LastModified"),
            "content_type": response.get("ContentType"),
            "etag": response.get("ETag"),
        }
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return None
        raise


def get_object(key: str, bucket: str | None = None) -> bytes:
    """获取对象内容
    
    Args:
        key: S3 对象键
        bucket: 存储桶名称
        
    Returns:
        对象内容（字节）
    """
    settings = get_settings()
    bucket = bucket or settings.s3_bucket
    client = get_s3_client()
    
    response = client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


def object_exists(key: str, bucket: str | None = None) -> bool:
    """检查对象是否存在
    
    Args:
        key: S3 对象键
        bucket: 存储桶名称
        
    Returns:
        True 如果对象存在
    """
    return head_object(key, bucket) is not None


def delete_object(key: str, bucket: str | None = None) -> dict[str, Any]:
    """删除 S3/MinIO 对象
    
    Args:
        key: S3 对象键
        bucket: 存储桶名称
        
    Returns:
        删除结果信息
    """
    settings = get_settings()
    bucket = bucket or settings.s3_bucket
    client = get_s3_client()
    
    try:
        # 先检查对象是否存在
        if not object_exists(key, bucket):
            return {
                "deleted": False,
                "bucket": bucket,
                "key": key,
                "reason": "Object does not exist",
            }
        
        client.delete_object(Bucket=bucket, Key=key)
        return {
            "deleted": True,
            "bucket": bucket,
            "key": key,
        }
    except ClientError as e:
        return {
            "deleted": False,
            "bucket": bucket,
            "key": key,
            "error": str(e),
        }


def check_bucket() -> dict[str, Any]:
    """检查存储桶状态
    
    Returns:
        存储桶状态信息
    """
    settings = get_settings()
    client = get_s3_client()
    
    try:
        # 尝试列出少量对象来验证 bucket 存在且可访问
        response = client.list_objects_v2(
            Bucket=settings.s3_bucket,
            MaxKeys=1
        )
        return {
            "accessible": True,
            "bucket": settings.s3_bucket,
            "endpoint": settings.s3_endpoint,
        }
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        return {
            "accessible": False,
            "bucket": settings.s3_bucket,
            "endpoint": settings.s3_endpoint,
            "error": f"{error_code}: {e.response['Error']['Message']}",
        }
    except Exception as e:
        return {
            "accessible": False,
            "bucket": settings.s3_bucket,
            "endpoint": settings.s3_endpoint,
            "error": str(e),
        }
