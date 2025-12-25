"""
optixlog init - Initialize OptixLog configuration

Creates config file and optionally validates API key and project.
"""

import click
import requests
from typing import Optional

from ..config import get_config, CONFIG_FILE
from ..utils import print_success, print_error, print_warning, print_info, print_dim


@click.command()
@click.option("-p", "--project", "project_name", help="Project name")
@click.option("-k", "--api-key", help="API key")
@click.option("--api-url", help="API URL (default: https://optixlog.com)")
@click.pass_context
def init(
    ctx: click.Context,
    project_name: Optional[str],
    api_key: Optional[str],
    api_url: Optional[str],
) -> None:
    """Initialize OptixLog configuration.
    
    Creates a config file at ~/.config/optixlog/config.toml with your
    API key, project, and API URL settings.
    
    Examples:
    
        optixlog init --project "MyProject" --api-key "proj_xxx"
        
        optixlog init  # Interactive prompts
    """
    click.echo(click.style("\n🚀 Initializing OptixLog\n", bold=True))
    
    config = get_config()
    
    # Get API key
    if not api_key:
        existing_key = config.api_key
        if existing_key:
            print_info(f"Using existing API key: ***{existing_key[-8:]}")
            api_key = existing_key
        else:
            api_key = click.prompt(
                click.style("Enter your API key", fg="cyan"),
                default="",
                show_default=False,
            )
            if not api_key:
                print_warning("No API key provided")
                print_dim("Set it later with: optixlog login")
                print_dim("Get your API key from: https://optixlog.com")
    
    # Get API URL
    if not api_url:
        api_url = config.api_url
    
    # Get project name
    if not project_name:
        existing_project = config.get("project")
        if existing_project:
            project_name = click.prompt(
                click.style("Project name", fg="cyan"),
                default=existing_project,
            )
        else:
            project_name = click.prompt(
                click.style("Project name", fg="cyan"),
                default="MyProject",
            )
    
    # Validate API key and check/create project if key is available
    if api_key:
        print_dim(f"Validating API key...")
        
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
                return
            
            if response.ok:
                print_success("API key validated")
                
                # Check if project exists
                data = response.json()
                projects = data.get("projects", [])
                project_exists = any(
                    p.get("name") == project_name or p.get("id") == project_name
                    for p in projects
                )
                
                if project_exists:
                    print_success(f"Project '{project_name}' exists")
                else:
                    print_warning(f"Project '{project_name}' not found")
                    
                    if click.confirm(
                        click.style("Create project?", fg="yellow"),
                        default=True
                    ):
                        try:
                            create_response = requests.post(
                                f"{api_url}/projects",
                                json={"name": project_name},
                                headers=headers,
                                timeout=10,
                            )
                            
                            if create_response.ok:
                                print_success(f"Project '{project_name}' created")
                            else:
                                print_warning("Could not create project automatically")
                                print_dim("You can create it at https://optixlog.com")
                        except Exception as e:
                            print_warning(f"Could not create project: {e}")
            else:
                print_warning(f"Could not validate API key (status {response.status_code})")
                
        except requests.exceptions.ConnectionError:
            print_warning("Could not connect to server")
            print_dim("Configuration will be saved anyway")
        except Exception as e:
            print_warning(f"Validation error: {e}")
    
    # Save configuration
    if api_key:
        config.set("api_key", api_key)
    if api_url:
        config.set("api_url", api_url)
    if project_name:
        config.set("project", project_name)
    
    print_success(f"Config saved to {CONFIG_FILE}")
    
    click.echo()
    print_dim("Next steps:")
    print_dim("  1. Instrument code: optixlog add-logging script.py")
    print_dim("  2. Run your code: python script.py")
    print_dim("  3. View runs: optixlog runs")
    click.echo()

