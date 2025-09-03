from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import secrets

class Settings(BaseSettings):
    # database config
    DATABASE_URL: str = Field(..., description="Database connection URL")
    
    # security config
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # app config
    DEBUG: bool
    ALLOWED_HOSTS: List[str]
    API_PREFIX: str
    
    # CORS config
    CORS_ORIGINS: List[str]
    CORS_ALLOW_CREDENTIALS: bool 
    CORS_ALLOW_METHODS: List[str]
    CORS_ALLOW_HEADERS: List[str]
    
    # Pydantic model config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

# function for getting config with cache
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    return Settings()