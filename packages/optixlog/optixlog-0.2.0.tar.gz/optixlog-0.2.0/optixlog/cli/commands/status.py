"""
optixlog status - Show diagnostics and status

Shows version, config, and connection status.
"""

import click
import requests
from typing import Optional

from ..config import get_config, CONFIG_FILE
from ..utils import print_success, print_error, print_warning, print_dim, mask_api_key
from .. import __version__ as cli_version


@click.command()
@click.option("--api-url", help="API URL (default: from config)")
@click.option("--api-key", help="API key (default: from config)")
@click.pass_context
def status(
    ctx: click.Context,
    api_url: Optional[str],
    api_key: Optional[str],
) -> None:
    """Show OptixLog status and diagnostics.
    
    Displays version information, configuration, and tests the API connection.
    
    Examples:
    
        optixlog status
    """
    click.echo(click.style("\n📊 OptixLog Status\n", bold=True))
    
    config = get_config()
    
    # Get credentials
    if not api_key:
        api_key = config.api_key
    if not api_url:
        api_url = config.api_url
    
    # Version info
    click.echo(click.style("Version:", fg="cyan"))
    click.echo(f"  CLI: {cli_version}")
    
    try:
        import optixlog
        click.echo(f"  SDK: {optixlog.__version__}")
    except ImportError:
        click.echo("  SDK: not installed")
    except AttributeError:
        click.echo("  SDK: unknown")
    
    click.echo()
    
    # Config info
    click.echo(click.style("Configuration:", fg="cyan"))
    click.echo(f"  Config file: {CONFIG_FILE}")
    click.echo(f"  File exists: {'yes' if config.exists() else 'no'}")
    click.echo(f"  API URL: {api_url}")
    click.echo(f"  API Key: {mask_api_key(api_key)}")
    click.echo(f"  Project: {config.project}")
    
    click.echo()
    
    # Connection test
    click.echo(click.style("Connection:", fg="cyan"))
    
    if not api_key:
        print_warning("  No API key configured - cannot test connection")
        print_dim("  Run: optixlog login")
    else:
        print_dim(f"  Testing connection to {api_url}...")
        
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                f"{api_url}/api/sdk/initialize-run-check",
                headers=headers,
                timeout=10,
            )
            
            if response.status_code == 401:
                print_error("  Authentication failed - invalid API key")
            elif response.ok:
                data = response.json()
                projects = data.get("projects", [])
                print_success(f"  Connected successfully!")
                print_dim(f"  {len(projects)} project(s) accessible")
            else:
                print_warning(f"  Server responded with status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print_error(f"  Could not connect to {api_url}")
        except requests.exceptions.Timeout:
            print_error("  Connection timed out")
        except Exception as e:
            print_error(f"  Error: {e}")
    
    click.echo()
    
    # Environment variables
    click.echo(click.style("Environment Variables:", fg="cyan"))
    
    import os
    env_vars = [
        ("OPTIX_API_KEY", os.environ.get("OPTIX_API_KEY")),
        ("OPTIX_API_URL", os.environ.get("OPTIX_API_URL")),
        ("OPTIX_PROJECT", os.environ.get("OPTIX_PROJECT")),
    ]
    
    for name, value in env_vars:
        if value:
            display_value = mask_api_key(value) if "KEY" in name else value
            click.echo(f"  {name}: {display_value}")
        else:
            print_dim(f"  {name}: not set")
    
    click.echo()

