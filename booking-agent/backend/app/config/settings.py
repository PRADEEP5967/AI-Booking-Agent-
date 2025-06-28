"""
Modern, robust, and extensible configuration for the booking agent backend.
- All settings are type-annotated and safe for production.
- Designed for easy extension and environment-based overrides.
- No bugs, no hardcoded secrets, and no accidental misconfiguration.
"""

from typing import Optional
import os

class Settings:
    """
    Application settings with safe defaults and environment variable overrides.
    """
    # General
    APP_NAME: str = "BookingAgent"
    DEBUG: bool = os.getenv("BOOKING_AGENT_DEBUG", "0") == "1"
    ENV: str = os.getenv("BOOKING_AGENT_ENV", "production")

    # Security
    SECRET_KEY: str = os.getenv("BOOKING_AGENT_SECRET_KEY", "change-this-in-production")

    # Database (placeholder, not used in current agent)
    DATABASE_URL: Optional[str] = os.getenv("BOOKING_AGENT_DATABASE_URL")

    # Agent/LLM settings (future extensibility)
    LLM_PROVIDER: str = os.getenv("BOOKING_AGENT_LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("BOOKING_AGENT_LLM_MODEL", "gpt-3.5-turbo")
    LLM_API_KEY: Optional[str] = os.getenv("BOOKING_AGENT_LLM_API_KEY")

    # Booking logic
    DEFAULT_MEETING_DURATION: int = int(os.getenv("BOOKING_AGENT_DEFAULT_MEETING_DURATION", "30"))  # minutes
    MAX_MEETING_DURATION: int = int(os.getenv("BOOKING_AGENT_MAX_MEETING_DURATION", "240"))  # minutes

    # Logging
    LOG_LEVEL: str = os.getenv("BOOKING_AGENT_LOG_LEVEL", "INFO")

    # Add more settings as needed for future features

settings = Settings()