import os
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseSettings, Field, validator, PostgresDsn, EmailStr, HttpUrl, SecretStr


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseSettings(BaseSettings):
    """Database connection settings"""
    POSTGRES_SERVER: str = Field(..., env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    POSTGRES_PORT: str = Field("5432", env="POSTGRES_PORT")
    
    # Computed connection string
    DB_URI: Optional[str] = None
    
    @validator("DB_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class RedisSettings(BaseSettings):
    """Redis cache settings"""
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[SecretStr] = Field(None, env="REDIS_PASSWORD")
    REDIS_USE_SSL: bool = Field(False, env="REDIS_USE_SSL")
    
    # Cache configuration
    CACHE_TTL_DEFAULT: int = Field(300, env="CACHE_TTL_DEFAULT")  # 5 minutes
    CACHE_TTL_SHORT: int = Field(60, env="CACHE_TTL_SHORT")  # 1 minute
    CACHE_TTL_MEDIUM: int = Field(1800, env="CACHE_TTL_MEDIUM")  # 30 minutes
    CACHE_TTL_LONG: int = Field(86400, env="CACHE_TTL_LONG")  # 24 hours
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class EmailSettings(BaseSettings):
    """Email service settings"""
    SMTP_HOST: str = Field(..., env="SMTP_HOST")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    SMTP_USER: str = Field(..., env="SMTP_USER")
    SMTP_PASSWORD: SecretStr = Field(..., env="SMTP_PASSWORD")
    SMTP_TLS: bool = Field(True, env="SMTP_TLS")
    EMAIL_FROM: EmailStr = Field(..., env="EMAIL_FROM") 
    EMAIL_FROM_NAME: str = Field("Book Discovery Service", env="EMAIL_FROM_NAME")
    
    # Email sending frequency
    EMAIL_SEND_FREQUENCY: str = Field("weekly", env="EMAIL_SEND_FREQUENCY")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class LLMSettings(BaseSettings):
    """LLM service settings"""
    OPENAI_API_KEY: SecretStr = Field(..., env="OPENAI_API_KEY")
    OPENAI_ORG_ID: Optional[str] = Field(None, env="OPENAI_ORG_ID")
    DEFAULT_MODEL: str = Field("gpt-3.5-turbo", env="DEFAULT_MODEL")
    
    # RAG settings
    EMBEDDING_MODEL: str = Field("text-embedding-ada-002", env="EMBEDDING_MODEL")
    VECTOR_STORE_TYPE: str = Field("chroma", env="VECTOR_STORE_TYPE")
    VECTOR_STORE_PATH: str = Field("./vector_store", env="VECTOR_STORE_PATH")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class SearchSettings(BaseSettings):
    """Web search service settings"""
    SEARCH_ENGINE: str = Field("duckduckgo", env="SEARCH_ENGINE")
    GOOGLE_API_KEY: Optional[SecretStr] = Field(None, env="GOOGLE_API_KEY")
    GOOGLE_CSE_ID: Optional[str] = Field(None, env="GOOGLE_CSE_ID")
    SERPER_API_KEY: Optional[SecretStr] = Field(None, env="SERPER_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class SecuritySettings(BaseSettings):
    """Security and authentication settings"""
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS settings
    CORS_ORIGINS: List[str] = Field(["http://localhost:3000"], env="CORS_ORIGINS")
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class LoggingSettings(BaseSettings):
    """Logging configuration"""
    LOG_LEVEL: LogLevel = Field(LogLevel.INFO, env="LOG_LEVEL")
    LOG_TO_FILE: bool = Field(True, env="LOG_TO_FILE")
    LOG_DIR: str = Field("logs", env="LOG_DIR")
    JSON_LOGS: bool = Field(True, env="JSON_LOGS")
    REDACT_SENSITIVE_DATA: bool = Field(True, env="REDACT_SENSITIVE_DATA")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class AppSettings(BaseSettings):
    """Application-specific settings"""
    PROJECT_NAME: str = Field("Book Discovery Service", env="PROJECT_NAME")
    VERSION: str = Field("0.1.0", env="VERSION")
    ENVIRONMENT: EnvironmentType = Field(EnvironmentType.DEVELOPMENT, env="ENVIRONMENT")
    DEBUG: bool = Field(False, env="DEBUG")
    
    # API configuration
    API_V1_STR: str = Field("/api/v1", env="API_V1_STR")
    SERVER_HOST: str = Field("0.0.0.0", env="SERVER_HOST")
    SERVER_PORT: int = Field(8000, env="SERVER_PORT")
    
    # Service configuration
    MAX_RECOMMENDATIONS_PER_EMAIL: int = Field(5, env="MAX_RECOMMENDATIONS_PER_EMAIL")
    DEFAULT_SEARCH_LIMIT: int = Field(10, env="DEFAULT_SEARCH_LIMIT")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class Settings(BaseSettings):
    """Main settings container that includes all sub-settings"""
    app: AppSettings = AppSettings()
    db: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    email: EmailSettings = EmailSettings()
    llm: LLMSettings = LLMSettings()
    search: SearchSettings = SearchSettings()
    security: SecuritySettings = SecuritySettings()
    logging: LoggingSettings = LoggingSettings()
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Return settings instance for dependency injection"""
    return settings