# ///////////////////////////////////////////////////////////////
# EZPL - Wizard Dynamic Progress Mixin
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Dynamic progress methods mixin for Rich Wizard.

This module provides dynamic layered progress bar functionality with
layers that can appear, progress, and disappear automatically.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Optional

# External libraries
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.text import Text

# Internal modules

## ==> CLASSES
# ///////////////////////////////////////////////////////////////


class ConditionalStatusColumn(TextColumn):
    """A text column that only shows status if the field exists."""

    def __init__(self):
        super().__init__("")  # Empty text format, we override render

    def render(self, task):
        if hasattr(task, "fields") and "status" in task.fields:
            return Text(str(task.fields["status"]), style="dim")
        return Text("")


class ConditionalDetailsColumn(TextColumn):
    """A text column that only shows details if the field exists."""

    def __init__(self):
        super().__init__("")  # Empty text format, we override render

    def render(self, task):
        if hasattr(task, "fields") and "details" in task.fields:
            return Text(str(task.fields["details"]), style="dim")
        return Text("")


class DynamicLayeredProgress:
    """
    Manages a dynamic layered progress bar with disappearing layers.

    This class provides a progress bar system where layers can appear,
    progress, and disappear based on the current state of operations.
    """

    def __init__(
        self,
        console,
        progress_prefix: str,
        stages: list[dict],
        show_time: bool = True,
    ) -> None:
        """
        Initialize the dynamic layered progress bar.

        Args:
            console: Rich Console instance
            progress_prefix: Prefix string for progress bars
            stages: List of stage configurations
            show_time: Whether to show elapsed and remaining time
        """
        self._console = console
        self._progress_prefix = progress_prefix
        self.stages = stages
        self.show_time = show_time
        self.progress = None
        self.task_ids = {}
        self.active_layers = []
        self.completed_layers = []
        self.layer_metadata = {}  # Store additional layer info
        self._emergency_stopped = False
        self._emergency_message = None

        # Detect main layer and setup hierarchy
        self._setup_hierarchy()

    def _setup_hierarchy(self) -> None:
        """Setup layer hierarchy and detect main layer."""
        self.has_main_layer = False
        self.main_layer_name = None
        self.sub_layers = []

        # Detect main layer
        for stage in self.stages:
            if stage.get("type") == "main":
                self.has_main_layer = True
                self.main_layer_name = stage.get("name", "main")
                break

        # If main layer found, setup sub-layers
        if self.has_main_layer:
            self.sub_layers = [
                stage for stage in self.stages if stage.get("type") != "main"
            ]
            # Auto-configure main layer steps if not provided
            for stage in self.stages:
                if stage.get("type") == "main" and "steps" not in stage:
                    stage["steps"] = [
                        s.get("name", f"Step {i + 1}")
                        for i, s in enumerate(self.sub_layers)
                    ]

    def _create_progress_bar(self) -> Progress:
        """Create the Rich Progress instance with proper columns."""
        # Build columns for the main progress bar
        columns = [
            TextColumn(self._progress_prefix),  # Ezpl prefix
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            ConditionalDetailsColumn(),  # Conditional details column
            ConditionalStatusColumn(),  # Conditional status column
        ]

        # Check if we have any download layers to add download columns
        has_download = any(stage.get("type") == "download" for stage in self.stages)
        if has_download:
            columns.extend(
                [
                    DownloadColumn(),  # Download info column
                    TransferSpeedColumn(),  # Transfer speed column
                ]
            )

        if self.show_time:
            columns.extend(
                [
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                ]
            )

        return Progress(*columns, console=self._console)

    def _create_layer(self, layer_config: dict) -> int:
        """Create a new layer in the progress bar.

        Args:
            layer_config: Layer configuration dictionary

        Returns:
            Task ID of the created layer
        """
        layer_name = layer_config.get("name", f"Layer_{len(self.task_ids)}")
        layer_type = layer_config.get("type", "progress")
        layer_desc = layer_config.get("description", layer_name)
        layer_style = layer_config.get("style", "default")

        # Determine layer prefix and styling based on hierarchy
        if self.has_main_layer and layer_type == "main":
            # Main layer: bold and prominent
            layer_style = "bold " + layer_style if layer_style != "default" else "bold"
        elif self.has_main_layer and layer_type != "main":
            # Sub-layer: add indentation and use softer colors
            layer_desc = f"  ├─ {layer_desc}"

        # Initialize common fields for all layer types
        common_fields = {
            "details": "",  # Initialize details field for all types
        }

        if layer_type == "steps":
            # Handle step-based layer
            steps = layer_config.get("steps", [])
            layer_total = len(steps)
            task_id = self.progress.add_task(
                f"[{layer_style}]{layer_desc}",
                total=layer_total,
                steps=steps,  # Store steps for later use
                **common_fields,
            )
        elif layer_type == "spinner":
            # Handle spinner layer (indeterminate progress)
            task_id = self.progress.add_task(
                f"[{layer_style}]{layer_desc}",
                total=None,  # Indeterminate
                **common_fields,
            )
        elif layer_type == "download":
            # Handle download layer with speed and size info
            total_size = layer_config.get("total_size", 100)
            filename = layer_config.get("filename", "")
            download_fields = {
                **common_fields,
                "filename": filename,  # Store filename for download info
            }
            task_id = self.progress.add_task(
                f"[{layer_style}]{layer_desc}", total=total_size, **download_fields
            )
        elif layer_type == "main":
            # Handle main layer (special case)
            steps = layer_config.get("steps", [])
            layer_total = len(steps)
            task_id = self.progress.add_task(
                f"[{layer_style}]{layer_desc}",
                total=layer_total,
                steps=steps,  # Store steps for later use
                **common_fields,
            )
        else:
            # Handle regular progress layer
            layer_total = layer_config.get("total")
            task_id = self.progress.add_task(
                f"[{layer_style}]{layer_desc}", total=layer_total, **common_fields
            )

        # Store layer metadata
        self.layer_metadata[task_id] = {
            "name": layer_name,
            "type": layer_type,
            "config": layer_config,
            "is_main": layer_type == "main",
            "is_sub": self.has_main_layer and layer_type != "main",
        }

        self.active_layers.append(task_id)
        self.task_ids[layer_name] = task_id
        return task_id

    def update_layer(self, layer_name: str, progress: int, details: str = "") -> None:
        """Update a specific layer's progress.

        Args:
            layer_name: Name of the layer to update
            progress: Progress value (0-100 or step index)
            details: Additional details to display
        """
        if not self.progress:
            return

        task_id = self.task_ids.get(layer_name)
        if task_id is None:
            return

        metadata = self.layer_metadata.get(task_id)
        if metadata is None:
            return

        # Update the layer based on its type
        if metadata["type"] == "steps":
            # Handle step-based layer
            task = self.progress._tasks[task_id]
            steps = getattr(task, "fields", {}).get(
                "steps", metadata["config"].get("steps", [])
            )

            if steps and progress < len(steps):
                current_step = steps[progress]
                step_progress = f"Step {progress + 1}/{len(steps)}: {current_step}"

                self.progress.update(
                    task_id,
                    completed=progress,
                    description=f"{task.description} - {step_progress}",
                    details=details,
                )
            else:
                self.progress.update(task_id, completed=progress, details=details)
        elif metadata["type"] == "spinner":
            # Handle spinner layer - update details message
            self.progress.update(
                task_id,
                details=details,  # Use details consistently
            )
        elif metadata["type"] == "download":
            # Handle download layer - update progress and details
            self.progress.update(task_id, completed=progress, details=details)
        else:
            # Handle regular progress layer
            self.progress.update(task_id, completed=progress, details=details)

    def complete_layer(self, layer_name: str) -> None:
        """Mark a layer as completed and animate its success.

        Args:
            layer_name: Name of the layer to complete
        """
        if not self.progress:
            return

        task_id = self.task_ids.get(layer_name)
        if task_id is None:
            return

        # Mark as completed based on layer type
        metadata = self.layer_metadata[task_id]
        if metadata["type"] == "steps":
            steps = metadata["config"].get("steps", [])
            self.progress.update(task_id, completed=len(steps))
        elif metadata["type"] == "spinner":
            # For spinners, just mark as completed (no progress to update)
            pass
        else:
            total = metadata["config"].get("total", 100)
            self.progress.update(task_id, completed=total)

        # Don't remove main layer - it stays for reference
        if metadata.get("is_main", False):
            # Just mark as completed but keep it visible
            self.completed_layers.append(layer_name)
            return

        # Remove the layer (only for sub-layers)
        self.completed_layers.append(layer_name)
        metadata["state"] = "completed"

        # Animate success for this specific layer
        self._animate_layer_success(task_id, metadata)

        # Update main layer progress if it exists
        if self.has_main_layer:
            self._update_main_layer_progress()

    def _animate_layer_success(
        self,
        task_id: int,
        metadata: dict,  # noqa: ARG002
    ) -> None:
        """Animate success for a specific layer and then remove it.

        Args:
            task_id: Task ID to animate
            metadata: Layer metadata
        """
        # Flash green 2 times
        for flash in range(2):
            if task_id in self.progress._tasks:
                task = self.progress._tasks[task_id]

                # Clean description (remove all icons)
                clean_description = (
                    str(task.description)
                    .replace("❌ ", "")
                    .replace("⚠️ ", "")
                    .replace("✅ ", "")
                )

                if flash % 2 == 0:  # Green flash
                    success_description = Text(
                        clean_description, style="bold green on green"
                    )
                else:  # Normal green
                    success_description = Text(clean_description, style="bold green")

                self.progress.update(
                    task_id,
                    description=success_description,
                )

            time.sleep(0.1)  # Quick flash

        # Fade out by updating with dim style
        if task_id in self.progress._tasks:
            task = self.progress._tasks[task_id]
            clean_description = (
                str(task.description)
                .replace("❌ ", "")
                .replace("⚠️ ", "")
                .replace("✅ ", "")
            )
            faded_description = Text(clean_description, style="dim")
            self.progress.update(task_id, description=faded_description)
            time.sleep(0.3)  # Brief fade out

        # Remove the layer after animation
        if task_id in self.progress._tasks:
            self.progress.remove_task(task_id)
            if task_id in self.active_layers:
                self.active_layers.remove(task_id)
            if task_id in self.layer_metadata:
                del self.layer_metadata[task_id]
            if task_id in self.task_ids.values():
                # Remove from task_ids dict
                for name, tid in list(self.task_ids.items()):
                    if tid == task_id:
                        del self.task_ids[name]
                        break

    def _update_main_layer_progress(self) -> None:
        """Update main layer progress based on completed sub-layers."""
        if not self.has_main_layer or not self.main_layer_name:
            return

        # Find main layer task
        main_task_id = None
        for tid, metadata in self.layer_metadata.items():
            if metadata.get("is_main", False):
                main_task_id = tid
                break

        if main_task_id is None:
            return

        # Calculate progress based on completed sub-layers
        completed_sub_layers = len(
            [
                layer
                for layer in self.completed_layers
                if layer in [s.get("name") for s in self.sub_layers]
            ]
        )

        # Update main layer
        self.progress.update(main_task_id, completed=completed_sub_layers)

    def handle_error(self, layer_name: str, error: str) -> None:
        """Handle errors in a specific layer.

        Args:
            layer_name: Name of the layer with error
            error: Error message to display
        """
        if not self.progress:
            return

        task_id = self.task_ids.get(layer_name)
        if task_id is None:
            return

        # Update with error styling using Rich Text objects
        if task_id in self.progress._tasks:
            task = self.progress._tasks[task_id]
            error_description = Text(f"❌ {task.description}", style="red")
            error_details = Text(f"Error: {error}", style="red")

            self.progress.update(
                task_id,
                description=error_description,
                details=error_details,
            )

    def emergency_stop(self, error_message: str = "Critical error occurred") -> None:
        """Emergency stop all layers with animated failure effects.

        Args:
            error_message: The error message to display
        """
        if not self.progress:
            return

        # Create failure animation sequence: flash red 3 times
        for flash in range(3):
            # Apply flash effect to all active layers
            for task_id in list(self.active_layers):
                # Check if task still exists before updating
                if task_id in self.progress._tasks:
                    task = self.progress._tasks[task_id]

                    # Clean description (remove all icons)
                    clean_description = (
                        str(task.description)
                        .replace("❌ ", "")
                        .replace("⚠️ ", "")
                        .replace("✅ ", "")
                    )

                    if flash % 2 == 0:  # Red flash
                        error_description = Text(
                            clean_description, style="bold red on red"
                        )
                        error_details = Text(
                            f"Stopped: {error_message}", style="red on red"
                        )
                    else:  # Normal red
                        error_description = Text(clean_description, style="bold red")
                        error_details = Text(f"Stopped: {error_message}", style="red")

                    self.progress.update(
                        task_id,
                        description=error_description,
                        details=error_details,
                    )

            # Brief pause for flash effect
            time.sleep(0.15)

        # Final state: settle on clean error display
        for task_id in list(self.active_layers):
            if task_id in self.progress._tasks:
                task = self.progress._tasks[task_id]

                # Final error state (clean, no symbols)
                clean_description = (
                    str(task.description)
                    .replace("❌ ", "")
                    .replace("⚠️ ", "")
                    .replace("✅ ", "")
                )
                error_description = Text(f"{clean_description}", style="bold red")
                error_details = Text(f"Stopped: {error_message}", style="red")

                self.progress.update(
                    task_id,
                    description=error_description,
                    details=error_details,
                )

        # Stop the progress bar to freeze the display
        self.progress.stop()

        # Mark as emergency stopped
        self._emergency_stopped = True
        self._emergency_message = error_message

    def is_emergency_stopped(self) -> bool:
        """Check if the progress bar was emergency stopped.

        Returns:
            True if emergency stopped, False otherwise
        """
        return self._emergency_stopped

    def get_emergency_message(self) -> Optional[str]:
        """Get the emergency stop message.

        Returns:
            The emergency message if stopped, None otherwise
        """
        return self._emergency_message

    def start(self) -> None:
        """Start the progress bar and create initial layers."""
        self.progress = self._create_progress_bar()
        self.progress.start()

        # Create layers in order: main layer first, then sub-layers
        if self.has_main_layer:
            # Create main layer first
            main_stage = next(
                (stage for stage in self.stages if stage.get("type") == "main"), None
            )
            if main_stage:
                self._create_layer(main_stage)

            # Then create sub-layers
            for stage in self.stages:
                if stage.get("type") != "main":
                    self._create_layer(stage)
        else:
            # No main layer, create all layers in order
            for stage in self.stages:
                self._create_layer(stage)

    def stop(self, success: bool = True, show_success_animation: bool = True) -> None:
        """Stop the progress bar with appropriate animations.

        Args:
            success: Whether this stop represents a successful completion
            show_success_animation: Whether to show success animations
        """
        if not self.progress:
            return

        if success and show_success_animation:
            # SUCCESS CASE: Final cleanup for any remaining layers
            time.sleep(0.5)
        elif not success:
            # ERROR/WARNING CASE: Freeze current state
            for task_id in list(self.active_layers):
                if task_id in self.progress._tasks:
                    task = self.progress._tasks[task_id]
                    # Clean description (remove all icons)
                    clean_description = (
                        str(task.description)
                        .replace("❌ ", "")
                        .replace("⚠️ ", "")
                        .replace("✅ ", "")
                    )
                    error_description = Text(clean_description, style="bold orange")

                    self.progress.update(
                        task_id,
                        description=error_description,
                    )

        # Stop the underlying Rich progress
        self.progress.stop()


class DynamicProgressMixin:
    """
    Mixin providing dynamic layered progress bar methods for RichWizard.

    This mixin adds dynamic progress functionality with layers that can
    appear, progress, and disappear automatically.
    """

    # ///////////////////////////////////////////////////////////////
    # DYNAMIC PROGRESS METHODS
    # ///////////////////////////////////////////////////////////////

    @contextmanager
    def dynamic_layered_progress(
        self,
        stages: list[dict[str, Any]],
        show_time: bool = True,
    ) -> Generator[DynamicLayeredProgress, None, None]:
        """
        Create a dynamic layered progress bar context manager.

        Args:
            stages: List of stage configurations, each containing:
                - 'name': Layer name/identifier
                - 'type': Layer type ('progress', 'steps', 'spinner', 'download', 'main')
                - 'description': Display description for the layer
                - 'style': Rich style string (optional)
                - 'total': Total items (for 'progress' or 'download' type)
                - 'steps': List of step names (for 'steps' or 'main' type)
                - 'total_size': Total size in bytes (for 'download' type)
                - 'filename': Filename (for 'download' type)
            show_time: Whether to show elapsed and remaining time

        Yields:
            DynamicLayeredProgress instance with methods:
            - update_layer(name, progress, details): Update a layer's progress
            - complete_layer(name): Mark a layer as completed
            - handle_error(name, error): Handle errors in a layer
            - emergency_stop(message): Emergency stop all layers

        Example:
            >>> stages = [
            ...     {"name": "main", "type": "main", "description": "Overall Progress"},
            ...     {"name": "step1", "type": "progress", "description": "Step 1", "total": 100},
            ...     {"name": "step2", "type": "steps", "description": "Step 2", "steps": ["A", "B", "C"]},
            ... ]
            >>> with printer.wizard.dynamic_layered_progress(stages) as progress:
            ...     progress.update_layer("step1", 50, "Processing...")
            ...     progress.complete_layer("step1")
            ...     progress.update_layer("step2", 1, "Step B")
            ...     progress.complete_layer("step2")
        """
        progress_bar = DynamicLayeredProgress(
            self._console, self._progress_prefix, stages, show_time
        )

        try:
            progress_bar.start()
            yield progress_bar
        finally:
            # Check if emergency stopped before normal cleanup
            if not progress_bar.is_emergency_stopped():
                # Normal completion - assume success
                is_success = True
                progress_bar.stop(success=is_success, show_success_animation=is_success)
            else:
                # If emergency stopped, the progress bar is already stopped
                # Just display the emergency message
                emergency_msg = progress_bar.get_emergency_message()
                if emergency_msg:
                    self._console.print(
                        f"\n[bold red]🚨 EMERGENCY STOP: {emergency_msg}[/bold red]"
                    )
