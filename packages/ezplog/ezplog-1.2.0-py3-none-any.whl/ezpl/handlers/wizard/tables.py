# ///////////////////////////////////////////////////////////////
# EZPL - Wizard Tables Mixin
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Table methods mixin for Rich Wizard.

This module provides all table-related methods for the RichWizard class.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
from typing import Any, Optional

# External libraries
from rich.table import Table

# Internal modules

## ==> CLASSES
# ///////////////////////////////////////////////////////////////


class TableMixin:
    """
    Mixin providing table display methods for RichWizard.

    This mixin adds all table-related functionality including
    generic tables, status tables, dependency tables, and command tables.
    """

    # ///////////////////////////////////////////////////////////////
    # TABLE METHODS
    # ///////////////////////////////////////////////////////////////

    def table(
        self,
        data: list[dict[str, Any]],
        title: Optional[str] = None,
        show_header: bool = True,
        **kwargs,
    ) -> None:
        """
        Display a table from a list of dictionaries.

        Args:
            data: list of dictionaries representing table rows
            title: Optional table title
            show_header: Whether to show column headers
            **kwargs: Additional Table arguments
        """
        if not data:
            return

        try:
            table = Table(title=title, show_header=show_header, **kwargs)

            # Determine columns from first element
            if isinstance(data[0], dict):
                columns = list(data[0].keys())
                for col in columns:
                    table.add_column(col, style="cyan", no_wrap=False)

                # Add rows
                for row in data:
                    table.add_row(*[str(row.get(col, "")) for col in columns])

            self._console.print(table)
        except Exception as e:
            try:
                self._console.print(f"[red]Table error:[/red] {type(e).__name__}")
            except Exception as e:
                raise ValueError(f"Failed to display table: {e}") from e

    def table_from_columns(
        self,
        title: str,
        columns: list[str],
        rows: list[list[Any]],
        show_header: bool = True,
        **kwargs,
    ) -> None:
        """
        Display a table with explicit columns and rows.

        Args:
            title: Table title
            columns: list of column names
            rows: list of row data (each row is a list of values)
            show_header: Whether to show column headers
            **kwargs: Additional Table arguments
        """
        try:
            table = Table(title=title, show_header=show_header, **kwargs)

            # Add columns
            for column in columns:
                table.add_column(column, style="cyan", no_wrap=True)

            # Add rows
            for row in rows:
                table.add_row(*[str(cell) for cell in row])

            self._console.print(table)
        except Exception as e:
            try:
                self._console.print(f"[red]Table error:[/red] {type(e).__name__}")
            except Exception as e:
                raise ValueError(f"Failed to display table: {e}") from e

    def status_table(
        self,
        title: str,
        data: list[dict[str, Any]],
        status_column: str = "Status",
        **kwargs,
    ) -> None:
        """
        Display a status table with colored status indicators.

        Args:
            title: Table title
            data: list of dictionaries representing table rows
            status_column: Name of the status column
            **kwargs: Additional Table arguments
        """
        if not data:
            self.table([{"No data": ""}], title=title, **kwargs)
            return

        try:
            # Get columns from first row
            columns = list(data[0].keys())

            table = Table(title=title, show_header=True, **kwargs)

            # Add columns
            for column in columns:
                if column == status_column:
                    table.add_column(column, style="bold", no_wrap=True)
                else:
                    table.add_column(column, style="cyan", no_wrap=True)

            # Add rows with status styling
            for row_data in data:
                row = []
                for column in columns:
                    value = str(row_data.get(column, ""))
                    if column == status_column:
                        value_lower = value.lower()
                        if "success" in value_lower or "ok" in value_lower:
                            row.append(f"✅ {value}")
                        elif "error" in value_lower or "fail" in value_lower:
                            row.append(f"❌ {value}")
                        elif "warning" in value_lower:
                            row.append(f"⚠️ {value}")
                        else:
                            row.append(f"ℹ️ {value}")
                    else:
                        row.append(value)
                table.add_row(*row)

            self._console.print(table)
        except Exception as e:
            try:
                self._console.print(
                    f"[red]Status table error:[/red] {type(e).__name__}"
                )
            except Exception as e:
                raise ValueError(f"Failed to display status table: {e}") from e

    def dependency_table(self, dependencies: dict[str, str]) -> None:
        """
        Display a table for displaying dependencies.

        Args:
            dependencies: Dictionary mapping tool names to versions
        """
        try:
            table = Table(title="Dependencies", show_header=True)
            table.add_column("Tool", style="cyan", no_wrap=True)
            table.add_column("Version", style="green", no_wrap=True)
            table.add_column("Status", style="bold", no_wrap=True)

            for tool, version in dependencies.items():
                if version:
                    table.add_row(tool, version, "✅ Available")
                else:
                    table.add_row(tool, "N/A", "❌ Missing")

            self._console.print(table)
        except Exception as e:
            try:
                self._console.print(
                    f"[red]Dependency table error:[/red] {type(e).__name__}"
                )
            except Exception as e:
                raise ValueError(f"Failed to display dependency table: {e}") from e

    def command_table(self, commands: list[dict[str, str]]) -> None:
        """
        Display a table for displaying available commands.

        Args:
            commands: list of command dictionaries with keys: command, description, category
        """
        try:
            table = Table(title="Available Commands", show_header=True)
            table.add_column("Command", style="cyan", no_wrap=True)
            table.add_column("Description", style="green")
            table.add_column("Category", style="yellow", no_wrap=True)

            for cmd in commands:
                table.add_row(
                    cmd.get("command", ""),
                    cmd.get("description", ""),
                    cmd.get("category", ""),
                )

            self._console.print(table)
        except Exception as e:
            try:
                self._console.print(
                    f"[red]Command table error:[/red] {type(e).__name__}"
                )
            except Exception as e:
                raise ValueError(f"Failed to display command table: {e}") from e
