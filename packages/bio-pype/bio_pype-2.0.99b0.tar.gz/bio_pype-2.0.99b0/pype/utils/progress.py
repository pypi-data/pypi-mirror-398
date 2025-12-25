"""Progress tracking and display utilities for queue modules.

Provides:
- ProgressDisplay: Format and display job progress with rich formatting
- Works with ResourceManager + TaskScheduler paradigm
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from rich import box
from rich.console import Console
from rich.table import Table


@dataclass
class JobProgress:
    """Information about a single job for display."""

    run_id: str
    friendly_name: str
    status: str
    queue_id: Optional[str] = None


@dataclass
class PipelineProgress:
    """Overall pipeline progress statistics."""

    total_jobs: int
    completed: int
    running: int
    submitted: int
    pending: int
    failed: int

    @property
    def percent_complete(self) -> float:
        """Percentage of jobs completed."""
        if self.total_jobs == 0:
            return 100.0
        return 100.0 * self.completed / self.total_jobs

    @property
    def summary(self) -> str:
        """One-line summary of progress."""
        return (
            f"[{self.completed}/{self.total_jobs}] {self.percent_complete:.1f}% complete | "
            f"{self.running} running | {self.submitted} submitted | "
            f"{self.pending} pending | {self.failed} failed"
        )


class ProgressDisplay:
    """Display job progress with rich formatting.

    Example usage:
        progress = ProgressDisplay()
        stats = scheduler.get_stats()
        jobs = [(run_id, job_data) for run_id, job_data in scheduler.runtime.items()]
        progress.show_pipeline_status(jobs, stats, resource_stats)
    """

    def __init__(self):
        """Initialize progress display with rich console."""
        self.console = Console()
        self._last_display = None  # Cache last display to avoid redundant output

    def show_pipeline_status(
        self,
        jobs: List[tuple],
        stats: Dict[str, int],
        resource_stats: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Display pipeline execution status.

        Automatically filters out metadata entries (keys starting with '__').
        Only displays if content has changed since last call.

        Args:
            jobs: List of (run_id, job_data) tuples (may include metadata entries)
            stats: Job statistics from TaskScheduler.get_stats()
            resource_stats: Optional resource statistics from ResourceManager.get_stats()

        Returns:
            Summary string (also prints to console if changed)
        """
        # Filter out metadata entries internally - don't rely on callers
        filtered_jobs = [
            (run_id, job_data) for run_id, job_data in jobs
            if not run_id.startswith("__")
        ]

        # Sort by submit_at (earliest first), jobs without submit_at go to bottom
        filtered_jobs.sort(
            key=lambda x: (x[1].get("submit_at") is None, x[1].get("submit_at", ""))
        )

        # Create a hashable representation of the current state
        import hashlib
        state_str = str((filtered_jobs, stats, resource_stats))
        state_hash = hashlib.md5(state_str.encode()).hexdigest()

        # Skip if nothing changed
        if state_hash == self._last_display:
            return ""

        self._last_display = state_hash
        # Create job table with ASCII box style for better compatibility
        table = Table(title="Pipeline Job Status", show_header=True, box=box.ASCII)
        table.add_column("Job ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Queue ID", style="yellow")

        # Add all jobs with appropriate status colors
        for run_id, job_data in filtered_jobs:
            status = job_data.get("status", "pending")
            friendly_name = job_data.get("name", run_id[:8])
            queue_id = job_data.get("queue_id", "")

            # Color by status
            if status == "completed":
                status_color = "green"
                status_display = f"[{status_color}]{status}[/{status_color}]"
            elif status == "failed":
                status_color = "red"
                status_display = f"[{status_color}]{status}[/{status_color}]"
            elif status == "cancelled":
                status_color = "yellow"
                status_display = f"[{status_color}]{status}[/{status_color}]"
            elif status == "running":
                status_color = "blue"
                status_display = f"[{status_color}]{status}[/{status_color}]"
            elif status == "submitted":
                status_color = "yellow"
                status_display = f"[{status_color}]{status}[/{status_color}]"
            else:  # pending
                status_color = "dim"
                status_display = f"[{status_color}]{status}[/{status_color}]"

            table.add_row(
                run_id[:12],
                friendly_name,
                status_display,
                queue_id or "-",
            )

        self.console.print(table)

        # Print summary
        percent = 100.0 * stats["completed"] / max(stats["total"], 1)
        summary = (
            f"\n[cyan]Progress:[/cyan] [{stats['completed']}/{stats['total']}] "
            f"{percent:.1f}% | "
            f"[blue]{stats['running']} running[/blue] | "
            f"[yellow]{stats['submitted']} submitted[/yellow] | "
            f"[dim]{stats['pending']} pending[/dim]"
        )
        if stats["failed"] > 0:
            summary += f" | [red]{stats['failed']} failed[/red]"

        self.console.print(summary)

        # Resource stats if available
        if resource_stats:
            resource_summary = self._format_resource_stats(resource_stats)
            self.console.print(resource_summary)

        return summary

    def _format_resource_stats(self, stats: Dict[str, Any]) -> str:
        """Format resource statistics for display."""
        lines = ["RESOURCE USAGE:"]

        for key, value in stats.items():
            if key.endswith("_percent") or key.endswith("_pct"):
                lines.append(f"  {key}: {value:.1f}%")
            elif key.endswith("_count") or key.endswith("_tasks"):
                lines.append(f"  {key}: {value}")
            elif (
                key.startswith("used_mem") or key.startswith("max_mem")
            ) and not key.endswith("_pct"):
                # Convert bytes to GB for memory values (but not percentages)
                value_gb = value / (1024**3)
                lines.append(f"  {key}: {value_gb:.2f} GB")
            elif isinstance(value, (int, float)):
                if isinstance(value, float):
                    lines.append(f"  {key}: {value:.2f}")
                else:
                    lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    def show_summary(
        self,
        total_jobs: int,
        completed: int,
        failed: int,
        elapsed_time: Optional[float] = None,
        cancelled: int = 0,
    ) -> str:
        """Display final summary.

        Args:
            total_jobs: Total number of jobs
            completed: Jobs completed successfully
            failed: Jobs that failed
            elapsed_time: Optional execution time in seconds
            cancelled: Jobs that were cancelled due to blocking

        Returns:
            Summary text
        """
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("PIPELINE EXECUTION COMPLETE")
        lines.append("=" * 80)
        lines.append(f"Total jobs: {total_jobs}")
        lines.append(f"[green]Completed:[/green]  {completed}")
        lines.append(f"[red]Failed:[/red]     {failed}")
        if cancelled > 0:
            lines.append(f"[yellow]Cancelled:[/yellow]   {cancelled}")

        if elapsed_time:
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            lines.append(f"Time:       {time_str}")

        if failed == 0 and cancelled == 0:
            lines.append("\n[green]All jobs completed successfully![/green]")
        else:
            error_count = failed + cancelled
            lines.append(
                f"\n[yellow]WARNING:[/yellow] {error_count} job(s) did not complete - see logs for details"
            )

        lines.append("=" * 80)

        result = "\n".join(lines)
        self.console.print(result)
        return result
