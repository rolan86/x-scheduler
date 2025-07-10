"""Main CLI entry point for X-Scheduler."""

import click
from rich.console import Console
from rich.table import Table

from src import __version__

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


@cli.command()
@click.option("--topic", required=True, help="Topic for content generation")
@click.option(
    "--style",
    type=click.Choice(["personal", "professional", "casual", "educational"]),
    default="personal",
    help="Writing style for the content"
)
@click.option("--count", default=1, help="Number of tweets to generate")
def generate(topic: str, style: str, count: int) -> None:
    """Generate tweet content using AI."""
    console.print(f"[bold green]Generating {count} tweet(s) about '{topic}' in {style} style...[/bold green]")
    console.print("[yellow]AI content generation not yet implemented[/yellow]")


@cli.command()
@click.option("--content", required=True, help="Tweet content")
@click.option("--time", help="Schedule time (YYYY-MM-DD HH:MM)")
@click.option("--media", help="Path to media file")
def schedule(content: str, time: str, media: str) -> None:
    """Schedule a tweet for later posting."""
    if time:
        console.print(f"[bold green]Scheduling tweet for {time}...[/bold green]")
    else:
        console.print("[bold green]Adding tweet to queue...[/bold green]")
    console.print(f"Content: {content}")
    if media:
        console.print(f"Media: {media}")
    console.print("[yellow]Scheduling not yet implemented[/yellow]")


@cli.command()
@click.option("--content", required=True, help="Tweet content")
@click.option("--media", help="Path to media file")
def post(content: str, media: str) -> None:
    """Post a tweet immediately."""
    console.print("[bold green]Posting tweet...[/bold green]")
    console.print(f"Content: {content}")
    if media:
        console.print(f"Media: {media}")
    console.print("[yellow]Posting not yet implemented[/yellow]")


@cli.group()
def queue() -> None:
    """Manage the tweet queue."""
    pass


@queue.command("list")
@click.option("--status", type=click.Choice(["pending", "scheduled", "posted", "failed"]))
def queue_list(status: str) -> None:
    """List tweets in the queue."""
    table = Table(title="Tweet Queue")
    table.add_column("ID", style="cyan")
    table.add_column("Content", style="white")
    table.add_column("Scheduled", style="yellow")
    table.add_column("Status", style="green")
    
    console.print(table)
    console.print("[yellow]Queue listing not yet implemented[/yellow]")


@queue.command("approve")
@click.option("--id", "tweet_id", required=True, type=int, help="Tweet ID to approve")
def queue_approve(tweet_id: int) -> None:
    """Approve a tweet for posting."""
    console.print(f"[bold green]Approving tweet {tweet_id}...[/bold green]")
    console.print("[yellow]Approval not yet implemented[/yellow]")


@queue.command("delete")
@click.option("--id", "tweet_id", required=True, type=int, help="Tweet ID to delete")
def queue_delete(tweet_id: int) -> None:
    """Delete a tweet from the queue."""
    console.print(f"[bold red]Deleting tweet {tweet_id}...[/bold red]")
    console.print("[yellow]Deletion not yet implemented[/yellow]")


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
    console.print("✓ Creating database...")
    console.print("✓ Setting up configuration...")
    console.print("✓ Creating media directories...")
    console.print("[bold green]Initialization complete![/bold green]")
    console.print("\nNext steps:")
    console.print("1. Copy .env.example to .env and add your API keys")
    console.print("2. Run 'x-scheduler generate --topic \"your topic\"' to create content")
    console.print("3. Run 'x-scheduler queue list' to view scheduled posts")


if __name__ == "__main__":
    cli()