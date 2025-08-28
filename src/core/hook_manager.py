"""Manager for handling tweet hooks and patterns."""

import json
import logging
import random
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from src.models import (
    HookTemplate, HookUsage, HookCategory, 
    HookPatternType, Tweet, TweetStatus, get_db
)

logger = logging.getLogger(__name__)


class HookManager:
    """Manages tweet hooks and pattern matching."""
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize hook manager."""
        if session:
            self.session = session
        else:
            # Get a new database session
            self.session = next(get_db())
    
    def import_hooks(self, file_path: str, format: str = 'json') -> int:
        """Import hooks from a file.
        
        Args:
            file_path: Path to the hooks file
            format: File format ('json', 'csv', 'txt')
            
        Returns:
            Number of hooks imported
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if format == 'json':
            return self._import_json_hooks(path)
        elif format == 'txt':
            return self._import_text_hooks(path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _import_json_hooks(self, path: Path) -> int:
        """Import hooks from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported = 0
        hooks = data if isinstance(data, list) else data.get('hooks', [])
        
        for hook_data in hooks:
            try:
                hook = HookTemplate(
                    pattern_type=hook_data.get('pattern_type', 'custom'),
                    name=hook_data.get('name', ''),
                    hook_text=hook_data.get('hook_text', ''),
                    example_tweet=hook_data.get('example_tweet', ''),
                    structure_notes=hook_data.get('structure_notes', ''),
                    performance_metrics=hook_data.get('performance_metrics', {}),
                    min_views=hook_data.get('min_views', 0),
                    avg_engagement_rate=hook_data.get('avg_engagement_rate', 0.0),
                    tags=hook_data.get('tags', []),
                    use_cases=hook_data.get('use_cases', []),
                    target_audience=hook_data.get('target_audience', ''),
                    source=hook_data.get('source', str(path))
                )
                self.session.add(hook)
                imported += 1
            except Exception as e:
                logger.error(f"Failed to import hook: {e}")
        
        self.session.commit()
        logger.info(f"Imported {imported} hooks from {path}")
        return imported
    
    def _import_text_hooks(self, path: Path) -> int:
        """Import hooks from text file with examples."""
        content = path.read_text(encoding='utf-8')
        
        # Parse text file with pattern recognition
        imported = 0
        current_hook = None
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('—') or not line:
                if current_hook and current_hook.get('example_tweet'):
                    # Save the current hook
                    self._save_hook_from_text(current_hook)
                    imported += 1
                current_hook = None if line.startswith('—') else current_hook
            elif current_hook is None:
                # Start new hook
                current_hook = {'example_tweet': line}
            else:
                # Continue current hook
                current_hook['example_tweet'] += '\n' + line
        
        # Save last hook if exists
        if current_hook and current_hook.get('example_tweet'):
            self._save_hook_from_text(current_hook)
            imported += 1
        
        self.session.commit()
        logger.info(f"Imported {imported} hooks from {path}")
        return imported
    
    def _save_hook_from_text(self, hook_data: Dict[str, str]) -> None:
        """Save a hook parsed from text."""
        tweet_text = hook_data['example_tweet']
        
        # Analyze the tweet to determine pattern type
        pattern_type = self._detect_pattern_type(tweet_text)
        
        # Extract hook (first line or attention-grabbing part)
        lines = tweet_text.split('\n')
        hook_text = lines[0] if lines else tweet_text[:100]
        
        hook = HookTemplate(
            pattern_type=pattern_type,
            name=f"{pattern_type} hook",
            hook_text=hook_text,
            example_tweet=tweet_text,
            tags=self._extract_tags(tweet_text),
            source='text_import'
        )
        self.session.add(hook)
    
    def _detect_pattern_type(self, text: str) -> str:
        """Detect the pattern type from tweet text."""
        text_lower = text.lower()
        
        if any(phrase in text_lower for phrase in ['comment', "i'll send", "i'll dm", 'repost']):
            return HookPatternType.VALUE_GIVEAWAY
        elif any(phrase in text_lower for phrase in ['holy', 'sh*t', 'insane', 'crazy', 'wtf']):
            return HookPatternType.SHOCK
        elif re.search(r'\$[\d,]+[kK]?|\d+[kK]\s*(monthly|per|/)', text):
            return HookPatternType.RESULTS
        elif any(phrase in text_lower for phrase in ["i've cracked", "i've built", "i spent"]):
            return HookPatternType.AUTHORITY
        elif any(phrase in text_lower for phrase in ['asked me not to', 'secretly', 'nobody talks']):
            return HookPatternType.INSIDER
        elif re.search(r'\d+\s+\w+\s+that', text_lower):
            return HookPatternType.LIST
        elif any(phrase in text_lower for phrase in ['free for', 'next 24', 'limited time']):
            return HookPatternType.TIME_SENSITIVE
        elif text.startswith(('Why', 'How', 'What', 'When')):
            return HookPatternType.QUESTION
        else:
            return 'custom'
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from tweet text."""
        tags = []
        
        # Extract hashtags
        hashtags = re.findall(r'#(\w+)', text)
        tags.extend(hashtags)
        
        # Extract topic keywords
        keywords = {
            'AI': ['ai', 'chatgpt', 'claude', 'openai', 'llm'],
            'automation': ['automat', 'n8n', 'zapier', 'workflow'],
            'coding': ['code', 'coding', 'developer', 'programming'],
            'business': ['business', 'client', 'revenue', 'profit'],
            'viral': ['viral', 'views', 'million'],
        }
        
        text_lower = text.lower()
        for tag, patterns in keywords.items():
            if any(pattern in text_lower for pattern in patterns):
                tags.append(tag)
        
        return list(set(tags))
    
    def suggest_hooks(
        self, 
        topic: str = None,
        content_type: str = None,
        pattern_type: str = None,
        count: int = 3
    ) -> List[HookTemplate]:
        """Suggest hooks based on criteria.
        
        Args:
            topic: Topic to match against tags
            content_type: Type of content
            pattern_type: Specific pattern type to filter
            count: Number of hooks to return
            
        Returns:
            List of suggested hook templates
        """
        query = self.session.query(HookTemplate).filter(
            HookTemplate.is_active == True
        )
        
        if pattern_type:
            query = query.filter(HookTemplate.pattern_type == pattern_type)
        
        if topic:
            # Search in tags and use_cases
            topic_lower = topic.lower()
            hooks = query.all()
            
            # Score hooks by relevance
            scored_hooks = []
            for hook in hooks:
                score = 0
                
                # Check tags
                if hook.tags:
                    for tag in hook.tags:
                        if topic_lower in tag.lower():
                            score += 2
                
                # Check use cases
                if hook.use_cases:
                    for use_case in hook.use_cases:
                        if topic_lower in use_case.lower():
                            score += 1
                
                # Check example tweet
                if hook.example_tweet and topic_lower in hook.example_tweet.lower():
                    score += 0.5
                
                if score > 0:
                    scored_hooks.append((score, hook))
            
            # Sort by score and return top N
            scored_hooks.sort(key=lambda x: x[0], reverse=True)
            return [hook for _, hook in scored_hooks[:count]]
        else:
            # Return random high-performing hooks
            return query.order_by(desc(HookTemplate.avg_engagement_rate)).limit(count).all()
    
    def adapt_hook(self, hook_id: int, content: str, context: Dict[str, Any] = None) -> str:
        """Adapt a hook pattern to new content.
        
        Args:
            hook_id: ID of the hook template
            content: The main content to adapt
            context: Additional context (topic, product, etc.)
            
        Returns:
            Adapted content with hook applied
        """
        hook = self.session.query(HookTemplate).filter_by(id=hook_id).first()
        if not hook:
            raise ValueError(f"Hook {hook_id} not found")
        
        # Apply hook based on pattern type
        if hook.pattern_type == HookPatternType.VALUE_GIVEAWAY:
            return self._adapt_value_giveaway(hook, content, context)
        elif hook.pattern_type == HookPatternType.SHOCK:
            return self._adapt_shock_hook(hook, content, context)
        elif hook.pattern_type == HookPatternType.RESULTS:
            return self._adapt_results_hook(hook, content, context)
        elif hook.pattern_type == HookPatternType.LIST:
            return self._adapt_list_hook(hook, content, context)
        else:
            # Generic adaptation
            return f"{hook.hook_text}\n\n{content}"
    
    def _adapt_value_giveaway(self, hook: HookTemplate, content: str, context: Dict = None) -> str:
        """Adapt value giveaway pattern."""
        if context is None:
            context = {}
        action_word = context.get('action', 'comment')
        keyword = context.get('keyword', 'INFO')
        value_item = context.get('value', 'the guide')
        
        adapted = f"{content}\n\n"
        adapted += f"Want {value_item}?\n\n"
        adapted += f"👉 RT + Like & {action_word.capitalize()} \"{keyword}\" and I'll DM it to you\n\n"
        adapted += "(Must be following)"
        
        return adapted
    
    def _adapt_shock_hook(self, hook: HookTemplate, content: str, context: Dict = None) -> str:
        """Adapt shock/intrigue pattern."""
        if context is None:
            context = {}
        shock_phrases = [
            "HOLY SH*T..🤯",
            "This is INSANE...",
            "I can't believe this...",
            "Mind = BLOWN 🤯"
        ]
        
        intro = context.get('intro', random.choice(shock_phrases))
        return f"{intro}\n\n{content}"
    
    def _adapt_results_hook(self, hook: HookTemplate, content: str, context: Dict = None) -> str:
        """Adapt results/numbers pattern."""
        if context is None:
            context = {}
        result = context.get('result', '$10K monthly')
        timeframe = context.get('timeframe', 'in 30 days')
        
        return f"How I achieved {result} {timeframe}:\n\n{content}"
    
    def _adapt_list_hook(self, hook: HookTemplate, content: str, context: Dict = None) -> str:
        """Adapt list pattern."""
        if context is None:
            context = {}
        number = context.get('number', '10')
        item_type = context.get('item_type', 'tips')
        benefit = context.get('benefit', 'you need to know')
        
        return f"{number} {item_type} {benefit}:\n\n{content}"
    
    def analyze_tweet(self, content: str) -> Dict[str, Any]:
        """Analyze a tweet for hook patterns.
        
        Args:
            content: Tweet content to analyze
            
        Returns:
            Analysis results including detected patterns and suggestions
        """
        analysis = {
            'detected_pattern': self._detect_pattern_type(content),
            'has_hook': False,
            'hook_strength': 0,  # 0-10 scale
            'suggestions': [],
            'improvements': []
        }
        
        # Check if it starts with a hook
        first_line = content.split('\n')[0] if '\n' in content else content[:50]
        
        # Check for attention-grabbing elements
        attention_elements = {
            'caps': bool(re.search(r'[A-Z]{3,}', first_line)),
            'emoji': bool(re.search(r'[😀-🙏🌀-🗿🚀-🛿✂-➿]', first_line)),
            'numbers': bool(re.search(r'\d+', first_line)),
            'question': first_line.strip().endswith('?'),
            'exclamation': '!' in first_line,
        }
        
        # Calculate hook strength
        hook_strength = sum([
            attention_elements['caps'] * 2,
            attention_elements['emoji'] * 1,
            attention_elements['numbers'] * 2,
            attention_elements['question'] * 1.5,
            attention_elements['exclamation'] * 1,
        ])
        
        analysis['has_hook'] = hook_strength >= 3
        analysis['hook_strength'] = min(hook_strength, 10)
        analysis['attention_elements'] = attention_elements
        
        # Provide suggestions if weak hook
        if hook_strength < 5:
            analysis['improvements'].append("Consider starting with a stronger hook")
            analysis['improvements'].append("Add numbers or specific results")
            analysis['improvements'].append("Use attention-grabbing punctuation or emojis")
        
        # Suggest relevant hooks
        if not analysis['has_hook']:
            suggested_hooks = self.suggest_hooks(topic=content[:50], count=2)
            analysis['suggestions'] = [
                {'id': h.id, 'type': h.pattern_type, 'example': h.hook_text}
                for h in suggested_hooks
            ]
        
        return analysis
    
    def track_usage(
        self, 
        hook_id: int, 
        tweet_id: int,
        adapted_content: str = None,
        notes: str = None
    ) -> HookUsage:
        """Track hook usage for a tweet.
        
        Args:
            hook_id: ID of the hook used
            tweet_id: ID of the tweet
            adapted_content: The adapted content
            notes: Any adaptation notes
            
        Returns:
            HookUsage record
        """
        usage = HookUsage(
            hook_id=hook_id,
            tweet_id=tweet_id,
            adapted_content=adapted_content,
            adaptation_notes=notes,
            used_at=datetime.utcnow()
        )
        
        self.session.add(usage)
        self.session.commit()
        
        logger.info(f"Tracked hook {hook_id} usage for tweet {tweet_id}")
        return usage
    
    def get_hook_performance(self, hook_id: int) -> Dict[str, Any]:
        """Get performance statistics for a hook.
        
        Args:
            hook_id: ID of the hook
            
        Returns:
            Performance statistics
        """
        hook = self.session.query(HookTemplate).filter_by(id=hook_id).first()
        if not hook:
            return {}
        
        # Get usage statistics
        usages = self.session.query(HookUsage).filter_by(hook_id=hook_id).all()
        
        if not usages:
            return {
                'hook_id': hook_id,
                'total_uses': 0,
                'avg_performance': 0,
                'best_performance': 0,
                'pattern_type': hook.pattern_type
            }
        
        performances = [u.performance_score for u in usages if u.performance_score]
        
        return {
            'hook_id': hook_id,
            'total_uses': len(usages),
            'avg_performance': sum(performances) / len(performances) if performances else 0,
            'best_performance': max(performances) if performances else 0,
            'avg_engagement': sum([u.engagement_rate for u in usages if u.engagement_rate]) / len(usages),
            'pattern_type': hook.pattern_type,
            'tags': hook.tags
        }
    
    def list_hooks(
        self,
        pattern_type: str = None,
        min_views: int = None,
        tags: List[str] = None,
        limit: int = 20
    ) -> List[HookTemplate]:
        """List hooks with filters.
        
        Args:
            pattern_type: Filter by pattern type
            min_views: Minimum view count
            tags: Filter by tags
            limit: Maximum number of results
            
        Returns:
            List of hook templates
        """
        query = self.session.query(HookTemplate).filter(
            HookTemplate.is_active == True
        )
        
        if pattern_type:
            query = query.filter(HookTemplate.pattern_type == pattern_type)
        
        if min_views:
            query = query.filter(HookTemplate.min_views >= min_views)
        
        if tags:
            # Filter by tags (hooks that have any of the specified tags)
            hooks = query.all()
            filtered = []
            for hook in hooks:
                if hook.tags and any(tag in hook.tags for tag in tags):
                    filtered.append(hook)
            return filtered[:limit]
        
        return query.order_by(desc(HookTemplate.avg_engagement_rate)).limit(limit).all()
    
    def get_hook(self, hook_id: int) -> Optional[HookTemplate]:
        """Get a specific hook by ID."""
        return self.session.query(HookTemplate).filter_by(id=hook_id).first()
    
    def update_hook_performance(self, usage_id: int, performance_data: Dict[str, Any]) -> None:
        """Update performance data for a hook usage.
        
        Args:
            usage_id: ID of the hook usage
            performance_data: Performance metrics (views, likes, etc.)
        """
        usage = self.session.query(HookUsage).filter_by(id=usage_id).first()
        if not usage:
            return
        
        # Update usage performance
        usage.views = performance_data.get('views', 0)
        usage.likes = performance_data.get('likes', 0)
        usage.retweets = performance_data.get('retweets', 0)
        usage.replies = performance_data.get('replies', 0)
        
        # Calculate engagement rate
        if usage.views > 0:
            usage.engagement_rate = (
                (usage.likes + usage.retweets + usage.replies) / usage.views
            ) * 100
        
        # Calculate performance score (0-10)
        usage.performance_score = min(10, usage.engagement_rate * 2)
        
        # Update hook template statistics
        hook = usage.hook_template
        all_usages = self.session.query(HookUsage).filter_by(hook_id=hook.id).all()
        
        if all_usages:
            # Update average engagement rate
            engagement_rates = [u.engagement_rate for u in all_usages if u.engagement_rate]
            if engagement_rates:
                hook.avg_engagement_rate = sum(engagement_rates) / len(engagement_rates)
            
            # Update success rate (considers > 5% engagement as success)
            successful = len([u for u in all_usages if u.engagement_rate and u.engagement_rate > 5])
            hook.success_rate = successful / len(all_usages)
        
        self.session.commit()
        logger.info(f"Updated performance for hook usage {usage_id}")


def get_hook_manager(session: Optional[Session] = None) -> HookManager:
    """Get hook manager instance with proper session handling."""
    # Always create a new instance to ensure fresh database session
    return HookManager(session)