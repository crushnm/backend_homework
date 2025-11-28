"""应用配置管理"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """应用配置"""

    # 数据库配置
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://contoso_user:password@localhost/contoso_expense",
    )

    # JWT配置
    secret_key: str = os.getenv(
        "SECRET_KEY", "your-secret-key-change-this-in-production-min-32-chars"
    )
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # 应用配置
    app_name: str = "Contoso Expense Tracker"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    # CORS配置
    cors_origins: list = [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
    ]

    # 分页配置
    default_page_size: int = 50
    max_page_size: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()
