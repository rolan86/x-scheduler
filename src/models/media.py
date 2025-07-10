"""Media model for storing images and videos associated with tweets."""

from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship

from src.models.base import Base, TimestampMixin


class MediaType(str, Enum):
    """Media type enum."""
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"


class MediaSource(str, Enum):
    """Media source enum."""
    UPLOADED = "uploaded"
    DALL_E = "dall_e"
    POLLO_AI = "pollo_ai"
    URL = "url"
    LOCAL = "local"


class Media(Base, TimestampMixin):
    """Media model for storing media files."""
    
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # in bytes
    mime_type = Column(String(100), nullable=True)
    
    # Media details
    media_type = Column(SQLEnum(MediaType), nullable=False)
    media_source = Column(SQLEnum(MediaSource), nullable=False)
    
    # Dimensions (for images/videos)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)  # in seconds, for videos
    
    # Generation details (for AI-generated media)
    generation_prompt = Column(Text, nullable=True)
    generation_model = Column(String(50), nullable=True)
    generation_cost = Column(Float, default=0.0)
    
    # Twitter media ID (after upload)
    twitter_media_id = Column(String(100), nullable=True)
    
    # Alt text for accessibility
    alt_text = Column(Text, nullable=True)
    
    # Metadata
    extra_data = Column(JSON, nullable=True)
    
    # Relationships
    tweet_id = Column(Integer, ForeignKey("tweets.id"), nullable=True)
    tweet = relationship("Tweet", back_populates="media_items")
    
    def __repr__(self) -> str:
        return f"<Media(id={self.id}, type={self.media_type}, source={self.media_source}, file={self.filename})>"
    
    @property
    def is_ai_generated(self) -> bool:
        """Check if media is AI-generated."""
        return self.media_source in [MediaSource.DALL_E, MediaSource.POLLO_AI]
    
    @property
    def is_video(self) -> bool:
        """Check if media is a video."""
        return self.media_type == MediaType.VIDEO
    
    @property
    def is_image(self) -> bool:
        """Check if media is an image."""
        return self.media_type == MediaType.IMAGE