"""Analytics models for tracking performance and growth metrics."""

from datetime import datetime, date
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime,
    Boolean, JSON, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.sql import func

from src.models.base import Base, TimestampMixin


class MetricType(str, Enum):
    """Metric type enum."""
    FOLLOWERS = "followers"
    FOLLOWING = "following"
    TWEETS = "tweets"
    ENGAGEMENT_RATE = "engagement_rate"
    IMPRESSIONS = "impressions"
    PROFILE_VISITS = "profile_visits"


class DailyStats(Base, TimestampMixin):
    """Daily statistics for tracking posting consistency and growth."""
    
    __tablename__ = "daily_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Date
    stat_date = Column(Date, nullable=False, unique=True, index=True)
    
    # Posting metrics
    tweets_posted = Column(Integer, default=0)
    tweets_scheduled = Column(Integer, default=0)
    tweets_failed = Column(Integer, default=0)
    
    # Engagement metrics
    total_likes = Column(Integer, default=0)
    total_retweets = Column(Integer, default=0)
    total_replies = Column(Integer, default=0)
    total_impressions = Column(Integer, default=0)
    
    # Growth metrics
    followers_count = Column(Integer, default=0)
    followers_gained = Column(Integer, default=0)
    followers_lost = Column(Integer, default=0)
    
    # API usage
    api_calls_made = Column(Integer, default=0)
    api_cost = Column(Float, default=0.0)
    
    # Media usage
    images_generated = Column(Integer, default=0)
    videos_generated = Column(Integer, default=0)
    
    # Additional metrics
    extra_data = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        return f"<DailyStats(date={self.stat_date}, tweets={self.tweets_posted}, followers={self.followers_count})>"
    
    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate."""
        total_engagement = self.total_likes + self.total_retweets + self.total_replies
        if self.total_impressions == 0:
            return 0.0
        return (total_engagement / self.total_impressions) * 100
    
    @property
    def net_follower_change(self) -> int:
        """Get net follower change."""
        return self.followers_gained - self.followers_lost


class PostingPattern(Base, TimestampMixin):
    """Analyze posting patterns for optimal timing."""
    
    __tablename__ = "posting_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Time analysis
    hour = Column(Integer, nullable=False)  # 0-23
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Monday-Sunday)
    
    # Performance metrics
    avg_likes = Column(Float, default=0.0)
    avg_retweets = Column(Float, default=0.0)
    avg_replies = Column(Float, default=0.0)
    avg_impressions = Column(Float, default=0.0)
    avg_engagement_rate = Column(Float, default=0.0)
    
    # Sample size
    tweet_count = Column(Integer, default=0)
    
    # Last updated
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('hour', 'day_of_week', name='_hour_day_uc'),
    )
    
    def __repr__(self) -> str:
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return f"<PostingPattern({days[self.day_of_week]} {self.hour}:00, engagement={self.avg_engagement_rate:.2f}%)>"


class UserMetrics(Base, TimestampMixin):
    """Track user-specific metrics over time."""
    
    __tablename__ = "user_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Metric details
    metric_type = Column(SQLEnum(MetricType), nullable=False)
    metric_value = Column(Float, nullable=False)
    
    # Timestamp
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Additional data
    extra_data = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        return f"<UserMetrics(type={self.metric_type}, value={self.metric_value}, time={self.recorded_at})>"