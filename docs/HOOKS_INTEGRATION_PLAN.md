# Hook Integration Implementation Plan

## Overview
Integrate a library of high-performing tweet hooks into X-Scheduler to help generate more engaging content while maintaining authenticity.

## Phase 1: Database & Models (Week 1)

### 1.1 Create Hook Models
```python
# src/models/hooks.py
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Float
from src.models.base import Base

class HookTemplate(Base):
    __tablename__ = 'hook_templates'
    
    id = Column(Integer, primary_key=True)
    pattern_type = Column(String(50))  # 'shock', 'value_prop', 'story', etc.
    hook_text = Column(Text)           # The hook pattern
    example_tweet = Column(Text)       # Full example
    performance_metrics = Column(JSON) # {'views': 100000, 'likes': 5000}
    tags = Column(JSON)                # ['AI', 'automation', 'viral']
    notes = Column(Text)               # Usage notes
    success_rate = Column(Float)       # Historical performance
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class HookUsage(Base):
    __tablename__ = 'hook_usage'
    
    id = Column(Integer, primary_key=True)
    hook_id = Column(Integer, ForeignKey('hook_templates.id'))
    tweet_id = Column(Integer, ForeignKey('tweets.id'))
    adaptation = Column(Text)
    performance_score = Column(Float)
    used_at = Column(DateTime)
```

### 1.2 Migration Script
```bash
# Add to database initialization
x-scheduler db migrate --add-hooks
```

## Phase 2: Hook Manager (Week 1)

### 2.1 Core Hook Manager
```python
# src/core/hook_manager.py
class HookManager:
    def __init__(self, db_session):
        self.session = db_session
        
    def import_hooks(self, file_path: str):
        """Import hooks from JSON/CSV file"""
        
    def suggest_hook(self, topic: str, style: str = None) -> List[HookTemplate]:
        """Suggest best hooks for topic"""
        
    def adapt_hook(self, hook_id: int, content: str) -> str:
        """Adapt hook pattern to new content"""
        
    def analyze_effectiveness(self, tweet: str) -> dict:
        """Analyze if tweet uses proven patterns"""
        
    def track_usage(self, hook_id: int, tweet_id: int):
        """Track which hooks are being used"""
```

## Phase 3: CLI Commands (Week 2)

### 3.1 Hook Management Commands
```python
# src/cli/hook_commands.py
@click.group()
def hooks():
    """Manage high-performing tweet hooks."""
    pass

@hooks.command()
@click.option('--file', required=True, help='Path to hooks file')
@click.option('--format', type=click.Choice(['json', 'csv', 'txt']))
def import_hooks(file, format):
    """Import hooks from file."""
    
@hooks.command()
@click.option('--type', help='Filter by pattern type')
@click.option('--min-views', type=int, help='Minimum view count')
@click.option('--tags', help='Filter by tags (comma-separated)')
def list(type, min_views, tags):
    """List available hooks."""
    
@hooks.command()
@click.option('--topic', required=True)
@click.option('--count', default=3)
def suggest(topic, count):
    """Suggest hooks for a topic."""
    
@hooks.command()
@click.option('--hook-id', required=True, type=int)
@click.option('--content', required=True)
def preview(hook_id, content):
    """Preview how a hook would look with your content."""
```

### 3.2 Enhanced Create Command
```python
# Update src/cli/main.py
@cli.command()
@click.option('--content', required=True)
@click.option('--use-hook', type=int, help='Hook ID to use')
@click.option('--hook-type', help='Type of hook to apply')
@click.option('--auto-hook', is_flag=True, help='Automatically select best hook')
def create(content, use_hook, hook_type, auto_hook):
    """Create tweet with optional hook enhancement."""
```

## Phase 4: Claude Code Integration (Week 2)

### 4.1 Hook-Aware Content Generation
```python
# src/core/content_generator.py enhancement
class ContentGenerator:
    def generate_with_hook(self, topic: str, hook_pattern: str = None):
        """Generate content using proven hook patterns"""
        
    def enhance_with_hook(self, content: str, hook_id: int):
        """Enhance existing content with hook"""
        
    def validate_hook_usage(self, content: str):
        """Check if hook is properly applied"""
```

### 4.2 Claude Code Prompts
Create prompt templates for Claude to use hooks effectively:
```
"Generate a tweet about {topic} using the {hook_type} pattern"
"Apply hook #{hook_id} to this content: {content}"
"Create a value giveaway tweet about {product}"
```

## Phase 5: Analytics & Optimization (Week 3)

### 5.1 Performance Tracking
```python
# Track which hooks perform best
x-scheduler hooks performance --period month
x-scheduler hooks top --limit 10
```

### 5.2 A/B Testing
```python
# Test different hooks for same content
x-scheduler test create --content "..." --hooks 1,5,9
x-scheduler test results --test-id 123
```

## Example Workflow

```bash
# 1. Import your high-performing hooks
x-scheduler hooks import --file viral_hooks.json

# 2. Find relevant hooks for your topic
x-scheduler hooks suggest --topic "AI automation"
# Output: 
# Hook #5: "HOLY SH*T..🤯" pattern (shock/intrigue)
# Hook #12: "Comment 'X' and I'll send" (value giveaway)
# Hook #18: "$X monthly from Y" (results/numbers)

# 3. Create content with hook
x-scheduler create --content "New AI workflow that replaces $50K employees" --use-hook 18

# 4. Or let Claude Code use it
# "Claude, create a tweet about n8n workflows using a value giveaway hook"
# Claude automatically:
# - Fetches relevant hooks
# - Adapts pattern to content
# - Creates engaging tweet
```

## Hook Categories to Implement

1. **Shock/Intrigue Hooks**
   - "HOLY SH*T..🤯"
   - "Nobody talks about this..."
   - "[Authority] asked me not to share this"

2. **Value Giveaway Hooks**
   - "Comment 'X' and I'll DM you..."
   - "FREE for next 24 hours"
   - "Worth $X, but free today"

3. **Authority/Expertise Hooks**
   - "I've cracked [topic]"
   - "After X hours/years of [activity]"
   - "[Product] is the best [category] and it's not close"

4. **Results/Numbers Hooks**
   - "$X monthly from Y"
   - "X to Y in Z days"
   - "X% increase in Y"

5. **Contrarian Hooks**
   - "Stop doing X"
   - "Forget X, do Y instead"
   - "Everyone's wrong about X"

6. **List/Resource Hooks**
   - "X [things] that [benefit]"
   - "The only X [resources] you need"
   - "X hidden [category] you must know"

## Success Metrics

- **Adoption Rate**: % of tweets using hooks
- **Performance Lift**: Average engagement increase with hooks
- **Hook Effectiveness**: Which patterns work best for which topics
- **User Satisfaction**: Ease of use and quality of suggestions

## Security & Ethics Considerations

1. **Authenticity**: Hooks should enhance, not replace genuine content
2. **Transparency**: Track which tweets use hooks for analysis
3. **Customization**: Always adapt hooks to maintain unique voice
4. **Moderation**: Flag potentially misleading patterns
5. **Performance**: Don't guarantee viral success

## Technical Requirements

- SQLAlchemy models for hook storage
- JSON import/export capability
- Pattern matching algorithms
- Performance tracking system
- Integration with existing tweet creation flow

## Timeline

- **Week 1**: Database schema, models, basic CRUD operations
- **Week 2**: CLI commands, Claude integration
- **Week 3**: Analytics, optimization, testing
- **Week 4**: Documentation, refinement, launch

## Future Enhancements

1. **ML-Based Suggestions**: Learn which hooks work for user's audience
2. **Automatic A/B Testing**: Test multiple hooks automatically
3. **Hook Evolution**: Track how hooks perform over time
4. **Custom Hook Creation**: Let users create their own patterns
5. **Industry-Specific Hooks**: Curated hooks for different niches