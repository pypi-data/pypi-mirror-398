"""
optixlog artifacts - List artifacts for a run

Wraps the query.get_artifacts() function with CLI interface.
"""

import click
from typing import Optional

from ..config import get_config
from ..utils import (
    print_success, print_error, print_dim,
    print_json, format_size, format_datetime
)


@click.command()
@click.argument("run_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--api-url", help="API URL (default: from config)")
@click.option("--api-key", help="API key (default: from config)")
@click.pass_context
def artifacts(
    ctx: click.Context,
    run_id: str,
    as_json: bool,
    api_url: Optional[str],
    api_key: Optional[str],
) -> None:
    """List artifacts for a run.
    
    Shows all images, files, and other artifacts attached to a run.
    
    RUN_ID is the ID of the run to query.
    
    Examples:
    
        optixlog artifacts abc123
        
        optixlog artifacts abc123 --json
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
    
    if not as_json:
        click.echo(click.style(f"\n🎨 Fetching artifacts for run {run_id}...\n", bold=True))
    
    try:
        from optixlog import query
        
        artifacts_list = query.get_artifacts(
            api_url=api_url,
            api_key=api_key,
            run_id=run_id,
        )
        
        if not artifacts_list:
            if not as_json:
                print_dim("No artifacts found")
            else:
                print_json([])
            return
        
        if as_json:
            artifacts_data = [
                {
                    "media_id": a.media_id,
                    "key": a.key,
                    "kind": a.kind,
                    "url": a.url,
                    "content_type": a.content_type,
                    "file_size": a.file_size,
                    "created_at": a.created_at,
                    "meta": a.meta,
                }
                for a in artifacts_list
            ]
            print_json(artifacts_data)
        else:
            click.echo(click.style(f"Found {len(artifacts_list)} artifacts:\n", bold=True))
            
            for artifact in artifacts_list:
                # Icon based on kind
                icon = "🖼️" if artifact.kind == "image" else "📄"
                size_str = format_size(artifact.file_size)
                
                click.echo(f"{icon} {click.style(artifact.key, fg='cyan')}")
                print_dim(f"   ID: {artifact.media_id}")
                print_dim(f"   Type: {artifact.content_type}")
                print_dim(f"   Size: {size_str}")
                if artifact.created_at:
                    print_dim(f"   Created: {format_datetime(artifact.created_at)}")
                click.echo()
            
            print_dim("Download with: optixlog download <media_id> -o <output_path>")
            click.echo()
                
    except ImportError:
        print_error("Could not import optixlog SDK")
        ctx.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        ctx.exit(1)

