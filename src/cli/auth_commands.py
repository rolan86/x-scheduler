"""Authentication management CLI commands."""

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from src.api.auth import auth_manager
from src.api.twitter import twitter_api
from src.api.openai_client import openai_client
from src.api.pollo import pollo_client


console = Console()


@click.group()
def auth() -> None:
    """Manage API authentication credentials."""
    pass


@auth.command("status")
def auth_status() -> None:
    """Show authentication status for all providers."""
    console.print("[bold cyan]Authentication Status[/bold cyan]")
    
    # Get status
    status = auth_manager.get_auth_status()
    
    # Create table
    table = Table(title="API Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Details", style="yellow")
    
    for provider, is_configured in status.items():
        if is_configured:
            status_text = "[green]✓ Configured[/green]"
            
            # Test connections
            if provider == 'twitter':
                test_result = twitter_api.test_connection()
                details = "[green]Connected[/green]" if test_result else "[red]Connection Failed[/red]"
            elif provider == 'openai':
                test_result = openai_client.test_connection()
                details = "[green]Connected[/green]" if test_result else "[red]Connection Failed[/red]"
            elif provider == 'pollo':
                test_result = pollo_client.test_connection()
                details = "[green]Connected[/green]" if test_result else "[red]Connection Failed[/red]"
            else:
                details = "Unknown"
        else:
            status_text = "[red]✗ Not Configured[/red]"
            details = "Credentials needed"
        
        table.add_row(provider.title(), status_text, details)
    
    console.print(table)


@auth.command("setup")
@click.option("--provider", type=click.Choice(["twitter", "openai", "pollo"]), required=True)
def auth_setup(provider: str) -> None:
    """Setup authentication for a specific provider."""
    console.print(f"[bold green]Setting up {provider.title()} authentication[/bold green]")
    
    if provider == "twitter":
        _setup_twitter()
    elif provider == "openai":
        _setup_openai()
    elif provider == "pollo":
        _setup_pollo()


def _setup_twitter() -> None:
    """Setup Twitter authentication."""
    console.print("\n[bold]Twitter API Credentials[/bold]")
    console.print("Get these from: https://developer.twitter.com/")
    console.print()
    
    # Get credentials
    api_key = Prompt.ask("API Key", password=True)
    api_secret = Prompt.ask("API Secret", password=True)
    access_token = Prompt.ask("Access Token", password=True)
    access_token_secret = Prompt.ask("Access Token Secret", password=True)
    
    # Setup authentication
    success = auth_manager.setup_twitter_auth(
        api_key, api_secret, access_token, access_token_secret
    )
    
    if success:
        console.print("[green]✓ Twitter authentication configured successfully[/green]")
        
        # Test connection
        if twitter_api.test_connection():
            console.print("[green]✓ Connection test successful[/green]")
        else:
            console.print("[yellow]⚠ Authentication saved but connection test failed[/yellow]")
    else:
        console.print("[red]✗ Failed to configure Twitter authentication[/red]")


def _setup_openai() -> None:
    """Setup OpenAI authentication."""
    console.print("\n[bold]OpenAI API Credentials[/bold]")
    console.print("Get these from: https://platform.openai.com/api-keys")
    console.print()
    
    # Get credentials
    api_key = Prompt.ask("API Key (starts with sk-)", password=True)
    organization = Prompt.ask("Organization ID (optional)", default="")
    
    # Setup authentication
    success = auth_manager.setup_openai_auth(
        api_key, organization if organization else None
    )
    
    if success:
        console.print("[green]✓ OpenAI authentication configured successfully[/green]")
        
        # Test connection
        if openai_client.test_connection():
            console.print("[green]✓ Connection test successful[/green]")
        else:
            console.print("[yellow]⚠ Authentication saved but connection test failed[/yellow]")
    else:
        console.print("[red]✗ Failed to configure OpenAI authentication[/red]")


def _setup_pollo() -> None:
    """Setup Pollo.ai authentication."""
    console.print("\n[bold]Pollo.ai API Credentials[/bold]")
    console.print("Get these from: https://pollo.ai/")
    console.print()
    
    # Get credentials
    api_key = Prompt.ask("API Key", password=True)
    
    # Setup authentication
    success = auth_manager.setup_pollo_auth(api_key)
    
    if success:
        console.print("[green]✓ Pollo.ai authentication configured successfully[/green]")
        
        # Test connection
        if pollo_client.test_connection():
            console.print("[green]✓ Connection test successful[/green]")
        else:
            console.print("[yellow]⚠ Authentication saved but connection test failed[/yellow]")
    else:
        console.print("[red]✗ Failed to configure Pollo.ai authentication[/red]")


@auth.command("test")
@click.option("--provider", type=click.Choice(["twitter", "openai", "pollo", "all"]), default="all")
def auth_test(provider: str) -> None:
    """Test API connections."""
    console.print("[bold cyan]Testing API Connections[/bold cyan]")
    
    providers_to_test = ["twitter", "openai", "pollo"] if provider == "all" else [provider]
    
    for p in providers_to_test:
        console.print(f"\n[bold]{p.title()}:[/bold]")
        
        if not auth_manager.is_provider_configured(p):
            console.print("  [red]✗ Not configured[/red]")
            continue
        
        try:
            if p == "twitter":
                result = twitter_api.test_connection()
                if result:
                    user_info = twitter_api.get_user_info()
                    if user_info:
                        console.print(f"  [green]✓ Connected as @{user_info['username']}[/green]")
                        console.print(f"    Followers: {user_info['followers_count']:,}")
                    else:
                        console.print("  [green]✓ Connected[/green]")
                else:
                    console.print("  [red]✗ Connection failed[/red]")
            
            elif p == "openai":
                result = openai_client.test_connection()
                console.print(f"  {'[green]✓ Connected[/green]' if result else '[red]✗ Connection failed[/red]'}")
            
            elif p == "pollo":
                result = pollo_client.test_connection()
                console.print(f"  {'[green]✓ Connected[/green]' if result else '[red]✗ Connection failed[/red]'}")
        
        except Exception as e:
            console.print(f"  [red]✗ Error: {str(e)}[/red]")


@auth.command("load-env")
def auth_load_env() -> None:
    """Load credentials from environment variables."""
    console.print("[bold cyan]Loading credentials from environment variables[/bold cyan]")
    
    results = auth_manager.load_credentials_from_env()
    
    for provider, success in results.items():
        status = "[green]✓ Loaded[/green]" if success else "[yellow]- Not found[/yellow]"
        console.print(f"{provider.title()}: {status}")
    
    loaded_count = sum(results.values())
    console.print(f"\n[bold]Total loaded: {loaded_count}/3 providers[/bold]")


@auth.command("remove")
@click.option("--provider", type=click.Choice(["twitter", "openai", "pollo"]), required=True)
@click.confirmation_option(prompt="Are you sure you want to remove these credentials?")
def auth_remove(provider: str) -> None:
    """Remove stored credentials for a provider."""
    success = auth_manager.credential_manager.delete_credentials(provider)
    
    if success:
        console.print(f"[green]✓ Removed {provider} credentials[/green]")
    else:
        console.print(f"[yellow]No {provider} credentials found to remove[/yellow]")


@auth.command("rate-limits")
def auth_rate_limits() -> None:
    """Show current API rate limit status."""
    console.print("[bold cyan]API Rate Limits[/bold cyan]")
    
    # Twitter rate limits
    if auth_manager.is_provider_configured('twitter'):
        console.print("\n[bold]Twitter:[/bold]")
        limits = twitter_api.get_rate_limit_status()
        
        for endpoint, info in limits.items():
            status = "[green]Available[/green]" if info['can_call'] else f"[red]Limited ({info['wait_time_seconds']:.0f}s wait)[/red]"
            console.print(f"  {endpoint}: {info['calls_made']}/{info['limit']} - {status}")
    else:
        console.print("\n[yellow]Twitter: Not configured[/yellow]")
    
    # OpenAI and Pollo.ai don't have explicit rate limiting in this implementation
    console.print("\n[bold]OpenAI:[/bold] Usage-based pricing")
    console.print("[bold]Pollo.ai:[/bold] Usage-based pricing")