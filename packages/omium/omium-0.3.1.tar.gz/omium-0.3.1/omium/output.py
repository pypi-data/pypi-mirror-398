"""
Omium CLI Output Utilities - Rich console output for beautiful CLI experience.

This module provides consistent, beautiful terminal output using the Rich library.
"""

from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.markdown import Markdown
from rich.text import Text
from rich.style import Style
from rich import box

# Create global console instance for consistent output
console = Console()

# Omium brand colors
OMIUM_PRIMARY = "#6366f1"  # Indigo
OMIUM_SUCCESS = "#22c55e"  # Green
OMIUM_WARNING = "#f59e0b"  # Amber
OMIUM_ERROR = "#ef4444"    # Red
OMIUM_INFO = "#3b82f6"     # Blue
OMIUM_MUTED = "#6b7280"    # Gray


def print_success(message: str, title: str = "Success") -> None:
    """Print a success message with green styling."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str, title: str = "Error") -> None:
    """Print an error message with red styling."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message with amber styling."""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message with blue styling."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def print_step(step: int, total: int, message: str) -> None:
    """Print a step indicator for multi-step processes."""
    console.print(f"[dim]({step}/{total})[/dim] {message}")


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """Print a styled header for command output."""
    console.print()
    console.print(f"[bold {OMIUM_PRIMARY}]{title}[/bold {OMIUM_PRIMARY}]")
    if subtitle:
        console.print(f"[dim]{subtitle}[/dim]")
    console.print()


def print_panel(
    content: str,
    title: str = "",
    style: str = "blue",
    padding: tuple = (1, 2)
) -> None:
    """Print content in a styled panel/box."""
    console.print(Panel(
        content,
        title=title if title else None,
        border_style=style,
        padding=padding
    ))


def print_json(data: Any, title: Optional[str] = None) -> None:
    """Print JSON with syntax highlighting."""
    json_str = json.dumps(data, indent=2, default=str)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    if title:
        console.print(f"[bold]{title}[/bold]")
    console.print(syntax)


def print_table(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
    show_header: bool = True
) -> None:
    """Print data as a formatted table."""
    if not data:
        console.print("[dim]No data to display[/dim]")
        return
    
    # Auto-detect columns if not provided
    if columns is None:
        columns = list(data[0].keys())
    
    table = Table(
        title=title,
        box=box.ROUNDED,
        header_style=f"bold {OMIUM_PRIMARY}",
        show_header=show_header,
        row_styles=["", "dim"]  # Alternating row colors
    )
    
    # Add columns
    for col in columns:
        table.add_column(col.replace("_", " ").title())
    
    # Add rows
    for row in data:
        values = [str(row.get(col, "")) for col in columns]
        table.add_row(*values)
    
    console.print(table)


def print_tree(
    data: Dict[str, Any],
    title: str = "Tree",
) -> None:
    """Print hierarchical data as a tree."""
    tree = Tree(f"[bold]{title}[/bold]")
    
    def add_branch(parent: Tree, key: str, value: Any):
        if isinstance(value, dict):
            branch = parent.add(f"[bold]{key}[/bold]")
            for k, v in value.items():
                add_branch(branch, k, v)
        elif isinstance(value, list):
            branch = parent.add(f"[bold]{key}[/bold] [dim]({len(value)} items)[/dim]")
            for i, item in enumerate(value[:5]):  # Show first 5
                add_branch(branch, f"[{i}]", item)
            if len(value) > 5:
                branch.add(f"[dim]... and {len(value) - 5} more[/dim]")
        else:
            parent.add(f"[bold]{key}:[/bold] {value}")
    
    for k, v in data.items():
        add_branch(tree, k, v)
    
    console.print(tree)


def print_execution_status(
    execution_id: str,
    status: str,
    workflow_id: Optional[str] = None,
    progress: Optional[float] = None
) -> None:
    """Print a formatted execution status."""
    status_colors = {
        "running": "yellow",
        "completed": "green",
        "failed": "red",
        "pending": "blue",
        "cancelled": "dim"
    }
    color = status_colors.get(status.lower(), "white")
    
    status_icons = {
        "running": "⟳",
        "completed": "✓",
        "failed": "✗",
        "pending": "○",
        "cancelled": "⊘"
    }
    icon = status_icons.get(status.lower(), "•")
    
    line = f"[{color}]{icon}[/{color}] [bold]{execution_id}[/bold]"
    if workflow_id:
        line += f" [dim]({workflow_id})[/dim]"
    line += f" [{color}]{status.upper()}[/{color}]"
    
    if progress is not None:
        line += f" [dim]{progress:.0%}[/dim]"
    
    console.print(line)


@contextmanager
def progress_spinner(message: str = "Processing..."):
    """Context manager for a spinner during async operations."""
    with console.status(f"[bold blue]{message}[/bold blue]", spinner="dots"):
        yield


def create_progress_bar(description: str = "Progress") -> Progress:
    """Create a progress bar for iterative operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}[/bold blue]"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    )


def print_logo() -> None:
    """Print the Omium ASCII logo."""
    logo = """
[bold #6366f1]
   ██████╗ ███╗   ███╗██╗██╗   ██╗███╗   ███╗
  ██╔═══██╗████╗ ████║██║██║   ██║████╗ ████║
  ██║   ██║██╔████╔██║██║██║   ██║██╔████╔██║
  ██║   ██║██║╚██╔╝██║██║██║   ██║██║╚██╔╝██║
  ╚██████╔╝██║ ╚═╝ ██║██║╚██████╔╝██║ ╚═╝ ██║
   ╚═════╝ ╚═╝     ╚═╝╚═╝ ╚═════╝ ╚═╝     ╚═╝
[/bold #6366f1]
[dim]Fault-tolerant operating system for multi-agent AI[/dim]
    """
    console.print(logo)


def print_welcome(version: str = "0.1.5") -> None:
    """Print welcome message for init command."""
    print_logo()
    console.print(f"[dim]Version {version}[/dim]\n")


def print_divider(style: str = "dim") -> None:
    """Print a horizontal divider line."""
    console.print(f"[{style}]{'─' * console.width}[/{style}]")


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_bytes(size: int) -> str:
    """Format byte size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


class OmiumSpinner:
    """Context manager for spinner with status updates."""
    
    def __init__(self, message: str):
        self.message = message
        self.status = None
    
    def __enter__(self):
        self.status = console.status(f"[bold blue]{self.message}[/bold blue]", spinner="dots")
        self.status.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.status.stop()
        if exc_type is None:
            print_success(self.message.replace("...", " complete"))
        else:
            print_error(f"{self.message.replace('...', ' failed')}: {exc_val}")
        return False
    
    def update(self, message: str) -> None:
        """Update the spinner message."""
        self.message = message
        self.status.update(f"[bold blue]{message}[/bold blue]")
