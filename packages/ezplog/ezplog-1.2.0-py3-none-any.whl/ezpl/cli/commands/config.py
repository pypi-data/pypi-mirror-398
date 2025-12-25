# ///////////////////////////////////////////////////////////////
# EZPL - CLI Config Commands
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
CLI commands for configuration management.

This module provides commands for getting, setting, and resetting
Ezpl configuration with support for user environment variables.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
from typing import Optional

import click

# External libraries
from rich.console import Console
from rich.table import Table

# Internal modules
from ...config import ConfigurationManager
from ..utils.env_manager import UserEnvManager

## ==> GLOBALS
# ///////////////////////////////////////////////////////////////

console = Console()

## ==> COMMAND GROUP
# ///////////////////////////////////////////////////////////////


@click.group(name="config", help="⚙️  Manage Ezpl configuration")
def config_group() -> None:
    """
    Configuration management commands.

    Get, set, and reset Ezpl configuration with support for
    user environment variables.
    """


## ==> COMMANDS
# ///////////////////////////////////////////////////////////////


@config_group.command(name="get", help="Get configuration value(s)")
@click.argument("key", required=False, type=str)
@click.option(
    "--show-env",
    "-e",
    is_flag=True,
    help="Show environment variable names for each key",
)
def get_command(key: Optional[str], show_env: bool) -> None:
    """
    Get configuration value(s).

    If KEY is provided, display the value for that key.
    Otherwise, display all configuration values.

    Use --show-env to display the corresponding environment variable names.
    """
    try:
        config_manager = ConfigurationManager()
        env_manager = UserEnvManager()

        if key:
            # Get specific key
            value = config_manager.get(key)
            if value is not None:
                console.print(f"[green]{key}[/green]: {value}")
                if show_env and key in env_manager.CONFIG_TO_ENV:
                    env_var = env_manager.CONFIG_TO_ENV[key]
                    console.print(f"[dim]Environment variable: {env_var}[/dim]")
            else:
                console.print(f"[red]Key '{key}' not found[/red]")
        else:
            # Get all config
            all_config = config_manager.get_all()

            if not all_config:
                console.print("[yellow]No configuration found[/yellow]")
                return

            # Display as table
            if show_env:
                table = Table(
                    title="Ezpl Configuration",
                    show_header=True,
                    header_style="bold blue",
                )
                table.add_column("Key", style="cyan", no_wrap=True)
                table.add_column("Value", style="white")
                table.add_column("Env Variable", style="dim")

                for k, v in sorted(all_config.items()):
                    env_var = env_manager.CONFIG_TO_ENV.get(k, "")
                    table.add_row(k, str(v), env_var if env_var else "-")
            else:
                table = Table(
                    title="Ezpl Configuration",
                    show_header=True,
                    header_style="bold blue",
                )
                table.add_column("Key", style="cyan", no_wrap=True)
                table.add_column("Value", style="white")

                for k, v in sorted(all_config.items()):
                    table.add_row(k, str(v))

            console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@config_group.command(name="set", help="Set configuration value")
@click.argument("key", type=str)
@click.argument("value", type=str)
@click.option(
    "--env",
    "-e",
    is_flag=True,
    help="Also set as user environment variable (uses predefined variable name)",
)
def set_command(key: str, value: str, env: bool) -> None:
    """
    Set a configuration value.

    Set KEY to VALUE in the configuration file.
    The KEY must be one of the predefined configuration keys (e.g., 'log-level', 'printer-level').

    Use --env to also set it as a user environment variable.
    The environment variable name is automatically determined from the key.
    """
    try:
        # Validate key exists in environment variable mapping
        env_manager = UserEnvManager()
        available_keys = list(env_manager.CONFIG_TO_ENV.keys())

        if key not in available_keys:
            console.print(f"[red]✗[/red] Invalid configuration key: [cyan]{key}[/cyan]")
            console.print("\n[yellow]Available configuration keys:[/yellow]")
            for available_key in sorted(available_keys):
                env_var_name = env_manager.CONFIG_TO_ENV[available_key]
                console.print(
                    f"  [cyan]{available_key:25}[/cyan] → [dim]{env_var_name}[/dim]"
                )
            return

        # Set configuration
        config_manager = ConfigurationManager()
        config_manager.set(key, value)
        config_manager.save()

        console.print(
            f"[green]✓[/green] Set [cyan]{key}[/cyan] = [white]{value}[/white]"
        )

        # Set environment variable if requested
        if env:
            env_var_name = env_manager.CONFIG_TO_ENV[key]
            if env_manager.set_user_env(key, value):
                console.print(
                    f"[green]✓[/green] Also set as user environment variable: [dim]{env_var_name}[/dim]"
                )
            else:
                console.print(
                    f"[yellow]⚠[/yellow] Could not set environment variable '{env_var_name}' for '{key}'"
                )
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@config_group.command(name="reset", help="Reset configuration to defaults")
@click.option(
    "--confirm",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def reset_command(confirm: bool) -> None:
    """
    Reset configuration to default values.

    This will reset all configuration values to their defaults
    and remove all user environment variables.
    """
    try:
        if not confirm and not click.confirm(
            "Are you sure you want to reset all configuration to defaults?"
        ):
            console.print("[yellow]Reset cancelled[/yellow]")
            return

        config_manager = ConfigurationManager()
        config_manager.reset_to_defaults()
        config_manager.save()

        env_manager = UserEnvManager()
        env_manager.remove_all_user_env()

        console.print("[green]✓[/green] Configuration reset to defaults")
        console.print("[green]✓[/green] User environment variables removed")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
