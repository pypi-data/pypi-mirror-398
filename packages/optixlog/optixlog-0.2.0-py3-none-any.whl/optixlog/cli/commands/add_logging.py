"""
optixlog add-logging - Auto-instrument Python code

Sends code to the backend for transformation to add OptixLog instrumentation.
"""

import click
import requests
import shutil
from pathlib import Path
from typing import Optional

from ..config import get_config
from ..utils import print_success, print_error, print_warning, print_dim


def detect_language(file_path: Path) -> str:
    """Detect file language based on extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".py":
        return "python"
    elif suffix == ".ipynb":
        return "notebook"
    return "unknown"


@click.command("add-logging")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--no-backup", is_flag=True, help="Do not create a backup file")
@click.option("--api-url", help="API URL (default: from config)")
@click.pass_context
def add_logging(
    ctx: click.Context,
    file: Path,
    no_backup: bool,
    api_url: Optional[str],
) -> None:
    """Auto-instrument Python code with OptixLog.
    
    Sends the file to the OptixLog backend for transformation, which adds
    the necessary imports, initialization, and logging calls.
    
    FILE is the path to the .py or .ipynb file to instrument.
    
    Examples:
    
        optixlog add-logging script.py
        
        optixlog add-logging notebook.ipynb --no-backup
    """
    file = file.resolve()
    
    # Check file type
    language = detect_language(file)
    if language == "unknown":
        print_error("Only .py and .ipynb files are supported")
        ctx.exit(1)
        return
    
    config = get_config()
    
    # Get API URL
    if not api_url:
        api_url = config.api_url
    
    click.echo(click.style(f"\n🔍 Instrumenting: {file.name}\n", bold=True))
    
    # Read original file
    try:
        original_content = file.read_text(encoding="utf-8")
    except Exception as e:
        print_error(f"Could not read file: {e}")
        ctx.exit(1)
        return
    
    # Send to backend for transformation
    print_dim(f"Sending to backend at {api_url}...")
    
    try:
        response = requests.post(
            f"{api_url}/cli/transform",
            json={
                "path": str(file),
                "language": language,
                "contents": original_content,
            },
            timeout=30,
        )
        
        if response.status_code == 404:
            print_error("Transform endpoint not available on this server")
            print_dim("The server may not support code transformation")
            ctx.exit(1)
            return
        
        if not response.ok:
            print_error(f"Transformation failed (status {response.status_code})")
            try:
                error_data = response.json()
                if "error" in error_data:
                    print_dim(f"Error: {error_data['error']}")
            except Exception:
                pass
            ctx.exit(1)
            return
        
        data = response.json()
        modified_content = data.get("contents")
        
        if not modified_content:
            print_error("Transformation returned empty content")
            ctx.exit(1)
            return
        
    except requests.exceptions.ConnectionError:
        print_error(f"Could not connect to {api_url}")
        print_dim("Please check your internet connection")
        ctx.exit(1)
        return
    except requests.exceptions.Timeout:
        print_error("Request timed out")
        ctx.exit(1)
        return
    except Exception as e:
        print_error(f"Error during transformation: {e}")
        ctx.exit(1)
        return
    
    # Create backup if requested
    if not no_backup:
        backup_suffix = "_backup"
        backup_path = file.with_stem(file.stem + backup_suffix)
        try:
            shutil.copy2(file, backup_path)
            print_dim(f"Backup created: {backup_path.name}")
        except Exception as e:
            print_warning(f"Could not create backup: {e}")
    
    # Write modified file
    try:
        file.write_text(modified_content, encoding="utf-8")
        print_success(f"File instrumented: {file}")
    except Exception as e:
        print_error(f"Could not write file: {e}")
        ctx.exit(1)
        return
    
    click.echo()
    print_dim("Run your code:")
    print_dim(f"  python {file}")
    click.echo()

