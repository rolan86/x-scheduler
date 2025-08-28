# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Initialize the application database
x-scheduler init

# Import sample high-performing hooks
x-scheduler hooks import --file data/sample_hooks.json
```

### Testing
```bash
# Run all tests
python3 tests/test_integration.py

# Run specific test files
python3 tests/test_auth.py
python3 tests/test_database_comprehensive.py
```

### Code Quality
```bash
# Run linting
ruff check .

# Format code
black .

# Type checking
mypy src
```

## Architecture Overview

### Core Components

The application follows a layered architecture with clear separation of concerns:

1. **CLI Layer** (`src/cli/`): Command-line interface using Click
   - `main.py`: Entry point with core commands (create, schedule, post, queue, stats)
   - `auth_commands.py`: Authentication setup and management
   - `media_commands.py`: Media generation (DALL-E images, Pollo.ai videos)
   - `hook_commands.py`: High-performing tweet hooks management

2. **Core Business Logic** (`src/core/`):
   - `tweet_manager.py`: Handles tweet lifecycle, scheduling, and queue management
   - `hook_manager.py`: Manages viral tweet patterns and hook applications
   - `content_generator.py`: AI content generation (currently uses Claude Code integration)
   - `config.py`: Application configuration using Pydantic settings
   - `database.py`: SQLAlchemy database initialization and session management

3. **External APIs** (`src/api/`):
   - `twitter.py`: Twitter/X API client using Tweepy
   - `openai_client.py`: OpenAI DALL-E integration for image generation
   - `pollo.py`: Pollo.ai integration for video generation
   - `auth.py`: Centralized authentication manager with encryption

4. **Data Models** (`src/models/`):
   - SQLAlchemy ORM models for tweets, media, analytics, API usage tracking, and hooks
   - Uses SQLite database stored in `data/x_scheduler.db`

### Key Design Patterns

- **Manager Pattern**: `TweetManager`, `AuthManager`, and `HookManager` centralize business logic
- **Repository Pattern**: Database models abstract data access
- **Configuration Management**: Pydantic settings for type-safe configuration
- **Encrypted Storage**: API keys stored encrypted using Fernet symmetric encryption

### Integration Points

The application is designed for Claude Code integration:
1. Claude Code generates tweet content
2. X-Scheduler applies high-performing hooks to boost engagement
3. X-Scheduler stores content using `x-scheduler create`
4. Returns `TWEET_ID` for subsequent operations
5. Media can be generated and attached to tweets
6. Queue management for scheduling and posting
7. Hook suggestions and analysis for content optimization

### Database Schema

- **tweets**: Core tweet storage with content, status, scheduling
- **hook_templates**: High-performing tweet patterns and structures
- **hook_usage**: Track hook applications and their performance
- **media**: Generated media files linked to tweets
- **api_usage**: Track API calls and costs
- **analytics**: Tweet performance metrics
- **settings**: User preferences and authentication tokens

### Authentication Flow

1. API keys stored in `.env` file
2. `auth setup` commands encrypt and store credentials
3. `AuthManager` handles credential retrieval and decryption
4. All API clients initialized through centralized auth system

## Working with Media

Media files are stored in `data/media/` with subdirectories:
- `images/`: DALL-E generated images
- `videos/`: Pollo.ai generated videos
- `uploads/`: User-provided media files

## Common Tasks

### Adding a new CLI command
1. Add command function in appropriate file (`main.py`, `auth_commands.py`, or `media_commands.py`)
2. Use Click decorators for options and arguments
3. Call appropriate manager methods for business logic
4. Use Rich console for formatted output

### Modifying database schema
1. Update models in `src/models/`
2. Database uses SQLAlchemy with automatic schema creation
3. Consider migration strategy for existing databases

### Adding new API integration
1. Create new client in `src/api/`
2. Add authentication setup in `auth.py`
3. Update `auth_commands.py` for CLI setup command
4. Store credentials encrypted via `AuthManager`

## Working with Hooks

### Hook System Architecture

The hook system provides proven viral tweet patterns to boost engagement:

1. **HookTemplate**: Stores pattern structures with performance data
2. **HookManager**: Handles pattern matching and content adaptation
3. **HookUsage**: Tracks which hooks are used and their effectiveness

### Common Hook Tasks

#### Creating Content with Hooks
```bash
# Apply specific hook pattern
x-scheduler create --content "Your content" --hook-type shock
x-scheduler create --content "Your content" --use-hook 5
x-scheduler create --content "Your content" --auto-hook
```

#### Hook Management
```bash
# Import new hook collections
x-scheduler hooks import --file viral_hooks.json

# Suggest hooks for topic
x-scheduler hooks suggest --topic "AI automation"

# Analyze tweet effectiveness
x-scheduler hooks analyze --tweet "Your tweet content"

# View hook performance
x-scheduler hooks performance --top 10
```

### Adding New Hook Patterns

1. Add new patterns to JSON file with structure:
```json
{
  "pattern_type": "custom",
  "name": "Pattern Name",
  "hook_text": "The hook pattern",
  "example_tweet": "Full example...",
  "tags": ["relevant", "tags"],
  "performance_metrics": {"views": 100000, "engagement_rate": 5.0}
}
```

2. Import using `x-scheduler hooks import`

### Hook Pattern Types

- `shock`: Attention-grabbing intros
- `value_giveaway`: Engagement for value exchange
- `authority`: Expertise establishment
- `contrarian`: Challenge common beliefs
- `insider`: Share "secret" information
- `results`: Lead with impressive numbers
- `time_sensitive`: Create urgency
- `list`: Numbered resources/tips
- `question`: Engaging curiosity
- `story`: Personal narratives