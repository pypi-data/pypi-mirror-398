# ///////////////////////////////////////////////////////////////
# EZPL - CLI Main Entry Point
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Main CLI entry point for Ezpl logging framework.

This module provides the command-line interface for managing Ezpl
configuration, viewing logs, and performing various operations.
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

from .commands import config, info, logs, version

## ==> GLOBALS
# ///////////////////////////////////////////////////////////////

console = Console()

## ==> CLI GROUP
# ///////////////////////////////////////////////////////////////


@click.group(
    name="ezpl",
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(
    version=ezpl.__version__ if EZPL_AVAILABLE else "1.0.0",
    prog_name="Ezpl CLI",
    message="%(prog)s version %(version)s",
)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    🚀 Ezpl CLI - Modern Python Logging Framework

    Command-line interface for managing Ezpl logging configuration,
    viewing logs, and performing various operations.

    Use 'ezpl <command> --help' for more information on a specific command.
    """
    # Si aucune commande n'est invoquée, afficher l'aide
    if ctx.invoked_subcommand is None:
        _display_welcome()
        click.echo(ctx.get_help())


def _display_welcome() -> None:
    """Display welcome message with Rich."""
    try:
        welcome_text = Text()
        welcome_text.append("🚀 ", style="bold bright_green")
        welcome_text.append("Ezpl CLI", style="bold bright_blue")
        welcome_text.append(" - Modern Python Logging Framework", style="dim white")

        panel = Panel(
            welcome_text,
            title="[bold bright_blue]Welcome[/bold bright_blue]",
            border_style="bright_blue",
            padding=(1, 2),
        )
        console.print(panel)
    except Exception:
        # Fallback si Rich n'est pas disponible
        click.echo("🚀 Ezpl CLI - Modern Python Logging Framework")


## ==> COMMAND GROUPS
# ///////////////////////////////////////////////////////////////


# Logs group
cli.add_command(logs.logs_group)

# Config group
cli.add_command(config.config_group)

# Version command
cli.add_command(version.version_command)

# Info command
cli.add_command(info.info_command)


## ==> MAIN ENTRY POINT
# ///////////////////////////////////////////////////////////////


def main() -> None:
    """
    Main entry point for the CLI.

    This function is called when the CLI is invoked from the command line.
    """
    try:
        cli()
    except KeyboardInterrupt as e:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise SystemExit(1) from e
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
