import json
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Application
    APP_NAME : str = Field("Bus Ticket System API", env="APP_NAME")
    APP_VERSION : str = Field("1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(True, env="DEBUG")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    
    # Redis
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    # Celery
    CELERY_BROKER_URL: str = Field("redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field("redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    # Email
    SMTP_HOST: str = Field(..., env="SMTP_HOST")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    SMTP_USER: str = Field(..., env="SMTP_USER")
    SMTP_PASSWORD: str = Field(..., env="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = Field(..., env="SMTP_FROM_EMAIL")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    
    # CORS
    ALLOWED_ORIGINS: str = Field(
        "http://localhost:3000,http://localhost:8000,http://localhost:5173",
        env="ALLOWED_ORIGINS",
    )
    
    # Sentry
    SENTRY_DSN: str = Field("", env="SENTRY_DSN")
    
    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field("app.log", env="LOG_FILE")
    
    @property
    def allowed_origins(self) -> List[str]:
        value = self.ALLOWED_ORIGINS.strip()
        if value.startswith("["):
            return json.loads(value)
        return [origin.strip() for origin in value.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

    
    
    
