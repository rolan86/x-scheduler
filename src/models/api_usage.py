"""API usage tracking model for monitoring costs and rate limits."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    JSON, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.sql import func

from src.models.base import Base, TimestampMixin


class APIProvider(str, Enum):
    """API provider enum."""
    TWITTER = "twitter"
    OPENAI = "openai"
    POLLO_AI = "pollo_ai"


class APIEndpoint(str, Enum):
    """API endpoint enum."""
    # Twitter
    TWEET_CREATE = "tweet_create"
    MEDIA_UPLOAD = "media_upload"
    USER_LOOKUP = "user_lookup"
    
    # OpenAI
    CHAT_COMPLETION = "chat_completion"
    DALL_E_GENERATION = "dall_e_generation"
    
    # Pollo.ai
    VIDEO_GENERATION = "video_generation"


class APIUsage(Base, TimestampMixin):
    """API usage tracking for cost monitoring and rate limiting."""
    
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # API details
    provider = Column(SQLEnum(APIProvider), nullable=False, index=True)
    endpoint = Column(SQLEnum(APIEndpoint), nullable=False)
    
    # Usage details
    request_count = Column(Integer, default=1)
    tokens_used = Column(Integer, nullable=True)  # For OpenAI
    
    # Cost tracking
    cost = Column(Float, default=0.0)
    
    # Timestamp
    usage_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Request metadata
    request_metadata = Column(JSON, nullable=True)
    response_metadata = Column(JSON, nullable=True)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_provider_date', 'provider', 'usage_date'),
        Index('idx_endpoint_date', 'endpoint', 'usage_date'),
    )
    
    def __repr__(self) -> str:
        return f"<APIUsage(id={self.id}, provider={self.provider}, endpoint={self.endpoint}, cost=${self.cost:.4f})>"


class APIBudget(Base, TimestampMixin):
    """Monthly API budget tracking."""
    
    __tablename__ = "api_budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Budget period
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    # Budget limits
    provider = Column(SQLEnum(APIProvider), nullable=False)
    budget_limit = Column(Float, nullable=False)
    
    # Current usage
    current_spend = Column(Float, default=0.0)
    request_count = Column(Integer, default=0)
    
    # Alert threshold (percentage)
    alert_threshold = Column(Float, default=0.8)  # Alert at 80% by default
    alert_sent = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('year', 'month', 'provider', name='_year_month_provider_uc'),
    )
    
    def __repr__(self) -> str:
        return f"<APIBudget(provider={self.provider}, {self.year}-{self.month:02d}, spent=${self.current_spend:.2f}/${self.budget_limit:.2f})>"
    
    @property
    def usage_percentage(self) -> float:
        """Get usage percentage."""
        if self.budget_limit == 0:
            return 0.0
        return (self.current_spend / self.budget_limit) * 100
    
    @property
    def is_over_budget(self) -> bool:
        """Check if over budget."""
        return self.current_spend >= self.budget_limit
    
    @property
    def should_alert(self) -> bool:
        """Check if should send alert."""
        return (self.usage_percentage >= self.alert_threshold * 100) and not self.alert_sent