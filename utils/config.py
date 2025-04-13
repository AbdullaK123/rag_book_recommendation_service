import os
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import Field, PostgresDsn, EmailStr, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    
    POSTGRES_SERVER: str = Field("localhost", env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field("postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("postgres", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field("rag_db", env="POSTGRES_DB")
    POSTGRES_PORT: str = Field("5432", env="POSTGRES_PORT")
    
    # Computed connection string
    DB_URI: Optional[str] = None
    
    @model_validator(mode='after')
    def assemble_db_connection(self) -> 'DatabaseSettings':
        if not self.DB_URI:
            self.DB_URI = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return self


class RedisSettings(BaseSettings):
    """Redis cache settings"""
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    REDIS_USE_SSL: bool = Field(False, env="REDIS_USE_SSL")
    
    # Cache configuration
    CACHE_TTL_DEFAULT: int = Field(300, env="CACHE_TTL_DEFAULT")  # 5 minutes
    CACHE_TTL_SHORT: int = Field(60, env="CACHE_TTL_SHORT")  # 1 minute
    CACHE_TTL_MEDIUM: int = Field(1800, env="CACHE_TTL_MEDIUM")  # 30 minutes
    CACHE_TTL_LONG: int = Field(86400, env="CACHE_TTL_LONG")  # 24 hours


class EmailSettings(BaseSettings):
    """Email service settings"""
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    
    SMTP_HOST: str = Field("smtp.example.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    SMTP_USER: str = Field("user@example.com", env="SMTP_USER")
    SMTP_PASSWORD: str = Field("password", env="SMTP_PASSWORD")
    SMTP_TLS: bool = Field(True, env="SMTP_TLS")
    EMAIL_FROM: str = Field("noreply@example.com", env="EMAIL_FROM") 
    EMAIL_FROM_NAME: str = Field("Book Discovery Service", env="EMAIL_FROM_NAME")
    
    # Email sending frequency
    EMAIL_SEND_FREQUENCY: str = Field("weekly", env="EMAIL_SEND_FREQUENCY")


class LLMSettings(BaseSettings):
    """LLM service settings"""
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    
    OPENAI_API_KEY: str = Field("", env="OPENAI_API_KEY")
    OPENAI_ORG_ID: Optional[str] = Field(None, env="OPENAI_ORG_ID")
    DEFAULT_MODEL: str = Field("gpt-3.5-turbo", env="DEFAULT_MODEL")
    
    # RAG settings
    EMBEDDING_MODEL: str = Field("text-embedding-ada-002", env="EMBEDDING_MODEL")
    VECTOR_STORE_TYPE: str = Field("chroma", env="VECTOR_STORE_TYPE")
    VECTOR_STORE_PATH: str = Field("./vector_store", env="VECTOR_STORE_PATH")


class SearchSettings(BaseSettings):
    """Web search service settings"""
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    
    SEARCH_ENGINE: str = Field("duckduckgo", env="SEARCH_ENGINE")
    GOOGLE_API_KEY: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    GOOGLE_CSE_ID: Optional[str] = Field(None, env="GOOGLE_CSE_ID")
    SERPER_API_KEY: Optional[str] = Field(None, env="SERPER_API_KEY")


class SecuritySettings(BaseSettings):
    """Security and authentication settings"""
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    
    SECRET_KEY: str = Field("your-secret-key-change-in-production", env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS settings
    CORS_ORIGINS: List[str] = Field(["http://localhost:3000"], env="CORS_ORIGINS")
    
    @model_validator(mode='after')
    def assemble_cors_origins(self) -> 'SecuritySettings':
        if isinstance(self.CORS_ORIGINS, str) and not self.CORS_ORIGINS.startswith("["):
            self.CORS_ORIGINS = [i.strip() for i in self.CORS_ORIGINS.split(",")]
        return self


class LoggingSettings(BaseSettings):
    """Logging configuration"""
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    
    LOG_LEVEL: LogLevel = Field(LogLevel.INFO, env="LOG_LEVEL")
    LOG_TO_FILE: bool = Field(True, env="LOG_TO_FILE")
    LOG_DIR: str = Field("logs", env="LOG_DIR")
    JSON_LOGS: bool = Field(True, env="JSON_LOGS")
    REDACT_SENSITIVE_DATA: bool = Field(True, env="REDACT_SENSITIVE_DATA")


class AppSettings(BaseSettings):
    """Application-specific settings"""
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    
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


class Settings(BaseSettings):
    """Main settings container that includes all sub-settings"""
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    
    app: AppSettings = Field(default_factory=AppSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    search: SearchSettings = Field(default_factory=SearchSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Return settings instance for dependency injection"""
    return settings