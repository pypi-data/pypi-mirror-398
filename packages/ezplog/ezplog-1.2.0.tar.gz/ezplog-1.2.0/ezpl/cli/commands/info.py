# ///////////////////////////////////////////////////////////////
# EZPL - CLI Info Command
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
CLI command for displaying package information.

This module provides the info command for Ezpl.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
from pathlib import Path

import click

# External libraries
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Internal modules
try:
    import ezpl

    EZPL_AVAILABLE = True
except ImportError:
    EZPL_AVAILABLE = False
    ezpl = None

from ...config import ConfigurationManager

## ==> GLOBALS
# ///////////////////////////////////////////////////////////////

console = Console()

## ==> COMMANDS
# ///////////////////////////////////////////////////////////////


@click.command(name="info", help="Display package information")
def info_command() -> None:
    """
    Display package information.

    Show detailed information about the Ezpl package including
    version, location, configuration, and dependencies.
    """
    try:
        if not EZPL_AVAILABLE:
            console.print("[red]Ezpl not available[/red]")
            return

        # Package info
        version = getattr(ezpl, "__version__", "unknown")
        author = getattr(ezpl, "__author__", "unknown")
        maintainer = getattr(ezpl, "__maintainer__", "unknown")
        license_type = getattr(ezpl, "__license__", "unknown")
        description = getattr(ezpl, "__description__", "unknown")
        url = getattr(ezpl, "__url__", "unknown")

        # Package location
        try:
            package_path = (
                Path(ezpl.__file__).parent if hasattr(ezpl, "__file__") else None
            )
        except Exception:
            package_path = None

        # Configuration info
        config_manager = ConfigurationManager()
        config_file = config_manager._config_file
        log_file = config_manager.get_log_file()

        # Build info text
        text = Text()
        text.append("Package Information\n", style="bold bright_blue")
        text.append("=" * 50 + "\n\n", style="dim")

        # Version
        text.append("Version: ", style="bold")
        text.append(f"{version}\n", style="white")

        # Author
        text.append("Author: ", style="bold")
        text.append(f"{author}\n", style="white")

        if maintainer != author:
            text.append("Maintainer: ", style="bold")
            text.append(f"{maintainer}\n", style="white")

        # License
        text.append("License: ", style="bold")
        text.append(f"{license_type}\n", style="white")

        # Description
        text.append("\nDescription:\n", style="bold")
        text.append(f"  {description}\n", style="dim white")

        # URL
        text.append("\nURL: ", style="bold")
        text.append(f"{url}\n", style="cyan")

        # Package location
        if package_path:
            text.append("\nPackage Location: ", style="bold")
            text.append(f"{package_path}\n", style="dim white")

        # Configuration paths
        text.append("\nConfiguration:\n", style="bold")
        text.append("  Config File: ", style="dim")
        text.append(f"{config_file}\n", style="white")
        text.append("  Log File: ", style="dim")
        text.append(f"{log_file}\n", style="white")

        # Display panel
        panel = Panel(
            text,
            title="[bold bright_blue]Ezpl Information[/bold bright_blue]",
            border_style="bright_blue",
            padding=(1, 2),
        )
        console.print(panel)

        # Dependencies table
        try:
            import click as click_module
            import loguru
            import rich

            deps_table = Table(
                title="Dependencies", show_header=True, header_style="bold blue"
            )
            deps_table.add_column("Package", style="cyan")
            deps_table.add_column("Version", style="green")

            deps_table.add_row("loguru", getattr(loguru, "__version__", "unknown"))
            deps_table.add_row("rich", getattr(rich, "__version__", "unknown"))
            deps_table.add_row("click", getattr(click_module, "__version__", "unknown"))

            console.print("\n")
            console.print(deps_table)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
