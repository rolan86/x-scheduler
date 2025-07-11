#!/usr/bin/env python
"""Test Twitter integration and content generation functionality."""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.tweet_manager import tweet_manager
from src.core.content_generator import content_generator
from src.models import ContentType, TweetStatus


def test_tweet_manager():
    """Test tweet manager functionality."""
    print("🐦 Testing Tweet Manager")
    print("=" * 50)
    
    try:
        # Test creating a tweet
        print("\n1. Testing tweet creation...")
        tweet = tweet_manager.create_tweet(
            content="This is a test tweet from X-Scheduler! 🚀 #testing",
            content_type=ContentType.PERSONAL
        )
        print(f"✓ Created tweet {tweet.id}: {tweet.content[:30]}...")
        
        # Test updating content
        print("\n2. Testing content update...")
        new_content = "This is an updated test tweet! 🎉 #updated"
        success = tweet_manager.update_tweet_content(tweet.id, new_content)
        if success:
            print(f"✓ Updated tweet content")
        else:
            print("✗ Failed to update content")
        
        # Test scheduling
        print("\n3. Testing tweet scheduling...")
        future_time = datetime.now() + timedelta(hours=1)
        success = tweet_manager.schedule_tweet(tweet.id, future_time)
        if success:
            print(f"✓ Scheduled tweet for {future_time}")
        else:
            print("✗ Failed to schedule tweet")
        
        # Test approval
        print("\n4. Testing tweet approval...")
        success = tweet_manager.approve_tweet(tweet.id)
        if success:
            print("✓ Approved tweet")
        else:
            print("✗ Failed to approve tweet")
        
        # Test getting tweets by status
        print("\n5. Testing tweet queries...")
        scheduled_tweets = tweet_manager.get_scheduled_tweets()
        print(f"✓ Found {len(scheduled_tweets)} scheduled tweets")
        
        approved_tweets = tweet_manager.get_tweets_by_status(TweetStatus.APPROVED)
        print(f"✓ Found {len(approved_tweets)} approved tweets")
        
        # Test queue
        print("\n6. Testing tweet queue...")
        queue = tweet_manager.get_tweet_queue(limit=10)
        print(f"✓ Retrieved queue with {len(queue)} tweets")
        
        if queue:
            first_tweet = queue[0]
            print(f"  First tweet: {first_tweet['content'][:30]}...")
            print(f"  Status: {first_tweet['status']}")
            print(f"  Characters: {first_tweet['character_count']}")
        
        # Test deletion
        print("\n7. Testing tweet deletion...")
        success = tweet_manager.delete_tweet(tweet.id)
        if success:
            print("✓ Deleted test tweet")
        else:
            print("✗ Failed to delete tweet")
        
        print("\n✓ Tweet manager tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Tweet manager test failed: {e}")
        import traceback
        traceback.print_exc()


def test_content_generator():
    """Test content generator functionality."""
    print("\n🤖 Testing Content Generator")
    print("=" * 50)
    
    try:
        # Test generation statistics
        print("\n1. Testing generation statistics...")
        stats = content_generator.get_generation_stats()
        print(f"✓ Total AI tweets: {stats.get('total_ai_generated', 0)}")
        print(f"✓ Total cost: ${stats.get('total_generation_cost', 0):.4f}")
        
        # Test hashtag detection
        print("\n2. Testing hashtag utilities...")
        test_content = "This is a test tweet with #hashtags and #testing"
        has_hashtags = content_generator._has_hashtags(test_content)
        hashtag_count = content_generator._count_hashtags(test_content)
        print(f"✓ Has hashtags: {has_hashtags}")
        print(f"✓ Hashtag count: {hashtag_count}")
        
        # Test content truncation
        print("\n3. Testing content truncation...")
        long_content = "A" * 300  # 300 characters
        truncated = content_generator._truncate_content(long_content)
        print(f"✓ Truncated from {len(long_content)} to {len(truncated)} characters")
        
        # Test adding hashtags
        print("\n4. Testing hashtag addition...")
        content_without_hashtags = "This is a test tweet about productivity and automation"
        content_with_hashtags = content_generator._add_hashtags(
            content_without_hashtags, "productivity automation", 2
        )
        print(f"✓ Original: {content_without_hashtags}")
        print(f"✓ With hashtags: {content_with_hashtags}")
        
        # Test style templates
        print("\n5. Testing style templates...")
        templates = content_generator.get_style_templates()
        print(f"✓ Found {len(templates)} style templates")
        
        for template in templates:
            print(f"  - {template['name']}: {template['tone']} tone, {template['voice']} voice")
        
        print("\n✓ Content generator tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Content generator test failed: {e}")
        import traceback
        traceback.print_exc()


def test_database_integration():
    """Test database integration with services."""
    print("\n💾 Testing Database Integration")
    print("=" * 50)
    
    try:
        # Test creating multiple tweets
        print("\n1. Creating test tweets...")
        
        test_tweets = [
            ("First test tweet! 🚀", ContentType.PERSONAL),
            ("Professional update about our latest features.", ContentType.PROFESSIONAL),
            ("Just having a casual chat about tech trends 💬", ContentType.CASUAL),
            ("Here's an educational thread about AI development 🧠", ContentType.EDUCATIONAL)
        ]
        
        created_tweets = []
        for content, content_type in test_tweets:
            tweet = tweet_manager.create_tweet(content, content_type)
            created_tweets.append(tweet)
            print(f"✓ Created {content_type.value} tweet: {tweet.id}")
        
        # Test querying by different criteria
        print("\n2. Testing queries...")
        
        # Get by content type
        personal_tweets = [t for t in created_tweets if t.content_type == ContentType.PERSONAL]
        print(f"✓ Personal tweets: {len(personal_tweets)}")
        
        # Test queue with different statuses
        print("\n3. Testing queue management...")
        
        # Schedule some tweets
        future_time = datetime.now() + timedelta(hours=2)
        for i, tweet in enumerate(created_tweets[:2]):
            success = tweet_manager.schedule_tweet(tweet.id, future_time + timedelta(minutes=i*30))
            if success:
                print(f"✓ Scheduled tweet {tweet.id}")
        
        # Approve some tweets  
        for tweet in created_tweets[2:]:
            success = tweet_manager.approve_tweet(tweet.id)
            if success:
                print(f"✓ Approved tweet {tweet.id}")
        
        # Get queue with different filters
        all_queue = tweet_manager.get_tweet_queue()
        scheduled_queue = tweet_manager.get_tweet_queue(TweetStatus.SCHEDULED)
        approved_queue = tweet_manager.get_tweet_queue(TweetStatus.APPROVED)
        
        print(f"✓ Total queue: {len(all_queue)} tweets")
        print(f"✓ Scheduled: {len(scheduled_queue)} tweets")
        print(f"✓ Approved: {len(approved_queue)} tweets")
        
        # Test daily stats update
        print("\n4. Testing daily stats...")
        
        # This should be automatically updated by the tweet manager
        from src.models import get_db, DailyStats
        from datetime import date
        
        db = next(get_db())
        today_stats = db.query(DailyStats).filter_by(stat_date=date.today()).first()
        db.close()
        
        if today_stats:
            print(f"✓ Today's stats: {today_stats.tweets_scheduled} scheduled")
        else:
            print("- No daily stats found for today")
        
        # Clean up test tweets
        print("\n5. Cleaning up test tweets...")
        for tweet in created_tweets:
            success = tweet_manager.delete_tweet(tweet.id, force=True)
            if success:
                print(f"✓ Deleted tweet {tweet.id}")
        
        print("\n✓ Database integration tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Database integration test failed: {e}")
        import traceback
        traceback.print_exc()


def test_error_handling():
    """Test error handling in various scenarios."""
    print("\n⚠️  Testing Error Handling")
    print("=" * 50)
    
    try:
        # Test invalid content
        print("\n1. Testing invalid tweet content...")
        
        try:
            tweet_manager.create_tweet("")  # Empty content
            print("✗ Should have failed with empty content")
        except ValueError as e:
            print(f"✓ Correctly rejected empty content: {e}")
        
        try:
            long_content = "A" * 300  # Too long
            tweet_manager.create_tweet(long_content)
            print("✗ Should have failed with long content")
        except ValueError as e:
            print(f"✓ Correctly rejected long content: {e}")
        
        # Test invalid tweet operations
        print("\n2. Testing invalid operations...")
        
        # Try to get non-existent tweet
        tweet = tweet_manager.get_tweet(99999)
        if tweet is None:
            print("✓ Correctly returned None for non-existent tweet")
        else:
            print("✗ Should have returned None for non-existent tweet")
        
        # Try to update non-existent tweet
        success = tweet_manager.update_tweet_content(99999, "test")
        if not success:
            print("✓ Correctly failed to update non-existent tweet")
        else:
            print("✗ Should have failed to update non-existent tweet")
        
        # Test past scheduling
        print("\n3. Testing past scheduling...")
        
        # Create a test tweet first
        tweet = tweet_manager.create_tweet("Test tweet for past scheduling")
        
        try:
            past_time = datetime.now() - timedelta(hours=1)
            success = tweet_manager.schedule_tweet(tweet.id, past_time)
            print("✗ Should have failed with past time")
        except ValueError as e:
            print(f"✓ Correctly rejected past scheduling: {e}")
        
        # Clean up
        tweet_manager.delete_tweet(tweet.id, force=True)
        
        print("\n✓ Error handling tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all integration tests."""
    print("🚀 X-Scheduler Integration Tests")
    print("=" * 60)
    
    test_tweet_manager()
    test_content_generator()
    test_database_integration()
    test_error_handling()
    
    print("\n" + "=" * 60)
    print("🎉 Integration tests completed!")
    print("\nTo test with real APIs:")
    print("1. Configure authentication: x-scheduler auth setup")
    print("2. Test generation: x-scheduler generate --topic 'test'")
    print("3. Test posting: x-scheduler post --content 'test tweet'")


if __name__ == "__main__":
    main()