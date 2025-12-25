"""
optixlog login - Interactive API key setup

Validates and stores the API key.
"""

import click
import requests
from typing import Optional

from ..config import get_config, CONFIG_FILE
from ..utils import print_success, print_error, print_warning, print_dim


@click.command()
@click.option("-k", "--api-key", help="API key (or enter interactively)")
@click.option("--api-url", help="API URL (default: from config)")
@click.pass_context
def login(
    ctx: click.Context,
    api_key: Optional[str],
    api_url: Optional[str],
) -> None:
    """Login to OptixLog by setting your API key.
    
    The API key will be validated against the server before saving.
    
    Examples:
    
        optixlog login
        
        optixlog login --api-key "proj_xxx"
    """
    click.echo(click.style("\n🔐 OptixLog Login\n", bold=True))
    
    config = get_config()
    
    # Get API URL
    if not api_url:
        api_url = config.api_url
    
    # Get API key interactively if not provided
    if not api_key:
        api_key = click.prompt(
            click.style("Enter your API key", fg="cyan"),
            hide_input=False,
        )
    
    if not api_key:
        print_error("API key is required")
        return
    
    # Validate API key
    print_dim("Validating API key...")
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(
            f"{api_url}/api/sdk/initialize-run-check",
            headers=headers,
            timeout=10,
        )
        
        if response.status_code == 401:
            print_error("Invalid API key")
            print_dim("Please check your API key and try again")
            print_dim("Get your API key from: https://optixlog.com")
            ctx.exit(1)
            return
        
        if response.ok:
            data = response.json()
            projects = data.get("projects", [])
            
            print_success("Login successful!")
            
            # Save API key
            config.set("api_key", api_key)
            print_success(f"API key saved to {CONFIG_FILE}")
            
            # Show available projects
            if projects:
                click.echo()
                print_dim(f"Available projects ({len(projects)}):")
                for proj in projects[:5]:
                    print_dim(f"  - {proj.get('name', proj.get('id'))}")
                if len(projects) > 5:
                    print_dim(f"  ... and {len(projects) - 5} more")
            
            click.echo()
        else:
            print_warning(f"Could not validate API key (status {response.status_code})")
            
            if click.confirm("Save API key anyway?", default=False):
                config.set("api_key", api_key)
                print_success("API key saved")
            
    except requests.exceptions.ConnectionError:
        print_error(f"Could not connect to {api_url}")
        print_dim("Please check your internet connection")
        ctx.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        ctx.exit(1)

