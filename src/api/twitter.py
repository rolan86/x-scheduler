"""Twitter/X API integration with rate limiting and error handling."""

import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path

import tweepy
from tweepy.errors import TweepyException

from src.api.auth import auth_manager
from src.models import APIUsage, APIProvider, APIEndpoint, get_db
from src.core.config import settings


logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for Twitter API calls."""
    
    def __init__(self):
        self.call_history: Dict[str, List[float]] = {}
        self.limits = {
            'tweet_create': {'calls': 50, 'window': 24 * 3600},  # 50 per 24 hours
            'media_upload': {'calls': 50, 'window': 24 * 3600},   # 50 per 24 hours
            'user_lookup': {'calls': 75, 'window': 15 * 60},      # 75 per 15 minutes
        }
    
    def can_make_call(self, endpoint: str) -> bool:
        """Check if we can make a call to the endpoint."""
        if endpoint not in self.limits:
            return True
        
        limit_info = self.limits[endpoint]
        now = time.time()
        window_start = now - limit_info['window']
        
        # Clean old calls
        if endpoint in self.call_history:
            self.call_history[endpoint] = [
                call_time for call_time in self.call_history[endpoint]
                if call_time > window_start
            ]
        else:
            self.call_history[endpoint] = []
        
        # Check if we're under the limit
        return len(self.call_history[endpoint]) < limit_info['calls']
    
    def record_call(self, endpoint: str) -> None:
        """Record a call to the endpoint."""
        if endpoint not in self.call_history:
            self.call_history[endpoint] = []
        
        self.call_history[endpoint].append(time.time())
    
    def get_wait_time(self, endpoint: str) -> float:
        """Get time to wait before next call (in seconds)."""
        if endpoint not in self.limits or self.can_make_call(endpoint):
            return 0.0
        
        limit_info = self.limits[endpoint]
        oldest_call = min(self.call_history[endpoint])
        return (oldest_call + limit_info['window']) - time.time()


class TwitterAPI:
    """Twitter API client with authentication and rate limiting."""
    
    def __init__(self):
        self.client: Optional[tweepy.Client] = None
        self.api_v1: Optional[tweepy.API] = None
        self.rate_limiter = RateLimiter()
        self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """Initialize Twitter API client."""
        try:
            creds = auth_manager.get_twitter_credentials()
            if not creds:
                logger.warning("Twitter credentials not found")
                return False
            
            # Initialize API v2 client
            self.client = tweepy.Client(
                consumer_key=creds.api_key.get_secret_value(),
                consumer_secret=creds.api_secret.get_secret_value(),
                access_token=creds.access_token.get_secret_value(),
                access_token_secret=creds.access_token_secret.get_secret_value(),
                wait_on_rate_limit=True
            )
            
            # Initialize API v1 for media upload
            auth = tweepy.OAuth1UserHandler(
                creds.api_key.get_secret_value(),
                creds.api_secret.get_secret_value(),
                creds.access_token.get_secret_value(),
                creds.access_token_secret.get_secret_value()
            )
            self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
            
            logger.info("Twitter API client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {e}")
            return False
    
    def _log_api_usage(self, endpoint: APIEndpoint, cost: float = 0.0, 
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log API usage for cost tracking."""
        try:
            db = next(get_db())
            usage = APIUsage(
                provider=APIProvider.TWITTER,
                endpoint=endpoint,
                cost=cost,
                request_metadata=metadata or {}
            )
            db.add(usage)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")
    
    def test_connection(self) -> bool:
        """Test Twitter API connection."""
        try:
            if not self.client:
                return False
            
            # Check rate limits
            if not self.rate_limiter.can_make_call('user_lookup'):
                logger.warning("Rate limit exceeded for user lookup")
                return False
            
            # Get user info
            user = self.client.get_me()
            if user.data:
                self.rate_limiter.record_call('user_lookup')
                self._log_api_usage(APIEndpoint.USER_LOOKUP, metadata={
                    'username': user.data.username,
                    'user_id': user.data.id
                })
                logger.info(f"Twitter connection successful: @{user.data.username}")
                return True
            
            return False
            
        except TweepyException as e:
            logger.error(f"Twitter API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing Twitter connection: {e}")
            return False
    
    def post_tweet(self, content: str, media_ids: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Post a tweet."""
        try:
            if not self.client:
                raise Exception("Twitter client not initialized")
            
            # Check rate limits
            if not self.rate_limiter.can_make_call('tweet_create'):
                wait_time = self.rate_limiter.get_wait_time('tweet_create')
                raise Exception(f"Rate limit exceeded. Wait {wait_time:.0f} seconds")
            
            # Check character limit
            if len(content) > 280:
                raise Exception(f"Tweet too long: {len(content)} characters (max 280)")
            
            # Post tweet
            response = self.client.create_tweet(
                text=content,
                media_ids=media_ids
            )
            
            if response.data:
                self.rate_limiter.record_call('tweet_create')
                
                result = {
                    'id': response.data['id'],
                    'text': content,
                    'url': f"https://twitter.com/user/status/{response.data['id']}",
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                
                self._log_api_usage(APIEndpoint.TWEET_CREATE, metadata={
                    'tweet_id': response.data['id'],
                    'content_length': len(content),
                    'media_count': len(media_ids) if media_ids else 0
                })
                
                logger.info(f"Tweet posted successfully: {response.data['id']}")
                return result
            
            raise Exception("No data returned from Twitter API")
            
        except TweepyException as e:
            logger.error(f"Twitter API error posting tweet: {e}")
            return None
        except Exception as e:
            logger.error(f"Error posting tweet: {e}")
            return None
    
    def upload_media(self, file_path: Path, alt_text: Optional[str] = None) -> Optional[str]:
        """Upload media file to Twitter."""
        try:
            if not self.api_v1:
                raise Exception("Twitter API v1 not initialized")
            
            if not file_path.exists():
                raise Exception(f"Media file not found: {file_path}")
            
            # Check rate limits
            if not self.rate_limiter.can_make_call('media_upload'):
                wait_time = self.rate_limiter.get_wait_time('media_upload')
                raise Exception(f"Rate limit exceeded. Wait {wait_time:.0f} seconds")
            
            # Upload media
            media = self.api_v1.media_upload(filename=str(file_path))
            
            # Add alt text if provided
            if alt_text and hasattr(media, 'media_id'):
                self.api_v1.create_media_metadata(
                    media_id=media.media_id,
                    alt_text=alt_text
                )
            
            self.rate_limiter.record_call('media_upload')
            
            self._log_api_usage(APIEndpoint.MEDIA_UPLOAD, metadata={
                'media_id': media.media_id,
                'file_size': file_path.stat().st_size,
                'alt_text_provided': bool(alt_text)
            })
            
            logger.info(f"Media uploaded successfully: {media.media_id}")
            return media.media_id
            
        except TweepyException as e:
            logger.error(f"Twitter API error uploading media: {e}")
            return None
        except Exception as e:
            logger.error(f"Error uploading media: {e}")
            return None
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user information."""
        try:
            if not self.client:
                return None
            
            if not self.rate_limiter.can_make_call('user_lookup'):
                return None
            
            user = self.client.get_me(
                user_fields=['public_metrics', 'created_at', 'description', 'location']
            )
            
            if user.data:
                self.rate_limiter.record_call('user_lookup')
                
                metrics = user.data.public_metrics or {}
                result = {
                    'id': user.data.id,
                    'username': user.data.username,
                    'name': user.data.name,
                    'description': user.data.description,
                    'location': user.data.location,
                    'created_at': user.data.created_at.isoformat() if user.data.created_at else None,
                    'followers_count': metrics.get('followers_count', 0),
                    'following_count': metrics.get('following_count', 0),
                    'tweet_count': metrics.get('tweet_count', 0),
                    'listed_count': metrics.get('listed_count', 0)
                }
                
                self._log_api_usage(APIEndpoint.USER_LOOKUP, metadata={
                    'user_id': user.data.id,
                    'username': user.data.username
                })
                
                return result
            
            return None
            
        except TweepyException as e:
            logger.error(f"Twitter API error getting user info: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        status = {}
        
        for endpoint, limit_info in self.rate_limiter.limits.items():
            can_call = self.rate_limiter.can_make_call(endpoint)
            wait_time = self.rate_limiter.get_wait_time(endpoint)
            calls_made = len(self.rate_limiter.call_history.get(endpoint, []))
            
            status[endpoint] = {
                'can_call': can_call,
                'wait_time_seconds': wait_time,
                'calls_made': calls_made,
                'limit': limit_info['calls'],
                'window_seconds': limit_info['window']
            }
        
        return status


# Global Twitter API instance
twitter_api = TwitterAPI()