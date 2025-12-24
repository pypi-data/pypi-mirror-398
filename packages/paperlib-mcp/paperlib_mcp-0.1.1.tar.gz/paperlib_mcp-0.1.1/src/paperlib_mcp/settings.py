"""Pydantic Settings 配置管理"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从环境变量和 .env 文件读取"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PostgreSQL 配置
    postgres_user: str = "paper"
    postgres_password: str = "paper"
    postgres_db: str = "paperlib"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def pg_dsn(self) -> str:
        """构建 PostgreSQL DSN 连接字符串"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # MinIO/S3 配置
    minio_root_user: str = "minio"
    minio_root_password: str = "minio123"
    minio_bucket: str = "papers"
    s3_endpoint: str = "http://localhost:9000"

    @property
    def s3_access_key(self) -> str:
        """S3 访问密钥（使用 MinIO root user）"""
        return self.minio_root_user

    @property
    def s3_secret_key(self) -> str:
        """S3 密钥（使用 MinIO root password）"""
        return self.minio_root_password

    @property
    def s3_bucket(self) -> str:
        """S3 存储桶名称"""
        return self.minio_bucket

    # OpenRouter 配置
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    embedding_model: str = "openai/text-embedding-3-small"
    
    # LLM 模型配置
    llm_model: str = "openai/gpt-5-nano"  # 通用模型（图谱抽取等）
    llm_summarize_model: str = ""  # 社区摘要专用模型，留空则使用 llm_model

    # Embedding 批处理配置
    embedding_batch_size: int = 64


@lru_cache
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()
