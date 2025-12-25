"""
OptixLog CLI - Main entry point

Usage:
    optixlog <command> [options]
    ox <command> [options]  # Short alias
"""

import click
from typing import Optional

from . import __version__


# Create the main CLI group
@click.group()
@click.version_option(version=__version__, prog_name="optixlog")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """OptixLog CLI - Experiment tracking for photonic simulations.
    
    Use 'optixlog <command> --help' for more information on a command.
    """
    ctx.ensure_object(dict)


# Import and register commands
from .commands.init import init
from .commands.login import login
from .commands.config_cmd import config
from .commands.add_logging import add_logging
from .commands.runs import runs
from .commands.run import run
from .commands.projects import projects
from .commands.artifacts import artifacts
from .commands.download import download
from .commands.metrics import metrics
from .commands.compare import compare
from .commands.status import status

cli.add_command(init)
cli.add_command(login)
cli.add_command(config)
cli.add_command(add_logging)
cli.add_command(runs)
cli.add_command(run)
cli.add_command(projects)
cli.add_command(artifacts)
cli.add_command(download)
cli.add_command(metrics)
cli.add_command(compare)
cli.add_command(status)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

