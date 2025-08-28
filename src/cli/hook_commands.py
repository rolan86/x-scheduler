"""CLI commands for managing tweet hooks."""

import json
import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box

from src.core.hook_manager import get_hook_manager
from src.models import HookPatternType

console = Console()
logger = logging.getLogger(__name__)


@click.group()
def hooks():
    """Manage high-performing tweet hooks and patterns."""
    pass


@hooks.command('import')
@click.option('--file', '-f', required=True, type=click.Path(exists=True), help='Path to hooks file')
@click.option('--format', '-t', type=click.Choice(['json', 'txt']), default='json', help='File format')
def import_hooks(file: str, format: str):
    """Import hooks from a file.
    
    Supported formats:
    - JSON: Structured hook data with metadata
    - TXT: Raw tweet examples separated by dashes
    """
    try:
        manager = get_hook_manager()
        count = manager.import_hooks(file, format)
        
        console.print(f"[green]✓ Successfully imported {count} hooks from {file}[/green]")
        
        # Show summary of imported hooks
        hooks = manager.list_hooks(limit=5)
        if hooks:
            console.print("\n[bold]Recently imported hooks:[/bold]")
            for hook in hooks[:3]:
                console.print(f"  • {hook.pattern_type}: {hook.hook_text[:50]}...")
                
    except Exception as e:
        console.print(f"[red]Error importing hooks: {str(e)}[/red]")
        logger.error(f"Import error: {e}", exc_info=True)


@hooks.command('list')
@click.option('--type', '-t', 'pattern_type', help='Filter by pattern type (shock, value_giveaway, etc.)')
@click.option('--min-views', '-v', type=int, help='Minimum view count')
@click.option('--tags', '-g', help='Filter by tags (comma-separated)')
@click.option('--limit', '-l', default=20, help='Number of hooks to show')
def list_hooks(pattern_type: Optional[str], min_views: Optional[int], tags: Optional[str], limit: int):
    """List available hooks with filters."""
    try:
        manager = get_hook_manager()
        
        # Parse tags if provided
        tag_list = [t.strip() for t in tags.split(',')] if tags else None
        
        # Get hooks
        hooks = manager.list_hooks(
            pattern_type=pattern_type,
            min_views=min_views,
            tags=tag_list,
            limit=limit
        )
        
        if not hooks:
            console.print("[yellow]No hooks found matching criteria[/yellow]")
            return
        
        # Create table
        table = Table(title=f"Tweet Hooks ({len(hooks)} found)", box=box.ROUNDED)
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Type", style="magenta", width=15)
        table.add_column("Hook", style="white", width=50)
        table.add_column("Tags", style="blue", width=20)
        table.add_column("Views", style="green", width=10)
        table.add_column("Success", style="yellow", width=8)
        
        for hook in hooks:
            tags_str = ', '.join(hook.tags[:3]) if hook.tags else '-'
            views_str = f"{hook.min_views:,}" if hook.min_views else '-'
            success_str = f"{hook.success_rate:.1%}" if hook.success_rate else '-'
            
            table.add_row(
                str(hook.id),
                hook.pattern_type,
                hook.hook_text[:47] + "..." if len(hook.hook_text) > 50 else hook.hook_text,
                tags_str,
                views_str,
                success_str
            )
        
        console.print(table)
        console.print(f"\n[dim]Use 'x-scheduler hooks show --id ID' to see full details[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error listing hooks: {str(e)}[/red]")
        logger.error(f"List error: {e}", exc_info=True)


@hooks.command('show')
@click.option('--id', 'hook_id', required=True, type=int, help='Hook ID to display')
def show_hook(hook_id: int):
    """Show detailed information about a specific hook."""
    try:
        manager = get_hook_manager()
        hook = manager.get_hook(hook_id)
        
        if not hook:
            console.print(f"[red]Hook {hook_id} not found[/red]")
            return
        
        # Create info panel
        info = f"""[bold cyan]Hook #{hook.id}[/bold cyan]
[yellow]Type:[/yellow] {hook.pattern_type}
[yellow]Name:[/yellow] {hook.name or 'Unnamed'}
[yellow]Tags:[/yellow] {', '.join(hook.tags) if hook.tags else 'None'}
[yellow]Use Cases:[/yellow] {', '.join(hook.use_cases) if hook.use_cases else 'General'}
[yellow]Target Audience:[/yellow] {hook.target_audience or 'General'}"""
        
        # Performance metrics
        if hook.performance_metrics:
            metrics = hook.performance_metrics
            info += f"""

[bold]Performance Metrics:[/bold]
  • Views: {metrics.get('views', 'N/A'):,}
  • Likes: {metrics.get('likes', 'N/A'):,}
  • Engagement: {metrics.get('engagement_rate', 'N/A')}%"""
        
        console.print(Panel(info, title="Hook Details", border_style="cyan"))
        
        # Show hook pattern
        console.print(Panel(
            hook.hook_text,
            title="Hook Pattern",
            border_style="green"
        ))
        
        # Show example tweet if available
        if hook.example_tweet:
            console.print(Panel(
                hook.example_tweet,
                title="Example Tweet",
                border_style="blue"
            ))
        
        # Show structure notes if available
        if hook.structure_notes:
            console.print(Panel(
                hook.structure_notes,
                title="How to Use",
                border_style="yellow"
            ))
        
        # Get usage statistics
        performance = manager.get_hook_performance(hook_id)
        if performance['total_uses'] > 0:
            stats = f"""[yellow]Total Uses:[/yellow] {performance['total_uses']}
[yellow]Avg Performance:[/yellow] {performance['avg_performance']:.1f}/10
[yellow]Best Performance:[/yellow] {performance['best_performance']:.1f}/10
[yellow]Avg Engagement:[/yellow] {performance.get('avg_engagement', 0):.2f}%"""
            
            console.print(Panel(stats, title="Usage Statistics", border_style="magenta"))
        
    except Exception as e:
        console.print(f"[red]Error showing hook: {str(e)}[/red]")
        logger.error(f"Show error: {e}", exc_info=True)


@hooks.command('suggest')
@click.option('--topic', '-t', help='Topic or keyword to match')
@click.option('--type', 'pattern_type', help='Specific pattern type')
@click.option('--count', '-c', default=3, help='Number of suggestions')
def suggest_hooks(topic: Optional[str], pattern_type: Optional[str], count: int):
    """Suggest hooks for your content."""
    try:
        manager = get_hook_manager()
        
        suggestions = manager.suggest_hooks(
            topic=topic,
            pattern_type=pattern_type,
            count=count
        )
        
        if not suggestions:
            console.print("[yellow]No matching hooks found. Try different keywords.[/yellow]")
            return
        
        console.print(f"[bold green]Top {len(suggestions)} Hook Suggestions:[/bold green]\n")
        
        for i, hook in enumerate(suggestions, 1):
            # Create suggestion panel
            content = f"""[cyan]Type:[/cyan] {hook.pattern_type}
[cyan]Hook:[/cyan] {hook.hook_text}
[cyan]Tags:[/cyan] {', '.join(hook.tags[:5]) if hook.tags else 'None'}"""
            
            if hook.example_tweet:
                # Show truncated example
                example = hook.example_tweet[:200] + "..." if len(hook.example_tweet) > 200 else hook.example_tweet
                content += f"\n\n[dim]Example:[/dim]\n{example}"
            
            console.print(Panel(
                content,
                title=f"Suggestion #{i} (ID: {hook.id})",
                border_style="green" if i == 1 else "blue"
            ))
            console.print()
        
        console.print("[dim]Use 'x-scheduler create --content \"...\" --use-hook ID' to apply a hook[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error suggesting hooks: {str(e)}[/red]")
        logger.error(f"Suggest error: {e}", exc_info=True)


@hooks.command('analyze')
@click.option('--tweet', '-t', 'content', required=True, help='Tweet content to analyze')
def analyze_tweet(content: str):
    """Analyze a tweet for hook effectiveness."""
    try:
        manager = get_hook_manager()
        analysis = manager.analyze_tweet(content)
        
        # Display analysis results
        console.print(Panel.fit(
            f"[bold]Hook Analysis Results[/bold]",
            border_style="cyan"
        ))
        
        # Hook detection
        if analysis['has_hook']:
            console.print(f"[green]✓ Hook detected![/green] Pattern type: [cyan]{analysis['detected_pattern']}[/cyan]")
            console.print(f"Hook strength: [yellow]{'█' * int(analysis['hook_strength'])}{'░' * (10 - int(analysis['hook_strength']))}[/yellow] {analysis['hook_strength']:.1f}/10")
        else:
            console.print(f"[red]✗ No strong hook detected[/red]")
            console.print(f"Hook strength: [red]{'█' * int(analysis['hook_strength'])}{'░' * (10 - int(analysis['hook_strength']))}[/red] {analysis['hook_strength']:.1f}/10")
        
        # Attention elements
        console.print("\n[bold]Attention Elements:[/bold]")
        elements = analysis['attention_elements']
        for element, present in elements.items():
            symbol = "✓" if present else "✗"
            color = "green" if present else "dim"
            console.print(f"  [{color}]{symbol}[/{color}] {element.replace('_', ' ').title()}")
        
        # Improvements
        if analysis['improvements']:
            console.print("\n[bold yellow]Suggested Improvements:[/bold yellow]")
            for improvement in analysis['improvements']:
                console.print(f"  • {improvement}")
        
        # Hook suggestions
        if analysis['suggestions']:
            console.print("\n[bold green]Recommended Hooks:[/bold green]")
            for suggestion in analysis['suggestions']:
                console.print(f"  • [{suggestion['type']}] {suggestion['example'][:50]}... (ID: {suggestion['id']})")
        
    except Exception as e:
        console.print(f"[red]Error analyzing tweet: {str(e)}[/red]")
        logger.error(f"Analyze error: {e}", exc_info=True)


@hooks.command('preview')
@click.option('--hook-id', '-h', required=True, type=int, help='Hook ID to use')
@click.option('--content', '-c', required=True, help='Your content')
@click.option('--context', '-x', help='Additional context as JSON (e.g., \'{"result": "$10K"}\')')
def preview_hook(hook_id: int, content: str, context: Optional[str]):
    """Preview how a hook would look with your content."""
    try:
        manager = get_hook_manager()
        
        # Parse context if provided
        context_dict = {}
        if context:
            try:
                context_dict = json.loads(context)
            except json.JSONDecodeError:
                console.print("[yellow]Warning: Invalid JSON context, ignoring[/yellow]")
        
        # Get the hook
        hook = manager.get_hook(hook_id)
        if not hook:
            console.print(f"[red]Hook {hook_id} not found[/red]")
            return
        
        # Adapt the content
        adapted = manager.adapt_hook(hook_id, content, context_dict)
        
        # Show original hook
        console.print(Panel(
            hook.hook_text,
            title=f"Original Hook Pattern ({hook.pattern_type})",
            border_style="blue"
        ))
        
        # Show adapted content
        console.print(Panel(
            adapted,
            title="Your Tweet with Hook Applied",
            border_style="green"
        ))
        
        # Character count
        char_count = len(adapted)
        color = "green" if char_count <= 280 else "red"
        console.print(f"\n[{color}]Character count: {char_count}/280[/{color}]")
        
        if char_count > 280:
            console.print("[yellow]⚠ Tweet exceeds character limit. Consider shortening.[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error previewing hook: {str(e)}[/red]")
        logger.error(f"Preview error: {e}", exc_info=True)


@hooks.command('performance')
@click.option('--hook-id', '-h', type=int, help='Specific hook ID')
@click.option('--top', '-t', default=10, help='Show top N hooks by performance')
def hook_performance(hook_id: Optional[int], top: int):
    """View hook performance statistics."""
    try:
        manager = get_hook_manager()
        
        if hook_id:
            # Show specific hook performance
            performance = manager.get_hook_performance(hook_id)
            
            if not performance or performance['total_uses'] == 0:
                console.print(f"[yellow]No usage data for hook {hook_id}[/yellow]")
                return
            
            console.print(Panel.fit(
                f"""[bold cyan]Hook #{hook_id} Performance[/bold cyan]

[yellow]Pattern Type:[/yellow] {performance['pattern_type']}
[yellow]Total Uses:[/yellow] {performance['total_uses']}
[yellow]Average Performance:[/yellow] {performance['avg_performance']:.1f}/10
[yellow]Best Performance:[/yellow] {performance['best_performance']:.1f}/10
[yellow]Average Engagement:[/yellow] {performance.get('avg_engagement', 0):.2f}%
[yellow]Tags:[/yellow] {', '.join(performance.get('tags', [])) if performance.get('tags') else 'None'}""",
                border_style="cyan"
            ))
        else:
            # Show top performing hooks
            hooks = manager.list_hooks(limit=top)
            
            if not hooks:
                console.print("[yellow]No hooks found[/yellow]")
                return
            
            table = Table(title=f"Top {min(len(hooks), top)} Performing Hooks", box=box.ROUNDED)
            table.add_column("Rank", style="cyan", width=6)
            table.add_column("ID", style="magenta", width=6)
            table.add_column("Type", style="blue", width=15)
            table.add_column("Success Rate", style="green", width=12)
            table.add_column("Avg Engagement", style="yellow", width=14)
            table.add_column("Uses", style="white", width=8)
            
            for i, hook in enumerate(hooks, 1):
                performance = manager.get_hook_performance(hook.id)
                
                table.add_row(
                    str(i),
                    str(hook.id),
                    hook.pattern_type,
                    f"{hook.success_rate:.1%}" if hook.success_rate else '-',
                    f"{hook.avg_engagement_rate:.2f}%" if hook.avg_engagement_rate else '-',
                    str(performance.get('total_uses', 0))
                )
            
            console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error showing performance: {str(e)}[/red]")
        logger.error(f"Performance error: {e}", exc_info=True)


@hooks.command('types')
def list_hook_types():
    """List all available hook pattern types."""
    console.print("[bold cyan]Available Hook Pattern Types:[/bold cyan]\n")
    
    types_info = {
        HookPatternType.SHOCK: "Attention-grabbing intros (HOLY SH*T, INSANE, etc.)",
        HookPatternType.VALUE_GIVEAWAY: "Offer value in exchange for engagement",
        HookPatternType.AUTHORITY: "Establish expertise or achievement",
        HookPatternType.CONTRARIAN: "Challenge common beliefs",
        HookPatternType.INSIDER: "Share 'secret' information",
        HookPatternType.RESULTS: "Lead with impressive numbers/outcomes",
        HookPatternType.TIME_SENSITIVE: "Create urgency with time limits",
        HookPatternType.LIST: "Numbered lists of tips/resources",
        HookPatternType.QUESTION: "Engaging questions to spark curiosity",
        HookPatternType.STORY: "Personal narratives and experiences"
    }
    
    for pattern_type, description in types_info.items():
        console.print(f"  [green]{pattern_type:20}[/green] {description}")
    
    console.print("\n[dim]Use --type flag with any command to filter by pattern type[/dim]")