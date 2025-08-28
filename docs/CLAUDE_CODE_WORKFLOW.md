# Claude Code Integration Workflow

This document describes how to use X-Scheduler with Claude Code for content creation.

## Overview

X-Scheduler is designed to work seamlessly with Claude Code. Claude Code generates the tweet content, and X-Scheduler handles scheduling, posting, media generation, and applies proven viral hooks to boost engagement.

## Basic Workflow

### 1. Setup (One-time)

Import the high-performing hooks collection:

```bash
x-scheduler hooks import --file data/sample_hooks.json
```

### 2. Create a Tweet (Using Claude Code)

When Claude Code generates tweet content, save it to the database with optional viral hooks:

```bash
# Basic creation
x-scheduler create --content "Your tweet content here" --type personal

# With proven viral hooks for better engagement
x-scheduler create --content "Your content" --hook-type shock
x-scheduler create --content "Your content" --use-hook 5
x-scheduler create --content "Your content" --auto-hook
```

This returns a `TWEET_ID` that can be used for further operations.

### 3. Get Hook Suggestions (Optional)

Get suggestions for better engagement:

```bash
# Get hook suggestions for your topic
x-scheduler hooks suggest --topic "AI automation"

# Analyze existing tweet effectiveness
x-scheduler hooks analyze --tweet "Your tweet content"
```

### 4. Generate Media (Optional)

#### Generate an Image with DALL-E:
```bash
x-scheduler media generate-image --prompt "Beautiful sunset over mountains" --tweet-id 123
```

#### Generate a Video with Pollo.ai:
```bash
x-scheduler media generate-video --prompt "Time-lapse of coding" --duration 10 --tweet-id 123
```

### 5. Schedule or Post

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

### Example 1: Basic Tweet Creation

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

### Example 2: Using Viral Hooks for Maximum Engagement

```bash
# Step 1: Get hook suggestions
x-scheduler hooks suggest --topic "automation"

# Claude Code sees the suggestions:
# - Shock: "HOLY SH*T..🤯"
# - Authority: "I've cracked automation"
# - Results: "$47K monthly from automation"

# Step 2: Claude creates content with hook
x-scheduler create --content "I spent 153 hours building the ultimate automation system that saves me 40+ hours per week. Here's what I learned" --hook-type authority

# Output: TWEET_ID=456 with hook applied

# Step 3: Generate relevant image
x-scheduler media generate-image --prompt "clean workflow automation dashboard showing time saved metrics" --tweet-id 456

# Step 4: Post immediately for maximum impact
x-scheduler queue post --id 456
```

### Example 3: Hook Analysis and Optimization

```bash
# Step 1: Analyze existing content
x-scheduler hooks analyze --tweet "Here are some automation tips"

# Claude Code sees: Weak hook (2/10 strength)
# Suggestions: Add numbers, urgency, or emotional trigger

# Step 2: Claude creates improved version
x-scheduler create --content "5 automation tricks that save me $10K monthly (took years to figure out)" --hook-type results

# Output: Much stronger engagement potential

# Step 3: Preview different hooks
x-scheduler hooks preview --hook-id 1 --content "5 automation tricks that save me $10K monthly"
x-scheduler hooks preview --hook-id 7 --content "5 automation tricks that save me $10K monthly"

# Claude Code can choose the best performing version
```

## Quick Commands Reference

### Content Management
- `x-scheduler create --content "..."` - Save tweet to database
- `x-scheduler create --content "..." --hook-type shock` - Apply shock hook
- `x-scheduler create --content "..." --use-hook 5` - Apply specific hook
- `x-scheduler create --content "..." --auto-hook` - Auto-select best hook
- `x-scheduler queue list` - View all tweets
- `x-scheduler queue show --id 123` - View tweet details

### Hook Management
- `x-scheduler hooks import --file hooks.json` - Import hook collection
- `x-scheduler hooks suggest --topic "automation"` - Get hook suggestions
- `x-scheduler hooks analyze --tweet "content"` - Analyze tweet effectiveness
- `x-scheduler hooks preview --hook-id 5 --content "..."` - Preview hook application
- `x-scheduler hooks list --type shock` - List hooks by type

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

## Advanced Claude Code Integration Patterns

### 1. Hook-Aware Content Generation
Claude Code can now reference hook patterns when creating content:

```
User: "Create a tweet about our new Python library release"
Claude: "I'll use an authority hook to establish credibility and add urgency"
-> Uses: x-scheduler create --content "..." --hook-type authority
```

### 2. Hook Suggestion Workflow
Claude Code can analyze topics and suggest appropriate hooks:

```
User: "I want to tweet about AI automation"
Claude: "Let me find the best hooks for automation content"
-> Uses: x-scheduler hooks suggest --topic "automation"
Claude: "I recommend the 'results' hook pattern for this topic"
```

### 3. Content Optimization Loop
Claude Code can analyze and improve content iteratively:

```
Claude: "Let me analyze your current tweet"
-> Uses: x-scheduler hooks analyze --tweet "content"
Claude: "This has weak engagement potential. Let me apply a proven hook"
-> Uses: x-scheduler create --content "improved" --hook-type shock
```

### 4. Batch Hook Applications
Create multiple variations with different hooks:

```
Claude: "I'll create 3 versions with different hooks for A/B testing"
-> Creates shock, authority, and results versions
-> User can choose the best performing option
```

## Tips for Claude Code Integration

1. **Content Creation**: Let Claude Code handle all content generation with hook awareness
2. **Hook Selection**: Claude Code can intelligently choose hooks based on content and audience
3. **Media Prompts**: Claude Code can suggest DALL-E prompts that match hook patterns
4. **Scheduling**: Claude Code can suggest optimal posting times based on hook types
5. **Batch Operations**: Create multiple tweets with different hooks for testing
6. **Performance Tracking**: Use hook analytics to improve future content

## Cost Management

- Image generation: ~$0.04-0.08 per image (DALL-E 3)
- Video generation: ~$0.20-0.80 per video (Pollo.ai)
- No cost for tweet creation/posting (Twitter API free tier)

Use `x-scheduler stats` to monitor API usage and costs.