# ///////////////////////////////////////////////////////////////
# EZPL - Log Statistics Utility
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Log statistics utility for CLI operations.

This module provides functionality to calculate statistics from log files.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional

# Internal modules
from ezpl.cli.utils.log_parser import LogEntry

from .log_parser import LogParser

## ==> CLASSES
# ///////////////////////////////////////////////////////////////


class LogStatistics:
    """
    Calculate and store statistics from log files.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, log_file: Path) -> None:
        """
        Initialize log statistics calculator.

        Args:
            log_file: Path to the log file
        """
        self.log_file = Path(log_file)
        self.parser = LogParser(self.log_file)
        self._entries: Optional[list[LogEntry]] = None

    # ------------------------------------------------
    # PRIVATE HELPER METHODS
    # ------------------------------------------------

    def _get_entries(self) -> list[LogEntry]:
        """Get all log entries (cached)."""
        if self._entries is None:
            self._entries = list[LogEntry](self.parser.parse())
        return self._entries

    # ///////////////////////////////////////////////////////////////
    # STATISTICS METHODS
    # ///////////////////////////////////////////////////////////////

    def get_level_counts(self) -> dict[str, int]:
        """
        Get count of messages by level.

        Returns:
            Dictionary mapping level names to counts
        """
        entries = self._get_entries()
        counter = Counter(entry.level for entry in entries)
        return dict(counter)

    def get_file_info(self) -> dict[str, Any]:
        """
        Get basic file information.

        Returns:
            Dictionary with file size, line count, etc.
        """
        try:
            size = self.log_file.stat().st_size if self.log_file.exists() else 0
            entries = self._get_entries()
            line_count = len(entries)

            # Get date range
            timestamps = [
                entry.timestamp for entry in entries if entry.timestamp is not None
            ]
            date_range = None
            if timestamps:
                date_range = {
                    "first": min(timestamps),
                    "last": max(timestamps),
                }

            return {
                "file_path": str(self.log_file),
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 2),
                "line_count": line_count,
                "date_range": date_range,
            }
        except Exception:
            return {
                "file_path": str(self.log_file),
                "size_bytes": 0,
                "size_mb": 0,
                "line_count": 0,
                "date_range": None,
            }

    def get_temporal_distribution(self, period: str = "hour") -> dict[str, int]:
        """
        Get distribution of logs over time.

        Args:
            period: Time period ('hour' or 'day')

        Returns:
            Dictionary mapping time periods to log counts
        """
        entries = self._get_entries()
        distribution: dict[str, int] = defaultdict(int)

        for entry in entries:
            if entry.timestamp is None:
                continue

            if period == "hour":
                key = entry.timestamp.strftime("%Y-%m-%d %H:00")
            elif period == "day":
                key = entry.timestamp.strftime("%Y-%m-%d")
            else:
                key = entry.timestamp.strftime("%Y-%m-%d %H:%M")

            distribution[key] += 1

        return dict(distribution)

    def get_all_stats(self) -> dict[str, Any]:
        """
        Get all statistics in a single dictionary.

        Returns:
            Dictionary containing all statistics
        """
        return {
            "file_info": self.get_file_info(),
            "level_counts": self.get_level_counts(),
            "temporal_distribution_hour": self.get_temporal_distribution("hour"),
            "temporal_distribution_day": self.get_temporal_distribution("day"),
        }
