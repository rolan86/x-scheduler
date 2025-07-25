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
    """X-Scheduler: AI-powered Twitter/X content scheduling and posting.
    
    Maintain consistent posting to grow your Twitter/X following with
    AI-generated content, flexible scheduling, and media creation.
    """
    ctx.ensure_object(dict)


# Add auth commands
cli.add_command(auth)


@cli.command()
@click.option("--topic", required=True, help="Topic for content generation")
@click.option(
    "--style",
    type=click.Choice(["personal", "professional", "casual", "educational"]),
    default="personal",
    help="Writing style for the content"
)
@click.option("--count", default=1, help="Number of tweets to generate")
@click.option("--model", default="gpt-4", help="AI model to use")
@click.option("--template", help="Style template to use")
@click.option("--save/--no-save", default=True, help="Save to database")
def generate(topic: str, style: str, count: int, model: str, template: str, save: bool) -> None:
    """Generate tweet content using AI."""
    # Check if OpenAI is configured
    if not auth_manager.is_provider_configured('openai'):
        console.print("[red]OpenAI not configured. Run 'x-scheduler auth setup openai' first.[/red]")
        return
    
    console.print(f"[bold green]Generating {count} tweet(s) about '{topic}'...[/bold green]")
    
    try:
        # Generate using template or style
        if template:
            console.print(f"Using template: [cyan]{template}[/cyan]")
            results = content_generator.generate_with_template(topic, template, count, save)
        else:
            console.print(f"Style: [cyan]{style}[/cyan], Model: [cyan]{model}[/cyan]")
            results = content_generator.generate_tweets(topic, style, count, model, save)
        
        if not results:
            console.print("[red]Failed to generate tweets. Check your OpenAI configuration.[/red]")
            return
        
        # Display results
        console.print(f"\n[bold green]Generated {len(results)} tweet(s):[/bold green]")
        
        for i, result in enumerate(results, 1):
            console.print(f"\n[bold cyan]Tweet {i}:[/bold cyan]")
            console.print(f"[white]{result['content']}[/white]")
            console.print(f"[dim]Characters: {result['character_count']}/280[/dim]")
            
            if result['has_hashtags']:
                console.print(f"[dim]Hashtags: {result['hashtag_count']}[/dim]")
            
            console.print(f"[dim]Cost: ${result['cost']:.4f} | Tokens: {result['tokens_used']}[/dim]")
            
            if save and result['id']:
                console.print(f"[dim]Saved as tweet ID: {result['id']}[/dim]")
        
        # Show total cost
        total_cost = sum(r['cost'] for r in results)
        console.print(f"\n[bold]Total cost: ${total_cost:.4f}[/bold]")
        
        if save:
            console.print("\n[green]Tweets saved to database. Use 'x-scheduler queue list' to view.[/green]")
    
    except Exception as e:
        console.print(f"[red]Error generating tweets: {str(e)}[/red]")
        logging.error(f"Error in generate command: {e}")


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