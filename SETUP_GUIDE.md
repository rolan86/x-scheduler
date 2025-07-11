# X-Scheduler Setup Guide

Complete step-by-step setup instructions for X-Scheduler.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [API Configuration](#api-configuration)
4. [First-Time Setup](#first-time-setup)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python 3.9 or higher**
- **Git** (for cloning the repository)
- **Internet connection** (for API calls)

Check your Python version:
```bash
python3 --version
# Should output: Python 3.9.x or higher
```

### Required API Accounts

You'll need accounts and API keys for:

1. **Twitter/X Developer Account** (Required)
2. **OpenAI Account** (Required for image generation)
3. **Pollo.ai Account** (Optional for video generation)

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/x-scheduler.git
cd x-scheduler
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

### Step 3: Install Dependencies

```bash
# Install the package and all dependencies
pip install -e .

# Verify installation
x-scheduler --help
```

If you see the help output, installation was successful!

## API Configuration

### Twitter/X Developer Account Setup

#### 1. Apply for Developer Access

1. **Visit the Twitter Developer Portal:**
   - Go to [developer.twitter.com](https://developer.twitter.com)
   - Click "Sign up" if you don't have a developer account

2. **Apply for Access:**
   - Fill out the application form
   - Describe your use case: "Personal automation tool for scheduling Twitter posts"
   - Wait for approval (usually 1-2 days)

3. **Create a New App:**
   - After approval, go to the Developer Portal
   - Click "Create App"
   - Fill in app details:
     - **App name**: "X-Scheduler Personal"
     - **Description**: "Personal Twitter scheduling tool"
     - **Website**: Your personal website or GitHub profile
     - **Use case**: "Personal use"

#### 2. Generate API Keys

1. **Navigate to Keys and Tokens:**
   - Go to your app's dashboard
   - Click "Keys and tokens" tab

2. **Generate API Keys:**
   - **API Key and Secret**: Click "Generate" (save these)
   - **Access Token and Secret**: Click "Generate" (save these)
   - **Permissions**: Set to "Read and Write"

3. **Save Your Keys** (you'll need these in the next step):
   ```
   API Key: abcd1234...
   API Secret: xyz9876...
   Access Token: 1234567890-abc...
   Access Token Secret: def456...
   ```

### OpenAI API Setup

#### 1. Create OpenAI Account

1. **Visit OpenAI Platform:**
   - Go to [platform.openai.com](https://platform.openai.com)
   - Sign up for an account

2. **Add Billing Information:**
   - Go to "Billing" in your account settings
   - Add a payment method
   - Set usage limits if desired

3. **Generate API Key:**
   - Go to "API Keys" section
   - Click "Create new secret key"
   - Name it "X-Scheduler"
   - **Save the key** (you won't see it again): `sk-...`

### Pollo.ai API Setup (Optional)

1. **Visit Pollo.ai:**
   - Go to [pollo.ai](https://pollo.ai)
   - Create an account

2. **Get API Key:**
   - Navigate to your dashboard
   - Find the API section
   - Generate or copy your API key

## First-Time Setup

### Step 1: Initialize Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Edit the file with your API keys
nano .env  # or use any text editor
```

### Step 2: Configure Environment Variables

Edit `.env` with your API keys:

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

# Application Settings (Optional - defaults work fine)
DAILY_POST_TARGET=2
BUDGET_LIMIT_MONTHLY=50.00
LOG_LEVEL=INFO
DATA_DIR=./data
MEDIA_DIR=./data/media
```

### Step 3: Initialize the Application

```bash
# Initialize database and directories
x-scheduler init
```

You should see:
```
✓ Creating directories...
✓ Creating database...
✓ Created .env file
Initialization complete!
```

### Step 4: Set Up Authentication

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

## Verification

### Test Basic Functionality

```bash
# 1. Test creating a tweet
x-scheduler create --content "Testing X-Scheduler setup! 🚀 #test"

# You should see:
# ✓ Created tweet 1
# Content: Testing X-Scheduler setup! 🚀 #test
# Characters: 42/280
# Type: personal
# 
# Tweet ID: 1 - Use this ID for scheduling or posting
# 
# TWEET_ID=1

# 2. Test viewing the queue
x-scheduler queue list

# You should see your test tweet in the queue

# 3. Test API connections
x-scheduler auth test twitter
x-scheduler auth test openai

# You should see success messages
```

### Test Image Generation (Optional)

```bash
# Generate a test image
x-scheduler media generate-image --prompt "A beautiful sunset over mountains" --tweet-id 1

# You should see:
# ✓ Image generated successfully!
# Cost: $0.0400
# ✓ Image saved as: ./data/media/dalle_image_20250711_120000.png
# ✓ Image attached to tweet 1
# 
# IMAGE_PATH=./data/media/dalle_image_20250711_120000.png
```

### Clean Up Test Data

```bash
# Delete the test tweet
x-scheduler queue delete --id 1 --force
```

## Troubleshooting

### Common Issues

#### 1. "Module not found" Error

**Problem**: `ModuleNotFoundError: No module named 'click'`

**Solution**:
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -e .
```

#### 2. Twitter Authentication Failed

**Problem**: `HTTP 401: Unauthorized`

**Solutions**:
```bash
# Check your API keys in .env file
cat .env | grep TWITTER

# Verify permissions on Twitter Developer Portal
# - Go to your app settings
# - Ensure permissions are "Read and Write"
# - Regenerate keys if necessary

# Re-setup authentication
x-scheduler auth setup twitter
```

#### 3. OpenAI Authentication Failed

**Problem**: `HTTP 401: Invalid API key`

**Solutions**:
```bash
# Check your API key format
cat .env | grep OPENAI
# Should start with "sk-"

# Verify key on OpenAI platform
# - Go to platform.openai.com
# - Check API Keys section
# - Generate new key if necessary

# Re-setup authentication
x-scheduler auth setup openai
```

#### 4. Database Initialization Failed

**Problem**: `sqlite3.OperationalError: database is locked`

**Solutions**:
```bash
# Remove existing database and reinitialize
rm -f data/scheduler.db
x-scheduler init
```

#### 5. Permission Denied Errors

**Problem**: `PermissionError: [Errno 13] Permission denied`

**Solutions**:
```bash
# Check directory permissions
ls -la data/

# Create directories with proper permissions
mkdir -p data/media
chmod 755 data data/media

# Reinitialize
x-scheduler init
```

### Getting Help

1. **Check command help**:
   ```bash
   x-scheduler --help
   x-scheduler create --help
   ```

2. **Check authentication status**:
   ```bash
   x-scheduler auth status
   ```

3. **View log files** (if created):
   ```bash
   tail -f data/scheduler.log
   ```

4. **Test in verbose mode**:
   ```bash
   # Add LOG_LEVEL=DEBUG to .env file
   echo "LOG_LEVEL=DEBUG" >> .env
   ```

## Next Steps

Once setup is complete:

1. **Read the main README.md** for complete usage instructions
2. **Check out CLAUDE_CODE_WORKFLOW.md** for Claude Code integration examples
3. **Start creating content**:
   ```bash
   x-scheduler create --content "Your first real tweet!"
   x-scheduler queue list
   x-scheduler queue post --id [tweet-id]
   ```

## Success Checklist

- [ ] Python 3.9+ installed
- [ ] Repository cloned and virtual environment created
- [ ] Dependencies installed (`x-scheduler --help` works)
- [ ] Twitter Developer account approved and app created
- [ ] OpenAI account created with billing setup
- [ ] API keys added to `.env` file
- [ ] Application initialized (`x-scheduler init`)
- [ ] Authentication setup (`x-scheduler auth status` shows all green)
- [ ] Test tweet created and posted successfully
- [ ] Image generation tested (optional)

You're ready to use X-Scheduler with Claude Code! 🎉