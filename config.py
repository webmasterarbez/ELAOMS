"""Configuration settings for ELAOMS."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # OpenMemory Configuration
    openmemory_url: str = "http://localhost:8080"
    openmemory_api_key: str
    
    # Eleven Labs Configuration
    elevenlabs_api_key: str
    elevenlabs_webhook_secret: str
    
    # Database Configuration
    database_url: str = "sqlite:///./elaoms.db"
    
    # ngrok Configuration (optional)
    ngrok_auth_token: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

