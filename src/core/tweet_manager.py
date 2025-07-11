"""Tweet management service for creating, scheduling, and posting tweets."""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

from sqlalchemy.orm import Session

from src.models import (
    get_db, Tweet, TweetStatus, ContentType, Media, MediaType, MediaSource,
    DailyStats
)
from src.api.twitter import twitter_api
from src.api.openai_client import openai_client
from src.core.config import settings


logger = logging.getLogger(__name__)


class TweetManager:
    """Manages tweet lifecycle from creation to posting."""
    
    def __init__(self):
        self.db: Optional[Session] = None
    
    def _get_db(self) -> Session:
        """Get database session."""
        if not self.db:
            self.db = next(get_db())
        return self.db
    
    def _close_db(self) -> None:
        """Close database session."""
        if self.db:
            self.db.close()
            self.db = None
    
    def create_tweet(self, content: str, content_type: ContentType = ContentType.PERSONAL,
                    scheduled_time: Optional[datetime] = None, ai_generated: bool = False,
                    generation_prompt: Optional[str] = None, generation_model: Optional[str] = None,
                    generation_cost: float = 0.0) -> Tweet:
        """Create a new tweet in the database."""
        try:
            db = self._get_db()
            
            # Validate content
            if not content.strip():
                raise ValueError("Tweet content cannot be empty")
            
            if len(content) > 280:
                raise ValueError(f"Tweet too long: {len(content)} characters (max 280)")
            
            # Determine initial status
            if scheduled_time:
                status = TweetStatus.SCHEDULED
            else:
                status = TweetStatus.DRAFT
            
            # Create tweet
            tweet = Tweet(
                content=content.strip(),
                content_type=content_type,
                scheduled_time=scheduled_time,
                status=status,
                ai_generated=ai_generated,
                generation_prompt=generation_prompt,
                generation_model=generation_model,
                generation_cost=generation_cost
            )
            
            db.add(tweet)
            db.commit()
            db.refresh(tweet)
            
            logger.info(f"Created tweet {tweet.id}: {content[:50]}...")
            return tweet
            
        except Exception as e:
            if self.db:
                self.db.rollback()
            logger.error(f"Failed to create tweet: {e}")
            raise
        finally:
            self._close_db()
    
    def get_tweet(self, tweet_id: int) -> Optional[Tweet]:
        """Get a tweet by ID."""
        try:
            db = self._get_db()
            tweet = db.query(Tweet).filter_by(id=tweet_id).first()
            if tweet:
                # Eagerly load relationships to avoid detached instance issues
                # This loads media_items while the session is still active
                _ = list(tweet.media_items)  # Force loading
                db.expunge(tweet)  # Remove from session to avoid issues
            return tweet
        except Exception as e:
            logger.error(f"Failed to get tweet {tweet_id}: {e}")
            return None
        finally:
            self._close_db()
    
    def get_tweets_by_status(self, status: TweetStatus, limit: int = 50) -> List[Tweet]:
        """Get tweets by status."""
        try:
            db = self._get_db()
            tweets = db.query(Tweet).filter_by(status=status).limit(limit).all()
            return tweets
        except Exception as e:
            logger.error(f"Failed to get tweets by status {status}: {e}")
            return []
        finally:
            self._close_db()
    
    def get_scheduled_tweets(self, due_now: bool = False) -> List[Tweet]:
        """Get scheduled tweets, optionally only those due now."""
        try:
            db = self._get_db()
            query = db.query(Tweet).filter_by(status=TweetStatus.SCHEDULED)
            
            if due_now:
                now = datetime.now(timezone.utc)
                query = query.filter(Tweet.scheduled_time <= now)
            
            tweets = query.order_by(Tweet.scheduled_time).all()
            return tweets
        except Exception as e:
            logger.error(f"Failed to get scheduled tweets: {e}")
            return []
        finally:
            self._close_db()
    
    def update_tweet_content(self, tweet_id: int, content: str) -> bool:
        """Update tweet content."""
        try:
            db = self._get_db()
            tweet = db.query(Tweet).filter_by(id=tweet_id).first()
            
            if not tweet:
                logger.error(f"Tweet {tweet_id} not found")
                return False
            
            if tweet.status == TweetStatus.POSTED:
                logger.error(f"Cannot update posted tweet {tweet_id}")
                return False
            
            if len(content) > 280:
                raise ValueError(f"Tweet too long: {len(content)} characters (max 280)")
            
            tweet.content = content.strip()
            db.commit()
            
            logger.info(f"Updated tweet {tweet_id} content")
            return True
            
        except Exception as e:
            if self.db:
                self.db.rollback()
            logger.error(f"Failed to update tweet {tweet_id}: {e}")
            return False
        finally:
            self._close_db()
    
    def schedule_tweet(self, tweet_id: int, scheduled_time: datetime) -> bool:
        """Schedule a tweet for posting."""
        try:
            db = self._get_db()
            tweet = db.query(Tweet).filter_by(id=tweet_id).first()
            
            if not tweet:
                logger.error(f"Tweet {tweet_id} not found")
                return False
            
            if tweet.status == TweetStatus.POSTED:
                logger.error(f"Cannot reschedule posted tweet {tweet_id}")
                return False
            
            # Ensure scheduled time is in the future
            # Handle timezone-aware vs naive datetime comparison
            now = datetime.now(timezone.utc)
            if scheduled_time.tzinfo is None:
                # If scheduled_time is naive, assume it's in UTC
                scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)
            
            if scheduled_time <= now:
                raise ValueError("Scheduled time must be in the future")
            
            tweet.scheduled_time = scheduled_time
            tweet.status = TweetStatus.SCHEDULED
            db.commit()
            
            logger.info(f"Scheduled tweet {tweet_id} for {scheduled_time}")
            return True
            
        except Exception as e:
            if self.db:
                self.db.rollback()
            logger.error(f"Failed to schedule tweet {tweet_id}: {e}")
            return False
        finally:
            self._close_db()
    
    def approve_tweet(self, tweet_id: int) -> bool:
        """Approve a tweet for posting."""
        try:
            db = self._get_db()
            tweet = db.query(Tweet).filter_by(id=tweet_id).first()
            
            if not tweet:
                logger.error(f"Tweet {tweet_id} not found")
                return False
            
            if tweet.status == TweetStatus.POSTED:
                logger.warning(f"Tweet {tweet_id} is already posted")
                return True
            
            tweet.status = TweetStatus.APPROVED
            db.commit()
            
            logger.info(f"Approved tweet {tweet_id}")
            return True
            
        except Exception as e:
            if self.db:
                self.db.rollback()
            logger.error(f"Failed to approve tweet {tweet_id}: {e}")
            return False
        finally:
            self._close_db()
    
    def post_tweet(self, tweet_id: int, force: bool = False) -> bool:
        """Post a tweet to Twitter/X."""
        try:
            db = self._get_db()
            tweet = db.query(Tweet).filter_by(id=tweet_id).first()
            
            if not tweet:
                logger.error(f"Tweet {tweet_id} not found")
                return False
            
            if tweet.status == TweetStatus.POSTED:
                logger.warning(f"Tweet {tweet_id} is already posted")
                return True
            
            # Check if tweet can be posted
            if not force and not tweet.can_be_posted:
                logger.error(f"Tweet {tweet_id} cannot be posted (status: {tweet.status})")
                return False
            
            # Update status to posting
            tweet.status = TweetStatus.POSTING
            db.commit()
            
            # Prepare media IDs if any
            media_ids = []
            for media in tweet.media_items:
                if media.twitter_media_id:
                    media_ids.append(media.twitter_media_id)
            
            # Post to Twitter
            result = twitter_api.post_tweet(
                content=tweet.content,
                media_ids=media_ids if media_ids else None
            )
            
            if result:
                # Update tweet with Twitter response
                tweet.status = TweetStatus.POSTED
                tweet.posted_time = datetime.now(timezone.utc)
                tweet.twitter_id = result['id']
                tweet.twitter_url = result['url']
                tweet.error_message = None
                tweet.retry_count = 0
                
                db.commit()
                
                # Update daily stats
                self._update_daily_stats(posted=1)
                
                logger.info(f"Successfully posted tweet {tweet_id} to Twitter: {result['id']}")
                return True
            else:
                # Post failed
                tweet.status = TweetStatus.FAILED
                tweet.error_message = "Failed to post to Twitter"
                tweet.retry_count += 1
                
                db.commit()
                
                # Update daily stats
                self._update_daily_stats(failed=1)
                
                logger.error(f"Failed to post tweet {tweet_id} to Twitter")
                return False
                
        except Exception as e:
            if self.db:
                self.db.rollback()
                # Update tweet status to failed
                try:
                    tweet.status = TweetStatus.FAILED
                    tweet.error_message = str(e)
                    tweet.retry_count += 1
                    self.db.commit()
                except Exception:
                    pass
            
            logger.error(f"Error posting tweet {tweet_id}: {e}")
            return False
        finally:
            self._close_db()
    
    def delete_tweet(self, tweet_id: int, force: bool = False) -> bool:
        """Delete a tweet from the database."""
        try:
            db = self._get_db()
            tweet = db.query(Tweet).filter_by(id=tweet_id).first()
            
            if not tweet:
                logger.error(f"Tweet {tweet_id} not found")
                return False
            
            if tweet.status == TweetStatus.POSTED and not force:
                logger.error(f"Cannot delete posted tweet {tweet_id} without force flag")
                return False
            
            db.delete(tweet)
            db.commit()
            
            logger.info(f"Deleted tweet {tweet_id}")
            return True
            
        except Exception as e:
            if self.db:
                self.db.rollback()
            logger.error(f"Failed to delete tweet {tweet_id}: {e}")
            return False
        finally:
            self._close_db()
    
    def attach_media(self, tweet_id: int, media_path: Path, alt_text: Optional[str] = None) -> bool:
        """Attach media to a tweet and upload to Twitter."""
        try:
            db = self._get_db()
            tweet = db.query(Tweet).filter_by(id=tweet_id).first()
            
            if not tweet:
                logger.error(f"Tweet {tweet_id} not found")
                return False
            
            if tweet.status == TweetStatus.POSTED:
                logger.error(f"Cannot attach media to posted tweet {tweet_id}")
                return False
            
            if not media_path.exists():
                logger.error(f"Media file not found: {media_path}")
                return False
            
            # Determine media type
            suffix = media_path.suffix.lower()
            if suffix in ['.jpg', '.jpeg', '.png', '.gif']:
                media_type = MediaType.IMAGE
            elif suffix in ['.mp4', '.mov', '.avi']:
                media_type = MediaType.VIDEO
            else:
                logger.error(f"Unsupported media type: {suffix}")
                return False
            
            # Upload to Twitter
            twitter_media_id = twitter_api.upload_media(media_path, alt_text)
            
            if not twitter_media_id:
                logger.error(f"Failed to upload media to Twitter: {media_path}")
                return False
            
            # Create media record
            media = Media(
                filename=media_path.name,
                file_path=str(media_path),
                file_size=media_path.stat().st_size,
                media_type=media_type,
                media_source=MediaSource.UPLOADED,
                twitter_media_id=twitter_media_id,
                alt_text=alt_text,
                tweet_id=tweet_id
            )
            
            db.add(media)
            db.commit()
            
            logger.info(f"Attached media {media_path.name} to tweet {tweet_id}")
            return True
            
        except Exception as e:
            if self.db:
                self.db.rollback()
            logger.error(f"Failed to attach media to tweet {tweet_id}: {e}")
            return False
        finally:
            self._close_db()
    
    def _update_daily_stats(self, posted: int = 0, scheduled: int = 0, failed: int = 0) -> None:
        """Update daily statistics."""
        try:
            from datetime import date
            
            db = self._get_db()
            today = date.today()
            
            # Get or create daily stats
            daily_stats = db.query(DailyStats).filter_by(stat_date=today).first()
            
            if not daily_stats:
                daily_stats = DailyStats(stat_date=today)
                db.add(daily_stats)
            
            # Update counts
            daily_stats.tweets_posted += posted
            daily_stats.tweets_scheduled += scheduled
            daily_stats.tweets_failed += failed
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update daily stats: {e}")
    
    def get_tweet_queue(self, status_filter: Optional[TweetStatus] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get tweet queue with formatting for display."""
        try:
            db = self._get_db()
            
            query = db.query(Tweet)
            if status_filter:
                query = query.filter_by(status=status_filter)
            
            tweets = query.order_by(Tweet.scheduled_time.asc().nullslast(), Tweet.created_at.desc()).limit(limit).all()
            
            queue = []
            for tweet in tweets:
                queue_item = {
                    'id': tweet.id,
                    'content': tweet.content[:50] + '...' if len(tweet.content) > 50 else tweet.content,
                    'full_content': tweet.content,
                    'status': tweet.status.value,
                    'content_type': tweet.content_type.value,
                    'scheduled_time': tweet.scheduled_time.isoformat() if tweet.scheduled_time else None,
                    'posted_time': tweet.posted_time.isoformat() if tweet.posted_time else None,
                    'character_count': len(tweet.content),
                    'ai_generated': tweet.ai_generated,
                    'has_media': len(tweet.media_items) > 0,
                    'media_count': len(tweet.media_items),
                    'twitter_id': tweet.twitter_id,
                    'twitter_url': tweet.twitter_url,
                    'error_message': tweet.error_message,
                    'retry_count': tweet.retry_count,
                    'created_at': tweet.created_at.isoformat()
                }
                queue.append(queue_item)
            
            return queue
            
        except Exception as e:
            logger.error(f"Failed to get tweet queue: {e}")
            return []
        finally:
            self._close_db()


# Global tweet manager instance
tweet_manager = TweetManager()