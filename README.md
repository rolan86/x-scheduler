# X-Scheduler: Twitter/X Content Scheduler & Poster

A command-line application designed to work with Claude Code for Twitter/X content creation and scheduling. The tool handles scheduling, posting, and media generation while you use Claude Code to create the actual tweet content.

## Features

- 🤖 **Claude Code Integration**: Use Claude Code for content creation, X-Scheduler for posting
- 🎣 **High-Performing Hooks**: Apply proven viral tweet patterns to boost engagement
- 📅 **Flexible Scheduling**: Manual and automated posting with queue management
- 🎨 **Media Generation**: Images with DALL-E 3, videos with Pollo.ai
- 📊 **Analytics Tracking**: Monitor posting consistency and follower growth
- 💰 **Cost Monitoring**: Track API usage and costs with budget alerts
- 🔐 **Secure Storage**: Encrypted API key storage
- 📝 **Queue Management**: Review, approve, and schedule content

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Twitter/X Developer Account with API access
- OpenAI API key (for image generation)
- Pollo.ai API key (optional, for video generation)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/x-scheduler.git
cd x-scheduler
```

2. **Create and activate a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install the package:**
```bash
pip install -e .
```

4. **Initialize the application:**
```bash
x-scheduler init
```

5. **Set up your API credentials:**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys (see Configuration section below)
nano .env  # or use your preferred editor
```

### Basic Workflow with Claude Code

1. **Import high-performing tweet hooks (one-time setup):**
```bash
x-scheduler hooks import --file data/sample_hooks.json
```

2. **Use Claude Code to generate tweet content**

3. **Save the content with X-Scheduler (optionally with hooks):**
```bash
# Basic creation
x-scheduler create --content "Your tweet content here" --type personal

# With proven viral hooks
x-scheduler create --content "Your content" --hook-type shock
x-scheduler create --content "Your content" --use-hook 5
x-scheduler create --content "Your content" --auto-hook
# Returns: TWEET_ID=123
```

4. **Get hook suggestions for better engagement:**
```bash
x-scheduler hooks suggest --topic "AI automation"
x-scheduler hooks analyze --tweet "Your existing tweet"
```

5. **Add media (optional):**
```bash
# Generate an image
x-scheduler media generate-image --prompt "Beautiful sunset over mountains" --tweet-id 123

# Or generate a video
x-scheduler media generate-video --prompt "Time-lapse of coding" --tweet-id 123
```

6. **Schedule or post:**
```bash
# Schedule for later
x-scheduler schedule --content "Your tweet" --time "2025-07-11 10:00"

# Or post immediately
x-scheduler queue post --id 123

# Or post immediately with content
x-scheduler post --content "Immediate tweet content"
```

7. **Manage your queue:**
```bash
# View all scheduled posts
x-scheduler queue list

# View specific tweet details
x-scheduler queue show --id 123

# Approve tweets for posting
x-scheduler queue approve --id 123
```

## Configuration

### API Setup Guide

#### 1. Twitter/X Developer Account

1. **Apply for Developer Access:**
   - Go to [developer.twitter.com](https://developer.twitter.com)
   - Apply for a developer account (may take 1-2 days for approval)
   - Create a new app in the developer portal

2. **Get API Keys:**
   - Navigate to your app's "Keys and tokens" tab
   - Generate API Key and Secret
   - Generate Access Token and Secret
   - Set permissions to "Read and Write"

#### 2. OpenAI API Key

1. **Create OpenAI Account:**
   - Go to [platform.openai.com](https://platform.openai.com)
   - Create an account and add billing information
   - Navigate to API Keys section
   - Create a new API key

#### 3. Pollo.ai API Key (Optional)

1. **Sign up for Pollo.ai:**
   - Visit [pollo.ai](https://pollo.ai) and create an account
   - Get your API key from the dashboard

### Environment Configuration

Create a `.env` file in the project root:

```env
# Twitter/X API Credentials (Required)
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here

# OpenAI API (Required for image generation)
OPENAI_API_KEY=your_openai_api_key_here

# Pollo.ai API (Optional for video generation)
POLLO_API_KEY=your_pollo_api_key_here

# Application Settings
DAILY_POST_TARGET=2
BUDGET_LIMIT_MONTHLY=50.00
LOG_LEVEL=INFO
DATA_DIR=./data
MEDIA_DIR=./data/media
```

### Authentication Setup

After adding your API keys to `.env`, set them up in the application:

```bash
# Set up Twitter authentication
x-scheduler auth setup twitter

# Set up OpenAI authentication  
x-scheduler auth setup openai

# Set up Pollo.ai authentication (optional)
x-scheduler auth setup pollo

# Verify all authentications
x-scheduler auth status
```

## High-Performing Tweet Hooks

X-Scheduler includes a library of proven viral tweet patterns that can boost engagement by 3-10x. These hooks are based on tweets with 100K+ views.

### Hook Pattern Types

- **Shock/Intrigue**: "HOLY SH*T..🤯", "This is INSANE..."
- **Value Giveaway**: "Comment 'X' and I'll send you...", "FREE for next 24hrs"
- **Authority**: "I've cracked X", "After 153 hours building..."
- **Results/Numbers**: "$47K monthly", "600 → 6k followers in 13 days"
- **Contrarian**: "Stop doing X", "Forget building a brand"
- **Insider**: "They asked me not to share", "Nobody talks about..."
- **Lists**: "10 X that Y", "Here are 3 hidden AI websites"
- **Questions**: "Why does nobody talk about...?"

### Hook Commands

```bash
# Import your viral hooks collection
x-scheduler hooks import --file data/sample_hooks.json

# View available hooks
x-scheduler hooks list --type shock --min-views 100000

# Get hook suggestions for your topic
x-scheduler hooks suggest --topic "AI automation"

# Analyze tweet effectiveness
x-scheduler hooks analyze --tweet "Your tweet content"

# Preview how a hook would look
x-scheduler hooks preview --hook-id 5 --content "Your content"

# View hook performance
x-scheduler hooks performance --top 10

# Create content with hooks
x-scheduler create --content "Your tweet" --hook-type value_giveaway
x-scheduler create --content "Your tweet" --use-hook 12
x-scheduler create --content "Your tweet" --auto-hook
```

## Complete Command Reference

### Content Management
```bash
# Create a tweet (for use with Claude Code)
x-scheduler create --content "Your tweet content" --type personal

# Schedule a tweet for later
x-scheduler schedule --content "Your tweet" --time "2025-07-11 15:30"

# Post immediately
x-scheduler post --content "Immediate tweet" --media /path/to/image.jpg
```

### Queue Management
```bash
# List all tweets in queue
x-scheduler queue list

# List by status
x-scheduler queue list --status scheduled
x-scheduler queue list --status draft
x-scheduler queue list --status approved

# Show detailed tweet information
x-scheduler queue show --id 123

# Approve a tweet for posting
x-scheduler queue approve --id 123

# Post a tweet from queue
x-scheduler queue post --id 123

# Delete a tweet from queue
x-scheduler queue delete --id 123
```

### Media Generation
```bash
# Generate image with DALL-E
x-scheduler media generate-image --prompt "Beautiful landscape" --tweet-id 123

# Generate video with Pollo.ai
x-scheduler media generate-video --prompt "Time-lapse coding" --duration 10 --tweet-id 123

# Attach existing media file
x-scheduler media attach --tweet-id 123 --file /path/to/media.jpg

# List media files
x-scheduler media list
x-scheduler media list --tweet-id 123
```

### Authentication & Setup
```bash
# Initialize application
x-scheduler init

# Set up API authentication
x-scheduler auth setup twitter
x-scheduler auth setup openai
x-scheduler auth setup pollo

# Check authentication status
x-scheduler auth status

# Test API connections
x-scheduler auth test twitter
x-scheduler auth test openai
```

### Analytics & Monitoring
```bash
# View posting statistics
x-scheduler stats --period today
x-scheduler stats --period week
x-scheduler stats --period month
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors:**
   ```bash
   # Make sure you're in the virtual environment
   source venv/bin/activate
   
   # Reinstall the package
   pip install -e .
   ```

2. **Twitter API authentication errors:**
   ```bash
   # Verify your API keys in .env
   x-scheduler auth status
   
   # Re-setup Twitter authentication
   x-scheduler auth setup twitter
   ```

3. **Database errors:**
   ```bash
   # Reinitialize the database
   x-scheduler init
   ```

4. **Media generation failures:**
   ```bash
   # Check API key configuration
   x-scheduler auth test openai
   
   # Verify media directory permissions
   ls -la data/media/
   ```

### Getting Help

```bash
# Get help for any command
x-scheduler --help
x-scheduler create --help
x-scheduler queue --help
x-scheduler media generate-image --help
```

## API Limits & Costs

### Twitter/X Free Tier
- **50 tweets per day**
- **1,500 tweets per month**
- **Rate limit**: 1 tweet per 5 minutes during peak hours

### OpenAI Pricing (Image Generation)
- **DALL-E 3 Standard**: ~$0.040 per image
- **DALL-E 3 HD**: ~$0.080 per image
- Images are 1024x1024 by default

### Pollo.ai Pricing (Video Generation)
- **Standard quality**: ~$0.20-0.40 per video
- **HD quality**: ~$0.40-0.80 per video
- **4K quality**: ~$0.80-1.20 per video

### Cost Management
```bash
# Monitor your spending
x-scheduler stats --period month

# Set monthly budget limits in .env
BUDGET_LIMIT_MONTHLY=50.00
```

## Integration with Claude Code

X-Scheduler is designed to work seamlessly with Claude Code. Here's the typical workflow:

1. **Ask Claude Code to generate tweet content** about your topic
2. **Claude Code creates the tweet** and uses X-Scheduler to save it
3. **Claude Code can suggest and generate media** using the media commands
4. **Claude Code schedules or posts** the tweet using the queue commands

See [CLAUDE_CODE_WORKFLOW.md](docs/CLAUDE_CODE_WORKFLOW.md) for detailed integration examples.

## Development

### Setting up for development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
python3 tests/test_integration.py

# Run linting
ruff check .
black --check .

# Run type checking  
mypy src
```

### Project Structure

```
x-scheduler/
├── src/
│   ├── cli/              # Command-line interface
│   │   ├── main.py       # Main CLI commands
│   │   ├── auth_commands.py    # Authentication commands  
│   │   └── media_commands.py   # Media generation commands
│   ├── core/             # Core business logic
│   │   ├── tweet_manager.py    # Tweet lifecycle management
│   │   ├── content_generator.py # AI content generation
│   │   ├── config.py     # Configuration management
│   │   └── database.py   # Database initialization
│   ├── api/              # External API integrations
│   │   ├── twitter.py    # Twitter/X API client
│   │   ├── openai_client.py # OpenAI API client
│   │   ├── pollo.py      # Pollo.ai API client
│   │   └── auth.py       # Authentication manager
│   ├── models/           # Database models
│   │   └── __init__.py   # SQLAlchemy models
│   └── utils/            # Utility functions
├── data/                 # Local storage
│   ├── scheduler.db      # SQLite database
│   └── media/            # Generated media files
├── docs/                 # Documentation
│   ├── CLAUDE_CODE_WORKFLOW.md # Claude Code integration guide
│   ├── SETUP_GUIDE.md    # Detailed setup instructions
│   └── PRD.md            # Product Requirements Document
├── tests/                # Test files
│   ├── test_integration.py # Integration tests
│   └── test_*.py         # Other test files
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Quick Reference Card

### Essential Commands
```bash
# Setup
x-scheduler init
x-scheduler auth setup twitter
x-scheduler auth setup openai

# Daily workflow with Claude Code
x-scheduler create --content "tweet content"     # Save tweet (returns TWEET_ID)
x-scheduler media generate-image --prompt "..."  # Optional: Add image  
x-scheduler queue post --id 123                  # Post immediately
x-scheduler queue list                            # Check queue status

# Emergency commands
x-scheduler post --content "urgent tweet"        # Post without saving to queue
x-scheduler queue delete --id 123 --force        # Delete any tweet
x-scheduler auth status                           # Check API connections
```

For more examples and advanced usage, see [CLAUDE_CODE_WORKFLOW.md](docs/CLAUDE_CODE_WORKFLOW.md).