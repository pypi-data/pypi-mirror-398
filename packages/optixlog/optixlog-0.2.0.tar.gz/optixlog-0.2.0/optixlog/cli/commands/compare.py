"""
optixlog compare - Compare multiple runs

Wraps the query.compare_runs() function with CLI interface.
"""

import click
from typing import Optional, Tuple

from ..config import get_config
from ..utils import (
    print_success, print_error, print_dim,
    print_json, print_table
)


@click.command()
@click.argument("run_ids", nargs=-1, required=True)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--api-url", help="API URL (default: from config)")
@click.option("--api-key", help="API key (default: from config)")
@click.pass_context
def compare(
    ctx: click.Context,
    run_ids: Tuple[str, ...],
    as_json: bool,
    api_url: Optional[str],
    api_key: Optional[str],
) -> None:
    """Compare metrics across multiple runs.
    
    Compares the same metrics logged in different runs side by side.
    
    RUN_IDS are the IDs of the runs to compare (at least 2 required).
    
    Examples:
    
        optixlog compare run1 run2
        
        optixlog compare run1 run2 run3 --json
    """
    if len(run_ids) < 2:
        print_error("At least 2 run IDs are required for comparison")
        ctx.exit(1)
        return
    
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
        click.echo(click.style(f"\n⚖️  Comparing {len(run_ids)} runs...\n", bold=True))
    
    try:
        from optixlog import query
        
        comparison = query.compare_runs(
            api_url=api_url,
            api_key=api_key,
            run_ids=list(run_ids),
        )
        
        if not comparison:
            print_error("Could not compare runs")
            ctx.exit(1)
            return
        
        if as_json:
            comparison_data = {
                "runs": [
                    {
                        "id": r.run_id,
                        "name": r.name,
                        "project_name": r.project_name,
                    }
                    for r in comparison.runs
                ],
                "common_metrics": comparison.common_metrics,
                "metrics_data": comparison.metrics_data,
            }
            print_json(comparison_data)
        else:
            # Summary output
            click.echo(click.style("Runs being compared:", bold=True))
            for run in comparison.runs:
                click.echo(f"  • {click.style(run.name or run.run_id, fg='cyan')}")
            click.echo()
            
            if comparison.common_metrics:
                click.echo(click.style(f"Common metrics ({len(comparison.common_metrics)}):", bold=True))
                
                for metric_name in comparison.common_metrics:
                    click.echo(f"\n  📈 {click.style(metric_name, fg='green')}")
                    
                    metric_data = comparison.metrics_data.get(metric_name, {})
                    for run_id, values in metric_data.items():
                        if values:
                            # Show summary stats
                            if isinstance(values[0], (int, float)):
                                min_val = min(values)
                                max_val = max(values)
                                avg_val = sum(values) / len(values)
                                last_val = values[-1]
                                
                                # Find run name
                                run_name = run_id
                                for r in comparison.runs:
                                    if r.run_id == run_id:
                                        run_name = r.name or run_id
                                        break
                                
                                print_dim(f"     {run_name}:")
                                print_dim(f"       Last: {last_val:.4g}, Min: {min_val:.4g}, Max: {max_val:.4g}, Avg: {avg_val:.4g}")
                            else:
                                print_dim(f"     {run_id}: {len(values)} values")
                
                click.echo()
            else:
                print_dim("No common metrics found between runs")
                click.echo()
                
    except ImportError:
        print_error("Could not import optixlog SDK")
        ctx.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        ctx.exit(1)

