
import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base
    base_dir: Path = Path(__file__).resolve().parent.parent
    
    # Database
    database_url: str = f"sqlite:///ojsterminalbio.db"
    
    # Security
    secret_key: str = "ranbir-portfolio-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440 # 24 hours
    
    # Admin Defaults
    default_admin_email: str = "admin@example.com"
    default_admin_password: str = "admin123"

    class Config:
        env_prefix = "OJSTB_"
        env_file = ".env"

settings = Settings()
