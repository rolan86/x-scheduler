# X-Scheduler: Twitter/X Content Scheduler & Poster with AI Enhancement

A command-line application that helps maintain consistent Twitter/X posting to grow follower base and drive sales opportunities. The tool combines AI-powered content generation, flexible scheduling, and media creation capabilities while staying within free API tier limits.

## Features

- 🤖 AI-powered content generation using OpenAI
- 📅 Flexible scheduling with manual and automated posting
- 🎨 Media generation (images with DALL-E, videos with Pollo.ai)
- 📊 Analytics tracking for posting consistency and follower growth
- 💰 API cost monitoring with budget alerts
- 🔐 Secure API key storage
- 📝 Document ingestion for style learning

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/x-scheduler.git
cd x-scheduler
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

4. Set up your API keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

```bash
# Generate content
x-scheduler generate --topic "AI productivity tools" --style personal

# Schedule a tweet
x-scheduler schedule --content "Your tweet content here" --time "2025-07-11 09:00"

# View scheduled posts
x-scheduler queue list

# Post immediately
x-scheduler post --content "Immediate tweet content"

# View analytics
x-scheduler stats --period week
```

## Configuration

Create a `.env` file in the project root with your API credentials:

```env
# Twitter/X API Credentials
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Pollo.ai API (optional)
POLLO_API_KEY=your_pollo_api_key

# Settings
DAILY_POST_TARGET=2
BUDGET_LIMIT_MONTHLY=50.00
```

## Development

### Setting up for development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

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
│   ├── cli/          # Command-line interface
│   ├── core/         # Core business logic
│   ├── api/          # External API integrations
│   ├── models/       # Database models
│   └── utils/        # Utility functions
├── tests/            # Test suite
├── docs/             # Documentation
└── data/             # Local storage for database and media
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_scheduler.py
```

## API Limits

- **Twitter/X Free Tier**: 50 tweets/day, 1,500/month
- **OpenAI**: Pay-per-use (monitor costs)
- **Pollo.ai**: Rate limits apply

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.