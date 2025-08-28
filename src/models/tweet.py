"""Tweet model for storing scheduled and posted tweets."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, Float, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship

from src.models.base import Base, TimestampMixin


class TweetStatus(str, Enum):
    """Tweet status enum."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    POSTING = "posting"
    POSTED = "posted"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ContentType(str, Enum):
    """Content type enum."""
    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    EDUCATIONAL = "educational"
    PROMOTIONAL = "promotional"
    NEWS = "news"
    CUSTOM = "custom"


class Tweet(Base, TimestampMixin):
    """Tweet model for storing tweet content and metadata."""
    
    __tablename__ = "tweets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Content
    content = Column(Text, nullable=False)
    content_type = Column(SQLEnum(ContentType), default=ContentType.PERSONAL)
    
    # Scheduling
    scheduled_time = Column(DateTime(timezone=True), nullable=True, index=True)
    posted_time = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(SQLEnum(TweetStatus), default=TweetStatus.DRAFT, index=True)
    
    # Generation metadata
    ai_generated = Column(Boolean, default=False)
    generation_prompt = Column(Text, nullable=True)
    generation_model = Column(String(50), nullable=True)
    generation_cost = Column(Float, default=0.0)
    
    # Twitter metadata
    twitter_id = Column(String(100), nullable=True, unique=True)
    twitter_url = Column(String(255), nullable=True)
    
    # Engagement metrics (updated after posting)
    likes_count = Column(Integer, default=0)
    retweets_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    impressions_count = Column(Integer, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Additional metadata
    extra_data = Column(JSON, nullable=True)
    
    # Relationships
    media_items = relationship("Media", back_populates="tweet", cascade="all, delete-orphan")
    hook_usage = relationship("HookUsage", back_populates="tweet", uselist=False)
    
    def __repr__(self) -> str:
        return f"<Tweet(id={self.id}, status={self.status}, content='{self.content[:50]}...')>"
    
    @property
    def is_posted(self) -> bool:
        """Check if tweet is posted."""
        return self.status == TweetStatus.POSTED
    
    @property
    def is_scheduled(self) -> bool:
        """Check if tweet is scheduled."""
        return self.status == TweetStatus.SCHEDULED
    
    @property
    def can_be_posted(self) -> bool:
        """Check if tweet can be posted."""
        return self.status in [TweetStatus.APPROVED, TweetStatus.SCHEDULED]
    
    def get_character_count(self) -> int:
        """Get character count for the tweet."""
        return len(self.content)
    
    def is_within_limit(self) -> bool:
        """Check if tweet is within Twitter character limit."""
        return self.get_character_count() <= 280