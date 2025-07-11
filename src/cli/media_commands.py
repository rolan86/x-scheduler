"""Media generation and management CLI commands."""

import click
from rich.console import Console
from pathlib import Path
import requests
from datetime import datetime

from src.api.auth import auth_manager
from src.api.openai_client import openai_client
from src.api.pollo import pollo_client
from src.core.tweet_manager import tweet_manager


console = Console()


@click.group()
def media() -> None:
    """Manage media generation and attachments."""
    pass


@media.command("generate-image")
@click.option("--prompt", required=True, help="Image generation prompt")
@click.option("--size", type=click.Choice(["1024x1024", "1024x1792", "1792x1024"]), default="1024x1024")
@click.option("--quality", type=click.Choice(["standard", "hd"]), default="standard")
@click.option("--save-as", help="Filename to save the image")
@click.option("--tweet-id", type=int, help="Tweet ID to attach the image to")
def generate_image(prompt: str, size: str, quality: str, save_as: str, tweet_id: int) -> None:
    """Generate an image using DALL-E 3."""
    # Check if OpenAI is configured
    if not auth_manager.is_provider_configured('openai'):
        console.print("[red]OpenAI not configured. Run 'x-scheduler auth setup openai' first.[/red]")
        return
    
    console.print(f"[bold green]Generating image...[/bold green]")
    console.print(f"Prompt: [white]{prompt}[/white]")
    console.print(f"Size: {size}, Quality: {quality}")
    
    try:
        # Generate image
        result = openai_client.generate_image(prompt, size, quality)
        
        if not result:
            console.print("[red]Failed to generate image[/red]")
            return
        
        console.print(f"[green]✓ Image generated successfully![/green]")
        console.print(f"Cost: ${result['cost']:.4f}")
        
        # Download and save image
        image_url = result['url']
        
        # Determine filename
        if not save_as:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_as = f"dalle_image_{timestamp}.png"
        
        # Ensure media directory exists
        from src.core.config import settings
        media_dir = Path(settings.media_dir)
        media_dir.mkdir(parents=True, exist_ok=True)
        
        # Download image
        file_path = media_dir / save_as
        console.print(f"Downloading image to {file_path}...")
        
        response = requests.get(image_url)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        console.print(f"[green]✓ Image saved as: {file_path}[/green]")
        
        # Attach to tweet if requested
        if tweet_id:
            console.print(f"Attaching to tweet {tweet_id}...")
            success = tweet_manager.attach_media(tweet_id, file_path, alt_text=prompt[:1000])
            
            if success:
                console.print(f"[green]✓ Image attached to tweet {tweet_id}[/green]")
            else:
                console.print(f"[red]✗ Failed to attach image to tweet {tweet_id}[/red]")
        
        # Output path for Claude Code
        print(f"\nIMAGE_PATH={file_path}")
        
        if result.get('revised_prompt'):
            console.print(f"\n[dim]Revised prompt: {result['revised_prompt']}[/dim]")
    
    except Exception as e:
        console.print(f"[red]Error generating image: {str(e)}[/red]")


@media.command("generate-video")
@click.option("--prompt", required=True, help="Video generation prompt")
@click.option("--duration", type=int, default=5, help="Video duration in seconds (1-30)")
@click.option("--quality", type=click.Choice(["standard", "hd", "4k"]), default="standard")
@click.option("--style", type=click.Choice(["realistic", "cartoon", "anime", "abstract"]), default="realistic")
@click.option("--save-as", help="Filename to save the video")
@click.option("--tweet-id", type=int, help="Tweet ID to attach the video to")
def generate_video(prompt: str, duration: int, quality: str, style: str, save_as: str, tweet_id: int) -> None:
    """Generate a video using Pollo.ai."""
    # Check if Pollo.ai is configured
    if not auth_manager.is_provider_configured('pollo'):
        console.print("[red]Pollo.ai not configured. Run 'x-scheduler auth setup pollo' first.[/red]")
        return
    
    console.print(f"[bold green]Generating video...[/bold green]")
    console.print(f"Prompt: [white]{prompt}[/white]")
    console.print(f"Duration: {duration}s, Quality: {quality}, Style: {style}")
    
    try:
        # Generate video
        result = pollo_client.generate_video(prompt, duration, quality, style)
        
        if not result:
            console.print("[red]Failed to generate video[/red]")
            return
        
        console.print(f"[green]✓ Video generation started![/green]")
        console.print(f"Video ID: {result['video_id']}")
        console.print(f"Cost: ${result['cost']:.4f}")
        
        # Wait for video to be ready
        console.print("Waiting for video processing...")
        import time
        
        video_url = None
        for i in range(60):  # Wait up to 5 minutes
            status = pollo_client.get_video_status(result['video_id'])
            
            if status and status['status'] == 'completed':
                video_url = status['video_url']
                break
            elif status and status['status'] == 'failed':
                console.print(f"[red]Video generation failed: {status.get('error_message')}[/red]")
                return
            
            time.sleep(5)
            console.print(f"[dim]Still processing... ({i*5}s)[/dim]")
        
        if not video_url:
            console.print("[red]Video generation timed out[/red]")
            return
        
        # Download video
        if not save_as:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_as = f"pollo_video_{timestamp}.mp4"
        
        from src.core.config import settings
        media_dir = Path(settings.media_dir)
        media_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = media_dir / save_as
        success = pollo_client.download_video(video_url, str(file_path))
        
        if success:
            console.print(f"[green]✓ Video saved as: {file_path}[/green]")
            
            # Attach to tweet if requested
            if tweet_id:
                console.print(f"Attaching to tweet {tweet_id}...")
                success = tweet_manager.attach_media(tweet_id, file_path, alt_text=prompt[:1000])
                
                if success:
                    console.print(f"[green]✓ Video attached to tweet {tweet_id}[/green]")
                else:
                    console.print(f"[red]✗ Failed to attach video to tweet {tweet_id}[/red]")
            
            # Output path for Claude Code
            print(f"\nVIDEO_PATH={file_path}")
        else:
            console.print("[red]Failed to download video[/red]")
    
    except Exception as e:
        console.print(f"[red]Error generating video: {str(e)}[/red]")


@media.command("attach")
@click.option("--tweet-id", required=True, type=int, help="Tweet ID to attach media to")
@click.option("--file", required=True, help="Path to media file")
@click.option("--alt-text", help="Alt text for accessibility")
def attach_media(tweet_id: int, file: str, alt_text: str) -> None:
    """Attach a media file to a tweet."""
    try:
        file_path = Path(file)
        
        if not file_path.exists():
            console.print(f"[red]File not found: {file}[/red]")
            return
        
        console.print(f"Attaching {file_path.name} to tweet {tweet_id}...")
        
        success = tweet_manager.attach_media(tweet_id, file_path, alt_text)
        
        if success:
            console.print(f"[green]✓ Media attached to tweet {tweet_id}[/green]")
        else:
            console.print(f"[red]✗ Failed to attach media[/red]")
    
    except Exception as e:
        console.print(f"[red]Error attaching media: {str(e)}[/red]")


@media.command("list")
@click.option("--tweet-id", type=int, help="Show media for specific tweet")
def list_media(tweet_id: int) -> None:
    """List media files."""
    try:
        from src.models import get_db, Media, Tweet
        
        db = next(get_db())
        
        if tweet_id:
            # Show media for specific tweet
            tweet = db.query(Tweet).filter_by(id=tweet_id).first()
            if not tweet:
                console.print(f"[red]Tweet {tweet_id} not found[/red]")
                return
            
            if not tweet.media_items:
                console.print(f"[yellow]No media attached to tweet {tweet_id}[/yellow]")
                return
            
            console.print(f"\n[bold]Media for Tweet {tweet_id}:[/bold]")
            for media in tweet.media_items:
                console.print(f"\n{media.filename}")
                console.print(f"  Type: {media.media_type.value}")
                console.print(f"  Source: {media.media_source.value}")
                if media.generation_cost > 0:
                    console.print(f"  Cost: ${media.generation_cost:.4f}")
                if media.alt_text:
                    console.print(f"  Alt text: {media.alt_text[:50]}...")
        else:
            # Show all media
            media_items = db.query(Media).order_by(Media.created_at.desc()).limit(20).all()
            
            if not media_items:
                console.print("[yellow]No media files found[/yellow]")
                return
            
            console.print(f"\n[bold]Recent Media Files:[/bold]")
            for media in media_items:
                console.print(f"\n{media.filename}")
                console.print(f"  Type: {media.media_type.value}")
                console.print(f"  Source: {media.media_source.value}")
                if media.tweet_id:
                    console.print(f"  Tweet ID: {media.tweet_id}")
                if media.generation_cost > 0:
                    console.print(f"  Cost: ${media.generation_cost:.4f}")
        
        db.close()
        
    except Exception as e:
        console.print(f"[red]Error listing media: {str(e)}[/red]")