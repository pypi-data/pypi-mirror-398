"""
optixlog config - Manage configuration

Get, set, and list config values stored in ~/.config/optixlog/config.toml
"""

import click
from typing import Optional

from ..config import get_config, CONFIG_FILE
from ..utils import print_success, print_error, print_dim, mask_api_key


@click.group(invoke_without_command=True)
@click.pass_context
def config(ctx: click.Context) -> None:
    """Manage OptixLog configuration.
    
    Configuration is stored at ~/.config/optixlog/config.toml
    
    Examples:
    
        optixlog config list
        
        optixlog config get api_key
        
        optixlog config set project "NewProject"
    """
    if ctx.invoked_subcommand is None:
        # Default to list
        ctx.invoke(list_config)


@config.command("list")
def list_config() -> None:
    """List all configuration values."""
    click.echo(click.style("\n📋 OptixLog Configuration\n", bold=True))
    
    cfg = get_config()
    
    if not cfg.exists():
        print_dim("No configuration found")
        print_dim("Run: optixlog init")
        click.echo()
        return
    
    all_config = cfg.get_all_sections()
    
    if not all_config or all(not v for v in all_config.values()):
        print_dim("Configuration file is empty")
        print_dim("Run: optixlog init")
        click.echo()
        return
    
    for section, values in all_config.items():
        if values:
            click.echo(click.style(f"[{section}]", fg="blue"))
            for key, value in values.items():
                display_value = mask_api_key(value) if key == "api_key" else value
                click.echo(f"  {click.style(key, fg='cyan')}: {display_value}")
            click.echo()
    
    print_dim(f"Config file: {CONFIG_FILE}")
    click.echo()


@config.command("get")
@click.argument("key")
@click.option("-s", "--section", default="default", help="Config section")
def get_value(key: str, section: str) -> None:
    """Get a configuration value.
    
    KEY is the config key to retrieve (e.g., api_key, project, api_url)
    """
    cfg = get_config()
    value = cfg.get(key, section=section)
    
    if value is not None:
        # Mask API key in output
        if key == "api_key":
            click.echo(mask_api_key(value))
        else:
            click.echo(value)
    else:
        print_dim("not set")


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.option("-s", "--section", default="default", help="Config section")
def set_value(key: str, value: str, section: str) -> None:
    """Set a configuration value.
    
    KEY is the config key to set (e.g., api_key, project, api_url)
    
    VALUE is the value to assign
    """
    cfg = get_config()
    cfg.set(key, value, section=section)
    print_success(f"Set {key}")


@config.command("delete")
@click.argument("key")
@click.option("-s", "--section", default="default", help="Config section")
def delete_value(key: str, section: str) -> None:
    """Delete a configuration value.
    
    KEY is the config key to delete
    """
    cfg = get_config()
    
    if cfg.delete(key, section=section):
        print_success(f"Deleted {key}")
    else:
        print_error(f"Key '{key}' not found")


@config.command("path")
def show_path() -> None:
    """Show the configuration file path."""
    click.echo(str(CONFIG_FILE))

