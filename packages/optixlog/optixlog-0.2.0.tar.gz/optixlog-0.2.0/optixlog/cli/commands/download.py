"""
optixlog download - Download an artifact

Wraps the query.download_artifact() function with CLI interface.
"""

import click
from pathlib import Path
from typing import Optional

from ..config import get_config
from ..utils import print_success, print_error, print_dim


@click.command()
@click.argument("media_id")
@click.option("-o", "--output", "output_path", type=click.Path(path_type=Path), help="Output file path")
@click.option("--api-url", help="API URL (default: from config)")
@click.option("--api-key", help="API key (default: from config)")
@click.pass_context
def download(
    ctx: click.Context,
    media_id: str,
    output_path: Optional[Path],
    api_url: Optional[str],
    api_key: Optional[str],
) -> None:
    """Download an artifact.
    
    Downloads a media artifact to a local file.
    
    MEDIA_ID is the ID of the artifact to download.
    
    Examples:
    
        optixlog download media_xyz -o ./output.png
        
        optixlog download media_xyz  # Downloads to current directory
    """
    config = get_config()
    
    # Get credentials
    if not api_key:
        api_key = config.api_key
    if not api_url:
        api_url = config.api_url
    
    if not api_key:
        print_error("No API key configured")
        print_dim("Run: optixlog login")
        ctx.exit(1)
        return
    
    # Default output path
    if not output_path:
        output_path = Path.cwd() / media_id
    
    click.echo(click.style(f"\n⬇️  Downloading artifact {media_id}...\n", bold=True))
    
    try:
        from optixlog import query
        
        success = query.download_artifact(
            api_url=api_url,
            api_key=api_key,
            media_id=media_id,
            output_path=str(output_path),
        )
        
        if success:
            print_success(f"Downloaded to: {output_path}")
        else:
            print_error("Download failed")
            ctx.exit(1)
            
    except ImportError:
        print_error("Could not import optixlog SDK")
        ctx.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        ctx.exit(1)

