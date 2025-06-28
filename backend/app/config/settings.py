import os
from typing import Optional, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = int(os.getenv("PORT", "8000"))
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
    
    # Redis Configuration (for session storage)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # CORS Configuration - store as string, parse as list
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501,http://localhost:8502,http://127.0.0.1:8502")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS_ORIGINS string into a list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Global settings instance
settings = Settings() 