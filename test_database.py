#!/usr/bin/env python
"""Test database functionality."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.models import (
    get_db, init_db,
    Tweet, TweetStatus, ContentType,
    Media, MediaType, MediaSource,
    DailyStats, UserSettings, SettingCategory
)
from src.core.database import initialize_database, get_setting, update_setting


def test_database():
    """Test database operations."""
    print("Testing Database Functionality")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    initialize_database()
    print("✓ Database initialized")
    
    # Test settings
    print("\n2. Testing settings...")
    daily_target = get_setting(SettingCategory.POSTING, "daily_post_target", 2)
    print(f"✓ Daily post target: {daily_target}")
    
    # Update a setting
    update_setting(SettingCategory.POSTING, "daily_post_target", 3)
    new_target = get_setting(SettingCategory.POSTING, "daily_post_target")
    print(f"✓ Updated daily post target: {new_target}")
    
    # Test tweet creation
    print("\n3. Testing tweet creation...")
    db = next(get_db())
    
    try:
        tweet = Tweet(
            content="This is a test tweet from X-Scheduler! 🚀",
            content_type=ContentType.PERSONAL,
            scheduled_time=datetime.now() + timedelta(hours=1),
            status=TweetStatus.SCHEDULED,
            ai_generated=True,
            generation_prompt="Test prompt",
            generation_model="gpt-4"
        )
        db.add(tweet)
        db.commit()
        print(f"✓ Created tweet: {tweet}")
        
        # Test media creation
        print("\n4. Testing media creation...")
        media = Media(
            filename="test_image.png",
            file_path="/data/media/test_image.png",
            media_type=MediaType.IMAGE,
            media_source=MediaSource.DALL_E,
            generation_prompt="A beautiful sunset",
            generation_cost=0.02,
            tweet_id=tweet.id
        )
        db.add(media)
        db.commit()
        print(f"✓ Created media: {media}")
        
        # Test daily stats
        print("\n5. Testing daily stats...")
        today_stats = DailyStats(
            stat_date=datetime.now().date(),
            tweets_posted=5,
            tweets_scheduled=10,
            total_likes=50,
            total_retweets=20,
            followers_count=1000,
            followers_gained=10
        )
        db.add(today_stats)
        db.commit()
        print(f"✓ Created daily stats: {today_stats}")
        print(f"  Engagement rate: {today_stats.engagement_rate:.2f}%")
        
        # Query tweets
        print("\n6. Testing queries...")
        scheduled_tweets = db.query(Tweet).filter_by(status=TweetStatus.SCHEDULED).all()
        print(f"✓ Found {len(scheduled_tweets)} scheduled tweets")
        
        # Query settings
        all_settings = db.query(UserSettings).all()
        print(f"✓ Found {len(all_settings)} settings")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("Database tests completed successfully!")


if __name__ == "__main__":
    test_database()