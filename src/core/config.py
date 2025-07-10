"""Configuration management for X-Scheduler."""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Twitter/X API
    twitter_api_key: str = Field(default="", description="Twitter API Key")
    twitter_api_secret: str = Field(default="", description="Twitter API Secret")
    twitter_access_token: str = Field(default="", description="Twitter Access Token")
    twitter_access_token_secret: str = Field(default="", description="Twitter Access Token Secret")
    
    # OpenAI API
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    
    # Pollo.ai API
    pollo_api_key: Optional[str] = Field(default=None, description="Pollo.ai API Key")
    
    # Application Settings
    daily_post_target: int = Field(default=2, description="Target number of daily posts")
    budget_limit_monthly: float = Field(default=50.0, description="Monthly budget limit in USD")
    
    # Database
    database_url: str = Field(
        default="sqlite:///data/x_scheduler.db",
        description="Database connection URL"
    )
    
    # Paths
    data_dir: Path = Field(default=Path("data"), description="Data directory path")
    media_dir: Path = Field(default=Path("data/media"), description="Media storage path")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Scheduler
    scheduler_timezone: str = Field(default="UTC", description="Timezone for scheduler")
    default_post_times: str = Field(
        default="09:00,17:00",
        description="Default posting times (comma-separated)"
    )
    
    # Twitter API Limits (Free Tier)
    twitter_daily_limit: int = Field(default=50, description="Daily tweet limit")
    twitter_monthly_limit: int = Field(default=1500, description="Monthly tweet limit")
    
    @field_validator("data_dir", "media_dir", mode="before")
    @classmethod
    def create_directories(cls, v: str) -> Path:
        """Create directories if they don't exist."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def twitter_configured(self) -> bool:
        """Check if Twitter API is configured."""
        return all([
            self.twitter_api_key,
            self.twitter_api_secret,
            self.twitter_access_token,
            self.twitter_access_token_secret
        ])
    
    @property
    def openai_configured(self) -> bool:
        """Check if OpenAI API is configured."""
        return bool(self.openai_api_key)
    
    @property
    def pollo_configured(self) -> bool:
        """Check if Pollo.ai API is configured."""
        return bool(self.pollo_api_key)
    
    def get_default_post_times(self) -> list[str]:
        """Get default posting times as a list."""
        return [time.strip() for time in self.default_post_times.split(",")]


# Global settings instance
settings = Settings()