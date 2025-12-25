# ///////////////////////////////////////////////////////////////
# EZPL - Wizard Core
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Core RichWizard class for Ezpl logging framework.

This module provides the main RichWizard class that combines all mixins
for panels, tables, JSON, and progress functionality.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports

# External libraries
from rich.console import Console

# Internal modules
from ...types import Pattern, get_pattern_color
from .dynamic import DynamicProgressMixin
from .json import JsonMixin
from .panels import PanelMixin
from .progress import ProgressMixin
from .tables import TableMixin

## ==> CLASSES
# ///////////////////////////////////////////////////////////////


class RichWizard(
    PanelMixin, TableMixin, JsonMixin, ProgressMixin, DynamicProgressMixin
):
    """
    Rich Wizard for advanced console display capabilities.

    This class provides specialized methods for creating and displaying
    Rich-based panels, tables, JSON, and other formatted outputs,
    including advanced progress bars.

    The class combines multiple mixins to provide a unified API:
    - PanelMixin: Panel display methods
    - TableMixin: Table display methods
    - JsonMixin: JSON display methods
    - ProgressMixin: Progress bar methods
    - DynamicProgressMixin: Dynamic layered progress bar methods
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, console: Console) -> None:
        """
        Initialize the Rich Wizard.

        Args:
            console: Rich Console instance to use for output
        """
        self._console = console
        # Build prefix with Rich markup for progress bars (using SYSTEM pattern)
        pattern_color = get_pattern_color(Pattern.SYSTEM)
        self._progress_prefix = (
            f"[{pattern_color}]• [bold {pattern_color}]{'SYSTEM'.ljust(8)}"
            f"[/bold {pattern_color}][dim white]:: [/dim white]"
        )

    # ///////////////////////////////////////////////////////////////
    # REPRESENTATION METHODS
    # ///////////////////////////////////////////////////////////////

    def __str__(self) -> str:
        """String representation of the Rich Wizard."""
        return "RichWizard()"

    def __repr__(self) -> str:
        """Detailed string representation of the Rich Wizard."""
        return "RichWizard(console=Console())"
