"""
optixlog projects - List all projects

Wraps the query.list_projects() function with CLI interface.
"""

import click
from typing import Optional

from ..config import get_config
from ..utils import (
    print_success, print_error, print_dim,
    print_json, print_table, format_datetime
)


@click.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--api-url", help="API URL (default: from config)")
@click.option("--api-key", help="API key (default: from config)")
@click.pass_context
def projects(
    ctx: click.Context,
    as_json: bool,
    api_url: Optional[str],
    api_key: Optional[str],
) -> None:
    """List all projects.
    
    Shows all projects available for your API key.
    
    Examples:
    
        optixlog projects
        
        optixlog projects --json
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
        click.echo(click.style("\n📁 Fetching projects...\n", bold=True))
    
    try:
        from optixlog import query
        
        projects_list = query.list_projects(
            api_url=api_url,
            api_key=api_key,
        )
        
        if not projects_list:
            if not as_json:
                print_dim("No projects found")
            else:
                print_json([])
            return
        
        if as_json:
            projects_data = [
                {
                    "id": p.project_id,
                    "name": p.name,
                    "created_at": p.created_at,
                    "run_count": p.run_count,
                }
                for p in projects_list
            ]
            print_json(projects_data)
        else:
            click.echo(click.style(f"Found {len(projects_list)} projects:\n", bold=True))
            
            for proj in projects_list:
                run_count_str = f" ({proj.run_count} runs)" if proj.run_count else ""
                click.echo(click.style(f"📁 {proj.name}", fg="blue") + click.style(run_count_str, dim=True))
                print_dim(f"   ID: {proj.project_id}")
                if proj.created_at:
                    print_dim(f"   Created: {format_datetime(proj.created_at)}")
                click.echo()
                
    except ImportError:
        print_error("Could not import optixlog SDK")
        ctx.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        ctx.exit(1)

