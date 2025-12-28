"""Configuration management."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    app_name: str = "Data Reconciliation API"
    database_url: str = "sqlite:///./data_recon.db"
    debug: bool = False
    
    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
