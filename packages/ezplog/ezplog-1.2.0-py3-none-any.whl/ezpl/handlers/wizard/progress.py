# ///////////////////////////////////////////////////////////////
# EZPL - Wizard Progress Mixin
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Progress methods mixin for Rich Wizard.

This module provides all progress bar-related methods for the RichWizard class.
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

# Internal modules

## ==> CLASSES
# ///////////////////////////////////////////////////////////////


class ProgressMixin:
    """
    Mixin providing progress bar methods for RichWizard.

    This mixin adds all progress-related functionality including
    generic progress bars, spinners, download progress, installation progress,
    and layered progress bars.
    """

    # ///////////////////////////////////////////////////////////////
    # PROGRESS METHODS
    # ///////////////////////////////////////////////////////////////

    @contextmanager
    def progress(
        self,
        description: str = "Working...",
        total: Optional[int] = None,
        transient: bool = False,
    ) -> Generator[tuple[Progress, int], None, None]:
        """
        Create a progress bar context manager.

        Args:
            description: Progress description
            total: Total number of items (None for indeterminate)
            transient: Whether to clear progress on exit

        Yields:
            tuple of (Progress, task_id)

        Example:
            >>> with printer.wizard.progress("Processing...", total=100) as (progress, task):
            ...     for i in range(100):
            ...         progress.update(task, advance=1)
        """
        progress = Progress(
            TextColumn(self._progress_prefix),
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self._console,
            transient=transient,
        )

        with progress:
            task = progress.add_task(description, total=total)
            yield progress, task

    @contextmanager
    def spinner(
        self, description: str = "Working..."
    ) -> Generator[tuple[Progress, int], None, None]:
        """
        Create a simple spinner with description.

        Args:
            description: Spinner description

        Yields:
            tuple of (Progress, task_id)

        Example:
            >>> with printer.wizard.spinner("Loading...") as (progress, task):
            ...     # Do work
            ...     pass
        """
        progress = Progress(
            TextColumn(self._progress_prefix),
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self._console,
        )

        with progress:
            task = progress.add_task(description, total=None)
            yield progress, task

    @contextmanager
    def spinner_with_status(
        self, description: str = "Working..."
    ) -> Generator[tuple[Progress, int], None, None]:
        """
        Create a spinner that can update status messages.

        Args:
            description: Spinner description

        Yields:
            tuple of (Progress, task_id)

        Example:
            >>> with printer.wizard.spinner_with_status("Processing...") as (progress, task):
            ...     progress.update(task, status="Step 1/3")
        """
        progress = Progress(
            TextColumn(self._progress_prefix),
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[dim]{task.fields[status]}"),
            console=self._console,
        )

        with progress:
            task = progress.add_task(description, total=None, status="")
            yield progress, task

    @contextmanager
    def download_progress(
        self, description: str = "Downloading..."
    ) -> Generator[tuple[Progress, int], None, None]:
        """
        Create a download progress bar with speed and size information.

        Args:
            description: Download description

        Yields:
            tuple of (Progress, task_id)

        Example:
            >>> with printer.wizard.download_progress() as (progress, task):
            ...     progress.update(task, completed=50, total=100)
        """
        progress = Progress(
            TextColumn(self._progress_prefix),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            DownloadColumn(),
            TransferSpeedColumn(),
            console=self._console,
        )

        with progress:
            task = progress.add_task(description, total=100)
            yield progress, task

    @contextmanager
    def file_download_progress(
        self, filename: str, total_size: int, description: str = "Downloading file..."
    ) -> Generator[tuple[Progress, int], None, None]:
        """
        Create a progress bar for downloading a specific file.

        Args:
            filename: Name of the file being downloaded
            total_size: Total size in bytes
            description: Main description

        Yields:
            tuple of (Progress, task_id)

        Example:
            >>> with printer.wizard.file_download_progress("file.zip", 1024000) as (progress, task):
            ...     progress.update(task, advance=512000)
        """
        progress = Progress(
            TextColumn(self._progress_prefix),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TextColumn("[dim]{task.fields[filename]}"),
            console=self._console,
        )

        with progress:
            task = progress.add_task(description, total=total_size, filename=filename)
            yield progress, task

    @contextmanager
    def dependency_progress(
        self, dependencies: list[str], description: str = "Installing dependencies..."
    ) -> Generator[tuple[Progress, int, str], None, None]:
        """
        Create a progress bar for dependency installation.

        Args:
            dependencies: list of dependency names
            description: Main description

        Yields:
            tuple of (Progress, task_id, dependency_name) for each dependency

        Example:
            >>> deps = ["package1", "package2", "package3"]
            >>> with printer.wizard.dependency_progress(deps) as (progress, task, dep):
            ...     # Install dependency
            ...     progress.advance(task)
        """
        progress = Progress(
            TextColumn(self._progress_prefix),
            SpinnerColumn(),
            TextColumn("[bold green]{task.description}"),
            TextColumn(
                "[dim]Dependency {task.fields[current]}/{task.fields[total_deps]}"
            ),
            TextColumn("[dim]{task.fields[dependency]}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self._console,
        )

        with progress:
            task = progress.add_task(
                description,
                total=len(dependencies),
                current=1,
                total_deps=len(dependencies),
                dependency="",
            )

            for i, dependency in enumerate(dependencies):
                progress.update(
                    task,
                    description=f"[bold green]Installing {dependency}",
                    current=i + 1,
                    dependency=dependency,
                )
                yield progress, task, dependency
                progress.advance(task)
                time.sleep(0.1)

    @contextmanager
    def package_install_progress(
        self,
        packages: list[tuple[str, str]],
        description: str = "Installing packages...",
    ) -> Generator[tuple[Progress, int, str, str], None, None]:
        """
        Create a progress bar for package installation with version info.

        Args:
            packages: list of tuples (package_name, version)
            description: Main description

        Yields:
            tuple of (Progress, task_id, package_name, version) for each package

        Example:
            >>> packages = [("requests", "2.31.0"), ("click", "8.1.0")]
            >>> with printer.wizard.package_install_progress(packages) as (progress, task, pkg, ver):
            ...     # Install package
            ...     progress.advance(task)
        """
        progress = Progress(
            TextColumn(self._progress_prefix),
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            TextColumn(
                "[dim]Package {task.fields[current]}/{task.fields[total_packages]}"
            ),
            TextColumn("[dim]{task.fields[package]}"),
            TextColumn("[dim]{task.fields[version]}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self._console,
        )

        with progress:
            task = progress.add_task(
                description,
                total=len(packages),
                current=1,
                total_packages=len(packages),
                package="",
                version="",
            )

            for i, (package_name, version) in enumerate(packages):
                progress.update(
                    task,
                    description=f"[bold cyan]Installing {package_name}",
                    current=i + 1,
                    package=package_name,
                    version=version,
                )
                yield progress, task, package_name, version
                progress.advance(task)
                time.sleep(0.1)

    @contextmanager
    def step_progress(
        self,
        steps: list[str],
        description: str = "Processing...",
        show_step_numbers: bool = True,
        show_time: bool = True,
    ) -> Generator[tuple[Progress, int, list[str]], None, None]:
        """
        Create a step-based progress bar with detailed step information.

        Args:
            steps: list of step names
            description: Main description
            show_step_numbers: Show step numbers (e.g., "Step 1/5")
            show_time: Show elapsed and remaining time

        Yields:
            tuple of (Progress, task_id, steps_list)

        Example:
            >>> steps = ["Step 1", "Step 2", "Step 3"]
            >>> with printer.wizard.step_progress(steps) as (progress, task, steps_list):
            ...     for i, step in enumerate(steps_list):
            ...         progress.update(task, completed=i, current_step=step)
            ...         progress.advance(task)
        """
        # Build columns based on options
        columns = [
            TextColumn(self._progress_prefix),
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
        ]

        if show_step_numbers:
            columns.append(
                TextColumn("[dim]Step {task.fields[step]}/{task.fields[total_steps]}")
            )

        columns.extend(
            [
                TextColumn("[dim]{task.fields[current_step]}"),
                BarColumn(),
                TaskProgressColumn(),
            ]
        )

        if show_time:
            columns.extend(
                [
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                ]
            )

        progress = Progress(*columns, console=self._console)

        with progress:
            task = progress.add_task(
                description,
                total=len(steps),
                step=1,
                total_steps=len(steps),
                current_step="",
            )

            yield progress, task, steps

    @contextmanager
    def file_copy_progress(
        self, files: list[str], description: str = "Copying files..."
    ) -> Generator[tuple[Progress, int, list[str]], None, None]:
        """
        Create a progress bar specifically for file copying operations.

        Args:
            files: list of file paths to copy
            description: Main description

        Yields:
            tuple of (Progress, task_id, files_list)

        Example:
            >>> files = ["file1.txt", "file2.txt"]
            >>> with printer.wizard.file_copy_progress(files) as (progress, task, files_list):
            ...     for i, file in enumerate(files_list):
            ...         progress.update(task, current_file=file)
            ...         progress.advance(task)
        """
        progress = Progress(
            TextColumn(self._progress_prefix),
            SpinnerColumn(),
            TextColumn("[bold magenta]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[dim]{task.fields[current_file]}"),
            console=self._console,
        )

        with progress:
            task = progress.add_task(description, total=len(files), current_file="")
            yield progress, task, files

    @contextmanager
    def installation_progress(
        self,
        steps: list[tuple[str, str]],
        description: str = "Installation in progress...",
    ) -> Generator[tuple[Progress, int, str, str], None, None]:
        """
        Create a progress bar for installation processes with step details.

        Args:
            steps: list of tuples (step_name, step_description)
            description: Main description

        Yields:
            tuple of (Progress, task_id, step_name, step_description) for each step

        Example:
            >>> steps = [("Init", "Initializing..."), ("Install", "Installing...")]
            >>> with printer.wizard.installation_progress(steps) as (progress, task, name, desc):
            ...     # Process step
            ...     progress.advance(task)
        """
        progress = Progress(
            TextColumn(self._progress_prefix),
            SpinnerColumn(),
            TextColumn("[bold green]{task.description}"),
            TextColumn("[dim]Step {task.fields[step]}/{task.fields[total_steps]}"),
            TextColumn("[dim]{task.fields[step_detail]}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self._console,
        )

        with progress:
            task = progress.add_task(
                description,
                total=len(steps),
                step=1,
                total_steps=len(steps),
                step_detail="",
            )

            for i, (step_name, step_detail) in enumerate(steps):
                progress.update(
                    task,
                    description=f"[bold green]{step_name}",
                    step=i + 1,
                    step_detail=step_detail,
                )
                yield progress, task, step_name, step_detail
                progress.advance(task)
                time.sleep(0.1)

    @contextmanager
    def build_progress(
        self, phases: list[tuple[str, int]], description: str = "Building project..."
    ) -> Generator[tuple[Progress, int, str, int], None, None]:
        """
        Create a progress bar for build processes with weighted phases.

        Args:
            phases: list of tuples (phase_name, weight_percentage)
            description: Main description

        Yields:
            tuple of (Progress, task_id, phase_name, weight) for each phase

        Example:
            >>> phases = [("Compile", 40), ("Test", 30), ("Package", 30)]
            >>> with printer.wizard.build_progress(phases) as (progress, task, phase, weight):
            ...     # Process phase
            ...     progress.update(task, advance=weight)
        """
        progress = Progress(
            TextColumn(self._progress_prefix),
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            TextColumn("[dim]{task.fields[current_phase]}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[bold yellow]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self._console,
        )

        with progress:
            task = progress.add_task(description, total=100, current_phase="")

            current_progress = 0
            for phase_name, weight in phases:
                progress.update(task, current_phase=phase_name)
                yield progress, task, phase_name, weight
                current_progress += weight
                progress.update(task, completed=current_progress)

    @contextmanager
    def deployment_progress(
        self, stages: list[str], description: str = "Deploying..."
    ) -> Generator[tuple[Progress, int, str], None, None]:
        """
        Create a progress bar for deployment processes.

        Args:
            stages: list of deployment stage names
            description: Main description

        Yields:
            tuple of (Progress, task_id, stage_name) for each stage

        Example:
            >>> stages = ["Build", "Test", "Deploy"]
            >>> with printer.wizard.deployment_progress(stages) as (progress, task, stage):
            ...     # Process stage
            ...     progress.advance(task)
        """
        progress = Progress(
            TextColumn(self._progress_prefix),
            SpinnerColumn(),
            TextColumn("[bold magenta]{task.description}"),
            TextColumn("[dim]Stage {task.fields[stage]}/{task.fields[total_stages]}"),
            TextColumn("[dim]{task.fields[current_stage]}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self._console,
        )

        with progress:
            task = progress.add_task(
                description,
                total=len(stages),
                stage=1,
                total_stages=len(stages),
                current_stage="",
            )

            for i, stage in enumerate(stages):
                progress.update(
                    task,
                    description=f"[bold magenta]{stage}",
                    stage=i + 1,
                    current_stage=stage,
                )
                yield progress, task, stage
                progress.advance(task)
                time.sleep(0.1)

    @contextmanager
    def layered_progress(
        self,
        layers: list[dict[str, Any]],
        show_time: bool = True,
    ) -> Generator[tuple[Progress, dict[str, int]], None, None]:
        """
        Create a multi-level progress bar with dynamic layers.

        Args:
            layers: list of layer configurations, each containing:
                - 'name': Layer name/description
                - 'total': Total items for this layer (optional, None for indeterminate)
                - 'description': Display description for the layer
                - 'style': Rich style for this layer (optional)
                - 'type': Layer type - 'progress' (default) or 'steps'
                - 'steps': list of step names (required if type='steps')
            show_time: Show elapsed and remaining time

        Yields:
            tuple of (Progress, task_ids_dict) where task_ids_dict maps layer names to task IDs

        Example:
            >>> layers = [
            ...     {"name": "layer1", "description": "Layer 1", "total": 10},
            ...     {"name": "layer2", "description": "Layer 2", "total": 5}
            ... ]
            >>> with printer.wizard.layered_progress(layers) as (progress, task_ids):
            ...     progress.update(task_ids["layer1"], advance=1)
        """
        # Build columns for the main progress bar
        columns = [
            TextColumn(self._progress_prefix),
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[dim]{task.fields[details]}"),
        ]

        if show_time:
            columns.extend(
                [
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                ]
            )

        progress = Progress(*columns, console=self._console)

        with progress:
            # Create tasks for each layer
            task_ids = {}

            for i, layer in enumerate(layers):
                layer_name = layer.get("name", f"Layer_{i}")
                layer_type = layer.get("type", "progress")
                layer_desc = layer.get("description", layer_name)
                layer_style = layer.get("style", "default")

                if layer_type == "steps":
                    # Handle step-based layer
                    steps = layer.get("steps", [])
                    layer_total = len(steps)
                    task_id = progress.add_task(
                        f"[{layer_style}]{layer_desc}",
                        total=layer_total,
                        details="",
                        steps=steps,
                    )
                else:
                    # Handle regular progress layer
                    layer_total = layer.get("total", None)
                    task_id = progress.add_task(
                        f"[{layer_style}]{layer_desc}",
                        total=layer_total,
                        details="",
                    )

                task_ids[layer_name] = task_id

            yield progress, task_ids
