"""
CLI Utilities - Shared helpers for output formatting and common operations
"""

import json
import sys
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# Initialize console
console = Console() if RICH_AVAILABLE else None


def print_success(message: str) -> None:
    """Print a success message with green checkmark."""
    if console:
        console.print(f"[green]✓[/green] {message}")
    else:
        print(f"✓ {message}")


def print_error(message: str) -> None:
    """Print an error message with red X."""
    if console:
        console.print(f"[red]✗[/red] {message}")
    else:
        print(f"✗ {message}", file=sys.stderr)


def print_warning(message: str) -> None:
    """Print a warning message with yellow symbol."""
    if console:
        console.print(f"[yellow]⚠[/yellow] {message}")
    else:
        print(f"⚠ {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    if console:
        console.print(f"[cyan]ℹ[/cyan] {message}")
    else:
        print(f"ℹ {message}")


def print_dim(message: str) -> None:
    """Print a dimmed/secondary message."""
    if console:
        console.print(f"[dim]{message}[/dim]")
    else:
        print(message)


def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, default=str))


def print_table(
    title: str,
    columns: List[str],
    rows: List[List[Any]],
    show_header: bool = True
) -> None:
    """Print data as a formatted table."""
    if console and RICH_AVAILABLE:
        table = Table(title=title, box=box.ROUNDED, show_header=show_header)
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        console.print(table)
    else:
        # Fallback to simple text output
        if title:
            print(f"\n{title}")
            print("-" * len(title))
        if show_header:
            print(" | ".join(columns))
            print("-" * (sum(len(c) for c in columns) + 3 * (len(columns) - 1)))
        for row in rows:
            print(" | ".join(str(cell) for cell in row))


def print_panel(title: str, content: str) -> None:
    """Print content in a bordered panel."""
    if console and RICH_AVAILABLE:
        console.print(Panel(content, title=title, border_style="blue"))
    else:
        print(f"\n=== {title} ===")
        print(content)
        print("=" * (len(title) + 8))


def mask_api_key(key: Optional[str]) -> str:
    """Mask an API key for display, showing only last 8 characters."""
    if not key:
        return "[not set]"
    if len(key) <= 8:
        return "***"
    return f"***{key[-8:]}"


def format_size(size_bytes: Optional[int]) -> str:
    """Format byte size as human-readable string."""
    if size_bytes is None:
        return "unknown"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_datetime(dt_str: Optional[str]) -> str:
    """Format ISO datetime string for display."""
    if not dt_str:
        return "unknown"
    # Simple formatting - just return date portion if it's an ISO string
    if "T" in dt_str:
        return dt_str.replace("T", " ").split(".")[0]
    return dt_str

