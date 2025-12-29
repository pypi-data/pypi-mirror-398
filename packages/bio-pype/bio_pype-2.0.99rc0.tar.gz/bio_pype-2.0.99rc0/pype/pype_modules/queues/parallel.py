"""Simplified parallel queue using handler-based architecture.

This is the minimal implementation showing how to use QueueCommandHandler.
All queue-specific logic is in ParallelCommandHandler.
All orchestration logic is in BaseQueue.
"""

import os
import shlex
import signal
import subprocess
from multiprocessing import Pool, Queue
from typing import Any, Dict, List, Optional, Tuple

import yaml
from psutil import cpu_count, virtual_memory

# Configuration
from pype.__config__ import PYPE_MEM, PYPE_NCPU
from pype.misc import bases_format
from pype.utils.compute_bio_api import initialize_api_watcher, stop_api_watchers
from pype.utils.queue_base import BaseQueue
from pype.utils.queue_commands import QueueCommandHandler
from pype.utils.queues import update_job_status, yaml_dump
from pype.utils.snippets import snippets_modules_list

PYPE_SNIPPETS_MODULES = snippets_modules_list({})


if PYPE_NCPU:
    MAX_CPU = int(PYPE_NCPU)
else:
    MAX_CPU = cpu_count()

if PYPE_MEM:
    MAX_MEM = bases_format(PYPE_MEM, 1024)
else:
    MAX_MEM = virtual_memory()[1]


POLL_INTERVAL = 1  # seconds


# ===== Local Resource Manager =====


class LocalResourceManager:
    """Manage local CPU and memory resources for parallel execution.

    Tracks CPU and memory allocation for tasks running in the local
    multiprocessing pool to ensure resource constraints are respected.
    """

    def __init__(self, max_cpus: int, max_mem: int):
        """Initialize resource manager.

        Args:
            max_cpus: Maximum CPUs to use
            max_mem: Maximum memory in bytes
        """
        self.max_cpus = max_cpus
        self.max_mem = max_mem
        self.allocated = {}  # job_id -> (cpus, mem) mapping

    def can_allocate(self, cpus: int, mem: int) -> bool:
        """Check if we have CPU and memory available.

        Args:
            cpus: CPUs required for task
            mem: Memory required in bytes

        Returns:
            True if resources are available
        """
        used_cpu = sum(c for c, m in self.allocated.values())
        used_mem = sum(m for c, m in self.allocated.values())

        return used_cpu + cpus <= self.max_cpus and used_mem + mem <= self.max_mem

    def allocate(self, task_id: str, cpus: int, mem: int) -> None:
        """Track resource allocation for a task.

        Args:
            task_id: Task identifier
            cpus: CPUs to allocate
            mem: Memory to allocate in bytes

        Notes:
            Always succeeds - tracks requested resources for visibility.
            Actual enforcement happens via multiprocessing pool concurrency limits.
        """
        self.allocated[task_id] = (cpus, mem)

    def release(self, task_id: str) -> None:
        """Free resources used by a task.

        Args:
            task_id: Task identifier
        """
        if task_id in self.allocated:
            del self.allocated[task_id]

    def get_stats(self) -> Dict[str, Any]:
        """Get current resource utilization.

        Returns:
            Dict with CPU and memory statistics
        """
        used_cpu = sum(c for c, m in self.allocated.values())
        used_mem = sum(m for c, m in self.allocated.values())

        return {
            "used_cpus": used_cpu,
            "max_cpus": self.max_cpus,
            "pct_cpu": 100.0 * used_cpu / self.max_cpus if self.max_cpus > 0 else 0,
            "used_mem": used_mem,
            "max_mem": self.max_mem,
            "pct_mem": 100.0 * used_mem / self.max_mem if self.max_mem > 0 else 0,
            "running_tasks": len(self.allocated),
        }


# ===== Parallel Command Handler =====


class ParallelCommandHandler(QueueCommandHandler):
    """Local parallel execution command operations.

    Manages job execution via multiprocessing pool with CPU/memory constraints.
    Jobs are queued locally and executed in separate processes.
    """

    def __init__(
        self,
        max_cpus: int,
        max_mem: int,
        task_queue: Queue,
        log: Any = None,
        resource_manager: Optional[Any] = None,
        runtime_file: Optional[str] = None,
    ):
        """Initialize parallel command handler.

        Args:
            max_cpus: Maximum CPUs for local execution
            max_mem: Maximum memory in bytes for local execution
            task_queue: Multiprocessing Queue for queuing jobs
            log: Optional logger object (PypeLogger)
            resource_manager: Optional LocalResourceManager instance (shared with queue)
            runtime_file: Path to pipeline_runtime.yaml (for reading PIDs during cancel)
        """
        self.max_cpus = max_cpus
        self.max_mem = max_mem
        self.task_queue = task_queue
        self.log = log
        self.runtime_file = runtime_file
        # Use provided resource manager or create a new one
        self.resource_manager = resource_manager or LocalResourceManager(
            max_cpus, max_mem
        )
        self.running_jobs = {}  # job_id -> command mapping

    def submit_job(
        self, command: str, requirements: Dict[str, Any], run_id: str
    ) -> Optional[str]:
        """Queue a job for local execution.

        Args:
            command: Command to execute
            requirements: Resource requirements (ncpu, mem)
            run_id: Pipeline run ID (used as job identifier for tracking)

        Returns:
            Job ID (run_id) for tracking
        """

        cpus, mem = self._get_task_requirements(requirements)

        # Track resource requirements (for visibility and monitoring)
        # Note: Don't block submission based on current resource availability
        # The multiprocessing pool naturally limits concurrency.
        # Resource tracking is for monitoring/reporting only.
        self.resource_manager.allocate(run_id, cpus, mem)

        # Queue the task for execution
        task_data = {"command": command}
        self.task_queue.put((run_id, task_data))

        # Track running job
        self.running_jobs[run_id] = command

        return run_id

    def check_job_status(self, queue_id: str) -> Tuple[str, Optional[str]]:
        """Check local job status.

        For local execution, the worker process updates status directly in YAML.
        We check if job is still running based on resource allocation.

        Args:
            queue_id: Job ID (run_id)

        Returns:
            (status, reason) tuple
        """
        # If job is in resource allocation, it's running or pending execution
        if queue_id in self.resource_manager.allocated:
            return ("running", None)

        # If we're tracking it but not allocated, it might be queued
        if queue_id in self.running_jobs:
            return ("running", None)

        # Job not found - it may have completed
        # Status will be updated by worker process to YAML
        return ("unknown", None)

    def _cancel_job_impl(self, queue_id: str) -> bool:
        """Cancel a local job by killing its subprocess.

        Reads the PID from the runtime YAML (stored by worker when job started)
        and sends SIGTERM to terminate the process.

        Args:
            queue_id: Job ID (run_id)

        Returns:
            True if successful (or job not found/already finished)
        """
        # Release resource tracking
        if queue_id in self.resource_manager.allocated:
            self.resource_manager.release(queue_id)

        if queue_id in self.running_jobs:
            del self.running_jobs[queue_id]

        # Try to kill the subprocess by PID (stored in runtime YAML by worker)
        if self.runtime_file:
            try:
                with open(self.runtime_file, "r") as f:
                    runtime_data = yaml.safe_load(f) or {}

                job_data = runtime_data.get(queue_id, {})
                pid = job_data.get("pid")

                if pid:
                    try:
                        # First try SIGTERM for graceful shutdown
                        os.kill(pid, signal.SIGTERM)
                        if self.log:
                            self.log.log.info(
                                f"Sent SIGTERM to process {pid} for job {queue_id}"
                            )
                        return True
                    except ProcessLookupError:
                        # Process already exited - that's fine
                        if self.log:
                            self.log.log.debug(
                                f"Process {pid} for job {queue_id} already exited"
                            )
                        return True
                    except PermissionError:
                        if self.log:
                            self.log.log.error(
                                f"Permission denied killing process {pid}"
                            )
                        return False
            except Exception as e:
                if self.log:
                    self.log.log.error(f"Error cancelling job {queue_id}: {e}")
                return False

        return True

    def get_queue_load(self) -> int:
        """Get number of running tasks.

        Returns:
            Count of jobs currently running locally
        """
        return len(self.resource_manager.allocated)

    def query_job_resources(self, queue_id: str) -> Optional[Dict[str, Any]]:
        """Query resource usage for a job.

        Local execution doesn't track detailed resource usage.
        Could be enhanced with process monitoring (psutil).

        Args:
            queue_id: Job ID

        Returns:
            None (feature not available for local execution)
        """
        # Could enhance this with psutil to monitor process resources
        # For now, return None to indicate feature unavailable
        return None

    # ===== Private Helper Methods =====

    def _get_task_requirements(self, requirements: Dict[str, Any]) -> Tuple[int, int]:
        """Extract CPU and memory requirements from task.

        Args:
            requirements: Requirements dict with ncpu and mem

        Returns:
            Tuple of (cpus, mem_bytes)
        """
        # Extract CPUs
        try:
            cpus = int(requirements.get("ncpu", 1))
        except (ValueError, TypeError):
            cpus = 1

        # Extract memory
        try:
            mem = bases_format(requirements.get("mem", "1gb"), 1024)
        except (ValueError, TypeError):
            mem = 1024**3  # Default 1GB

        return cpus, mem


def _worker_process(queue: Queue, runtime_file: str, log_parent: Any) -> None:
    """Worker process that executes queued tasks.

    Args:
        queue: Multiprocessing queue with tasks
        runtime_file: Path to pipeline_runtime.yaml
        log_parent: Parent logger for status updates
    """
    while True:
        try:
            task_id, task_data = queue.get(True)
        except KeyboardInterrupt:
            log_parent.log.error("KeyboardInterrupt intercepted")
            break

        # Mark as running
        update_job_status(runtime_file, task_id, "running")

        # Execute command
        command_str = task_data["command"]
        command_list = shlex.split(command_str)

        # Extract log directory from command
        try:
            log_index = command_list.index("--log")
            log_path = command_list[log_index + 1]
        except (ValueError, IndexError):
            log_parent.log.error(
                f"Could not extract log path from command: {command_str}"
            )
            update_job_status(
                runtime_file, task_id, "failed", error_msg="Could not extract log path"
            )
            continue

        # Prepare stdout/stderr paths
        stdout = os.path.join(log_path, "stdout")
        stderr = os.path.join(log_path, "stderr")

        # Execute with output redirection
        try:
            with open(stdout, "wt") as out, open(stderr, "wt") as err:
                proc = subprocess.Popen(command_list, stdout=out, stderr=err)

                # Store PID in runtime YAML for cancellation support
                update_job_status(runtime_file, task_id, None, pid=proc.pid)

                exit_code = proc.wait()

            # Clear PID and update status based on exit code
            if exit_code == 0:
                update_job_status(runtime_file, task_id, "completed", pid=None)
            elif exit_code == -signal.SIGTERM or exit_code == -signal.SIGKILL:
                # Process was killed by signal - mark as cancelled
                update_job_status(
                    runtime_file, task_id, "cancelled", pid=None,
                    error_msg=f"Killed by signal {-exit_code}"
                )
            else:
                update_job_status(
                    runtime_file, task_id, "failed", pid=None,
                    error_msg=f"Exit code: {exit_code}"
                )
        except Exception as e:
            update_job_status(runtime_file, task_id, "failed", pid=None, error_msg=str(e))


class ParallelQueue(BaseQueue):
    """Local execution queue using multiprocessing with handler pattern.

    Minimal implementation:
    - Handler manages job submission to multiprocessing pool
    - BaseQueue handles all orchestration (submission loop, monitoring, blocking detection)
    - Only override queue-specific init/cleanup
    """

    def __init__(self, log: Any):
        """Initialize parallel queue with handler.

        Args:
            log: Logger object (PypeLogger)
        """
        root_dir = os.path.dirname(log.__path__)
        runtime_file = os.path.join(root_dir, "pipeline_runtime.yaml")

        # Create shared resource manager (used by both handler and queue for tracking)
        self.resource_manager = LocalResourceManager(MAX_CPU, MAX_MEM)

        # Create handler with shared resource manager and logger
        self.task_queue = Queue()
        handler = ParallelCommandHandler(
            MAX_CPU,
            MAX_MEM,
            self.task_queue,
            log=log,
            resource_manager=self.resource_manager,
            runtime_file=runtime_file,
        )

        # Initialize multiprocessing pool (will execute _worker_process)
        self.pool = Pool(MAX_CPU, _worker_process, (self.task_queue, runtime_file, log))

        # API watcher instances (initialized in _initialize_queue)
        self.api_client = None
        self.progress_watcher = None
        self.command_watcher = None

        # Pass handler to BaseQueue - it will use default implementations
        super().__init__(
            log, runtime_file, handler=handler, poll_interval=POLL_INTERVAL
        )

    def _initialize_queue(self) -> None:
        """Initialize queue-specific resources and store config for resume."""
        # Log resource limits
        max_mem_gb = MAX_MEM / (1024**3)
        self.log.log.info(f"Max CPUs: {MAX_CPU}")
        self.log.log.info(f"Max Memory: {max_mem_gb:.2f} GB ({MAX_MEM} bytes)")

        # Store parallel execution configuration in metadata for resume pattern
        try:
            with open(self.runtime_file, "r") as f:
                runtime_data = yaml.safe_load(f) or {}

            if "__pipeline_metadata__" in runtime_data:
                # Store queue configuration so resume uses same settings
                runtime_data["__pipeline_metadata__"]["queue_config"] = {
                    "max_cpu": MAX_CPU,
                    "max_mem": MAX_MEM,
                }

                with open(self.runtime_file, "w") as f:
                    yaml.dump(
                        runtime_data, f, default_flow_style=False, sort_keys=False
                    )

                self.log.log.debug(
                    "Stored parallel configuration in metadata for resume"
                )
        except Exception as e:
            self.log.log.debug(f"Could not store queue config in metadata: {e}")

        # Initialize API watchers for compute.bio monitoring (optional)
        # Check for existing run_id and worker_id from previous execution (for resume)
        existing_run_id = None
        existing_worker_id = None
        try:
            with open(self.runtime_file, "r") as f:
                runtime_data = yaml.safe_load(f) or {}
                metadata = runtime_data.get("__pipeline_metadata__", {})
                existing_run_id = metadata.get("run_id")
                existing_worker_id = metadata.get("worker_id")
                if existing_run_id:
                    self.log.log.info(
                        f"Found existing run_id in metadata: {existing_run_id}"
                    )
                if existing_worker_id:
                    self.log.log.info(
                        f"Found existing worker_id in metadata: {existing_worker_id}"
                    )
        except Exception as e:
            self.log.log.debug(f"Could not read existing run_id/worker_id: {e}")

        # Initialize API watchers
        (
            self.api_client,
            self.progress_watcher,
            self.command_watcher,
            api_success,
        ) = initialize_api_watcher(
            self.runtime_file,
            self.log,
            existing_run_id=existing_run_id,
            existing_worker_id=existing_worker_id,
            queue_handler=self.handler,
        )

        if api_success:
            self.log.log.info("API watchers initialized and running")

            # Save run_id, run_hash, and worker_id to metadata if this is a new registration
            if (
                self.api_client
                and self.api_client.pipeline_id
                and existing_run_id is None
            ):
                try:
                    # Update runtime YAML directly with run_id, run_hash, and worker_id
                    with open(self.runtime_file, "r") as f:
                        runtime_data = yaml.safe_load(f) or {}

                    if "__pipeline_metadata__" in runtime_data:
                        runtime_data["__pipeline_metadata__"]["run_id"] = (
                            self.api_client.pipeline_id
                        )
                        runtime_data["__pipeline_metadata__"]["run_hash"] = (
                            self.api_client.pipeline_hash
                        )
                        runtime_data["__pipeline_metadata__"]["worker_id"] = (
                            self.api_client.worker_id
                        )

                        with open(self.runtime_file, "w") as f:
                            yaml.dump(
                                runtime_data,
                                f,
                                default_flow_style=False,
                                sort_keys=False,
                            )

                        self.log.log.info(
                            f"Saved run_id {self.api_client.pipeline_id} and worker_id {self.api_client.worker_id} to metadata"
                        )
                    else:
                        self.log.log.warning(
                            "No __pipeline_metadata__ section found in runtime YAML"
                        )
                except Exception as e:
                    self.log.log.warning(
                        f"Failed to save run_id/worker_id to metadata: {e}"
                    )
        else:
            self.log.log.info("API integration not configured or failed to initialize")

    def _cleanup_queue(self) -> None:
        """Close multiprocessing pool and stop API watchers."""
        # Send final progress update before stopping watchers
        if self.api_client:
            try:
                self.log.log.info("Sending final progress update...")
                self.api_client.send_progress(self.runtime_file)
                self.log.log.info("Final progress update sent")
            except Exception as e:
                self.log.log.error(f"Failed to send final progress update: {e}")

        # Stop API watchers before pool cleanup
        if self.progress_watcher or self.command_watcher:
            stop_api_watchers(self.progress_watcher, self.command_watcher, self.log)

        # Close multiprocessing pool
        if self.pool:
            self.pool.close()
            self.pool.terminate()

    def _get_resource_manager(self):
        """Return the LocalResourceManager for progress tracking.

        BaseQueue uses this to display CPU and memory usage in progress output.
        """
        return self.resource_manager

    def _monitor_job_completion(self) -> None:
        """Monitor submitted jobs for completion and release resources when done.

        Extends BaseQueue's implementation to also release resources from the
        resource manager when jobs complete or fail.
        """
        # Call parent implementation to update job status
        super()._monitor_job_completion()

        # Release resources for all completed/failed/cancelled jobs
        # Check all jobs in runtime, not just submitted ones
        for run_id, job_data in self.scheduler.runtime.items():
            # Skip metadata entries
            if run_id.startswith("__"):
                continue

            status = job_data.get("status")
            if status in ("completed", "failed", "cancelled"):
                # Only release if still allocated (avoid double-release)
                if run_id in self.resource_manager.allocated:
                    self.resource_manager.release(run_id)

    def _get_ready_jobs_queue_specific(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Get jobs ready for local parallel execution.

        For local execution: Must wait for all dependencies to COMPLETE.
        Unlike SLURM, we cannot submit jobs with pending dependencies.

        Returns:
            List of (run_id, job_data) tuples ready to submit
        """
        return self.scheduler.get_ready_jobs()


def submit(
    command: str,
    snippet_name: str,
    requirements: Dict[str, Any],
    dependencies: list,
    log: Any,
    profile: str,
    batch_id: Optional[str] = None,
) -> str:
    """Queue a job for local execution.

    Args:
        command: Bare snippet command
        snippet_name: Human-readable job name
        requirements: Resource requirements dict
        dependencies: List of job IDs to depend on
        log: Logger object
        profile: Profile name
        batch_id: Optional batch identifier

    Returns:
        Job run_id
    """
    run_id = yaml_dump(
        command,
        snippet_name,
        requirements,
        dependencies,
        log,
        profile,
        batch_id,
        PYPE_SNIPPETS_MODULES,
    )
    return run_id


def get_handler(
    runtime_data: Optional[Dict[str, Any]] = None,
    runtime_file: Optional[str] = None,
) -> ParallelCommandHandler:
    """Get a handler for queue operations (job cancellation, status checking, etc.).

    Used by resume and monitoring code to interact with the queue system.

    Args:
        runtime_data: Optional pipeline runtime data dict (from resume/metadata).
                     If provided, uses configuration from pipeline metadata.
                     If None, uses current system configuration.
        runtime_file: Optional path to pipeline_runtime.yaml (needed for cancel
                     operations to read PIDs).

    Returns:
        ParallelCommandHandler instance configured with system resources
    """
    # If runtime data provided, extract config from metadata
    if runtime_data:
        metadata = runtime_data.get("__pipeline_metadata__", {})
        config = metadata.get("queue_config", {})
        max_cpu = config.get("max_cpu", MAX_CPU)
        max_mem = config.get("max_mem", MAX_MEM)
    else:
        max_cpu = MAX_CPU
        max_mem = MAX_MEM

    task_queue = Queue()
    return ParallelCommandHandler(
        max_cpu, max_mem, task_queue, log=None, runtime_file=runtime_file
    )


def post_run(log: Any) -> None:
    """Execute all queued jobs with resource management.

    Args:
        log: Logger object
    """
    log.add_log("parallel_run")
    queuelog = log.programs_logs["parallel_run"]

    queuelog.log.info("=" * 80)
    queuelog.log.info("Parallel Queue Execution")
    queuelog.log.info("=" * 80)

    queue = ParallelQueue(queuelog)
    try:
        queue.post_run()
    except KeyboardInterrupt:
        queuelog.log.info("\nParent caught KeyboardInterrupt! Terminating workers...")
        queue.pool.terminate()  # Forcefully stop all worker processes
        queue.pool.join()  # Wait for processes to actually exit
        queuelog.log.info("Workers terminated.")
