"""Hook models for storing and managing high-performing tweet patterns."""

from datetime import datetime
from typing import Optional, Dict, List, Any
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from src.models.base import Base


class HookTemplate(Base):
    """Model for storing high-performing tweet hook templates."""
    
    __tablename__ = 'hook_templates'
    
    id = Column(Integer, primary_key=True)
    pattern_type = Column(String(50), nullable=False)  # 'shock', 'value_prop', 'authority', etc.
    name = Column(String(200))  # Human-friendly name for the hook
    hook_text = Column(Text, nullable=False)  # The actual hook pattern/template
    example_tweet = Column(Text)  # Full example tweet using this hook
    structure_notes = Column(Text)  # Notes on how to structure content with this hook
    
    # Performance data
    performance_metrics = Column(JSON)  # {'views': 100000, 'likes': 5000, 'engagement_rate': 5.2}
    min_views = Column(Integer, default=0)  # Minimum views achieved
    avg_engagement_rate = Column(Float, default=0.0)  # Average engagement rate
    success_rate = Column(Float, default=0.0)  # Success rate when used (0-1)
    
    # Categorization
    tags = Column(JSON)  # ['AI', 'automation', 'viral', 'tech']
    use_cases = Column(JSON)  # ['product_launch', 'educational', 'news']
    target_audience = Column(String(100))  # 'developers', 'marketers', etc.
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String(200))  # Where this hook came from
    
    # Relationships
    usages = relationship("HookUsage", back_populates="hook_template", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<HookTemplate(id={self.id}, type={self.pattern_type}, name={self.name})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert hook template to dictionary."""
        return {
            'id': self.id,
            'pattern_type': self.pattern_type,
            'name': self.name,
            'hook_text': self.hook_text,
            'example_tweet': self.example_tweet,
            'structure_notes': self.structure_notes,
            'performance_metrics': self.performance_metrics,
            'tags': self.tags,
            'use_cases': self.use_cases,
            'success_rate': self.success_rate,
            'is_active': self.is_active
        }


class HookUsage(Base):
    """Track how hooks are used and their performance."""
    
    __tablename__ = 'hook_usage'
    
    id = Column(Integer, primary_key=True)
    hook_id = Column(Integer, ForeignKey('hook_templates.id'), nullable=False)
    tweet_id = Column(Integer, ForeignKey('tweets.id'), nullable=False)
    
    # How the hook was adapted
    original_content = Column(Text)  # Content before hook application
    adapted_content = Column(Text)  # Content after hook application
    adaptation_notes = Column(Text)  # Notes on how it was adapted
    
    # Performance tracking
    performance_score = Column(Float)  # Performance score (0-10)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    
    # Metadata
    used_at = Column(DateTime, default=datetime.utcnow)
    feedback = Column(Text)  # User feedback on the hook usage
    
    # Relationships
    hook_template = relationship("HookTemplate", back_populates="usages")
    tweet = relationship("Tweet", back_populates="hook_usage")
    
    def __repr__(self):
        return f"<HookUsage(id={self.id}, hook_id={self.hook_id}, tweet_id={self.tweet_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert hook usage to dictionary."""
        return {
            'id': self.id,
            'hook_id': self.hook_id,
            'tweet_id': self.tweet_id,
            'adapted_content': self.adapted_content,
            'performance_score': self.performance_score,
            'engagement_rate': self.engagement_rate,
            'used_at': self.used_at.isoformat() if self.used_at else None
        }


class HookCategory(Base):
    """Categories for organizing hooks."""
    
    __tablename__ = 'hook_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    typical_performance = Column(JSON)  # Expected performance metrics
    best_for = Column(JSON)  # Best use cases
    examples = Column(JSON)  # Example patterns in this category
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<HookCategory(id={self.id}, name={self.name})>"


# Hook pattern types enum
class HookPatternType:
    SHOCK = 'shock'  # "HOLY SH*T..🤯"
    VALUE_GIVEAWAY = 'value_giveaway'  # "Comment X and I'll send"
    AUTHORITY = 'authority'  # "I've cracked X"
    CONTRARIAN = 'contrarian'  # "Stop doing X"
    INSIDER = 'insider'  # "They asked me not to share"
    RESULTS = 'results'  # "$47K monthly"
    TIME_SENSITIVE = 'time_sensitive'  # "FREE for 24hrs"
    LIST = 'list'  # "10 X that Y"
    QUESTION = 'question'  # "Why does nobody talk about X?"
    STORY = 'story'  # Personal narrative hooks
    
    @classmethod
    def all_types(cls) -> List[str]:
        """Get all hook pattern types."""
        return [
            cls.SHOCK, cls.VALUE_GIVEAWAY, cls.AUTHORITY,
            cls.CONTRARIAN, cls.INSIDER, cls.RESULTS,
            cls.TIME_SENSITIVE, cls.LIST, cls.QUESTION, cls.STORY
        ]