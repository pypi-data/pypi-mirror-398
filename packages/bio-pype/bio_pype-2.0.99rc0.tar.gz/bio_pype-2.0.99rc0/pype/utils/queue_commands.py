"""Abstract base class for queue-specific command handlers.

This module defines the QueueCommandHandler interface that all queue
implementations must follow. Each queue system (parallel, SLURM, PBS, etc.)
provides its own handler subclass.

Queue implementations are discovered via PYPE_MODULES environment variable,
which points to a folder containing queue modules in <PYPE_MODULES>/queues/.

Each queue module is self-contained:
- Defines its own QueueCommandHandler subclass
- Implements BaseQueue orchestration
- Provides get_handler() function for handler instantiation

Example:
    # In pype/pype_modules/queues/parallel.py
    class ParallelCommandHandler(QueueCommandHandler):
        def submit_job(self, command, requirements):
            # Implementation
            pass

    # Resume or monitoring code imports from active PYPE_MODULES
    from queues.parallel import ParallelCommandHandler
    handler = ParallelCommandHandler(max_cpus=4, max_mem=8gb)
    handler.cancel_job(queue_id)
"""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import yaml


def parse_command_data(
    cmd: Dict[str, Any],
    runtime_file: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Parse API command and return data dict for handler.

    Simply parses the JSON message field and adds runtime context.
    No field-specific extraction - handlers receive all data from API.

    Args:
        cmd: Command dict from API with 'message' field containing JSON string
        runtime_file: Path to pipeline_runtime.yaml (added to result)

    Returns:
        Dict containing all fields from the parsed message plus runtime_file
    """
    cmd_message = cmd.get("message", "{}")
    try:
        data = json.loads(cmd_message) if isinstance(cmd_message, str) else cmd_message
    except (json.JSONDecodeError, ValueError, TypeError):
        data = {}

    # Add runtime context
    data["runtime_file"] = str(runtime_file) if runtime_file else None
    data["_cmd"] = cmd  # Original command if needed

    return data


def execute_command(
    handler: "QueueCommandHandler",
    cmd: Dict[str, Any],
    runtime_file: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Execute an API command through the handler.

    Shared command execution logic used by both:
    - Listener daemon (pype.modules.compute_bio) for inactive workers
    - CommandWatcher (pype.utils.compute_bio_api) for active pipelines

    Uses direct dispatch via getattr() - handler method names must match
    API command_type exactly (e.g., "get_snippet_logs", "cancel").

    Args:
        handler: QueueCommandHandler instance
        cmd: Command dict from API with 'command_type' and 'message' fields
        runtime_file: Path to pipeline_runtime.yaml

    Returns:
        Dict with execution result (always includes 'success' key)
    """
    cmd_type = cmd.get("type") or cmd.get("command_type", "unknown")
    data = parse_command_data(cmd, runtime_file)

    method = getattr(handler, cmd_type, None)
    if method is None:
        return {"success": False, "error": f"Unknown command: {cmd_type}"}

    try:
        return method(data)
    except Exception as e:
        return {"success": False, "error": str(e)}


class QueueCommandHandler(ABC):
    """Abstract base for queue-specific operations.

    Subclasses implement queue-specific logic (SLURM, Torque, PBS, etc.).
    Generic operations (log handling) are provided here.

    All queue-specific logic is centralized in handler subclasses,
    making it easy to:
    - Add new queue systems
    - Use queue commands from other modules
    - Test queue-specific behavior in isolation
    """

    # ===== ABSTRACT METHODS - Queue-Specific Operations =====
    # Subclasses MUST implement these methods

    @abstractmethod
    def submit_job(
        self, command: str, requirements: Dict[str, Any], run_id: str
    ) -> Optional[str]:
        """Submit a job to the queue system.

        Args:
            command: Full command to execute (already wrapped/prepared)
            requirements: Resource requirements dict with keys:
                - ncpu: Number of CPUs (int)
                - mem: Memory requirement (str, e.g., "8gb")
                - time: Time limit (str, e.g., "02:00:00" or "1-12:00:00")
                - Other queue-specific keys (partition, account, etc.)
            run_id: Pipeline run ID (used as job identifier for tracking)

        Returns:
            Queue-specific job ID (e.g., SLURM job number, process ID)
            or None if submission failed

        Raises:
            Should NOT raise exceptions - log errors and return None
        """

    @abstractmethod
    def check_job_status(self, queue_id: str) -> Tuple[str, Optional[str]]:
        """Check the status of a submitted job.

        Args:
            queue_id: Queue-specific job identifier

        Returns:
            Tuple of (status, reason) where:
            - status: One of 'running', 'pending', 'completed', 'failed', 'unknown'
            - reason: Optional explanation (e.g., "Exit code: 1", "Dependency pending")

        Notes:
            - Should handle both active and completed jobs
            - Return 'completed' for successfully finished jobs
            - Return 'failed' for jobs that exited with error or were killed
            - Return 'running' for active jobs
            - Return 'pending' for queued but not started jobs
            - Return 'unknown' if status cannot be determined
        """

    @abstractmethod
    def _cancel_job_impl(self, queue_id: str) -> bool:
        """Cancel a single job (queue-specific implementation).

        Args:
            queue_id: Queue-specific job identifier

        Returns:
            True if cancellation was successful, False otherwise

        Notes:
            - Should handle already-completed jobs gracefully
            - Should NOT raise exceptions
            - Called by cancel_job() API handler
        """

    @abstractmethod
    def get_queue_load(self) -> int:
        """Get current number of jobs in the queue.

        Returns:
            Number of jobs currently queued/running for this user
            Returns large number if query fails (fail-safe for quotas)

        Notes:
            - Used for quota enforcement and throttling decisions
            - Should include only jobs for this user/account
        """

    @abstractmethod
    def query_job_resources(self, queue_id: str) -> Optional[Dict[str, Any]]:
        """Query actual resource usage for a completed job.

        Args:
            queue_id: Queue-specific job identifier

        Returns:
            Dict with resource usage info:
            {
                'mem_used_gb': float,           # Actual memory used in GB
                'cpu_used': float,               # CPU time used
                'mem_efficiency': float,         # Percentage (0-100)
                'cpu_efficiency': float,         # Percentage (0-100)
                'time_elapsed': str,             # HH:MM:SS format
                'status': str,                   # Job state (COMPLETED, FAILED, etc.)
                'notes': str,                    # Any additional info
            }
            or None if query fails

        Notes:
            - Only works for completed jobs
            - Used for resource optimization and reporting
            - Can return None if feature not available for this queue type
        """

    def cancel_jobs(self, queue_ids: list) -> bool:
        """Cancel multiple jobs (default: calls _cancel_job_impl for each).

        Override this for batch operations (e.g., scancel job1 job2 job3).

        Args:
            queue_ids: List of queue-specific job identifiers

        Returns:
            True if all cancellations succeeded, False if any failed
        """
        success = True
        for queue_id in queue_ids:
            if not self._cancel_job_impl(queue_id):
                success = False
        return success

    # ===== CONCRETE METHODS - Queue-Naive Operations =====
    # Generic implementations that don't need to be overridden

    def _read_snippet_logs(
        self,
        runtime_file: str,
        task_id: str,
        log_type: str,
        log_lines: Optional[int] = 500,
    ) -> Optional[Dict[str, Any]]:
        """Read logs for a snippet run from filesystem.

        Internal method called by get_snippet_logs() API handler.

        Args:
            runtime_file: Path to pipeline_runtime.yaml
            task_id: ID of the snippet run to get logs for
            log_lines: Optional limit on number of lines to return

        Returns:
            Dict with stdout and stderr content, or None if not found
        """
        try:
            # Load runtime to find job info
            with open(runtime_file, "r") as f:
                runtime_data = yaml.safe_load(f) or {}

            if task_id not in runtime_data:
                return None

            job_data = runtime_data[task_id]

            command = job_data.get("command", "")
            if not command or "--log" not in command.split():
                return {
                    "logs": "",
                    "status": "not_found",
                    "lines": 0,
                    "file_size": 0,
                    "message": "No --log path in command",
                }
            command_parts = command.split()
            log_index = command_parts.index("--log")
            if log_index + 1 >= len(command_parts):
                return {
                    "logs": "",
                    "status": "not_found",
                    "lines": 0,
                    "file_size": 0,
                    "message": "Invalid --log path",
                }
            log_dir = command_parts[log_index + 1]

            if not log_dir or not Path(log_dir).exists():
                return None

            # Read stdout and stderr
            if log_type not in ["stdout", "stderr"]:
                return None
            std_log_file = Path(log_dir) / log_type
            std_log_content = ""

            if std_log_file.exists():
                with open(std_log_file, "r") as f:
                    lines = f.readlines()
                    if log_lines:
                        lines = lines[-log_lines:]
                    std_log_content = "".join(lines)

            if std_log_content == "":
                std_log_content = "<no content>"

            return {
                "content": std_log_content,
                "timestamp": str(Path(log_dir).stat().st_mtime),
            }

        except Exception as e:
            # Log error but don't raise - fail gracefully
            return None

    def stop_following_logs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Stop following logs for a snippet - API command handler.

        Method name matches API command_type "stop_following_logs".

        Args:
            data: Should contain:
                - task_id: ID of the snippet run to stop following

        Returns:
            Dict with success status
        """
        # Default: no active log following to stop - always succeeds
        return {"success": True}

    # ===== API Command Handlers =====
    # Method names match API command_type exactly for direct dispatch via getattr

    def get_snippet_logs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get logs for a snippet/task - API command handler.

        Method name matches API command_type "get_snippet_logs".

        Args:
            data: Should contain (from API message):
                - runtime_file: Path to pipeline_runtime.yaml (added by parse_command_data)
                - task_id: Job identifier
                - log_type: "stdout" or "stderr" (default: "stderr")
                - log_lines or tail_lines (optional): Number of lines to return

        Returns:
            Dict with log content or error
        """
        runtime_file = data.get("runtime_file")
        task_id = data.get("task_id")
        log_type = data.get("log_type", "stderr")
        log_lines = data.get("log_lines") or data.get("tail_lines")

        if not runtime_file or not task_id:
            return {
                "success": False,
                "error": "Missing runtime_file or task_id",
            }

        result = self._read_snippet_logs(runtime_file, task_id, log_type, log_lines)
        if result:
            return {
                "success": True,
                "logs": result.get("content", ""),
                "log_type": log_type,
                "timestamp": result.get("timestamp"),
            }
        else:
            return {"success": False, "error": "Logs not found"}

    def cancel(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a running job - API command handler.

        Method name matches API command_type "cancel".

        Args:
            data: Should contain:
                - queue_id: Queue-specific job identifier
                OR
                - runtime_file: Path to pipeline_runtime.yaml (to cancel all jobs)

        Returns:
            Dict with cancellation success status
        """
        queue_id = data.get("queue_id")
        runtime_file = data.get("runtime_file")

        # If queue_id provided, cancel single job
        if queue_id:
            try:
                success = self._cancel_job_impl(queue_id)
                return {
                    "success": success,
                    "queue_id": queue_id,
                    "message": "Job cancelled" if success else "Cancellation failed",
                }
            except Exception as e:
                return {"success": False, "queue_id": queue_id, "error": str(e)}

        # If runtime_file provided, cancel all running/submitted jobs in pipeline
        if runtime_file:
            try:
                with open(runtime_file, "r") as f:
                    runtime_data = yaml.safe_load(f) or {}

                # Collect all queue_ids for running/submitted jobs
                queue_ids_to_cancel = []
                cancelled_jobs = []

                for run_id, job_data in runtime_data.items():
                    # Skip metadata entries
                    if run_id.startswith("__"):
                        continue
                    if not isinstance(job_data, dict):
                        continue

                    status = job_data.get("status", "")
                    job_queue_id = job_data.get("queue_id")

                    # Cancel running or submitted jobs
                    if status in ("running", "submitted") and job_queue_id:
                        queue_ids_to_cancel.append(job_queue_id)
                        cancelled_jobs.append({
                            "run_id": run_id,
                            "queue_id": job_queue_id,
                            "name": job_data.get("name", run_id[:12]),
                        })

                if not queue_ids_to_cancel:
                    return {
                        "success": True,
                        "message": "No running jobs to cancel",
                        "cancelled_count": 0,
                    }

                # Cancel all jobs (uses batch cancellation if available)
                success = self.cancel_jobs(queue_ids_to_cancel)

                return {
                    "success": success,
                    "message": f"Cancelled {len(queue_ids_to_cancel)} job(s)",
                    "cancelled_count": len(queue_ids_to_cancel),
                    "cancelled_jobs": cancelled_jobs,
                }

            except Exception as e:
                return {"success": False, "error": f"Failed to cancel pipeline: {str(e)}"}

        return {"success": False, "error": "Missing queue_id or runtime_file"}
