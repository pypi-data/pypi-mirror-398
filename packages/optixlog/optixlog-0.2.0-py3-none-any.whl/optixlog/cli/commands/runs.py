"""
optixlog runs - List recent runs

Wraps the query.list_runs() function with CLI interface.
"""

import click
import json
from typing import Optional

from ..config import get_config
from ..utils import (
    print_success, print_error, print_warning, print_dim,
    print_json, print_table, format_datetime
)


@click.command()
@click.option("-p", "--project", "project_name", help="Filter by project name")
@click.option("-l", "--limit", default=10, type=int, help="Number of runs to show")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--api-url", help="API URL (default: from config)")
@click.option("--api-key", help="API key (default: from config)")
@click.pass_context
def runs(
    ctx: click.Context,
    project_name: Optional[str],
    limit: int,
    as_json: bool,
    api_url: Optional[str],
    api_key: Optional[str],
) -> None:
    """List recent runs.
    
    Shows the most recent experiment runs, optionally filtered by project.
    
    Examples:
    
        optixlog runs
        
        optixlog runs --project "MyProject" --limit 20
        
        optixlog runs --json
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
        click.echo(click.style("\n🔍 Fetching runs...\n", bold=True))
    
    # Import and use the SDK query function
    try:
        from optixlog import query
        
        runs_list = query.list_runs(
            api_url=api_url,
            api_key=api_key,
            project=project_name,
            limit=limit,
        )
        
        if not runs_list:
            if not as_json:
                print_dim("No runs found")
            else:
                print_json([])
            return
        
        if as_json:
            # Convert to dict for JSON output
            runs_data = [
                {
                    "id": r.run_id,
                    "name": r.name,
                    "project_id": r.project_id,
                    "project_name": r.project_name,
                    "config": r.config,
                    "created_at": r.created_at,
                    "status": r.status,
                }
                for r in runs_list
            ]
            print_json(runs_data)
        else:
            # Table output
            click.echo(click.style(f"Found {len(runs_list)} runs:\n", bold=True))
            
            for run in runs_list:
                click.echo(click.style(f"✓ {run.name or run.run_id}", fg="green"))
                print_dim(f"  ID: {run.run_id}")
                print_dim(f"  Project: {run.project_name}")
                print_dim(f"  Created: {format_datetime(run.created_at)}")
                click.echo()
                
    except ImportError:
        print_error("Could not import optixlog SDK")
        ctx.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        ctx.exit(1)

