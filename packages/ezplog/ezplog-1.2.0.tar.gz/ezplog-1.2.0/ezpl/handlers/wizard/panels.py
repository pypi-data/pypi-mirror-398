# ///////////////////////////////////////////////////////////////
# EZPL - Wizard Panels Mixin
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Panel methods mixin for Rich Wizard.

This module provides all panel-related methods for the RichWizard class.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
from typing import Any, Optional

# External libraries
from rich.align import Align
from rich.panel import Panel
from rich.text import Text

# Internal modules
from ..utils import safe_str_convert

## ==> CLASSES
# ///////////////////////////////////////////////////////////////


class PanelMixin:
    """
    Mixin providing panel display methods for RichWizard.

    This mixin adds all panel-related functionality including
    generic panels, info panels, success panels, error panels,
    warning panels, and installation panels.
    """

    # ///////////////////////////////////////////////////////////////
    # PANEL METHODS
    # ///////////////////////////////////////////////////////////////

    def panel(
        self,
        content: Any,
        title: Optional[str] = None,
        border_style: str = "blue",
        width: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Display a Rich panel with the given content.

        Args:
            content: Panel content (any type, will be converted to string)
            title: Optional panel title
            border_style: Panel border style (Rich style string)
            width: Optional panel width
            **kwargs: Additional Panel arguments
        """
        try:
            if not isinstance(content, str):
                content = safe_str_convert(content)

            panel = Panel(
                content, title=title, border_style=border_style, width=width, **kwargs
            )
            self._console.print(panel)
        except Exception as e:
            try:
                self._console.print(f"[red]Panel error:[/red] {type(e).__name__}")
            except Exception as e:
                raise ValueError(f"Failed to display panel: {e}") from e

    def info_panel(
        self,
        title: str,
        content: str,
        style: str = "cyan",
        border_style: str = "cyan",
        width: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Display an info panel with title and content.

        Args:
            title: Panel title
            content: Panel content
            style: Content text style
            border_style: Panel border style
            width: Optional panel width
            **kwargs: Additional Panel arguments
        """
        try:
            text = Text(content, style=style)
            panel = Panel(
                Align(text, align="left"),
                title=f"ℹ️ {title}",
                border_style=border_style,
                width=width,
                **kwargs,
            )
            self._console.print(panel)
        except Exception as e:
            try:
                self._console.print(f"[red]Info panel error:[/red] {type(e).__name__}")
            except Exception as e:
                raise ValueError(f"Failed to display info panel: {e}") from e

    def success_panel(
        self,
        title: str,
        content: str,
        border_style: str = "green",
        width: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Display a success panel with green styling.

        Args:
            title: Panel title
            content: Panel content
            border_style: Panel border style
            width: Optional panel width
            **kwargs: Additional Panel arguments
        """
        try:
            text = Text(content, style="green")
            panel = Panel(
                Align(text, align="left"),
                title=f"✅ {title}",
                border_style=border_style,
                width=width,
                **kwargs,
            )
            self._console.print(panel)
        except Exception as e:
            try:
                self._console.print(
                    f"[red]Success panel error:[/red] {type(e).__name__}"
                )
            except Exception as e:
                raise ValueError(f"Failed to display success panel: {e}") from e

    def error_panel(
        self,
        title: str,
        content: str,
        border_style: str = "red",
        width: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Display an error panel with red styling.

        Args:
            title: Panel title
            content: Panel content
            border_style: Panel border style
            width: Optional panel width
            **kwargs: Additional Panel arguments
        """
        try:
            text = Text(content, style="red")
            panel = Panel(
                Align(text, align="left"),
                title=f"❌ {title}",
                border_style=border_style,
                width=width,
                **kwargs,
            )
            self._console.print(panel)
        except Exception as e:
            try:
                self._console.print(f"[red]Error panel error:[/red] {type(e).__name__}")
            except Exception as e:
                raise ValueError(f"Failed to display error panel: {e}") from e

    def warning_panel(
        self,
        title: str,
        content: str,
        border_style: str = "yellow",
        width: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Display a warning panel with yellow styling.

        Args:
            title: Panel title
            content: Panel content
            border_style: Panel border style
            width: Optional panel width
            **kwargs: Additional Panel arguments
        """
        try:
            text = Text(content, style="yellow")
            panel = Panel(
                Align(text, align="left"),
                title=f"⚠️ {title}",
                border_style=border_style,
                width=width,
                **kwargs,
            )
            self._console.print(panel)
        except Exception as e:
            try:
                self._console.print(
                    f"[red]Warning panel error:[/red] {type(e).__name__}"
                )
            except Exception as e:
                raise ValueError(f"Failed to display warning panel: {e}") from e

    def installation_panel(
        self,
        step: str,
        description: str,
        status: str = "pending",
        border_style: str = "blue",
        width: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Display an installation step panel.

        Args:
            step: Installation step name
            description: Step description
            status: Status ("success", "error", "warning", "pending")
            border_style: Panel border style
            width: Optional panel width
            **kwargs: Additional Panel arguments
        """
        try:
            if status == "success":
                icon = "✅"
                style = "green"
            elif status == "error":
                icon = "❌"
                style = "red"
            elif status == "warning":
                icon = "⚠️"
                style = "yellow"
            else:
                icon = "⏳"
                style = "blue"

            text = Text(description, style=style)
            panel = Panel(
                Align(text, align="left"),
                title=f"{icon} {step}",
                border_style=border_style,
                width=width,
                **kwargs,
            )
            self._console.print(panel)
        except Exception as e:
            try:
                self._console.print(
                    f"[red]Installation panel error:[/red] {type(e).__name__}"
                )
            except Exception as e:
                raise ValueError(f"Failed to display installation panel: {e}") from e
