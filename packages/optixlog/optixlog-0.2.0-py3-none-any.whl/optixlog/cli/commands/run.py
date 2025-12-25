"""
optixlog run - Get details for a specific run

Wraps the query.get_run() function with CLI interface.
"""

import click
import json
from typing import Optional

from ..config import get_config
from ..utils import (
    print_success, print_error, print_dim,
    print_json, print_panel, format_datetime
)


@click.command()
@click.argument("run_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--api-url", help="API URL (default: from config)")
@click.option("--api-key", help="API key (default: from config)")
@click.pass_context
def run(
    ctx: click.Context,
    run_id: str,
    as_json: bool,
    api_url: Optional[str],
    api_key: Optional[str],
) -> None:
    """Get details for a specific run.
    
    RUN_ID is the ID of the run to retrieve.
    
    Examples:
    
        optixlog run abc123
        
        optixlog run abc123 --json
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
        click.echo(click.style(f"\n🔍 Fetching run {run_id}...\n", bold=True))
    
    try:
        from optixlog import query
        
        run_info = query.get_run(
            api_url=api_url,
            api_key=api_key,
            run_id=run_id,
        )
        
        if not run_info:
            print_error(f"Run '{run_id}' not found")
            ctx.exit(1)
            return
        
        if as_json:
            run_data = {
                "id": run_info.run_id,
                "name": run_info.name,
                "project_id": run_info.project_id,
                "project_name": run_info.project_name,
                "config": run_info.config,
                "created_at": run_info.created_at,
                "status": run_info.status,
            }
            print_json(run_data)
        else:
            # Formatted output
            click.echo(click.style(f"Run: {run_info.name or run_info.run_id}", fg="green", bold=True))
            click.echo()
            
            click.echo(f"  {click.style('ID:', fg='cyan')} {run_info.run_id}")
            click.echo(f"  {click.style('Project:', fg='cyan')} {run_info.project_name}")
            click.echo(f"  {click.style('Status:', fg='cyan')} {run_info.status}")
            click.echo(f"  {click.style('Created:', fg='cyan')} {format_datetime(run_info.created_at)}")
            
            if run_info.config:
                click.echo()
                click.echo(click.style("  Config:", fg="cyan"))
                for key, value in run_info.config.items():
                    click.echo(f"    {key}: {value}")
            
            click.echo()
            
    except ImportError:
        print_error("Could not import optixlog SDK")
        ctx.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        ctx.exit(1)

