"""Settings model for storing user preferences and configuration."""

from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    JSON, Enum as SQLEnum, Float
)

from src.models.base import Base, TimestampMixin


class SettingCategory(str, Enum):
    """Setting category enum."""
    GENERAL = "general"
    POSTING = "posting"
    AI = "ai"
    MEDIA = "media"
    NOTIFICATIONS = "notifications"
    STYLE = "style"


class UserSettings(Base, TimestampMixin):
    """User settings and preferences."""
    
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Setting identification
    category = Column(SQLEnum(SettingCategory), nullable=False, index=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    
    # Setting value (stored as JSON for flexibility)
    value = Column(JSON, nullable=False)
    
    # Metadata
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self) -> str:
        return f"<UserSettings(category={self.category}, key={self.key}, value={self.value})>"
    
    @classmethod
    def get_default_settings(cls) -> Dict[str, Dict[str, Any]]:
        """Get default settings structure."""
        return {
            SettingCategory.GENERAL: {
                "timezone": "UTC",
                "language": "en",
                "theme": "dark",
            },
            SettingCategory.POSTING: {
                "daily_post_target": 2,
                "default_post_times": ["09:00", "17:00"],
                "auto_approve": False,
                "queue_size_limit": 50,
                "retry_failed_posts": True,
                "max_retry_attempts": 3,
            },
            SettingCategory.AI: {
                "default_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 280,
                "include_hashtags": True,
                "hashtag_count": 3,
                "content_variations": 3,
            },
            SettingCategory.MEDIA: {
                "auto_generate_images": False,
                "image_style": "realistic",
                "video_duration": 10,
                "compress_media": True,
                "max_file_size_mb": 15,
            },
            SettingCategory.NOTIFICATIONS: {
                "posting_success": True,
                "posting_failure": True,
                "budget_alerts": True,
                "daily_summary": True,
                "weekly_report": True,
            },
            SettingCategory.STYLE: {
                "writing_tone": "conversational",
                "emoji_usage": "moderate",
                "capitalization": "normal",
                "punctuation_style": "standard",
            }
        }


class StyleTemplate(Base, TimestampMixin):
    """Style templates for consistent content generation."""
    
    __tablename__ = "style_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Template details
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Style configuration
    tone = Column(String(50), nullable=False)
    voice = Column(String(50), nullable=False)
    
    # Content patterns
    opening_patterns = Column(JSON, nullable=True)  # List of opening patterns
    closing_patterns = Column(JSON, nullable=True)  # List of closing patterns
    
    # Language preferences
    vocabulary_level = Column(String(20), default="medium")  # simple, medium, advanced
    sentence_structure = Column(String(20), default="varied")  # simple, varied, complex
    
    # Formatting preferences
    use_emojis = Column(Boolean, default=True)
    emoji_frequency = Column(Float, default=0.2)  # Emojis per tweet
    use_hashtags = Column(Boolean, default=True)
    hashtag_style = Column(String(20), default="lowercase")  # lowercase, CamelCase, UPPERCASE
    
    # Example tweets for reference
    example_tweets = Column(JSON, nullable=True)  # List of example tweets
    
    # Usage tracking
    is_active = Column(Boolean, default=True)
    times_used = Column(Integer, default=0)
    
    def __repr__(self) -> str:
        return f"<StyleTemplate(name={self.name}, tone={self.tone}, voice={self.voice})>"