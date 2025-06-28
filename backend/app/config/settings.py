import os
from typing import Optional, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = int(os.getenv("PORT", "8080"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "false").lower() == "true"
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    
    # Google Calendar Configuration
    GOOGLE_CALENDAR_CREDENTIALS_FILE: Optional[str] = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_FILE")
    GOOGLE_CALENDAR_TOKEN_FILE: Optional[str] = os.getenv("GOOGLE_CALENDAR_TOKEN_FILE", "token.json")
    CALENDAR_ID: str = os.getenv("CALENDAR_ID", "primary")
    USE_MOCK_CALENDAR: bool = os.getenv("USE_MOCK_CALENDAR", "true").lower() == "true"
    
    # AI/LLM Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:8501",
        "http://localhost:3000",
        "https://your-frontend-domain.fly.dev",  # Update with your frontend domain
        "*"  # For development - remove in production
    ]
    
    # Cache Configuration
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    
    # Email Configuration
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@yourdomain.com")
    
    # Session Configuration
    SESSION_DIR: str = os.getenv("SESSION_DIR", "/tmp/sessions")
    SESSION_TTL: int = int(os.getenv("SESSION_TTL", "3600"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings() 