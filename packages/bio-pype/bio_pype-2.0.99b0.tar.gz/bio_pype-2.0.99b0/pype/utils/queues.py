"""Queue management system for bio_pype.

Key features:
- Queue selection and configuration
- Job dependency management
- Resource allocation
- Job status tracking
- Queue-specific command generation
- Runtime environment setup

Classes:
    SnippetRuntime: Helper for queue implementations

Functions:
    yaml_dump: Serialize job configuration
"""

import fcntl
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from enum import Enum
from time import sleep
from typing import Any, Dict, List, Optional, Tuple

import yaml

from pype.argparse import ArgumentParser
from pype.exceptions import CommandError
from pype.misc import generate_uid, get_module_method


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def yaml_dump(
    command: str,
    snippet_name: str,
    requirements: Dict[str, Any],
    dependencies: List[str],
    log: Any,
    profile: str,
    batch_id: Optional[str] = None,
    snippet_module: Optional[Any] = None,
) -> str:
    """Dump job configuration to YAML using SnippetRuntime for consistency.

    This function uses SnippetRuntime to generate the complete YAML structure
    including command wrapping. SnippetRuntime handles wrapping the command
    in a pype snippets call and generates the same YAML format as other
    queue modules (slurm_mock, etc.).

    Args:
        command: Bare snippet command to execute (e.g., "snippet_name --arg val")
        snippet_name: Human-readable name for the job
        requirements: Resource requirements dict
        dependencies: List of job IDs this depends on
        log: Logger object
        profile: Profile name
        batch_id: Optional batch identifier for grouping related jobs (batch_snippets only)

    Returns:
        str: Job run_id
    """
    # Use SnippetRuntime for consistent YAML format with all fields
    # SnippetRuntime handles command wrapping internally
    # This ensures yaml_dump() produces the same format as slurm_mock.py
    runtime = SnippetRuntime(command, log, profile)

    # Set the human-readable snippet name
    # runtime.snippet_name = snippet_name

    # Build complete runtime structure with all required fields
    runtime.get_runtime(requirements, dependencies)

    # Store friendly name in runtime for better progress display
    runtime.runtime[runtime.run_id]["name"] = snippet_name

    # Store batch_id if provided (used for grouping batch_snippet jobs into arrays)
    if batch_id:
        runtime.runtime[runtime.run_id]["batch_id"] = batch_id

    if snippet_module:
        runtime.add_snippet_description(runtime.command, snippet_module)
        log.log.info(
            f"Add snippet description for {snippet_name}:\n {runtime.runtime[runtime.run_id]['description']}"
        )

    # Log submission details
    log.log.info(f"Queue yaml_dump, snippet: {snippet_name}")
    log.log.info(f"Queue yaml_dump, command: {runtime.command}")
    log.log.info(f"Queue yaml_dump, requirements: {requirements}")
    log.log.info(f"Queue yaml_dump, dependencies: {dependencies}")
    log.log.info(f"Queue yaml_dump, run ID: {runtime.run_id}")
    if batch_id:
        log.log.info(f"Queue yaml_dump, batch_id: {batch_id}")

    # Commit to YAML file with complete structure
    runtime.commit_runtime()

    sleep(1)
    return runtime.run_id


# ========== YAML Runtime Status Tracking ==========
# Minimal helpers for resume/skip logic and array job grouping
# All functions use file locking to ensure thread-safe access
# With retry logic and fallback for systems with lock limits (e.g., NFS)

_LOCK_RETRY_ATTEMPTS = 5
_LOCK_RETRY_DELAY = 0.1  # seconds


def _try_acquire_lock(
    lockf, lock_type: int, max_retries: int = _LOCK_RETRY_ATTEMPTS
) -> bool:
    """Try to acquire a lock with retries.

    Handles "No locks available" error by retrying with backoff.

    Args:
        lockf: Open lock file
        lock_type: fcntl.LOCK_EX or fcntl.LOCK_SH
        max_retries: Number of retry attempts

    Returns:
        True if lock acquired, False if all retries exhausted
    """
    import time

    for attempt in range(max_retries):
        try:
            fcntl.flock(lockf.fileno(), lock_type)
            return True
        except OSError as e:
            if e.errno == 37:  # "No locks available"
                if attempt < max_retries - 1:
                    time.sleep(_LOCK_RETRY_DELAY * (attempt + 1))
                    continue
            # On final attempt or other errors, re-raise
            raise

    return False


def _read_runtime_file_locked(runtime_file: str) -> Dict[str, Any]:
    """Read runtime YAML file with shared lock.

    Helper to ensure consistent locking behavior across all read operations.
    Uses retry logic for systems with lock limits (e.g., NFS).

    Args:
        runtime_file: Path to pipeline_runtime.yaml

    Returns:
        Parsed YAML dict or empty dict if file not found
    """
    if not os.path.isfile(runtime_file):
        return {}

    lock_file = runtime_file + ".lock"

    try:
        with open(lock_file, "a") as lockf:
            # Try to acquire shared lock with retries
            if not _try_acquire_lock(lockf, fcntl.LOCK_SH):
                # If retries exhausted, read without lock (less safe but better than failure)
                pass

            try:
                with open(runtime_file, "rt") as f:
                    runtime = yaml.safe_load(f)
                return runtime or {}
            finally:
                try:
                    fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
                except (OSError, ValueError):
                    pass  # Lock wasn't acquired or already released
    except (OSError, IOError) as e:
        # If lock file operations fail, try to read without locking
        # This is less safe but better than crashing
        try:
            with open(runtime_file, "rt") as f:
                runtime = yaml.safe_load(f)
            return runtime or {}
        except (OSError, IOError):
            return {}


def _restore_environment_from_yaml(yaml_file: str) -> int:
    """Restore PYPE_* environment variables from pipeline runtime YAML.

    This function reads the __pipeline_environment__ section from the runtime
    YAML and restores all environment variables. The YAML is authoritative -
    all variables are restored regardless of current environment settings.

    This must be called BEFORE importing pype modules that depend on PYPE_MODULES
    (like queues, snippets, etc.) to ensure the correct modules are loaded.

    Args:
        yaml_file: Path to pipeline_runtime.yaml file

    Returns:
        Number of environment variables restored

    Raises:
        FileNotFoundError: If YAML file doesn't exist
        ValueError: If YAML file is invalid
    """
    if not os.path.isfile(yaml_file):
        raise FileNotFoundError(f"Runtime YAML not found: {yaml_file}")

    try:
        with open(yaml_file, "rt") as f:
            runtime_data = yaml.safe_load(f) or {}
    except Exception as e:
        raise ValueError(f"Failed to parse runtime YAML: {e}")

    environment = runtime_data.get("__pipeline_environment__", {})

    if not environment:
        print(
            "Warning: No environment variables found in YAML (__pipeline_environment__ section missing)",
            file=sys.stderr,
        )
        return 0

    # YAML is authoritative - always restore
    # These are PYPE_* vars that define the pipeline environment
    for key, value in environment.items():
        os.environ[key] = value
    return len(environment)


def extract_snippet_name(command: str) -> Optional[str]:
    """Extract snippet name from pype command string.

    Command format: pype --profile X snippets --log Y SNIPPET_NAME --args...

    The snippet name is the first non-flag argument AFTER --log argument and its value.

    Args:
        command: Full pype command

    Returns:
        Snippet name or None
    """
    try:
        parts = command.split()
        snippets_idx = parts.index("snippets")

        # Find --log and skip it plus its value
        log_idx = None
        for i in range(snippets_idx + 1, len(parts)):
            if parts[i] == "--log":
                log_idx = i
                break

        if log_idx is not None:
            # Skip --log and its value, then get next non-flag argument
            for i in range(log_idx + 2, len(parts)):
                if not parts[i].startswith("-"):
                    return parts[i]
        else:
            # No --log, find first non-flag after snippets
            for i in range(snippets_idx + 1, len(parts)):
                if not parts[i].startswith("-"):
                    return parts[i]
    except (ValueError, IndexError):
        pass

    return None


def get_snippet_description(command: str, snippet_modules: Any) -> str:
    """Get description for a snippet.

    Args:
        command: command: Full pype command
        snippet_modules: The modules in the snippets folder

    Returns:
        Description string or empty string
    """

    snippet_name = extract_snippet_name(command)
    snippet_module = snippet_modules[snippet_name]
    # Case 1: .md snippet with mod dictionary
    if hasattr(snippet_module, "mod") and isinstance(snippet_module.mod, dict):
        description = snippet_module.mod.get("description", "")
        return os.linesep.join([s for s in description.splitlines() if s.strip()])

    # Case 2: .py snippet with add_parser function
    if hasattr(snippet_module, "add_parser"):
        temp_parser = ArgumentParser()
        temp_subparsers = temp_parser.add_subparsers()
        snippet_module.mod.add_parser(temp_subparsers, snippet_name)

        # Help is stored in _choices_actions
        for choice_action in temp_subparsers._choices_actions:
            if choice_action.dest == snippet_name:
                description = choice_action.help or ""
                return description

    return ""


def get_job_status(runtime_file: str, run_id: str) -> Optional[str]:
    """Get status of a job from runtime YAML with file locking.

    Uses shared file lock to ensure we don't read while another process
    is writing, which could give us corrupted/partial data.

    Args:
        runtime_file: Path to pipeline_runtime.yaml
        run_id: Job run ID

    Returns:
        Status string ('pending', 'submitted', 'running', 'completed', 'failed')
        or None if job not found
    """
    runtime = _read_runtime_file_locked(runtime_file)
    if run_id in runtime:
        return runtime[run_id].get("status", JobStatus.PENDING.value)
    return None


def should_skip_job(runtime_file: str, run_id: str) -> Tuple[bool, str]:
    """Check if job should be skipped (already completed).

    Args:
        runtime_file: Path to pipeline_runtime.yaml
        run_id: Job run ID

    Returns:
        Tuple of (should_skip: bool, reason: str)
    """
    status = get_job_status(runtime_file, run_id)
    if status == JobStatus.COMPLETED.value:
        return True, "Already completed in previous run"
    return False, ""


def update_job_status(
    runtime_file: str, run_id: str, status: Optional[str], **kwargs
) -> None:
    """Update job status in runtime YAML with file locking.

    Uses fcntl file locking to ensure safe concurrent access from multiple
    processes (e.g., worker processes updating status simultaneously).

    This prevents:
    - Data corruption from concurrent writes
    - Lost updates when multiple processes write at same time
    - Reads of partial/corrupted YAML files

    Args:
        runtime_file: Path to pipeline_runtime.yaml
        run_id: Job run ID to update
        status: New status ('pending', 'submitted', 'running', 'completed', 'failed')
                If None, only kwargs are updated (status is not modified)
        **kwargs: Additional fields to update (queue_id, error_msg, resource_consumption, etc.)
    """
    # Ensure directory exists
    runtime_dir = os.path.dirname(runtime_file)
    if runtime_dir and not os.path.exists(runtime_dir):
        try:
            os.makedirs(runtime_dir, exist_ok=True)
        except OSError:
            pass  # May have been created by another process

    # Open with exclusive lock during read-modify-write
    lock_file = runtime_file + ".lock"

    lock_acquired = False
    try:
        with open(lock_file, "a") as lockf:
            # Try to acquire exclusive lock with retries
            lock_acquired = _try_acquire_lock(lockf, fcntl.LOCK_EX)

            if not lock_acquired:
                # Lock unavailable even after retries - use fallback without lock
                pass

            try:
                # Read current state
                if os.path.isfile(runtime_file):
                    with open(runtime_file, "rt") as f:
                        runtime = yaml.safe_load(f)
                else:
                    runtime = {}

                # Update job entry
                if not runtime:
                    runtime = {}

                if run_id not in runtime:
                    runtime[run_id] = {}

                # Only update status if provided (allows adding kwargs without changing status)
                if status is not None:
                    runtime[run_id]["status"] = status

                    # Add timestamps
                    if (
                        status == JobStatus.SUBMITTED.value
                        and "submitted_at" not in runtime[run_id]
                    ):
                        runtime[run_id]["submitted_at"] = datetime.now().isoformat()
                    if (
                        status == JobStatus.RUNNING.value
                        and "started_at" not in runtime[run_id]
                    ):
                        runtime[run_id]["started_at"] = datetime.now().isoformat()

                    if status in (JobStatus.COMPLETED.value, JobStatus.FAILED.value):
                        runtime[run_id]["completed_at"] = datetime.now().isoformat()

                # Update additional fields
                for key, value in kwargs.items():
                    runtime[run_id][key] = value

                # Write atomically: write to temp file, then rename
                temp_file = runtime_file + ".tmp"
                with open(temp_file, "wt") as f:
                    yaml.dump(runtime, f, default_flow_style=False)

                # Atomic rename (POSIX)
                os.replace(temp_file, runtime_file)

            finally:
                # Release lock if acquired
                if lock_acquired:
                    try:
                        fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
                    except (OSError, ValueError):
                        pass  # Lock already released
    except (OSError, IOError):
        # Lock file operations failed - try write without lock as fallback
        try:
            if os.path.isfile(runtime_file):
                with open(runtime_file, "rt") as f:
                    runtime = yaml.safe_load(f)
            else:
                runtime = {}

            if run_id not in runtime:
                runtime[run_id] = {}

            # Only update status if provided
            if status is not None:
                runtime[run_id]["status"] = status

            for key, value in kwargs.items():
                runtime[run_id][key] = value

            temp_file = runtime_file + ".tmp"
            with open(temp_file, "wt") as f:
                yaml.dump(runtime, f, default_flow_style=False)
            os.replace(temp_file, runtime_file)
        except Exception:
            # Best-effort - don't crash on lock failure
            pass


def add_resource_consumption(
    runtime_file: str, run_id: str, resource_data: Dict[str, Any]
) -> None:
    """Add resource consumption data to a job entry without changing status.

    This is a convenience wrapper around update_job_status that adds resource
    consumption data (from sjeff or similar) to a completed job. The job's
    status is not modified.

    Args:
        runtime_file: Path to pipeline_runtime.yaml
        run_id: Job run ID to update
        resource_data: Dict containing resource consumption data, typically:
            - mem_used_gb: Memory used in GB
            - cpu_used: CPU cores used
            - time_elapsed: Wall time elapsed (HH:MM:SS format)
            - mem_efficiency: Memory efficiency percentage
            - cpu_efficiency: CPU efficiency percentage
            - notes: Any additional notes from the resource query
    """
    update_job_status(
        runtime_file, run_id, status=None, resource_consumption=resource_data
    )


def get_ready_jobs(runtime_file: str) -> List[str]:
    """Get pending jobs whose dependencies are all completed.

    Uses file locking to ensure consistent reads during concurrent access.

    Args:
        runtime_file: Path to pipeline_runtime.yaml

    Returns:
        List of run_ids ready for submission
    """
    runtime = _read_runtime_file_locked(runtime_file)

    if not runtime:
        return []

    ready = []

    for run_id, job_data in runtime.items():
        job_status = job_data.get("status", JobStatus.PENDING.value)
        if job_status != JobStatus.PENDING.value:
            continue

        # Check all dependencies are completed
        deps = job_data.get("dependencies", [])
        all_deps_done = all(
            runtime.get(dep, {}).get("status") == JobStatus.COMPLETED.value
            for dep in deps
        )

        if all_deps_done:
            ready.append(run_id)

    return ready


def is_pipeline_complete(runtime_file: str) -> bool:
    """Check if all jobs in pipeline are completed.

    Uses file locking to ensure consistent reads during concurrent access.

    Args:
        runtime_file: Path to pipeline_runtime.yaml

    Returns:
        True if all jobs have status 'completed'
    """
    runtime = _read_runtime_file_locked(runtime_file)

    if not runtime:
        return False

    return all(
        job.get("status") == JobStatus.COMPLETED.value for job in runtime.values()
    )


def is_metadata_key(key: str) -> bool:
    """Check if a key in runtime data is metadata (not a job).

    Metadata entries start with '__' (e.g., '__pipeline_metadata__', '__pipeline_environment__').

    Args:
        key: Key from runtime dictionary

    Returns:
        True if key is metadata, False if it's a job entry
    """
    return key.startswith("__")


def read_pipeline_runtime(yaml_file: str) -> Dict[str, Any]:
    """Read pipeline runtime YAML file.

    Uses file locking to ensure consistent reads during concurrent access.

    Args:
        yaml_file: Path to pipeline_runtime.yaml

    Returns:
        Dictionary of runtime data (jobs and metadata)

    Raises:
        FileNotFoundError: If YAML file doesn't exist
        ValueError: If YAML file is invalid
    """
    if not os.path.isfile(yaml_file):
        raise FileNotFoundError(f"Runtime YAML not found: {yaml_file}")

    try:
        with open(yaml_file, "rt") as f:
            runtime_data = yaml.safe_load(f) or {}
    except Exception as e:
        raise ValueError(f"Failed to parse runtime YAML: {e}")

    return runtime_data


def get_job_entries(runtime_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get only job entries from runtime data, excluding metadata.

    Metadata entries are keys starting with '__' (e.g., '__pipeline_metadata__').

    Args:
        runtime_data: Complete runtime dictionary

    Returns:
        Dictionary containing only job entries (no metadata)
    """
    return {k: v for k, v in runtime_data.items() if not is_metadata_key(k)}


def load_queue_handler(
    queue_module: Any, queue_name: str, runtime_data: Dict[str, Any]
) -> Optional[Any]:
    """Load a queue command handler from a queue module.

    Retrieves the get_handler function from the queue module and uses it
    to instantiate a command handler for processing queue commands.

    Args:
        queue_module: The pype.pype_modules.queues module containing queue implementations
        queue_name: Name of the queue system (e.g., 'parallel', 'slurm')
        runtime_data: Pipeline runtime data to pass to handler initialization

    Returns:
        Queue command handler instance, or None if handler not found or fails to load

    Example:
        handler = load_queue_handler(PYPE_QUEUES, 'parallel', runtime_data)
        if handler:
            result = execute_command(handler, cmd, runtime_file)
    """
    try:
        # Get the get_handler function from the queue module
        get_handler_func = get_module_method(queue_module, queue_name, "get_handler")
        if get_handler_func is None:
            return None

        # Instantiate the handler with runtime data
        return get_handler_func(runtime_data)
    except Exception:
        return None


class SnippetRuntime:
    """Helper class for building queue module implementations.

    Handles:
    - Command preparation
    - Job tracking
    - Resource management
    - Dependencies
    - Queue status

    This provides a standard interface that queue implementations
    can build upon to handle system-specific details.
    """

    def __init__(self, command: str, log: Any, profile: str):
        """Initialize runtime for a snippet.

        Args:
            command: Snippet command to execute
            log: Logger instance
            profile: Profile name/path

        Example queue implementation:
            ```python
            class PBSQueue(SnippetRuntime):
                def submit(self):
                    # PBS-specific submission logic
                    qsub_cmd = f"qsub -N {self.name} {self.get_resource_args()}"
                    job_id = self.submit_queue(qsub_cmd)
                    self.add_queue_id(job_id)
            ```
        """
        pype_exec = shutil.which("pype")
        self.log = log
        if pype_exec is None:
            pype_exec = "%s -m pype.commands" % sys.executable
        self.command = "%s --profile %s snippets --log %s %s" % (
            pype_exec,
            profile,
            self.log.__path__,
            command,
        )
        self.run_id = generate_uid(10)[-10:]
        self.runtime_dir = os.path.dirname(self.log.__path__)
        self.runtime_file = os.path.join(self.runtime_dir, "pipeline_runtime.yaml")
        self.submit_attempts = 0
        self.sleep = 1

    def get_runtime(
        self, requirements: Dict[str, Any], dependencies: List[str]
    ) -> None:
        """Load or initialize the runtime configuration.

        Loads the existing runtime object from file if it exists, otherwise
        initializes a new runtime dictionary with the provided requirements
        and dependencies.

        Args:
            requirements: Dictionary specifying the snippet resource requirements.
            dependencies: List of job IDs this snippet depends on. The snippet
                will only run after these dependent jobs are terminated.
        """

        if os.path.isfile(self.runtime_file):
            with open(self.runtime_file, "rt") as pipeline_runtime:
                self.runtime = yaml.safe_load(pipeline_runtime) or {}
        else:
            self.runtime = {}

        # Check if this job already exists and is completed (resume scenario)
        if self.run_id in self.runtime:
            existing_status = self.runtime[self.run_id].get(
                "status", JobStatus.PENDING.value
            )
            if existing_status == JobStatus.COMPLETED.value:
                # Job already completed - don't reinitialize, keep existing entry
                return

        # Initialize or update job entry
        self.runtime[self.run_id] = {}
        self.runtime[self.run_id]["command"] = self.command
        self.runtime[self.run_id]["requirements"] = requirements
        self.runtime[self.run_id]["dependencies"] = dependencies
        self.runtime[self.run_id]["status"] = JobStatus.PENDING.value

    def add_queue_id(self, queue_id: str) -> None:
        """Register a queue system job ID for this snippet.

        Use this method when the queue command is not submitted using
        submit_queue(), to manually register the job ID in the runtime object.

        Args:
            queue_id: The job ID assigned by the queue system.
        """

        self.runtime[self.run_id]["queue_id"] = queue_id

    def add_queue_commands(self, commands: List[str]) -> None:
        """Register the queue submission commands for this job.

        The commands will be executed in a pipeline, where the output of each
        command becomes the stdin of the next command in the list.

        Args:
            commands: List of shell commands to execute in order.
        """

        self.runtime[self.run_id]["queue_commands"] = commands

    def add_snippet_description(self, command, snippet_modules):
        description = get_snippet_description(command, snippet_modules)
        self.runtime[self.run_id]["description"] = os.linesep.join(
            [s for s in description.splitlines() if s.strip()]
        )

    def submit_queue(self, retry: int = 1) -> None:
        """Execute the queue submission commands and register the job ID.

        Runs the queue commands and extracts the resulting job ID from the
        output. Supports automatic retry on failure.

        Args:
            retry: Number of retry attempts on failure (default: 1).

        Raises:
            CommandError: If all submission attempts fail.
        """

        submit_cmd = []
        pipe_nr = 1
        self.log.log.info(
            "Process queue command line %s"
            % " | ".join(self.runtime[self.run_id]["queue_commands"])
        )
        for command in self.runtime[self.run_id]["queue_commands"]:
            if pipe_nr <= 1:
                submit_cmd.append(
                    subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
                )
            else:
                submit_cmd.append(
                    subprocess.Popen(
                        shlex.split(command),
                        stdout=subprocess.PIPE,
                        stdin=submit_cmd[pipe_nr - 2].stdout,
                    )
                )
            pipe_nr += 1
        out = submit_cmd[pipe_nr - 2].communicate()[0]
        out = out.strip().decode("UTF-8")
        self.runtime[self.run_id]["queue_id"] = out
        sleep(self.sleep)
        self.submit_attempts += 1
        if not out and self.submit_attempts <= retry:
            self.log.log.info(
                f"New attempt to submit the job on the queue, retry: {retry + 1}"
            )
            self.submit_queue(retry)
        if not out:
            error_msg = "Command %s could not be submitted to the queue" % self.command
            self.log.log.error(error_msg)
            raise CommandError(error_msg, command=self.command)
        self.log.log.info("Command result with job ID: %s" % out)

    def queue_depends(self) -> List[str]:
        """Get the list of queue job IDs this job depends on.

        Converts the internal runtime dependency IDs to queue system job IDs
        for proper dependency specification in queue submission.

        Returns:
            List of queue system job IDs that this job depends on.
        """

        dependencies = []
        for dep in self.runtime[self.run_id]["dependencies"]:
            dependencies.append(self.runtime[dep]["queue_id"])
        return dependencies

    def commit_runtime(self) -> None:
        """Persist the runtime configuration to file.

        Saves the current runtime dictionary to pipeline_runtime.yaml in the
        parent directory of the snippet log.
        """

        if self.runtime_file:
            with open(self.runtime_file, "wt") as pipeline_runtime:
                yaml.dump(self.runtime, pipeline_runtime, default_flow_style=False)

    def change_sleep(self, sleep_sec: int) -> None:
        """Set the sleep duration after queue submission.

        Configures the number of seconds to wait after submitting a job to the
        queue system. This delay is used in submit_queue().

        Args:
            sleep_sec: Number of seconds to sleep after submission.
        """

        self.sleep = sleep_sec

    def should_skip(self) -> Tuple[bool, str]:
        """Check if this job should be skipped (already completed).

        Used for resume functionality - allows pipelines to skip jobs
        that completed successfully in a previous run.

        Returns:
            Tuple of (should_skip: bool, reason: str)

        Example:
            ```python
            runtime = SnippetRuntime(command, log, profile)
            runtime.get_runtime(requirements, dependencies)

            should_skip, reason = runtime.should_skip()
            if should_skip:
                log.log.info(f"Skipping: {reason}")
                return runtime.run_id

            # Continue with submission...
            ```
        """
        if self.run_id in self.runtime:
            status = self.runtime[self.run_id].get("status", JobStatus.PENDING.value)
            if status == JobStatus.COMPLETED.value:
                return True, "Already completed in previous run"
        return False, ""

    def mark_submitted(self, queue_id: str) -> None:
        """Mark job as submitted with queue ID and update status.

        This is a convenience method that combines add_queue_id() with
        status tracking.

        Args:
            queue_id: The job ID assigned by the queue system.
        """
        self.runtime[self.run_id]["queue_id"] = queue_id
        self.runtime[self.run_id]["status"] = JobStatus.SUBMITTED.value
        self.runtime[self.run_id]["submitted_at"] = datetime.now().isoformat()

    def mark_completed(self) -> None:
        """Mark job as completed with timestamp."""
        self.runtime[self.run_id]["status"] = JobStatus.COMPLETED.value
        self.runtime[self.run_id]["completed_at"] = datetime.now().isoformat()

    def mark_failed(self, error_msg: str) -> None:
        """Mark job as failed with error message and timestamp.

        Args:
            error_msg: Description of the error that caused failure.
        """
        self.runtime[self.run_id]["status"] = JobStatus.FAILED.value
        self.runtime[self.run_id]["error_msg"] = error_msg
        self.runtime[self.run_id]["completed_at"] = datetime.now().isoformat()


# ========== Resource Management Abstraction ==========
# Queue-specific resource constraints are managed by implementations


class ResourceManager:
    """Abstract base class for managing queue-specific resource constraints.

    Different queue systems have different resource models.

    Each queue module implements this interface to handle its specific
    resource constraints. TaskScheduler remains queue-agnostic by
    delegating to ResourceManager.

    Example implementations:
        LocalResourceManager: Track CPU/memory per running task
        SlurmQuotaManager: Monitor job count in squeue
        PBSQuotaManager: Monitor job count in qstat
    """

    def can_allocate(self, *args, **kwargs) -> bool:
        """Check if resources are available to allocate.

        Signature varies by queue system:
        - Local: can_allocate(cpus: int, mem: int) -> bool
        - SLURM quota: can_allocate(job_count: int) -> bool
        - PBS quota: can_allocate(job_count: int) -> bool

        Args:
            *args: Queue-specific allocation parameters
            **kwargs: Queue-specific options

        Returns:
            bool: True if resources are available, False otherwise
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement can_allocate()"
        )

    def allocate(self, *args, **kwargs) -> None:
        """Reserve resources for a task/job.

        Called when submitting a task. Queue system records the allocation.

        Args:
            *args: Queue-specific allocation parameters
            **kwargs: Queue-specific options
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement allocate()"
        )

    def release(self, *args, **kwargs) -> None:
        """Free up resources after task/job completes.

        Called when a task finishes successfully or fails.

        Args:
            *args: Task/job identifiers
            **kwargs: Queue-specific options
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement release()")

    def get_stats(self) -> Dict[str, Any]:
        """Return current resource utilization statistics.

        Used for logging and progress reporting.

        Returns:
            dict: Queue-specific statistics (e.g., CPU%, memory%, queue depth)
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_stats()"
        )


class TaskScheduler:
    """Generic task scheduler that works with any ResourceManager.

    Manages job scheduling based on:
    - Dependency satisfaction
    - Resource availability (via ResourceManager)
    - Overall pipeline progress

    This class is queue-agnostic. Resource enforcement is delegated
    to the ResourceManager implementation provided by each queue module.
    """

    def __init__(
        self,
        runtime_file: str,
        resource_manager: ResourceManager,
        log: Any = None,
    ):
        """Initialize task scheduler.

        Args:
            runtime_file: Path to pipeline_runtime.yaml
            resource_manager: Implementation handling queue-specific constraints
            log: Logger object for output
        """
        self.runtime_file = runtime_file
        self.resource_manager = resource_manager
        self.log = log
        self.runtime = {}
        self._load_runtime()

    def _load_runtime(self) -> None:
        """Load runtime configuration from YAML file."""
        if os.path.isfile(self.runtime_file):
            with open(self.runtime_file, "rt") as f:
                self.runtime = yaml.safe_load(f) or {}
        else:
            self.runtime = {}

    def _is_job_entry(self, key: str) -> bool:
        """Check if a runtime key is a job entry (not metadata).

        Metadata entries are keys starting with '__' (e.g., '__pipeline_metadata__').
        Regular job entries have status and command fields.

        Args:
            key: Runtime dictionary key

        Returns:
            True if this is a job entry, False if metadata
        """
        return not key.startswith("__")

    def get_pending_jobs(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Get all jobs that haven't been submitted yet.

        Returns:
            List of (run_id, job_data) tuples with status='pending'
        """
        pending = []
        for run_id, job_data in self.runtime.items():
            # Skip metadata entries (keys starting with __)
            if not self._is_job_entry(run_id):
                continue
            status = job_data.get("status", JobStatus.PENDING.value)
            if status == JobStatus.PENDING.value:
                pending.append((run_id, job_data))
        return pending

    def get_ready_jobs(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Get jobs ready to submit (dependencies satisfied, status='pending').

        A job is ready when:
        1. Status is 'pending' (not yet submitted)
        2. All dependencies are 'completed'

        Returns:
            List of (run_id, job_data) tuples ready for submission
        """
        ready = []

        for run_id, job_data in self.get_pending_jobs():
            dependencies = job_data.get("dependencies", [])

            # Check if all dependencies are completed
            all_deps_complete = True
            for dep_id in dependencies:
                if dep_id not in self.runtime:
                    # Dependency not found - error in pipeline
                    if self.log:
                        self.log.log.error(
                            f"Dependency {dep_id} not found in runtime for job {run_id}"
                        )
                    all_deps_complete = False
                    break

                dep_status = self.runtime[dep_id].get("status", JobStatus.PENDING.value)
                if dep_status != JobStatus.COMPLETED.value:
                    all_deps_complete = False
                    break

            if all_deps_complete:
                ready.append((run_id, job_data))

        return ready

    def get_submitted_jobs(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Get all jobs currently in queue or running.

        Returns:
            List of (run_id, job_data) with status in (submitted, running)
        """
        submitted = []
        for run_id, job_data in self.runtime.items():
            # Skip metadata entries (keys starting with __)
            if not self._is_job_entry(run_id):
                continue
            status = job_data.get("status", JobStatus.PENDING.value)
            if status in (JobStatus.SUBMITTED.value, JobStatus.RUNNING.value):
                submitted.append((run_id, job_data))
        return submitted

    def is_complete(self) -> bool:
        """Check if all jobs have completed.

        Returns:
            True if all jobs have status in (completed, failed, cancelled)
        """
        if not self.runtime:
            return True

        terminal_states = (
            JobStatus.COMPLETED.value,
            JobStatus.FAILED.value,
            JobStatus.CANCELLED.value,
        )

        for run_id, job_data in self.runtime.items():
            # Skip metadata entries (keys starting with __)
            if not self._is_job_entry(run_id):
                continue
            status = job_data.get("status", JobStatus.PENDING.value)
            if status not in terminal_states:
                return False

        return True

    def get_job_data(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific job.

        Args:
            run_id: Job run ID

        Returns:
            Job data dict or None if not found
        """
        return self.runtime.get(run_id)

    def reload(self) -> None:
        """Reload runtime from disk (for monitoring changes).

        Call this periodically in post_run() loops to pick up
        status changes from executed jobs.
        """
        self._load_runtime()

    def get_stats(self) -> Dict[str, Any]:
        """Get overall pipeline statistics.

        Returns:
            dict with counts of jobs by status
        """
        # Filter out metadata entries (keys starting with __)
        job_entries = {k: v for k, v in self.runtime.items() if self._is_job_entry(k)}

        stats = {
            "pending": 0,
            "submitted": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "total": len(job_entries),
        }

        for job_data in job_entries.values():
            status = job_data.get("status", JobStatus.PENDING.value)
            if status in stats:
                stats[status] += 1

        return stats

    def get_blocked_by_failed_deps(self) -> List[Tuple[str, Dict[str, Any], List[str]]]:
        """Get jobs blocked by failed or missing dependencies.

        A job is blocked if:
        1. Status is PENDING
        2. One or more dependencies have FAILED status or don't exist

        Returns:
            List of (run_id, job_data, failed_dep_ids) tuples
        """
        blocked = []

        for run_id, job_data in self.get_pending_jobs():
            dependencies = job_data.get("dependencies", [])
            failed_deps = []

            for dep_id in dependencies:
                if dep_id not in self.runtime:
                    # Missing dependency is also a blocker
                    failed_deps.append(dep_id)
                    continue

                dep_status = self.runtime[dep_id].get("status", JobStatus.PENDING.value)
                if dep_status == JobStatus.FAILED.value:
                    failed_deps.append(dep_id)

            if failed_deps:
                blocked.append((run_id, job_data, failed_deps))

        return blocked

    def get_blocked_by_resources(
        self, resource_manager: Any
    ) -> List[Tuple[str, Dict[str, Any], int, int]]:
        """Get jobs that require more resources than system maximum.

        These jobs can never run because they exceed system capacity.

        Args:
            resource_manager: LocalResourceManager instance with max_cpus and max_mem

        Returns:
            List of (run_id, job_data, required_cpu, required_mem) tuples
            Empty list if resource_manager doesn't have the required attributes
        """
        # Only check for LocalResourceManager with max limits
        if not hasattr(resource_manager, "max_cpus") or not hasattr(
            resource_manager, "max_mem"
        ):
            return []

        blocked = []

        for run_id, job_data in self.get_ready_jobs():
            requirements = job_data.get("requirements", {})

            try:
                cpus = int(requirements.get("ncpu", 1))
            except (ValueError, TypeError):
                cpus = 1

            try:
                # Try to parse memory requirement
                mem_str = requirements.get("mem", "1gb")
                if isinstance(mem_str, str):
                    from pype.misc import bases_format

                    mem = bases_format(mem_str, 1024)
                else:
                    mem = mem_str
            except (ValueError, TypeError):
                mem = 1024**3  # Default 1GB

            # Check if job exceeds system capacity
            if cpus > resource_manager.max_cpus or mem > resource_manager.max_mem:
                blocked.append((run_id, job_data, cpus, mem))

        return blocked

    def has_active_work(self) -> bool:
        """Check if pipeline has any active work (running or submitted jobs).

        Returns:
            True if there are jobs in SUBMITTED or RUNNING state
        """
        submitted_jobs = self.get_submitted_jobs()
        return len(submitted_jobs) > 0

    def get_job_entries(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Get all job entries, excluding metadata (keys starting with '__').

        Returns:
            List of (run_id, job_data) tuples for actual jobs only
        """
        return [(k, v) for k, v in self.runtime.items() if not k.startswith("__")]


# ========== Common Queue Operations ==========
# Shared utility functions used by all queue implementations


def check_for_blocked_jobs(
    scheduler: TaskScheduler,
    log: Any,
    resource_manager: Optional[ResourceManager] = None,
) -> Tuple[bool, Optional[str], Optional[List[str]]]:
    """Check if pipeline has jobs that cannot make progress.

    Uses candidate job detection:
    - Candidate jobs = ready jobs (can start now) + running jobs (executing)
    - If candidate jobs < pending jobs, some jobs are blocked

    Args:
        scheduler: TaskScheduler instance
        log: Logger object
        resource_manager: Optional ResourceManager to check for resource-blocked jobs
                         (required for local execution, optional for others)

    Returns:
        Tuple of (has_blocked_jobs, diagnostic_message, blocked_job_ids)
    """
    stats = scheduler.get_stats()
    pending_count = stats["pending"]

    if pending_count == 0:
        return False, None, None

    # Calculate candidate jobs (jobs that can run or are running)
    ready_jobs = scheduler.get_ready_jobs()
    submitted_jobs = scheduler.get_submitted_jobs()
    candidate_count = len(ready_jobs) + len(submitted_jobs)

    # If candidate < pending, some jobs are blocked
    if candidate_count >= pending_count:
        return False, None, None

    blocked_count = pending_count - candidate_count

    # Analyze why jobs are blocked
    blocked_by_deps = scheduler.get_blocked_by_failed_deps()
    blocked_by_resources = []
    if resource_manager:
        blocked_by_resources = scheduler.get_blocked_by_resources(resource_manager)

    reason_lines = [
        "=" * 80,
        "WARNING: BLOCKED JOBS DETECTED",
        "=" * 80,
        "Pipeline has jobs that cannot make progress",
        f"  Pending jobs: {pending_count}",
        f"  Candidate jobs (ready + running): {candidate_count}",
        f"  Blocked jobs: {blocked_count}",
    ]

    all_blocked_ids = []

    # Report jobs blocked by failed dependencies
    if blocked_by_deps:
        blocked_by_deps_ids = [run_id for run_id, _, _ in blocked_by_deps]
        all_blocked_ids.extend(blocked_by_deps_ids)

        reason_lines.append("")
        reason_lines.append("Jobs blocked by failed dependencies:")
        for run_id, job_data, failed_deps in blocked_by_deps[:10]:  # Show first 10
            job_name = job_data.get("name", run_id[:12])
            reason_lines.append(f"    - {job_name} (run_id: {run_id[:12]})")
            failed_dep_names = ", ".join([d[:12] for d in failed_deps])
            reason_lines.append(f"      Blocked by failed: {failed_dep_names}")

        if len(blocked_by_deps) > 10:
            reason_lines.append(f"    ... and {len(blocked_by_deps) - 10} more")

    # Report jobs blocked by impossible resources (if resource manager provided)
    if blocked_by_resources:
        blocked_by_resource_ids = [run_id for run_id, _, _, _ in blocked_by_resources]
        all_blocked_ids.extend(blocked_by_resource_ids)

        reason_lines.append("")
        reason_lines.append("Jobs blocked by insufficient system resources:")
        for run_id, job_data, req_cpu, req_mem in blocked_by_resources[
            :5
        ]:  # Show first 5
            job_name = job_data.get("name", run_id[:12])
            req_mem_gb = req_mem / (1024**3)
            max_mem_gb = resource_manager.max_mem / (1024**3)
            reason_lines.append(f"    - {job_name} (run_id: {run_id[:12]})")
            reason_lines.append(
                f"      Requires: {req_cpu} CPUs, {req_mem_gb:.2f} GB memory"
            )
            reason_lines.append(
                f"      System max: {resource_manager.max_cpus} CPUs, {max_mem_gb:.2f} GB memory"
            )

        if len(blocked_by_resources) > 5:
            reason_lines.append(f"    ... and {len(blocked_by_resources) - 5} more")

    reason_lines.append("=" * 80)

    reason = "\n".join(reason_lines)

    # De-duplicate blocked job IDs
    all_blocked_ids = list(set(all_blocked_ids))

    return True, reason, all_blocked_ids


def handle_graceful_shutdown(
    scheduler: TaskScheduler,
    runtime_file: str,
    log: Any,
    blocked_ids: Optional[List[str]] = None,
) -> None:
    """Handle graceful shutdown when pipeline is blocked.

    Marks blocked jobs as CANCELLED and logs shutdown message.

    Args:
        scheduler: TaskScheduler instance
        runtime_file: Path to pipeline_runtime.yaml
        log: Logger object
        blocked_ids: List of job IDs that are blocked (optional)
    """
    log.log.warning("=" * 80)
    log.log.warning("GRACEFUL SHUTDOWN - NO MORE JOBS CAN RUN")
    log.log.warning("=" * 80)

    # Mark blocked jobs as CANCELLED (if we have their IDs)
    if blocked_ids:
        log.log.info(f"Marking {len(blocked_ids)} blocked jobs as CANCELLED")
        for job_id in blocked_ids:
            update_job_status(
                runtime_file,
                job_id,
                JobStatus.CANCELLED.value,
                error_msg="Blocked by pipeline stall",
            )


def cascade_cancel_dependents(
    runtime_file: str,
    failed_job_id: str,
    log: Any,
) -> List[Tuple[str, str, str]]:
    """Find all jobs that depend on a failed job (transitively) for cancellation.

    Builds a reverse dependency graph and finds all jobs that transitively
    depend on the failed job. Returns information needed to cancel them.

    Args:
        runtime_file: Path to pipeline_runtime.yaml
        failed_job_id: ID of the job that failed
        log: Logger object

    Returns:
        List of tuples: (run_id, queue_id, job_name) for jobs to cancel
        Only includes jobs with queue_id (submitted/running jobs)
    """
    try:
        runtime_data = _read_runtime_file_locked(runtime_file)
    except Exception as e:
        log.log.error(f"Failed to read runtime file for cascade cancel: {e}")
        return []

    # Build reverse dependency graph: run_id -> list of run_ids that depend on it
    reverse_deps = {}
    for run_id, job_data in runtime_data.items():
        if is_metadata_key(run_id) or not isinstance(job_data, dict):
            continue

        dependencies = job_data.get("dependencies", [])
        for dep_id in dependencies:
            if dep_id not in reverse_deps:
                reverse_deps[dep_id] = []
            reverse_deps[dep_id].append(run_id)

    # Find all transitive dependents using BFS
    to_cancel = []
    visited = set()
    queue = [failed_job_id]

    while queue:
        current_id = queue.pop(0)
        if current_id in visited:
            continue
        visited.add(current_id)

        # Get all jobs that directly depend on current_id
        dependents = reverse_deps.get(current_id, [])
        for dep_run_id in dependents:
            if dep_run_id in visited:
                continue

            # Check if job is submitted or running (has queue_id)
            job_data = runtime_data.get(dep_run_id, {})
            status = job_data.get("status", "")
            queue_id = job_data.get("queue_id")
            job_name = job_data.get("name", dep_run_id[:12])

            if status in ("submitted", "running") and queue_id:
                to_cancel.append((dep_run_id, queue_id, job_name))
            elif status == "pending":
                # Pending jobs without queue_id - will be marked cancelled in YAML
                to_cancel.append((dep_run_id, None, job_name))

            # Continue traversing to find transitive dependents
            queue.append(dep_run_id)

    return to_cancel


def setup_api_watchers(
    runtime_file: str,
    log_path: str,
    log: Any,
    queue_handler: Any = None,
) -> Tuple[Any, Any, Any, bool]:
    """Initialize compute.bio API watchers with metadata management.

    Handles:
    - Reading existing run_id/worker_id from metadata (for resume)
    - Initializing API client and watchers
    - Saving run_id and worker_id to metadata on first registration
    - Passing queue handler to CommandWatcher for queue-specific operations

    Args:
        runtime_file: Path to pipeline_runtime.yaml
        log_path: Path to log directory
        log: Logger object
        queue_handler: Optional QueueCommandHandler for queue-specific operations

    Returns:
        Tuple of (api_client, progress_watcher, command_watcher, success)
    """
    from pype.utils.compute_bio_api import initialize_api_watcher

    # Check if there's an existing run_id and worker_id in metadata (for resume)
    existing_run_id = None
    existing_worker_id = None
    try:
        if os.path.isfile(runtime_file):
            with open(runtime_file, "r") as f:
                runtime_data = yaml.safe_load(f) or {}
                metadata = runtime_data.get("__pipeline_metadata__", {})
                existing_run_id = metadata.get("run_id")
                existing_worker_id = metadata.get("worker_id")
                if existing_run_id:
                    log.log.info(
                        f"Found existing run_id in metadata: {existing_run_id}"
                    )
                if existing_worker_id:
                    log.log.info(
                        f"Found existing worker_id in metadata: {existing_worker_id}"
                    )
    except Exception as e:
        log.log.debug(f"Could not read existing run_id/worker_id: {e}")

    api_client, progress_watcher, command_watcher, api_success = initialize_api_watcher(
        runtime_file,
        log,
        existing_run_id=existing_run_id,
        existing_worker_id=existing_worker_id,
        queue_handler=queue_handler,
    )
    if api_success:
        log.log.info("API watchers initialized and running")

        # Save run_id, run_hash, and worker_id to metadata if this is a new registration
        if api_client and api_client.pipeline_id and existing_run_id is None:
            try:
                # Update runtime YAML directly with run_id, run_hash, and worker_id
                with open(runtime_file, "r") as f:
                    runtime_data = yaml.safe_load(f) or {}

                if "__pipeline_metadata__" in runtime_data:
                    runtime_data["__pipeline_metadata__"]["run_id"] = (
                        api_client.pipeline_id
                    )
                    runtime_data["__pipeline_metadata__"]["run_hash"] = (
                        api_client.pipeline_hash
                    )
                    runtime_data["__pipeline_metadata__"]["worker_id"] = (
                        api_client.worker_id
                    )

                    with open(runtime_file, "w") as f:
                        yaml.dump(
                            runtime_data, f, default_flow_style=False, sort_keys=False
                        )

                    log.log.info(
                        f"Saved run_id {api_client.pipeline_id} and worker_id {api_client.worker_id} to metadata"
                    )
                else:
                    log.log.warning(
                        "No __pipeline_metadata__ section found in runtime YAML"
                    )
            except Exception as e:
                log.log.warning(f"Failed to save run_id/worker_id to metadata: {e}")
    else:
        log.log.info("API integration not configured or failed to initialize")

    return api_client, progress_watcher, command_watcher, api_success


def show_final_summary(
    scheduler: TaskScheduler,
    progress_display: "ProgressDisplay",
    log: Any,
    total_jobs: int,
) -> None:
    """Display final pipeline summary and job status table.

    Args:
        scheduler: TaskScheduler instance
        progress_display: ProgressDisplay instance
        log: Logger object
        total_jobs: Total number of jobs in pipeline
    """
    # Reload runtime to get final statuses
    scheduler.reload()

    # Show final job status table
    log.log.info("Final job statuses:")
    jobs = [(k, v) for k, v in scheduler.runtime.items() if not k.startswith("__")]
    stats = scheduler.get_stats()
    progress_display.show_pipeline_status(jobs, stats)

    # Show final summary
    final_stats = scheduler.get_stats()
    progress_display.show_summary(
        total_jobs=total_jobs,
        completed=final_stats["completed"],
        failed=final_stats["failed"],
        cancelled=final_stats.get("cancelled", 0),
    )

    # Report final pipeline status
    if final_stats["failed"] > 0 or final_stats.get("cancelled", 0) > 0:
        log.log.error(
            f"Pipeline completed with errors: "
            f"{final_stats['failed']} failed, {final_stats.get('cancelled', 0)} cancelled"
        )
