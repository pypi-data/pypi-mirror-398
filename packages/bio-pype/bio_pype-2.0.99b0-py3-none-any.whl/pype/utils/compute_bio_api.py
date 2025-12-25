"""
compute.bio API Integration Module

Handles communication between bio_pype and compute.bio API for progress tracking and job management.
"""

import json
import os
import socket
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

from pype.__config__ import COMPUTE_BIO_API_URL, COMPUTE_BIO_TOKEN
from pype.misc import responsive_sleep
from pype.utils.queue_commands import execute_command
from pype.utils.queues import get_job_entries, is_metadata_key, read_pipeline_runtime


def create_api_client(
    pipeline_name: str, queuelog: Any, timeout: int = 10
) -> Optional["ComputeBioAPIClient"]:
    """Create a ComputeBioAPIClient with configured credentials.

    Initializes API client with credentials from pype configuration.
    Returns None if API is not configured (missing token or URL).

    Args:
        pipeline_name: Display name for the pipeline in compute.bio UI
        queuelog: Logger object for API operations
        timeout: Request timeout in seconds (default: 10)

    Returns:
        Configured ComputeBioAPIClient instance, or None if not configured

    Example:
        api_client = create_api_client("my-pipeline", logger)
        if api_client:
            success = api_client.send_progress(runtime_file)
    """
    if not COMPUTE_BIO_TOKEN or not COMPUTE_BIO_API_URL:
        queuelog.log.debug("compute.bio API not configured (missing token or URL)")
        return None

    try:
        return ComputeBioAPIClient(
            api_url=COMPUTE_BIO_API_URL,
            token=COMPUTE_BIO_TOKEN,
            queuelog=queuelog,
            pipeline_name=pipeline_name,
            timeout=timeout,
        )
    except Exception as e:
        queuelog.log.error(f"Failed to initialize API client: {e}")
        return None


def initialize_api_watcher(
    runtime_file: Path,
    queuelog,
    existing_run_id: Optional[int] = None,
    existing_worker_id: Optional[str] = None,
    queue_handler: Optional[Any] = None,
):
    """
    Initialize and start compute.bio API watchers for pipeline monitoring.

    This function:
    1. Reads pipeline_runtime.yaml to get pipeline metadata
    2. Initializes ComputeBioAPIClient with token from config
    3. Registers worker with compute.bio API (or reuses existing run_id and worker_id)
    4. Starts background ProgressWatcher and CommandWatcher threads

    Returns tuple: (api_client, progress_watcher, command_watcher, success)

    If API is not configured (token/url missing), returns (None, None, None, False)
    with a warning log.

    Args:
        runtime_file: Path to pipeline_runtime.yaml file
        queuelog: Logger object for recording API operations
        existing_run_id: Optional existing run ID from previous execution (for resume)
        existing_worker_id: Optional existing worker ID from previous execution (for resume)
        queue_handler: Optional QueueCommandHandler for queue-specific operations

    Returns:
        Tuple of (api_client, progress_watcher, command_watcher, success)
        - api_client: ComputeBioAPIClient instance (None if not configured)
        - progress_watcher: ProgressWatcher thread (None if not configured)
        - command_watcher: CommandWatcher thread (None if not configured)
        - success: Boolean indicating successful initialization
    """

    # Check if API is configured
    if not COMPUTE_BIO_API_URL or not COMPUTE_BIO_TOKEN:
        queuelog.log.warning(
            "compute.bio API not configured (COMPUTE_BIO_API_URL or COMPUTE_BIO_TOKEN missing). "
            "Pipeline progress will not be sent to compute.bio API. "
            "Set environment variables or add to ~/.bio_pype/config to enable."
        )
        return None, None, None, False

    try:
        runtime_file = Path(runtime_file)

        # Read pipeline metadata from runtime YAML if available
        run_name = ""
        pipeline_name = ""
        pipeline_description = ""
        existing_run_hash = None
        try:
            runtime_data = read_pipeline_runtime(str(runtime_file))
            if "__pipeline_metadata__" in runtime_data:
                metadata = runtime_data["__pipeline_metadata__"]
                run_name = metadata.get("run_name", "")
                pipeline_name = metadata.get("pipeline_name", "")
                pipeline_description = metadata.get("pipeline_description", "")
                existing_run_hash = metadata.get("run_hash")
                # Use run_name if provided, otherwise fallback to pipeline template name
                display_name = run_name if run_name else pipeline_name
                queuelog.log.info(f"Read pipeline metadata: {display_name}")
                if pipeline_description:
                    queuelog.log.info(
                        f"Pipeline description: {pipeline_description}"
                    )
        except Exception as e:
            queuelog.log.debug(f"Could not read pipeline metadata: {e}")

        # Initialize API client with run name (or pipeline name as fallback)
        # This ensures the UI shows meaningful names instead of numeric IDs
        display_name = run_name if run_name else pipeline_name
        api_client = create_api_client(display_name, queuelog)
        if not api_client:
            queuelog.log.warning("compute.bio API not configured, skipping initialization")
            return None, None, None, False

        # If resuming with existing run_id and worker_id, skip registration
        if existing_run_id is not None and existing_worker_id is not None:
            queuelog.log.info(
                f"Resuming with existing run ID: {existing_run_id} and worker ID: {existing_worker_id}"
            )
            api_client.pipeline_id = existing_run_id
            api_client.worker_id = existing_worker_id
            if existing_run_hash:
                api_client.pipeline_hash = existing_run_hash
                queuelog.log.info(f"Restored pipeline hash: {existing_run_hash}")
        else:
            queuelog.log.info(
                f"Registering worker with compute.bio API ({COMPUTE_BIO_API_URL})"
            )

            # Register worker with API (and collect worker context info)
            if not api_client.register_worker(runtime_file=runtime_file):
                queuelog.log.warning("Failed to register worker with compute.bio API")
                return None, None, None, False

        queuelog.log.info(
            f"Worker registered: {api_client.worker_id} "
            f"(Pipeline ID: {api_client.pipeline_id})"
        )

        # Start progress watcher (sends updates every 30s)
        progress_interval = int(os.environ.get("PYPE_API_PROGRESS_INTERVAL", "30"))
        progress_watcher = ProgressWatcher(
            api_client=api_client,
            runtime_file=runtime_file,
            queuelog=queuelog,
            update_interval=progress_interval,
        )
        progress_watcher.start()

        queuelog.log.info(
            f"Started progress watcher (updates every {progress_interval}s)"
        )

        # Start command watcher (polls every 60s)
        command_interval = int(os.environ.get("PYPE_API_COMMAND_INTERVAL", "60"))
        command_watcher = CommandWatcher(
            api_client=api_client,
            queuelog=queuelog,
            poll_interval=command_interval,
            runtime_file=runtime_file,
            queue_handler=queue_handler,
        )
        command_watcher.start()

        queuelog.log.info(f"Started command watcher (polls every {command_interval}s)")

        return api_client, progress_watcher, command_watcher, True

    except Exception as e:
        queuelog.log.error(f"Failed to initialize compute.bio API watcher: {e}")
        return None, None, None, False


def stop_api_watchers(progress_watcher, command_watcher, queuelog):
    """
    Stop compute.bio API watchers cleanly.

    Args:
        progress_watcher: ProgressWatcher instance (can be None)
        command_watcher: CommandWatcher instance (can be None)
        queuelog: Logger object for recording shutdown
    """
    try:
        if progress_watcher is not None:
            progress_watcher.stop()
            queuelog.log.info("Stopped progress watcher")

        if command_watcher is not None:
            command_watcher.stop()
            queuelog.log.info("Stopped command watcher")
    except Exception as e:
        queuelog.log.error(f"Error stopping watchers: {e}")


class ComputeBioAPIClient:
    """
    Client for communicating with compute.bio API.

    Handles:
    - Worker registration
    - Progress updates (pipeline_runtime.yaml)
    - Command polling (cancel, pause, retry)
    """

    def __init__(
        self,
        api_url: str,
        token: str,
        queuelog,
        pipeline_name: str = "",
        hpc_system: str = "slurm",
        timeout: int = 10,
    ):
        """
        Initialize API client.

        Args:
            api_url: Base URL of compute.bio API (e.g., "http://localhost:8000/api")
            token: API token from compute.bio (from APIToken model)
            queuelog: Logger object for recording API operations
            pipeline_name: Optional name for this pipeline run
            hpc_system: HPC system type ('slurm', 'pbs', 'lsf', 'local')
            timeout: Request timeout in seconds
        """
        # Ensure URL has proper scheme
        if not api_url.startswith(("http://", "https://")):
            api_url = f"http://{api_url}"

        self.api_url = api_url.rstrip("/")
        self.token = token
        self.queuelog = queuelog
        self.pipeline_name = pipeline_name
        self.hpc_system = hpc_system
        self.timeout = timeout

        # Assigned by API on registration
        self.worker_id: Optional[str] = None
        self.pipeline_id: Optional[int] = None
        self.pipeline_hash: Optional[str] = None

        # Try to get worker_id from hostname or generate random
        self.worker_id = self._generate_worker_id()

        self.queuelog.log.info(f"ComputeBioAPI client initialized for {self.api_url}")

    def _generate_worker_id(self) -> str:
        """Generate unique worker ID per run.

        Uses hostname + unique suffix to allow multiple pipelines from same host.
        Format: hostname-xxxxxxxx (8-char hex suffix)
        """
        try:
            hostname = socket.gethostname()
            # Add unique suffix per run to avoid conflicts when multiple pipelines run from same host
            unique_suffix = uuid.uuid4().hex[:8]
            return f"{hostname}-{unique_suffix}"
        except Exception:
            return f"worker-{uuid.uuid4().hex[:8]}"

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        full_response: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to compute.bio API.

        Args:
            method: HTTP method ('GET', 'POST', etc.)
            endpoint: API endpoint (e.g., 'workers/register/')
            data: JSON data to send
            full_response: Return full response dict (for debugging)

        Returns:
            Parsed JSON response or None on error
        """
        url = f"{self.api_url}/{endpoint}"
        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
        }

        try:
            if data:
                data = json.dumps(data).encode("utf-8")

            request = Request(url, data=data, headers=headers, method=method)

            with urlopen(request, timeout=self.timeout) as response:
                response_data = json.loads(response.read().decode("utf-8"))

                if full_response:
                    return {"status": response.status, "data": response_data}
                return response_data

        except HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            self.queuelog.log.error(f"HTTP {e.code} from {url}: {error_body}")
            return None
        except URLError as e:
            self.queuelog.log.error(f"Request error to {url}: {e.reason}")
            return None
        except Exception as e:
            self.queuelog.log.error(f"Unexpected error in API request: {e}")
            return None

    def register_worker(self, runtime_file: Optional[Path] = None) -> bool:
        """
        Register this worker with compute.bio API.

        Args:
            runtime_file: Path to pipeline_runtime.yaml (for collecting worker context)

        Returns:
            True if successful, False otherwise
        """
        self.queuelog.log.info(f"Registering worker {self.worker_id}...")

        # Collect worker context information
        worker_context = self._collect_worker_context(runtime_file)

        # Collect pipeline metadata and environment from runtime YAML sections
        pipeline_metadata = {}
        pipeline_environment = {}
        if runtime_file:
            try:
                runtime_data = read_pipeline_runtime(str(runtime_file))
                if "__pipeline_metadata__" in runtime_data:
                    pipeline_metadata = runtime_data["__pipeline_metadata__"]
                    self.queuelog.log.info(
                        f"Collected pipeline metadata with keys: {list(pipeline_metadata.keys())}"
                    )
                if "__pipeline_environment__" in runtime_data:
                    pipeline_environment = runtime_data["__pipeline_environment__"]
                    self.queuelog.log.info(
                        f"Collected pipeline environment with keys: {list(pipeline_environment.keys())}"
                    )
            except Exception as e:
                self.queuelog.log.debug(
                    f"Could not read pipeline metadata/environment: {e}"
                )

        payload = {
            "worker_id": self.worker_id,
            "hpc_system": self.hpc_system,
            "pipeline_name": self.pipeline_name,
            "pipeline_metadata": pipeline_metadata,
            "pipeline_environment": pipeline_environment,
            **worker_context,  # Include hostname, username, yaml_path, work_directory
        }

        response = self._make_request("POST", "workers/register/", payload)

        if response:
            self.pipeline_id = response.get("pipeline_id")
            self.pipeline_hash = response.get("pipeline_hash")
            self.queuelog.log.info(
                f"Worker registered successfully. "
                f"Pipeline ID: {self.pipeline_id}, Hash: {self.pipeline_hash}"
            )
            return True

        self.queuelog.log.error("Failed to register worker with compute.bio")
        return False

    def _collect_worker_context(
        self, runtime_file: Optional[Path] = None
    ) -> Dict[str, str]:
        """
        Collect worker environment context for pipeline resubmission support.

        Args:
            runtime_file: Path to pipeline_runtime.yaml

        Returns:
            Dict with worker_hostname, worker_username, yaml_path, work_directory
        """
        context = {}

        # Get hostname
        try:
            context["worker_hostname"] = socket.gethostname()
        except Exception as e:
            self.queuelog.log.warning(f"Failed to get hostname: {e}")

        # Get current user
        try:
            context["worker_username"] = os.getenv("USER") or os.getenv(
                "USERNAME", "unknown"
            )
        except Exception as e:
            self.queuelog.log.warning(f"Failed to get username: {e}")

        # Get YAML file path
        if runtime_file:
            try:
                context["yaml_path"] = str(Path(runtime_file).resolve())
            except Exception as e:
                self.queuelog.log.warning(f"Failed to get YAML path: {e}")

        # Get work directory
        try:
            context["work_directory"] = os.getcwd()
        except Exception as e:
            self.queuelog.log.warning(f"Failed to get work directory: {e}")

        return context

    def send_progress(self, runtime_file: Path) -> bool:
        """
        Send pipeline progress to compute.bio API.

        Args:
            runtime_file: Path to pipeline_runtime.yaml file

        Returns:
            True if successful, False otherwise
        """
        if not self.pipeline_id:
            self.queuelog.log.warning(
                "Pipeline not registered yet, skipping progress update"
            )
            return False

        try:
            runtime_data = read_pipeline_runtime(runtime_file)
        except Exception as e:
            self.queuelog.log.error(f"Failed to read pipeline_runtime.yaml: {e}")
            return False

        payload = {
            "runtime_data": runtime_data,
            "worker_id": self.worker_id,
        }

        endpoint = f"pipelines/{self.pipeline_id}/progress/"
        response = self._make_request("POST", endpoint, payload)

        if response:
            progress = response.get("progress_percent", "unknown")
            completed = response.get("tasks_completed", "?")
            total = response.get("tasks_total", "?")
            self.queuelog.log.debug(f"Progress sent: {completed}/{total} ({progress}%)")
            return True

        self.queuelog.log.warning("Failed to send progress update")
        return False

    def poll_commands(self) -> list:
        """
        Poll compute.bio API for pending commands.

        Returns:
            List of pending commands, empty list if none or error
        """
        if not self.worker_id:
            return []

        endpoint = f"workers/{self.worker_id}/commands/"
        response = self._make_request("GET", endpoint)

        if response:
            commands = response.get("commands", [])
            if commands:
                self.queuelog.log.info(f"Retrieved {len(commands)} command(s)")
            return commands

        return []

    def acknowledge_command(self, command_id: int) -> bool:
        """
        Acknowledge receipt of a command.

        Args:
            command_id: ID of the command to acknowledge

        Returns:
            True if successful
        """
        endpoint = f"workers/{self.worker_id}/commands/{command_id}/ack/"
        response = self._make_request("POST", endpoint)
        return response is not None

    def complete_command(
        self,
        command_id: int,
        success: bool = True,
        message: str = "",
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Report command completion.

        Args:
            command_id: ID of the command
            success: Whether the command was successful
            message: Optional completion message

        Returns:
            True if successful
        """
        payload = {
            "success": success,
            "message": message,
        }
        if result:
            payload["result"] = result

        endpoint = f"workers/{self.worker_id}/commands/{command_id}/complete/"
        response = self._make_request("POST", endpoint, payload)
        return response is not None


class ProgressWatcher(threading.Thread):
    """
    Background thread that periodically sends progress to compute.bio API.
    Only sends when pipeline state actually changes (optimization).
    """

    def __init__(
        self,
        api_client: ComputeBioAPIClient,
        runtime_file: Path,
        queuelog,
        update_interval: int = 30,
    ):
        """
        Initialize progress watcher.

        Args:
            api_client: ComputeBioAPIClient instance
            runtime_file: Path to pipeline_runtime.yaml
            queuelog: Logger object for recording progress updates
            update_interval: Seconds between progress checks
        """
        super().__init__(daemon=True)
        self.api_client = api_client
        self.runtime_file = Path(runtime_file)
        self.queuelog = queuelog
        self.update_interval = update_interval
        self._stop_event = threading.Event()
        self.last_runtime_data = None  # Track previous state for change detection

        self.queuelog.log.info(
            f"Progress watcher initialized. Will check every {update_interval} seconds (only send on state changes)"
        )

    def _has_state_changed(self, current_data):
        """Check if runtime state changed since last report."""
        if self.last_runtime_data is None:
            return True  # First report, always send

        # Compare task statuses (ignore timestamps and other changing fields)
        # Extract only task entries (skip metadata starting with __)
        def extract_task_states(data):
            return {
                k: v.get("status")
                for k, v in data.items()
                if not is_metadata_key(k) and isinstance(v, dict) and "status" in v
            }

        current_states = extract_task_states(current_data)
        last_states = extract_task_states(self.last_runtime_data)

        return current_states != last_states

    def run(self):
        """Main watcher loop - only sends progress when state changes."""
        while not self._stop_event.is_set():
            try:
                if self.runtime_file.exists():
                    # Read current runtime data
                    current_data = read_pipeline_runtime(str(self.runtime_file))

                    # Only send if state changed
                    if self._has_state_changed(current_data):
                        self.api_client.send_progress(self.runtime_file)
                        self.last_runtime_data = current_data
                        self.queuelog.log.debug("Progress sent (state changed)")
                    else:
                        self.queuelog.log.debug("Progress skipped (no state change)")

                # Sleep in small increments so we can stop quickly
                responsive_sleep(self._stop_event, self.update_interval)

            except Exception as e:
                self.queuelog.log.error(f"Error in progress watcher: {e}")
                time.sleep(5)  # Back off on error

    def stop(self):
        """Stop the watcher thread."""
        self._stop_event.set()
        self.queuelog.log.info("Progress watcher stopped")


class CommandWatcher(threading.Thread):
    """
    Background thread that periodically polls for commands from compute.bio.

    Supports both generic commands (log retrieval) and queue-specific commands
    (job cancellation, status checking, resource queries) via pluggable handler.
    """

    def __init__(
        self,
        api_client: ComputeBioAPIClient,
        queuelog,
        poll_interval: int = 60,
        runtime_file: Optional[Path] = None,
        queue_handler: Optional[Any] = None,
    ):
        """
        Initialize command watcher.

        Args:
            api_client: ComputeBioAPIClient instance
            queuelog: Logger object for recording command polling
            poll_interval: Seconds between polls
            runtime_file: Path to pipeline_runtime.yaml (for processing log commands)
            queue_handler: Optional QueueCommandHandler for queue-specific operations
                          (cancel_job, get_job_status, query_resources)
        """
        super().__init__(daemon=True)
        self.api_client = api_client
        self.queuelog = queuelog
        self.poll_interval = poll_interval
        self.runtime_file = Path(runtime_file) if runtime_file else None
        self.queue_handler = queue_handler
        self._stop_event = threading.Event()
        self.pending_commands: list = []

        handler_info = ""
        if queue_handler:
            handler_info = f" (with {queue_handler.__class__.__name__} for queue-specific commands)"

        self.queuelog.log.info(
            f"Command watcher initialized. Will poll every {poll_interval} seconds{handler_info}"
        )

    def run(self):
        """Main command polling loop."""
        while not self._stop_event.is_set():
            try:
                commands = self.api_client.poll_commands()
                self.pending_commands = commands

                # Process commands
                for cmd in commands:
                    try:
                        cmd_type = cmd.get("type") or cmd.get("command_type", "unknown")
                        cmd_id = cmd.get("id")

                        # Acknowledge command
                        self.api_client.acknowledge_command(cmd_id)

                        # Execute command through shared function
                        if self.queue_handler:
                            result = execute_command(
                                self.queue_handler, cmd, self.runtime_file
                            )
                            self.api_client.complete_command(
                                cmd_id,
                                success=result.get("success", False),
                                result=result,
                            )
                        else:
                            # No handler available
                            self.api_client.complete_command(
                                cmd_id,
                                success=False,
                                message="Queue handler not available",
                            )

                    except Exception as e:
                        self.queuelog.log.error(
                            f"Error processing command {cmd.get('id')}: {e}"
                        )

                # Sleep in small increments
                responsive_sleep(self._stop_event, self.poll_interval)

            except Exception as e:
                self.queuelog.log.error(f"Error in command watcher: {e}")
                time.sleep(5)

    def stop(self):
        """Stop the command watcher thread."""
        self._stop_event.set()
        self.queuelog.log.info("Command watcher stopped")

    def get_pending_commands(self) -> list:
        """Get list of pending commands."""
        return self.pending_commands.copy()
