"""Main CLI entry point for X-Scheduler."""

import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

from src import __version__
from src.core.database import initialize_database
from src.core.config import settings
from src.cli.auth_commands import auth
from src.cli.media_commands import media
from src.cli.hook_commands import hooks
from src.core.content_generator import content_generator
from src.core.tweet_manager import tweet_manager
from src.api.auth import auth_manager

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="x-scheduler")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """X-Scheduler: Twitter/X content scheduling and posting tool.
    
    Designed to work with Claude Code for content creation.
    Handles scheduling, posting, and media generation (DALL-E images, Pollo.ai videos).
    
    Quick start:
    1. Use Claude Code to generate tweet content
    2. Save with: x-scheduler create --content "your tweet"
    3. Add media: x-scheduler media generate-image --prompt "..." --tweet-id ID
    4. Post: x-scheduler queue post --id ID
    """
    ctx.ensure_object(dict)


# Add subcommands
cli.add_command(auth)
cli.add_command(media)
cli.add_command(hooks)


@cli.command()
@click.option("--content", required=True, help="Tweet content to save")
@click.option("--type", "content_type", type=click.Choice(["personal", "professional", "casual", "educational"]), default="personal")
@click.option("--use-hook", type=int, help="Hook ID to apply to content")
@click.option("--hook-type", help="Type of hook pattern to apply (shock, value_giveaway, etc.)")
@click.option("--auto-hook", is_flag=True, help="Automatically select best hook")
def create(content: str, content_type: str, use_hook: int = None, hook_type: str = None, auto_hook: bool = False) -> None:
    """Create a tweet and save to database (for use with Claude Code).
    
    Optionally apply high-performing hooks to enhance engagement."""
    try:
        from src.models import ContentType
        from src.core.hook_manager import get_hook_manager
        
        # Handle hook application if requested
        final_content = content
        hook_used = None
        
        if use_hook or hook_type or auto_hook:
            hook_manager = get_hook_manager()
            
            if use_hook:
                # Use specific hook ID
                console.print(f"[cyan]Applying hook #{use_hook}...[/cyan]")
                final_content = hook_manager.adapt_hook(use_hook, content)
                hook_used = use_hook
            elif hook_type:
                # Find and apply hook by type
                hooks = hook_manager.suggest_hooks(pattern_type=hook_type, count=1)
                if hooks:
                    console.print(f"[cyan]Applying {hook_type} hook...[/cyan]")
                    final_content = hook_manager.adapt_hook(hooks[0].id, content)
                    hook_used = hooks[0].id
                else:
                    console.print(f"[yellow]No {hook_type} hooks found, using original content[/yellow]")
            elif auto_hook:
                # Auto-select best hook
                hooks = hook_manager.suggest_hooks(topic=content[:50], count=1)
                if hooks:
                    console.print(f"[cyan]Auto-applying {hooks[0].pattern_type} hook...[/cyan]")
                    final_content = hook_manager.adapt_hook(hooks[0].id, content)
                    hook_used = hooks[0].id
                else:
                    console.print("[yellow]No suitable hooks found, using original content[/yellow]")
        
        # Create tweet with potentially hooked content
        tweet = tweet_manager.create_tweet(
            content=final_content,
            content_type=ContentType(content_type)
        )
        
        # Track hook usage if a hook was applied
        if hook_used:
            hook_manager.track_usage(
                hook_id=hook_used,
                tweet_id=tweet.id,
                adapted_content=final_content,
                notes=f"Applied via CLI create command"
            )
            console.print(f"[green]✓ Hook #{hook_used} applied successfully[/green]")
        
        console.print(f"[green]✓ Created tweet {tweet.id}[/green]")
        console.print(f"Content: [white]{final_content}[/white]")
        console.print(f"Characters: {len(final_content)}/280")
        console.print(f"Type: {content_type}")
        if hook_used:
            console.print(f"Hook: #{hook_used}")
        console.print(f"\n[dim]Tweet ID: {tweet.id} - Use this ID for scheduling or posting[/dim]")
        
        # Return just the ID for easy parsing by Claude Code
        print(f"\nTWEET_ID={tweet.id}")
        
    except Exception as e:
        console.print(f"[red]Error creating tweet: {str(e)}[/red]")
        logging.error(f"Error in create command: {e}")


@cli.command()
@click.option("--content", required=True, help="Tweet content")
@click.option("--time", help="Schedule time (YYYY-MM-DD HH:MM)")
@click.option("--media", help="Path to media file")
@click.option("--type", "content_type", type=click.Choice(["personal", "professional", "casual", "educational"]), default="personal")
def schedule(content: str, time: str, media: str, content_type: str) -> None:
    """Schedule a tweet for later posting."""
    try:
        from datetime import datetime
        from pathlib import Path
        from src.models import ContentType
        
        # Parse scheduled time if provided
        scheduled_time = None
        if time:
            try:
                scheduled_time = datetime.fromisoformat(time.replace(' ', 'T'))
                console.print(f"[bold green]Scheduling tweet for {scheduled_time}...[/bold green]")
            except ValueError:
                console.print("[red]Invalid time format. Use YYYY-MM-DD HH:MM[/red]")
                return
        else:
            console.print("[bold green]Adding tweet to queue...[/bold green]")
        
        # Create tweet
        tweet = tweet_manager.create_tweet(
            content=content,
            content_type=ContentType(content_type),
            scheduled_time=scheduled_time
        )
        
        console.print(f"[green]✓ Created tweet {tweet.id}[/green]")
        console.print(f"Content: [white]{content}[/white]")
        console.print(f"Characters: {len(content)}/280")
        
        # Add media if provided
        if media:
            media_path = Path(media)
            if media_path.exists():
                success = tweet_manager.attach_media(tweet.id, media_path)
                if success:
                    console.print(f"[green]✓ Attached media: {media_path.name}[/green]")
                else:
                    console.print(f"[red]✗ Failed to attach media: {media_path.name}[/red]")
            else:
                console.print(f"[red]✗ Media file not found: {media}[/red]")
        
        if scheduled_time:
            console.print(f"[dim]Scheduled for: {scheduled_time}[/dim]")
        else:
            console.print("[dim]Status: Draft (use 'x-scheduler queue approve' to schedule)[/dim]")
    
    except Exception as e:
        console.print(f"[red]Error scheduling tweet: {str(e)}[/red]")
        logging.error(f"Error in schedule command: {e}")


@cli.command()
@click.option("--content", required=True, help="Tweet content")
@click.option("--media", help="Path to media file")
@click.option("--type", "content_type", type=click.Choice(["personal", "professional", "casual", "educational"]), default="personal")
def post(content: str, media: str, content_type: str) -> None:
    """Post a tweet immediately."""
    # Check if Twitter is configured
    if not auth_manager.is_provider_configured('twitter'):
        console.print("[red]Twitter not configured. Run 'x-scheduler auth setup twitter' first.[/red]")
        return
    
    try:
        from pathlib import Path
        from src.models import ContentType
        
        console.print("[bold green]Posting tweet immediately...[/bold green]")
        console.print(f"Content: [white]{content}[/white]")
        console.print(f"Characters: {len(content)}/280")
        
        # Create tweet
        tweet = tweet_manager.create_tweet(
            content=content,
            content_type=ContentType(content_type)
        )
        
        # Add media if provided
        if media:
            media_path = Path(media)
            if media_path.exists():
                success = tweet_manager.attach_media(tweet.id, media_path)
                if success:
                    console.print(f"[green]✓ Attached media: {media_path.name}[/green]")
                else:
                    console.print(f"[red]✗ Failed to attach media: {media_path.name}[/red]")
                    return
            else:
                console.print(f"[red]✗ Media file not found: {media}[/red]")
                return
        
        # Post immediately
        success = tweet_manager.post_tweet(tweet.id, force=True)
        
        if success:
            tweet_obj = tweet_manager.get_tweet(tweet.id)
            console.print(f"[bold green]✓ Tweet posted successfully![/bold green]")
            if tweet_obj and tweet_obj.twitter_url:
                console.print(f"[cyan]URL: {tweet_obj.twitter_url}[/cyan]")
        else:
            console.print("[red]✗ Failed to post tweet[/red]")
    
    except Exception as e:
        console.print(f"[red]Error posting tweet: {str(e)}[/red]")
        logging.error(f"Error in post command: {e}")


@cli.group()
def queue() -> None:
    """Manage the tweet queue."""
    pass


@queue.command("list")
@click.option("--status", type=click.Choice(["draft", "scheduled", "approved", "posted", "failed"]))
@click.option("--limit", default=20, help="Number of tweets to show")
def queue_list(status: str, limit: int) -> None:
    """List tweets in the queue."""
    try:
        from src.models import TweetStatus
        
        # Get status filter
        status_filter = None
        if status:
            status_filter = TweetStatus(status)
        
        # Get tweets
        tweets = tweet_manager.get_tweet_queue(status_filter, limit)
        
        if not tweets:
            console.print("[yellow]No tweets found[/yellow]")
            return
        
        # Create table
        table = Table(title=f"Tweet Queue ({len(tweets)} tweets)")
        table.add_column("ID", style="cyan", width=5)
        table.add_column("Content", style="white", width=40)
        table.add_column("Status", style="green", width=10)
        table.add_column("Scheduled", style="yellow", width=16)
        table.add_column("Type", style="magenta", width=10)
        table.add_column("Media", style="blue", width=5)
        
        for tweet in tweets:
            # Format scheduled time
            scheduled = "Now" if tweet['status'] == 'posted' and tweet['posted_time'] else \
                       tweet['scheduled_time'][:16] if tweet['scheduled_time'] else "-"
            
            # Status with emoji
            status_display = {
                'draft': '📝 Draft',
                'scheduled': '⏰ Scheduled', 
                'approved': '✅ Approved',
                'posted': '🚀 Posted',
                'failed': '❌ Failed'
            }.get(tweet['status'], tweet['status'])
            
            # Media indicator
            media_indicator = "📷" if tweet['has_media'] else ""
            
            table.add_row(
                str(tweet['id']),
                tweet['content'],
                status_display,
                scheduled,
                tweet['content_type'],
                media_indicator
            )
        
        console.print(table)
        
        # Show summary
        if status:
            console.print(f"\n[dim]Showing {len(tweets)} {status} tweets[/dim]")
        else:
            console.print(f"\n[dim]Showing {len(tweets)} tweets (use --status to filter)[/dim]")
    
    except Exception as e:
        console.print(f"[red]Error listing queue: {str(e)}[/red]")
        logging.error(f"Error in queue list command: {e}")


@queue.command("approve")
@click.option("--id", "tweet_id", required=True, type=int, help="Tweet ID to approve")
def queue_approve(tweet_id: int) -> None:
    """Approve a tweet for posting."""
    try:
        success = tweet_manager.approve_tweet(tweet_id)
        
        if success:
            console.print(f"[bold green]✓ Approved tweet {tweet_id}[/bold green]")
            console.print("[dim]Tweet is now ready for posting[/dim]")
        else:
            console.print(f"[red]✗ Failed to approve tweet {tweet_id}[/red]")
    
    except Exception as e:
        console.print(f"[red]Error approving tweet: {str(e)}[/red]")
        logging.error(f"Error in queue approve command: {e}")


@queue.command("post")
@click.option("--id", "tweet_id", required=True, type=int, help="Tweet ID to post")
@click.option("--force", is_flag=True, help="Force post even if not approved")
def queue_post(tweet_id: int, force: bool) -> None:
    """Post a tweet from the queue."""
    # Check if Twitter is configured
    if not auth_manager.is_provider_configured('twitter'):
        console.print("[red]Twitter not configured. Run 'x-scheduler auth setup twitter' first.[/red]")
        return
    
    try:
        console.print(f"[bold green]Posting tweet {tweet_id}...[/bold green]")
        
        success = tweet_manager.post_tweet(tweet_id, force=force)
        
        if success:
            tweet_obj = tweet_manager.get_tweet(tweet_id)
            console.print(f"[bold green]✓ Tweet {tweet_id} posted successfully![/bold green]")
            if tweet_obj and tweet_obj.twitter_url:
                console.print(f"[cyan]URL: {tweet_obj.twitter_url}[/cyan]")
        else:
            console.print(f"[red]✗ Failed to post tweet {tweet_id}[/red]")
    
    except Exception as e:
        console.print(f"[red]Error posting tweet: {str(e)}[/red]")
        logging.error(f"Error in queue post command: {e}")


@queue.command("delete")
@click.option("--id", "tweet_id", required=True, type=int, help="Tweet ID to delete")
@click.option("--force", is_flag=True, help="Force delete even if posted")
def queue_delete(tweet_id: int, force: bool) -> None:
    """Delete a tweet from the queue."""
    try:
        success = tweet_manager.delete_tweet(tweet_id, force=force)
        
        if success:
            console.print(f"[bold green]✓ Deleted tweet {tweet_id}[/bold green]")
        else:
            console.print(f"[red]✗ Failed to delete tweet {tweet_id}[/red]")
            if not force:
                console.print("[dim]Use --force to delete posted tweets[/dim]")
    
    except Exception as e:
        console.print(f"[red]Error deleting tweet: {str(e)}[/red]")
        logging.error(f"Error in queue delete command: {e}")


@queue.command("show")
@click.option("--id", "tweet_id", required=True, type=int, help="Tweet ID to show")
def queue_show(tweet_id: int) -> None:
    """Show detailed information about a tweet."""
    try:
        tweet = tweet_manager.get_tweet(tweet_id)
        
        if not tweet:
            console.print(f"[red]Tweet {tweet_id} not found[/red]")
            return
        
        console.print(f"\n[bold cyan]Tweet {tweet.id} Details[/bold cyan]")
        console.print(f"[white]{tweet.content}[/white]")
        console.print()
        
        # Status and timing
        console.print(f"Status: {tweet.status.value}")
        console.print(f"Type: {tweet.content_type.value}")
        console.print(f"Characters: {len(tweet.content)}/280")
        console.print(f"Created: {tweet.created_at}")
        
        if tweet.scheduled_time:
            console.print(f"Scheduled: {tweet.scheduled_time}")
        if tweet.posted_time:
            console.print(f"Posted: {tweet.posted_time}")
        
        # AI generation info
        if tweet.ai_generated:
            console.print(f"\n[dim]AI Generated:[/dim]")
            console.print(f"  Model: {tweet.generation_model}")
            console.print(f"  Prompt: {tweet.generation_prompt}")
            console.print(f"  Cost: ${tweet.generation_cost:.4f}")
        
        # Media info
        if tweet.media_items:
            console.print(f"\n[dim]Media ({len(tweet.media_items)}):[/dim]")
            for media in tweet.media_items:
                console.print(f"  {media.filename} ({media.media_type.value})")
        
        # Twitter info
        if tweet.twitter_id:
            console.print(f"\n[dim]Twitter:[/dim]")
            console.print(f"  ID: {tweet.twitter_id}")
            console.print(f"  URL: {tweet.twitter_url}")
            console.print(f"  Likes: {tweet.likes_count}")
            console.print(f"  Retweets: {tweet.retweets_count}")
            console.print(f"  Replies: {tweet.replies_count}")
        
        # Error info
        if tweet.error_message:
            console.print(f"\n[red]Error:[/red] {tweet.error_message}")
            console.print(f"Retry count: {tweet.retry_count}")
    
    except Exception as e:
        console.print(f"[red]Error showing tweet: {str(e)}[/red]")
        logging.error(f"Error in queue show command: {e}")


@cli.command()
@click.option(
    "--period",
    type=click.Choice(["today", "week", "month", "all"]),
    default="week",
    help="Time period for statistics"
)
def stats(period: str) -> None:
    """View posting statistics and analytics."""
    console.print(f"[bold cyan]Statistics for {period}[/bold cyan]")
    
    table = Table(title="Posting Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Posts", "0")
    table.add_row("Daily Average", "0.0")
    table.add_row("Engagement Rate", "0%")
    table.add_row("Follower Growth", "+0")
    
    console.print(table)
    console.print("[yellow]Statistics not yet implemented[/yellow]")


@cli.command()
def init() -> None:
    """Initialize the X-Scheduler database and configuration."""
    console.print("[bold green]Initializing X-Scheduler...[/bold green]")
    
    try:
        # Create data and media directories
        console.print("✓ Creating directories...")
        data_dir = Path(settings.data_dir)
        media_dir = Path(settings.media_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        media_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        console.print("✓ Creating database...")
        initialize_database()
        
        # Check for .env file
        env_path = Path(".env")
        if not env_path.exists():
            console.print("[yellow]⚠ No .env file found![/yellow]")
            console.print("  Creating .env from template...")
            
            env_example = Path(".env.example")
            if env_example.exists():
                env_path.write_text(env_example.read_text())
                console.print("  ✓ Created .env file")
            else:
                console.print("  [red]✗ .env.example not found![/red]")
        
        console.print("[bold green]Initialization complete![/bold green]")
        console.print("\nNext steps:")
        console.print("1. Edit .env and add your API keys")
        console.print("2. Run 'x-scheduler generate --topic \"your topic\"' to create content")
        console.print("3. Run 'x-scheduler queue list' to view scheduled posts")
        
    except Exception as e:
        console.print(f"[bold red]Error during initialization:[/bold red] {str(e)}")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    cli()