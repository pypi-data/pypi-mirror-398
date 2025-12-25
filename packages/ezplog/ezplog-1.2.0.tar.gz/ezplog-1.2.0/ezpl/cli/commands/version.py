# ///////////////////////////////////////////////////////////////
# EZPL - CLI Version Command
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
CLI command for displaying version information.

This module provides the version command for Ezpl.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
import click

# External libraries
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Internal modules
try:
    import ezpl

    EZPL_AVAILABLE = True
except ImportError:
    EZPL_AVAILABLE = False
    ezpl = None

## ==> GLOBALS
# ///////////////////////////////////////////////////////////////

console = Console()

## ==> COMMANDS
# ///////////////////////////////////////////////////////////////


@click.command(name="version", help="Display version information")
@click.option(
    "--full",
    "-f",
    is_flag=True,
    help="Display full version information",
)
def version_command(full: bool) -> None:
    """
    Display version information.

    Show the current version of Ezpl.
    Use --full for detailed version information.
    """
    try:
        if not EZPL_AVAILABLE:
            console.print("[red]Ezpl not available[/red]")
            return

        version = getattr(ezpl, "__version__", "unknown")
        author = getattr(ezpl, "__author__", "unknown")
        license_type = getattr(ezpl, "__license__", "unknown")

        if full:
            # Full version info
            text = Text()
            text.append("Ezpl ", style="bold bright_blue")
            text.append(f"v{version}", style="bold green")
            text.append("\n\n", style="reset")

            text.append("Author: ", style="dim")
            text.append(f"{author}\n", style="white")
            text.append("License: ", style="dim")
            text.append(f"{license_type}\n", style="white")

            if hasattr(ezpl, "__url__"):
                text.append("URL: ", style="dim")
                text.append(f"{ezpl.__url__}\n", style="white")

            panel = Panel(
                text,
                title="[bold bright_blue]Version Information[/bold bright_blue]",
                border_style="bright_blue",
                padding=(1, 2),
            )
            console.print(panel)
        else:
            # Simple version
            console.print(
                f"[bold bright_blue]Ezpl[/bold bright_blue] v[bold green]{version}[/bold green]"
            )
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
