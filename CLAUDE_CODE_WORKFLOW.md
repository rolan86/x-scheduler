# Claude Code Integration Workflow

This document describes how to use X-Scheduler with Claude Code for content creation.

## Overview

X-Scheduler is designed to work seamlessly with Claude Code. Claude Code generates the tweet content, and X-Scheduler handles scheduling, posting, and media generation.

## Basic Workflow

### 1. Create a Tweet (Using Claude Code)

When Claude Code generates tweet content, save it to the database:

```bash
x-scheduler create --content "Your tweet content here" --type personal
```

This returns a `TWEET_ID` that can be used for further operations.

### 2. Generate Media (Optional)

#### Generate an Image with DALL-E:
```bash
x-scheduler media generate-image --prompt "Beautiful sunset over mountains" --tweet-id 123
```

#### Generate a Video with Pollo.ai:
```bash
x-scheduler media generate-video --prompt "Time-lapse of coding" --duration 10 --tweet-id 123
```

### 3. Schedule or Post

#### Schedule for later:
```bash
x-scheduler schedule --content "Your tweet" --time "2025-07-11 10:00"
```

#### Post immediately:
```bash
x-scheduler post --content "Your tweet"
```

#### Post from queue:
```bash
x-scheduler queue post --id 123
```

## Complete Example with Claude Code

```bash
# Step 1: Claude Code generates content
# You: "Create a tweet about the benefits of automation"
# Claude Code: "Here's a tweet about automation benefits..."

# Step 2: Save the tweet
x-scheduler create --content "Automation isn't about replacing humans, it's about amplifying human potential. When we automate repetitive tasks, we free our minds for creativity, strategy, and meaningful connections. 🚀 #Productivity #Automation"

# Output: TWEET_ID=123

# Step 3: Generate an image (optional)
x-scheduler media generate-image --prompt "futuristic office with robots and humans working together harmoniously" --tweet-id 123

# Step 4: Schedule the tweet
x-scheduler queue approve --id 123
x-scheduler queue post --id 123
```

## Quick Commands Reference

### Content Management
- `x-scheduler create --content "..."` - Save tweet to database
- `x-scheduler queue list` - View all tweets
- `x-scheduler queue show --id 123` - View tweet details

### Media Generation
- `x-scheduler media generate-image --prompt "..."` - Generate image
- `x-scheduler media generate-video --prompt "..."` - Generate video
- `x-scheduler media attach --tweet-id 123 --file image.jpg` - Attach existing media

### Posting
- `x-scheduler post --content "..."` - Post immediately
- `x-scheduler queue post --id 123` - Post from queue
- `x-scheduler queue approve --id 123` - Approve for posting

### Queue Management
- `x-scheduler queue list --status draft` - View drafts
- `x-scheduler queue delete --id 123` - Delete tweet

## Environment Variables for Claude Code

When using X-Scheduler in scripts, these environment variables are output:
- `TWEET_ID` - After creating a tweet
- `IMAGE_PATH` - After generating an image
- `VIDEO_PATH` - After generating a video

## Tips for Claude Code Integration

1. **Content Creation**: Let Claude Code handle all content generation
2. **Media Prompts**: Claude Code can suggest DALL-E prompts based on tweet content
3. **Scheduling**: Claude Code can suggest optimal posting times
4. **Batch Operations**: Create multiple tweets and schedule them in sequence

## Cost Management

- Image generation: ~$0.04-0.08 per image (DALL-E 3)
- Video generation: ~$0.20-0.80 per video (Pollo.ai)
- No cost for tweet creation/posting (Twitter API free tier)

Use `x-scheduler stats` to monitor API usage and costs.