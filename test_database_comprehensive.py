#!/usr/bin/env python
"""Comprehensive database testing script."""

import sys
from datetime import datetime, timedelta, date
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.sql import func

from src.models import *
from src.core.database import initialize_database, get_setting, update_setting, get_all_settings


def test_comprehensive():
    """Comprehensive database functionality test."""
    print("🚀 Comprehensive Database Test")
    print("=" * 60)
    
    # Initialize database first
    print("\n0. Initializing database...")
    initialize_database()
    print("✓ Database initialized")
    
    db = next(get_db())
    
    try:
        # Test 1: Settings Management
        print("\n1. Testing Settings Management...")
        settings = get_all_settings()
        print(f"✓ Loaded {len(settings)} setting categories")
        
        for category, items in settings.items():
            print(f"  - {category}: {len(items)} settings")
        
        # Test 2: Tweet Lifecycle
        print("\n2. Testing Tweet Lifecycle...")
        
        # Create draft tweet
        tweet = Tweet(
            content="Testing tweet lifecycle! This is a draft. #test",
            content_type=ContentType.PERSONAL,
            status=TweetStatus.DRAFT,
            ai_generated=True,
            generation_prompt="Create a test tweet",
            generation_model="gpt-4",
            generation_cost=0.01
        )
        db.add(tweet)
        db.commit()
        print(f"✓ Created draft tweet: ID {tweet.id}")
        
        # Update to scheduled
        tweet.status = TweetStatus.SCHEDULED
        tweet.scheduled_time = datetime.now() + timedelta(hours=2)
        db.commit()
        print(f"✓ Scheduled tweet for {tweet.scheduled_time}")
        
        # Simulate posting
        tweet.status = TweetStatus.POSTED
        tweet.posted_time = datetime.now()
        tweet.twitter_id = f"tweet_{tweet.id}_{int(datetime.now().timestamp())}"
        tweet.twitter_url = f"https://twitter.com/user/status/{tweet.twitter_id}"
        tweet.likes_count = 15
        tweet.retweets_count = 3
        tweet.replies_count = 2
        tweet.impressions_count = 500
        db.commit()
        print(f"✓ Posted tweet with engagement: {tweet.likes_count} likes, {tweet.retweets_count} RTs")
        
        # Test 3: Media Management
        print("\n3. Testing Media Management...")
        
        # AI-generated image
        image = Media(
            filename="ai_image.png",
            file_path="/data/media/ai_image.png",
            media_type=MediaType.IMAGE,
            media_source=MediaSource.DALL_E,
            width=1024,
            height=1024,
            generation_prompt="A futuristic city skyline at sunset",
            generation_model="dall-e-3",
            generation_cost=0.04,
            alt_text="Futuristic city skyline at sunset",
            tweet_id=tweet.id
        )
        db.add(image)
        
        # AI-generated video
        video = Media(
            filename="ai_video.mp4",
            file_path="/data/media/ai_video.mp4",
            media_type=MediaType.VIDEO,
            media_source=MediaSource.POLLO_AI,
            width=1920,
            height=1080,
            duration=10.5,
            generation_prompt="Time-lapse of coding session",
            generation_cost=0.25,
            tweet_id=tweet.id
        )
        db.add(video)
        db.commit()
        print(f"✓ Created media: {image.filename} and {video.filename}")
        
        # Test 4: API Usage Tracking
        print("\n4. Testing API Usage Tracking...")
        
        # OpenAI usage
        openai_usage = APIUsage(
            provider=APIProvider.OPENAI,
            endpoint=APIEndpoint.CHAT_COMPLETION,
            tokens_used=150,
            cost=0.01,
            request_metadata={"model": "gpt-4", "temperature": 0.7}
        )
        db.add(openai_usage)
        
        # Twitter usage
        twitter_usage = APIUsage(
            provider=APIProvider.TWITTER,
            endpoint=APIEndpoint.TWEET_CREATE,
            cost=0.0,
            response_metadata={"tweet_id": tweet.twitter_id}
        )
        db.add(twitter_usage)
        
        # DALL-E usage
        dalle_usage = APIUsage(
            provider=APIProvider.OPENAI,
            endpoint=APIEndpoint.DALL_E_GENERATION,
            cost=0.04,
            request_metadata={"size": "1024x1024", "quality": "standard"}
        )
        db.add(dalle_usage)
        db.commit()
        print("✓ Recorded API usage for OpenAI, Twitter, and DALL-E")
        
        # Test 5: Budget Management
        print("\n5. Testing Budget Management...")
        
        budgets = db.query(APIBudget).all()
        for budget in budgets:
            # Simulate spending
            if budget.provider == APIProvider.OPENAI:
                budget.current_spend = 15.50
                budget.request_count = 100
            elif budget.provider == APIProvider.POLLO_AI:
                budget.current_spend = 2.75
                budget.request_count = 3
            
            print(f"✓ {budget.provider}: ${budget.current_spend:.2f}/${budget.budget_limit:.2f} ({budget.usage_percentage:.1f}%)")
            
            if budget.should_alert:
                print(f"  ⚠️  Budget alert needed for {budget.provider}")
        
        db.commit()
        
        # Test 6: Analytics
        print("\n6. Testing Analytics...")
        
        # Create daily stats for the past week (skip today since it might exist)
        for i in range(1, 8):  # Start from yesterday
            stat_date = date.today() - timedelta(days=i)
            
            # Check if this date already exists
            existing_stat = db.query(DailyStats).filter_by(stat_date=stat_date).first()
            if existing_stat:
                print(f"✓ Day {i}: Using existing stats for {stat_date}")
                continue
            
            daily_stat = DailyStats(
                stat_date=stat_date,
                tweets_posted=2 + (i % 3),  # Varying daily posts
                tweets_scheduled=5,
                total_likes=25 + (i * 10),
                total_retweets=8 + (i * 3),
                total_replies=5 + (i * 2),
                total_impressions=1000 + (i * 200),
                followers_count=1000 + (i * 5),
                followers_gained=3 + (i % 2),
                followers_lost=1,
                api_calls_made=10 + i,
                api_cost=0.15 + (i * 0.05)
            )
            db.add(daily_stat)
            print(f"✓ Day {i}: {daily_stat.tweets_posted} tweets, {daily_stat.engagement_rate:.1f}% engagement")
        
        db.commit()
        
        # Test 7: Posting Patterns
        print("\n7. Testing Posting Patterns...")
        
        # Create posting pattern data
        patterns = [
            (9, 1, 12.5, 4.2, 2.1, 850),   # Monday 9am
            (17, 1, 18.3, 6.1, 3.2, 1200), # Monday 5pm
            (12, 3, 15.2, 5.5, 2.8, 950),  # Wednesday noon
            (20, 5, 22.1, 8.3, 4.5, 1400), # Friday 8pm
        ]
        
        for hour, day, likes, rts, replies, impressions in patterns:
            pattern = PostingPattern(
                hour=hour,
                day_of_week=day,
                avg_likes=likes,
                avg_retweets=rts,
                avg_replies=replies,
                avg_impressions=impressions,
                avg_engagement_rate=(likes + rts + replies) / impressions * 100,
                tweet_count=25
            )
            db.add(pattern)
        
        db.commit()
        print("✓ Created posting pattern analysis")
        
        # Test 8: Style Templates
        print("\n8. Testing Style Templates...")
        
        template = StyleTemplate(
            name="Casual Tech",
            description="Casual, friendly tech content with emojis",
            tone="conversational",
            voice="friendly",
            opening_patterns=["Hey everyone!", "Quick thought:", "Just discovered:"],
            closing_patterns=["What do you think?", "Let me know!", "Thoughts? 💭"],
            vocabulary_level="medium",
            use_emojis=True,
            emoji_frequency=0.3,
            hashtag_style="lowercase",
            example_tweets=["Hey everyone! Just discovered this amazing new tool 🚀 #productivity"]
        )
        db.add(template)
        db.commit()
        print(f"✓ Created style template: {template.name}")
        
        # Test 9: User Metrics
        print("\n9. Testing User Metrics...")
        
        metrics = [
            (MetricType.FOLLOWERS, 1005),
            (MetricType.FOLLOWING, 250),
            (MetricType.TWEETS, 142),
            (MetricType.ENGAGEMENT_RATE, 3.2),
        ]
        
        for metric_type, value in metrics:
            user_metric = UserMetrics(
                metric_type=metric_type,
                metric_value=value
            )
            db.add(user_metric)
        
        db.commit()
        print("✓ Recorded user metrics")
        
        # Test 10: Query Tests
        print("\n10. Testing Complex Queries...")
        
        # Tweet queries
        scheduled_tweets = db.query(Tweet).filter_by(status=TweetStatus.SCHEDULED).count()
        posted_tweets = db.query(Tweet).filter_by(status=TweetStatus.POSTED).count()
        ai_tweets = db.query(Tweet).filter_by(ai_generated=True).count()
        
        print(f"✓ Tweets: {scheduled_tweets} scheduled, {posted_tweets} posted, {ai_tweets} AI-generated")
        
        # Media queries
        ai_images = db.query(Media).filter_by(media_source=MediaSource.DALL_E).count()
        ai_videos = db.query(Media).filter_by(media_source=MediaSource.POLLO_AI).count()
        
        print(f"✓ Media: {ai_images} AI images, {ai_videos} AI videos")
        
        # Analytics queries
        total_api_cost = db.query(APIUsage).with_entities(func.sum(APIUsage.cost)).scalar() or 0
        avg_engagement = db.query(DailyStats).with_entities(func.avg(DailyStats.total_likes)).scalar() or 0
        
        print(f"✓ Analytics: ${total_api_cost:.4f} total API cost, {avg_engagement:.1f} avg likes")
        
        # Relationship tests
        tweet_with_media = db.query(Tweet).filter(Tweet.media_items.any()).first()
        if tweet_with_media:
            print(f"✓ Relationships: Tweet {tweet_with_media.id} has {len(tweet_with_media.media_items)} media items")
        
        print("\n" + "=" * 60)
        print("🎉 All database tests passed successfully!")
        print("=" * 60)
        
        # Summary
        print("\nDatabase Summary:")
        print(f"- Tweets: {db.query(Tweet).count()}")
        print(f"- Media: {db.query(Media).count()}")
        print(f"- Daily Stats: {db.query(DailyStats).count()}")
        print(f"- API Usage: {db.query(APIUsage).count()}")
        print(f"- Settings: {db.query(UserSettings).count()}")
        print(f"- Budgets: {db.query(APIBudget).count()}")
        print(f"- Patterns: {db.query(PostingPattern).count()}")
        print(f"- Templates: {db.query(StyleTemplate).count()}")
        print(f"- Metrics: {db.query(UserMetrics).count()}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_comprehensive()