from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://reportchecker:reportchecker_dev@localhost:5432/reportchecker"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO / S3
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "reports"
    minio_secure: bool = False

    # Anthropic
    anthropic_api_key: str = ""

    # Auth
    jwt_secret: str = "change-me-in-production"
    app_url: str = "http://localhost:3000"

    # SMTP (magic link e-post)
    smtp_host: str = "smtp.sendgrid.net"
    smtp_port: int = 587
    smtp_user: str = ""        # Tom = ingen e-post, link printes i logg
    smtp_password: str = ""
    smtp_from: str = "noreply@example.com"

    # CORS
    allowed_origins: str = "http://localhost:3000"

    # App
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
