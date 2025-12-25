"""Abstract base class for queue implementations using template method pattern.

This module provides a reusable framework for implementing queue systems
(local multiprocessing, SLURM, PBS, etc.) by defining:

1. Template method: post_run() - orchestrates the entire execution loop
2. Abstract methods: Implementation-specific operations (submission, monitoring)
3. Concrete helpers: Shared functionality (blocking detection, graceful shutdown)

To implement a new queue type, subclass BaseQueue and implement:
- _initialize_queue(): Start queue-specific services
- _cleanup_queue(): Stop queue-specific services
- _get_ready_jobs_queue_specific(): Find jobs ready to submit (queue-specific logic)
- _submit_job(): Submit a single job to the queue system
- _check_job_status(): Check if job completed or failed
"""

import os
import sys
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from pype.utils.progress import ProgressDisplay
from pype.utils.queues import (
    JobStatus,
    ResourceManager,
    TaskScheduler,
    cascade_cancel_dependents,
    check_for_blocked_jobs,
    handle_graceful_shutdown,
    show_final_summary,
    update_job_status,
)


class BaseQueue(ABC):
    """Abstract base class for queue implementations.

    Implements template method pattern with:
    - Concrete post_run() orchestrating main execution loop
    - Abstract methods for queue-specific operations
    - Helper methods using shared utilities

    Subclasses must implement 5 abstract methods:
    1. _initialize_queue() - Queue-specific startup
    2. _cleanup_queue() - Queue-specific cleanup
    3. _get_ready_jobs_queue_specific() - Find ready jobs (can vary by queue type)
    4. _submit_job() - Submit a job to queue system
    5. _check_job_status() - Check job completion/failure

    Example usage:

        class MyQueue(BaseQueue):
            def _initialize_queue(self):
                # Start queue service
                pass

            def _cleanup_queue(self):
                # Stop queue service
                pass

            def _get_ready_jobs_queue_specific(self):
                # Get jobs ready to submit
                return self.scheduler.get_ready_jobs()

            def _submit_job(self, run_id, job_data):
                # Submit job and return queue ID
                return queue_id_or_none

            def _check_job_status(self, run_id, job_data):
                # Check job status
                return status, reason

        queue = MyQueue(log)
        queue.post_run()
    """

    def __init__(
        self,
        log: Any,
        runtime_file: str,
        handler: Any = None,
        poll_interval: int = 1,
    ):
        """Initialize base queue handler.

        Args:
            log: Logger object for output
            runtime_file: Path to pipeline_runtime.yaml
            handler: Optional QueueCommandHandler for queue-specific operations
                     If provided, concrete implementations of abstract methods will use it
            poll_interval: Seconds between status check iterations (default: 1)
        """
        self.log = log
        self.runtime_file = runtime_file
        self.handler = handler
        self.poll_interval = poll_interval
        self.scheduler = None
        self.progress_display = None
        self.shutdown_pending = False
        self.initial_jobs_observed = False

    # ===== Template Method - Main Execution Loop =====
    # This is the core orchestration logic shared by all queue types.
    # Do not override this method - instead override the abstract methods.

    def post_run(self) -> None:
        """Main execution loop (template method).

        Orchestrates:
        1. Queue initialization
        2. Scheduler setup
        3. Main loop:
           - Submit ready jobs
           - Monitor job completion
           - Detect and handle blocking
           - Graceful shutdown on pipeline stall
        4. Final summary display
        5. Queue cleanup

        Do not override this method. Instead, implement the abstract methods
        to customize behavior for your queue system.
        """
        self.log.log.info("=" * 80)
        self.log.log.info("Queue Initialization")
        self.log.log.info("=" * 80)

        # Initialize queue-specific services
        self._initialize_queue()
        self._setup_scheduler()

        # Check if there are jobs to execute
        if self.scheduler.is_complete():
            self.log.log.info("No jobs to execute")
            self._cleanup_queue()
            return

        total_jobs = self._count_jobs()
        self.log.log.info(f"Total jobs to execute: {total_jobs}")

        self.log.log.info("=" * 80)
        self.log.log.info("Queue Execution")
        self.log.log.info("=" * 80)

        has_blocked = False
        blocked_ids = None

        try:
            while not self.scheduler.is_complete():
                # Reload runtime to pick up job completions
                self.scheduler.reload()

                # Check for blocked jobs only if:
                # 1. We've observed jobs being submitted, AND
                # 2. Now either no ready jobs remain OR no submitted jobs are running
                if not self.shutdown_pending:
                    ready_jobs = self._get_ready_jobs_queue_specific()
                    submitted_jobs = self.scheduler.get_submitted_jobs()

                    # Mark when we first observe jobs being submitted
                    if len(submitted_jobs) > 0:
                        self.initial_jobs_observed = True

                    # Count how many jobs have failed or completed
                    stats = self.scheduler.get_stats()
                    has_completed_or_failed = (stats["completed"] + stats["failed"]) > 0

                    # Only trigger blocking check if:
                    # - We have no ready jobs (all pending blocked by dependencies), AND
                    # - We have no submitted jobs (nothing running to unblock them), AND
                    # - Some jobs have failed (indicating a problem)
                    should_check_blocking = (
                        len(ready_jobs) == 0
                        and len(submitted_jobs) == 0
                        and has_completed_or_failed
                    )

                    if should_check_blocking:
                        has_blocked, block_msg, blocked_ids = (
                            self._detect_blocked_jobs()
                        )
                        if has_blocked:
                            self._log_block_message(block_msg)
                            self.shutdown_pending = True

                # Handle graceful shutdown if pending
                if self.shutdown_pending:
                    if self._handle_shutdown(has_blocked, blocked_ids):
                        break  # Exit main loop
                else:
                    # Normal operation: submit ready jobs and monitor completion
                    self._submit_ready_jobs()
                    self._monitor_job_completion()

                # Show progress
                self._show_progress(total_jobs)

                time.sleep(self.poll_interval)

        finally:
            # Final summary and cleanup
            self._finalize(total_jobs)
            self._cleanup_queue()

    # ===== Abstract Methods - Must Implement in Subclass =====

    @abstractmethod
    def _initialize_queue(self) -> None:
        """Queue-specific initialization.

        Called at the start of post_run() to set up queue system.

        Examples:
        - Create multiprocessing pool (parallel)
        - Query SLURM user and quotas (SLURM)
        - Initialize connection to queue system (PBS, LSF, etc.)

        Should raise an exception if initialization fails.
        """
        pass

    @abstractmethod
    def _cleanup_queue(self) -> None:
        """Queue-specific cleanup.

        Called at the end of post_run() to shut down queue system.

        Examples:
        - Close and terminate multiprocessing pool (parallel)
        - Stop quota manager threads (SLURM)
        - Close external connections
        """
        pass

    @abstractmethod
    def _get_ready_jobs_queue_specific(
        self,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Get jobs ready to submit (queue-specific logic).

        Different queue systems have different dependency models:
        - Local execution: Must wait for all dependencies to COMPLETE
        - SLURM: Can submit jobs with SUBMITTED dependencies (native --dependency)
        - PBS: Similar to SLURM, native dependencies available

        Returns:
            List of (run_id, job_data) tuples for jobs ready to submit
        """
        pass

    def _submit_job(
        self,
        run_id: str,
        job_data: Dict[str, Any],
    ) -> Optional[str]:
        """Submit a single job to queue system.

        Called for each ready job. Should update runtime YAML status internally
        or return queue ID for tracking.

        Default implementation (if handler provided):
            - Extracts command and requirements from job_data
            - Passes run_id to handler for tracking
            - Delegates to handler.submit_job()
            - Returns queue ID for tracking

        Args:
            run_id: Pipeline job ID (internal tracking)
            job_data: Job configuration dict from runtime YAML
                     Contains: command, requirements, dependencies, etc.

        Returns:
            Queue-specific job ID (e.g., SLURM job number) or None if failed

        Override if you need custom submission logic beyond the handler.
        """
        if self.handler:
            command = job_data.get("command")
            requirements = job_data.get("requirements", {})
            # Check if handler accepts run_id parameter (newer handlers)
            import inspect

            sig = inspect.signature(self.handler.submit_job)
            if "run_id" in sig.parameters:
                return self.handler.submit_job(command, requirements, run_id=run_id)
            else:
                # Fallback for old handlers without run_id parameter
                return self.handler.submit_job(command, requirements)
        # Subclasses must override if no handler provided
        raise NotImplementedError(
            "_submit_job must be implemented or handler must be provided"
        )

    def _check_job_status(
        self,
        run_id: str,
        job_data: Dict[str, Any],
    ) -> Tuple[str, Optional[str]]:
        """Check if a submitted job completed/failed.

        Called for each submitted job to determine its current state.

        Default implementation (if handler provided):
            - Gets queue_id from job_data
            - Delegates to handler.check_job_status()
            - Returns status tuple

        Args:
            run_id: Pipeline job ID
            job_data: Job configuration dict (includes queue_id)

        Returns:
            Tuple of (status, reason):
            - status: One of 'completed', 'failed', 'running', 'pending', 'unknown'
            - reason: Optional message explaining state (e.g., "Exit code: 1")

        Override if you need custom status checking logic beyond the handler.
        """
        if self.handler:
            queue_id = job_data.get("queue_id")
            if not queue_id:
                return ("unknown", "No queue_id")
            return self.handler.check_job_status(queue_id)
        # Subclasses must override if no handler provided
        raise NotImplementedError(
            "_check_job_status must be implemented or handler must be provided"
        )

    # ===== Concrete Helper Methods (Can override for customization) =====

    def _setup_scheduler(self) -> None:
        """Set up TaskScheduler and ProgressDisplay.

        Can be overridden to use custom ResourceManager implementations.
        Default: Use output from _get_resource_manager().
        """
        self.scheduler = TaskScheduler(
            self.runtime_file,
            self._get_resource_manager(),
            self.log,
        )
        self.progress_display = ProgressDisplay()

    def _get_resource_manager(self) -> ResourceManager:
        """Get ResourceManager implementation (override for custom managers).

        Default: No-op manager (returns True for all allocation checks).
        Override: Return LocalResourceManager (for parallel), SlurmQuotaManager (for SLURM).

        Returns:
            ResourceManager instance
        """

        # Default no-op resource manager
        class NoOpResourceManager(ResourceManager):
            def can_allocate(self, *args, **kwargs) -> bool:
                return True

            def allocate(self, *args, **kwargs) -> None:
                pass

            def release(self, *args, **kwargs) -> None:
                pass

            def get_stats(self) -> Dict[str, Any]:
                return {}

        return NoOpResourceManager()

    def _count_jobs(self) -> int:
        """Count actual jobs (excluding metadata entries)."""
        return len([k for k in self.scheduler.runtime.keys() if not k.startswith("__")])

    def _detect_blocked_jobs(self) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """Detect blocked jobs using common utility function."""
        return check_for_blocked_jobs(
            self.scheduler,
            self.log,
            self._get_resource_manager(),
        )

    def _log_block_message(self, message: str) -> None:
        """Log blocked job diagnostic message with formatting."""
        self.log.log.warning("")
        for line in message.split("\n"):
            self.log.log.warning(line)
        self.log.log.warning("")

    def _handle_shutdown(
        self,
        has_blocked: bool,
        blocked_ids: Optional[List[str]],
    ) -> bool:
        """Handle graceful shutdown.

        Args:
            has_blocked: Whether blocking was detected
            blocked_ids: List of blocked job IDs to cancel (if any)

        Returns:
            True if we should break from main loop, False to continue waiting
        """
        submitted = self.scheduler.get_submitted_jobs()
        if len(submitted) == 0:
            # No jobs running - safe to shutdown
            handle_graceful_shutdown(
                self.scheduler,
                self.runtime_file,
                self.log,
                blocked_ids,
            )
            return True  # Break from loop

        return False  # Continue waiting for jobs to finish

    def _submit_ready_jobs(self) -> None:
        """Get ready jobs and submit them.

        Calls _submit_job() for each ready job and updates status in YAML.
        """
        ready_jobs = self._get_ready_jobs_queue_specific()

        submitted_count = 0
        for run_id, job_data in ready_jobs:
            queue_id = self._submit_job(run_id, job_data)
            if queue_id:
                update_job_status(
                    self.runtime_file,
                    run_id,
                    JobStatus.SUBMITTED.value,
                    queue_id=queue_id,
                )
                submitted_count += 1

        if submitted_count > 0:
            self.log.log.debug(f"Submitted {submitted_count} job(s)")

    def _monitor_job_completion(self) -> None:
        """Monitor submitted jobs for completion and status transitions.

        Calls _check_job_status() for each submitted job and updates YAML
        when jobs transition to running, completed, failed, or cancelled states.

        When a job fails, automatically cancels all jobs that depend on it
        (cascade cancellation).
        """
        submitted = self.scheduler.get_submitted_jobs()
        for run_id, job_data in submitted:
            status, reason = self._check_job_status(run_id, job_data)

            if status == "running":
                # Job transitioned from submitted to running
                update_job_status(self.runtime_file, run_id, JobStatus.RUNNING.value)
                self.log.log.debug(f"[RUNNING] {run_id}")
            elif status == "completed":
                update_job_status(self.runtime_file, run_id, JobStatus.COMPLETED.value)
                self.log.log.debug(f"[COMPLETED] {run_id}")
            elif status == "cancelled":
                update_job_status(self.runtime_file, run_id, JobStatus.CANCELLED.value)
                self.log.log.info(f"[CANCELLED] {run_id}")
            elif status == "failed":
                error_msg = "Job failed"
                if reason:
                    error_msg += f": {reason}"
                update_job_status(
                    self.runtime_file,
                    run_id,
                    JobStatus.FAILED.value,
                    error_msg=error_msg,
                )
                self.log.log.error(f"[FAILED] {run_id}: {reason or 'unknown'}")

                # Cascade cancel all dependent jobs
                self._cascade_cancel_on_failure(run_id)

    def _cascade_cancel_on_failure(self, failed_job_id: str) -> None:
        """Cancel all jobs that depend on a failed job (cascade cancellation).

        Finds all jobs (transitively) that depend on the failed job and:
        - Cancels submitted/running jobs via handler.cancel_jobs()
          (monitoring will detect and update status)
        - Marks pending jobs as cancelled in runtime YAML

        Args:
            failed_job_id: Run ID of the job that failed
        """
        # Find all jobs that need to be cancelled
        to_cancel = cascade_cancel_dependents(
            self.runtime_file,
            failed_job_id,
            self.log,
        )

        if not to_cancel:
            return

        # Separate jobs with queue_id (submitted/running) from pending jobs
        jobs_with_queue_id = [
            (run_id, queue_id, name) for run_id, queue_id, name in to_cancel if queue_id
        ]
        pending_jobs = [
            (run_id, name) for run_id, queue_id, name in to_cancel if not queue_id
        ]

        # Cancel submitted/running jobs via queue system
        # Monitoring will detect the cancellation and update YAML
        if jobs_with_queue_id:
            queue_ids = [queue_id for _, queue_id, _ in jobs_with_queue_id]
            job_names = ", ".join([name for _, _, name in jobs_with_queue_id])
            self.log.log.warning(
                f"Cascade cancelling {len(jobs_with_queue_id)} submitted/running job(s) "
                f"that depend on failed job {failed_job_id}: {job_names}"
            )

            try:
                self.handler.cancel_jobs(queue_ids)
            except Exception as e:
                self.log.log.error(f"Failed to cancel jobs via queue system: {e}")

        # Mark pending jobs as cancelled (they haven't been submitted yet)
        if pending_jobs:
            self.log.log.warning(
                f"Marking {len(pending_jobs)} pending job(s) as cancelled "
                f"due to failed dependency {failed_job_id}"
            )
            for run_id, name in pending_jobs:
                update_job_status(
                    self.runtime_file,
                    run_id,
                    JobStatus.CANCELLED.value,
                    error_msg=f"Dependency failed: {failed_job_id}",
                )
                self.log.log.info(f"[CASCADE CANCEL] {name} ({run_id})")

    def _show_progress(self, total_jobs: int) -> None:
        """Display current progress.

        Shows job table with status counts and resource utilization.
        """
        stats = self.scheduler.get_stats()
        resource_stats = self._get_resource_manager().get_stats()

        # Filter out metadata entries
        jobs = self.scheduler.get_job_entries()

        self.progress_display.show_pipeline_status(jobs, stats, resource_stats)

    def _finalize(self, total_jobs: int) -> None:
        """Show final summary and cleanup.

        Args:
            total_jobs: Total number of jobs in pipeline
        """
        show_final_summary(
            self.scheduler,
            self.progress_display,
            self.log,
            total_jobs,
        )
