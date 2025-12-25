# ///////////////////////////////////////////////////////////////
# EZPL - CLI Logs Commands
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
CLI commands for log file operations.

This module provides commands for viewing, searching, analyzing,
and managing log files.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click

# External libraries
from rich.console import Console
from rich.table import Table

# Internal modules
from ...config import ConfigurationManager
from ..utils.log_parser import LogParser
from ..utils.log_stats import LogStatistics

## ==> GLOBALS
# ///////////////////////////////////////////////////////////////

console = Console()

## ==> HELPER FUNCTIONS
# ///////////////////////////////////////////////////////////////


def _get_log_file(file: Optional[Path]) -> Path:
    """
    Get log file path from parameter or configuration.

    Args:
        file: Optional file path from command line

    Returns:
        Path to log file

    Raises:
        click.ClickException: If file doesn't exist
    """
    if file:
        log_file = Path(file)
    else:
        config_manager = ConfigurationManager()
        log_file = config_manager.get_log_file()

    if not log_file.exists():
        raise click.ClickException(f"Log file not found: {log_file}")

    return log_file


def _get_log_dir(dir: Optional[Path]) -> Path:
    """
    Get log directory from parameter or configuration.

    Args:
        dir: Optional directory path from command line

    Returns:
        Path to log directory
    """
    if dir:
        return Path(dir)
    else:
        config_manager = ConfigurationManager()
        log_dir = config_manager.get("log-dir")
        if isinstance(log_dir, str):
            return Path(log_dir)
        return Path(log_dir) if log_dir else Path.home() / ".ezpl" / "logs"


def _parse_size(size_str: str) -> int:
    """
    Parse size string to bytes.

    Args:
        size_str: Size string (e.g., "100MB", "1GB", "500KB")

    Returns:
        Size in bytes
    """
    size_str = size_str.upper().strip()
    multipliers = {"KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}

    for unit, multiplier in multipliers.items():
        if size_str.endswith(unit):
            try:
                value = float(size_str[: -len(unit)])
                return int(value * multiplier)
            except ValueError as e:
                raise click.ClickException(f"Invalid size format: {size_str}") from e

    # Try to parse as bytes
    try:
        return int(size_str)
    except ValueError as e:
        raise click.ClickException(f"Invalid size format: {size_str}") from e


## ==> COMMAND GROUP
# ///////////////////////////////////////////////////////////////


@click.group(name="logs", help="📊 Manage and view log files")
def logs_group() -> None:
    """
    Log file management commands.

    View, search, analyze, and manage Ezpl log files.
    """


## ==> COMMANDS
# ///////////////////////////////////////////////////////////////


@logs_group.command(name="view", help="View log file contents")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    help="Path to log file (default: from config)",
)
@click.option("--lines", "-n", type=int, default=50, help="Number of lines to display")
@click.option(
    "--level",
    "-l",
    type=str,
    help="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--follow",
    "-F",
    is_flag=True,
    help="Follow log file (like tail -f)",
)
def view_command(
    file: Optional[Path], lines: int, level: Optional[str], follow: bool
) -> None:
    """
    View log file contents.

    Display log entries from the specified file with optional filtering.
    """
    try:
        log_file = _get_log_file(file)
        parser = LogParser(log_file)

        if follow:
            # Follow mode (tail -f)
            console.print(f"[cyan]Following {log_file}...[/cyan]")
            console.print("[dim]Press Ctrl+C to stop[/dim]\n")

            try:
                with open(log_file, encoding="utf-8") as f:
                    # Go to end of file
                    f.seek(0, 2)

                    while True:
                        line = f.readline()
                        if line:
                            entry = parser.parse_line(line, 0)
                            if entry:  # noqa: SIM102
                                if not level or entry.level.upper() == level.upper():
                                    console.print(entry.raw_line)
                        else:
                            time.sleep(0.1)
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopped following[/yellow]")
        else:
            # Regular view
            entries = parser.parse_lines(max_lines=lines)

            if level:
                entries = [e for e in entries if e.level.upper() == level.upper()]

            if not entries:
                console.print("[yellow]No log entries found[/yellow]")
                return

            # Display entries
            for entry in entries:
                console.print(entry.raw_line)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@logs_group.command(name="search", help="Search log entries")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    help="Path to log file (default: from config)",
)
@click.option(
    "--pattern",
    "-p",
    type=str,
    required=True,
    help="Search pattern (regex supported)",
)
@click.option(
    "--level",
    "-l",
    type=str,
    help="Filter by log level",
)
@click.option(
    "--case-sensitive",
    "-c",
    is_flag=True,
    help="Case-sensitive search",
)
def search_command(
    file: Optional[Path],
    pattern: str,
    level: Optional[str],
    case_sensitive: bool,
) -> None:
    """
    Search for log entries matching a pattern.

    Search through log files using regex patterns with optional level filtering.
    """
    try:
        log_file = _get_log_file(file)
        parser = LogParser(log_file)

        # Search entries
        results = list(parser.search(pattern, case_sensitive=case_sensitive))

        # Filter by level if specified
        if level:
            results = [e for e in results if e.level.upper() == level.upper()]

        if not results:
            console.print(
                f"[yellow]No entries found matching pattern: {pattern}[/yellow]"
            )
            return

        # Display results
        console.print(f"[green]Found {len(results)} matching entries:[/green]\n")
        for entry in results:
            console.print(entry.raw_line)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@logs_group.command(name="stats", help="Display log statistics")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    help="Path to log file (default: from config)",
)
@click.option(
    "--format",
    "-F",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    help="Output format",
)
def stats_command(file: Optional[Path], format: str) -> None:
    """
    Display statistics about log files.

    Show counts by level, file size, date ranges, and temporal distribution.
    """
    try:
        log_file = _get_log_file(file)
        stats = LogStatistics(log_file)
        all_stats = stats.get_all_stats()

        if format == "json":
            # JSON output
            console.print(json.dumps(all_stats, indent=2, default=str))
        else:
            # Table output
            # File info
            file_info = all_stats["file_info"]
            info_table = Table(
                title="File Information", show_header=True, header_style="bold blue"
            )
            info_table.add_column("Property", style="cyan")
            info_table.add_column("Value", style="white")

            info_table.add_row("Path", file_info["file_path"])
            info_table.add_row(
                "Size", f"{file_info['size_mb']} MB ({file_info['size_bytes']} bytes)"
            )
            info_table.add_row("Entries", str(file_info["line_count"]))

            if file_info["date_range"]:
                date_range = file_info["date_range"]
                info_table.add_row(
                    "First Entry",
                    (
                        date_range["first"].strftime("%Y-%m-%d %H:%M:%S")
                        if date_range["first"]
                        else "N/A"
                    ),
                )
                info_table.add_row(
                    "Last Entry",
                    (
                        date_range["last"].strftime("%Y-%m-%d %H:%M:%S")
                        if date_range["last"]
                        else "N/A"
                    ),
                )

            console.print(info_table)

            # Level counts
            level_counts = all_stats["level_counts"]
            if level_counts:
                level_table = Table(
                    title="Level Distribution",
                    show_header=True,
                    header_style="bold blue",
                )
                level_table.add_column("Level", style="cyan")
                level_table.add_column("Count", style="green")

                for level, count in sorted(
                    level_counts.items(), key=lambda x: x[1], reverse=True
                ):
                    level_table.add_row(level, str(count))

                console.print("\n")
                console.print(level_table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@logs_group.command(name="tail", help="Display last lines of log file")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    help="Path to log file (default: from config)",
)
@click.option("--lines", "-n", type=int, default=20, help="Number of lines to display")
@click.option(
    "--follow",
    "-F",
    is_flag=True,
    help="Follow log file (like tail -f)",
)
def tail_command(file: Optional[Path], lines: int, follow: bool) -> None:
    """
    Display the last lines of a log file.

    Similar to Unix 'tail' command with optional follow mode.
    """
    try:
        log_file = _get_log_file(file)
        parser = LogParser(log_file)

        if follow:
            # Use view command's follow mode
            view_command(file, lines=lines, level=None, follow=True)
        else:
            # Get last N lines
            entries = parser.get_last_lines(lines)

            if not entries:
                console.print("[yellow]No log entries found[/yellow]")
                return

            # Display entries
            for entry in entries:
                console.print(entry.raw_line)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@logs_group.command(name="list", help="List log files")
@click.option(
    "--dir",
    "-d",
    type=click.Path(exists=True, path_type=Path),
    help="Directory to search (default: from config)",
)
def list_command(dir: Optional[Path]) -> None:
    """
    List available log files.

    Display all log files in the configured log directory.
    """
    try:
        log_dir = _get_log_dir(dir)

        if not log_dir.exists():
            console.print(f"[yellow]Log directory does not exist: {log_dir}[/yellow]")
            return

        # Find all log files
        log_files = sorted(
            log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True
        )

        if not log_files:
            console.print(f"[yellow]No log files found in {log_dir}[/yellow]")
            return

        # Display as table
        table = Table(
            title=f"Log Files in {log_dir}", show_header=True, header_style="bold blue"
        )
        table.add_column("File", style="cyan")
        table.add_column("Size", style="green")
        table.add_column("Modified", style="white")

        for log_file in log_files:
            try:
                size = log_file.stat().st_size
                size_mb = size / (1024 * 1024)
                modified = datetime.fromtimestamp(log_file.stat().st_mtime)
                table.add_row(
                    log_file.name,
                    f"{size_mb:.2f} MB",
                    modified.strftime("%Y-%m-%d %H:%M:%S"),
                )
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@logs_group.command(name="clean", help="Clean old log files")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    help="Specific file to clean",
)
@click.option(
    "--days",
    "-d",
    type=int,
    help="Delete files older than N days",
)
@click.option(
    "--size",
    "-s",
    type=str,
    help="Delete files larger than SIZE (e.g., '100MB')",
)
@click.option(
    "--confirm",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def clean_command(
    file: Optional[Path], days: Optional[int], size: Optional[str], confirm: bool
) -> None:
    """
    Clean old or large log files.

    Remove log files based on age or size criteria.
    """
    try:
        if file:
            # Clean specific file
            files_to_clean = [Path(file)]
        else:
            # Clean from directory
            log_dir = _get_log_dir(None)
            if not log_dir.exists():
                console.print(
                    f"[yellow]Log directory does not exist: {log_dir}[/yellow]"
                )
                return

            files_to_clean = list(log_dir.glob("*.log"))

        if not files_to_clean:
            console.print("[yellow]No log files to clean[/yellow]")
            return

        # Filter by criteria
        files_to_delete = []

        for log_file in files_to_clean:
            should_delete = False

            if days:
                # Check age
                file_age = datetime.now() - datetime.fromtimestamp(
                    log_file.stat().st_mtime
                )
                if file_age > timedelta(days=days):
                    should_delete = True

            if size:
                # Check size
                file_size = log_file.stat().st_size
                size_bytes = _parse_size(size)
                if file_size > size_bytes:
                    should_delete = True

            if should_delete:
                files_to_delete.append(log_file)

        if not files_to_delete:
            console.print("[green]No files match the cleanup criteria[/green]")
            return

        # Confirm deletion
        if not confirm:
            console.print(
                f"[yellow]Files to be deleted ({len(files_to_delete)}):[/yellow]"
            )
            for f in files_to_delete:
                console.print(f"  - {f}")

            if not click.confirm("\nAre you sure you want to delete these files?"):
                console.print("[yellow]Cleanup cancelled[/yellow]")
                return

        # Delete files
        deleted_count = 0
        for log_file in files_to_delete:
            try:
                log_file.unlink()
                deleted_count += 1
                console.print(f"[green]✓[/green] Deleted: {log_file}")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to delete {log_file}: {e}")

        console.print(f"\n[green]Deleted {deleted_count} file(s)[/green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@logs_group.command(name="export", help="Export log file")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    help="Path to log file (default: from config)",
)
@click.option(
    "--format",
    "-F",
    type=click.Choice(["json", "csv", "txt"], case_sensitive=False),
    default="json",
    help="Export format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: stdout)",
)
def export_command(file: Optional[Path], format: str, output: Optional[Path]) -> None:
    """
    Export log file to different formats.

    Convert log files to JSON, CSV, or plain text format.
    """
    try:
        log_file = _get_log_file(file)
        parser = LogParser(log_file)
        entries = list(parser.parse())

        if not entries:
            console.print("[yellow]No log entries to export[/yellow]")
            return

        # Export based on format
        if format == "json":
            data = [entry.to_dict() for entry in entries]
            content = json.dumps(data, indent=2, default=str)
        elif format == "csv":
            import csv
            from io import StringIO

            output_buffer = StringIO()
            writer = csv.DictWriter(
                output_buffer,
                fieldnames=[
                    "timestamp",
                    "level",
                    "module",
                    "function",
                    "line",
                    "message",
                ],
            )
            writer.writeheader()
            for entry in entries:
                writer.writerow(entry.to_dict())
            content = output_buffer.getvalue()
        else:  # txt
            content = "\n".join(entry.raw_line for entry in entries)

        # Write output
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            console.print(f"[green]✓[/green] Exported to {output_path}")
        else:
            console.print(content)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
