"""
optixlog metrics - Show metrics for a run

Wraps the query.get_metrics() function with CLI interface.
"""

import click
import csv
import sys
from typing import Optional

from ..config import get_config
from ..utils import (
    print_success, print_error, print_dim,
    print_json, print_table
)


@click.command()
@click.argument("run_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--csv", "as_csv", is_flag=True, help="Output as CSV")
@click.option("--api-url", help="API URL (default: from config)")
@click.option("--api-key", help="API key (default: from config)")
@click.pass_context
def metrics(
    ctx: click.Context,
    run_id: str,
    as_json: bool,
    as_csv: bool,
    api_url: Optional[str],
    api_key: Optional[str],
) -> None:
    """Show metrics for a run.
    
    Displays all metrics logged during a run, organized by metric name.
    
    RUN_ID is the ID of the run to query.
    
    Examples:
    
        optixlog metrics abc123
        
        optixlog metrics abc123 --json
        
        optixlog metrics abc123 --csv > metrics.csv
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
    
    if not as_json and not as_csv:
        click.echo(click.style(f"\n📊 Fetching metrics for run {run_id}...\n", bold=True))
    
    try:
        from optixlog import query
        
        metrics_data = query.get_metrics(
            api_url=api_url,
            api_key=api_key,
            run_id=run_id,
        )
        
        if not metrics_data:
            if not as_json and not as_csv:
                print_dim("No metrics found")
            elif as_json:
                print_json({})
            return
        
        if as_json:
            # Convert to JSON-serializable format
            json_data = {}
            for metric_name, values in metrics_data.items():
                json_data[metric_name] = [
                    {"step": step, "value": value}
                    for step, value in values
                ]
            print_json(json_data)
            
        elif as_csv:
            # CSV output - flatten all metrics
            writer = csv.writer(sys.stdout)
            writer.writerow(["metric", "step", "value"])
            for metric_name, values in metrics_data.items():
                for step, value in values:
                    writer.writerow([metric_name, step, value])
        else:
            # Table output
            click.echo(click.style(f"Found {len(metrics_data)} metrics:\n", bold=True))
            
            for metric_name, values in metrics_data.items():
                click.echo(click.style(f"📈 {metric_name}", fg="cyan"))
                print_dim(f"   {len(values)} data points")
                
                # Show first and last few values
                if len(values) <= 6:
                    for step, value in values:
                        print_dim(f"   step {step}: {value}")
                else:
                    for step, value in values[:3]:
                        print_dim(f"   step {step}: {value}")
                    print_dim("   ...")
                    for step, value in values[-2:]:
                        print_dim(f"   step {step}: {value}")
                click.echo()
                
    except ImportError:
        print_error("Could not import optixlog SDK")
        ctx.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        ctx.exit(1)

