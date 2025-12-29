"""Pipeline Resume Module

Manages resumption of existing pipeline runs from runtime YAML files.

This module provides functionality to resume previously-started pipelines,
including:
- Automatic environment restoration from pipeline metadata
- Status reporting
- Selective job re-execution
- Queue system override

Example:
    pype resume logs/251112224941.984109_GUB5_test_simple_chain/pipeline_runtime.yaml
    pype resume --status pipeline_runtime.yaml
    pype resume --queue slurm --force-errors pipeline_runtime.yaml
"""

import os
import sys
from typing import Any, Optional

import yaml

from pype.argparse import ArgumentParser, _SubParsersAction
from pype.exceptions import PypeError
from pype.logger import PypeLogger
from pype.misc import create_minimal_profile, get_module_method
from pype.modules import create_module_parser
from pype.utils.queues import (
    _restore_environment_from_yaml,
    get_job_entries,
    is_metadata_key,
    load_queue_handler,
    read_pipeline_runtime,
)


def _print_pipeline_status(runtime_yaml: str) -> None:
    """Print pipeline status summary and exit.

    Args:
        runtime_yaml: Path to pipeline_runtime.yaml file
    """
    try:
        runtime_data = read_pipeline_runtime(runtime_yaml)
        metadata = runtime_data.get("__pipeline_metadata__", {})

        # Count jobs by status (exclude metadata entries)
        jobs = get_job_entries(runtime_data)

        if not jobs:
            print("No jobs found in pipeline")
            return

        status_counts = {}
        for job_id, job_data in jobs.items():
            status = job_data.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Print summary
        print("=" * 80)
        print("Pipeline Status Summary")
        print("=" * 80)

        if metadata:
            print(f"Run Name: {metadata.get('run_name', 'Unknown')}")
            print(f"Pipeline: {metadata.get('pipeline_name', 'Unknown')}")
            print(f"Submitted: {metadata.get('submission_time', 'Unknown')}")
            print(f"Queue: {metadata.get('queue_system', 'Unknown')}")
            if metadata.get("run_id"):
                print(f"Run ID: {metadata.get('run_id')}")
            print(f"Log: {metadata.get('log_directory', 'Unknown')}")
            print("-" * 80)

        total = len(jobs)
        print(f"Total jobs: {total}")
        print()

        for status in ["completed", "running", "pending", "failed", "submitted"]:
            count = status_counts.get(status, 0)
            if count > 0:
                pct = 100.0 * count / total
                print(f"  {status.capitalize():12s}: {count:4d} ({pct:5.1f}%)")

        # Show any other statuses
        for status, count in status_counts.items():
            if status not in ["completed", "running", "pending", "failed", "submitted"]:
                pct = 100.0 * count / total
                print(f"  {status.capitalize():12s}: {count:4d} ({pct:5.1f}%)")

        print("=" * 80)

    except Exception as e:
        print(f"Error reading pipeline status: {e}", file=sys.stderr)
        sys.exit(1)


def _execute_resume(
    runtime_yaml: str,
    queue: Optional[str],
    force_errors: bool = False,
    force_all: bool = False,
) -> bool:
    """Execute pipeline resume.

    Args:
        runtime_yaml: Path to pipeline_runtime.yaml file
        queue: Queue system to use (or None to use original from metadata)
        force_errors: Re-run failed jobs
        force_all: Re-run all jobs regardless of status

    Returns:
        True if resume completed successfully, False otherwise

    Raises:
        FileNotFoundError: If runtime YAML doesn't exist
        ValueError: If runtime YAML is invalid
    """
    # Reload PYPE_QUEUES after environment restoration
    # (environment was restored in resume_args before calling this function)
    # This import statement need to occur after the enviroment restoration,
    # otherwise pype.__config__ will be initialised arbitrarily with the
    # current working envoironment

    from pype.__config__ import reload_pype_queues

    PYPE_QUEUES = reload_pype_queues()

    try:
        # Validate runtime YAML exists
        # Read runtime YAML to extract metadata
        runtime_data = read_pipeline_runtime(runtime_yaml)

        metadata = runtime_data.get("__pipeline_metadata__", {})
        environment = runtime_data.get("__pipeline_environment__", {})

        # Determine queue (user override or original)
        if not queue:
            queue = metadata.get("queue_system")
            if not queue:
                raise ValueError(
                    "Queue system not found in metadata and not specified with --queue"
                )

        # Get log directory name (used as logger name)
        log_name = os.path.basename(os.path.dirname(runtime_yaml))
        log_dir = os.path.dirname(os.path.dirname(runtime_yaml))

        # Create minimal profile for PypeLogger
        profile = create_minimal_profile("resume")

        # Create PypeLogger pointing to existing log directory
        log = PypeLogger(log_name, log_dir, profile)
        log.log.info("=" * 80)
        log.log.info("Pipeline Resume")
        log.log.info("=" * 80)
        log.log.info(f"Resuming from: {runtime_yaml}")
        log.log.info(f"Using queue: {queue}")
        if environment:
            log.log.info(f"Environment variables restored: {len(environment)}")
        if force_errors:
            log.log.info("Force mode: Re-running failed jobs")
        if force_all:
            log.log.info("Force mode: Re-running all jobs")

        # Try to get queue handler for job cancellation from the queue module (optional)
        # Pass runtime_data so handler uses original pipeline configuration
        queue_handler = load_queue_handler(PYPE_QUEUES, queue, runtime_data)
        if queue_handler:
            log.log.info(
                f"Queue handler loaded: {queue_handler.__class__.__name__}"
            )

        # Cancel running/submitted jobs to prevent duplicates (if handler available)
        if queue_handler:
            log.log.info("Cancelling any running/submitted jobs before resuming...")
            _cancel_running_jobs(runtime_yaml, queue_handler, log)
            # Automatically reset cancelled jobs to pending so they can be re-queued
            log.log.info("Resetting cancelled jobs to pending for re-execution...")
        else:
            log.log.warning(
                "No queue handler available - skipping job cancellation. "
                "Resume may create duplicate jobs if some are still running in the queue system."
            )
        # Handle additional force modes if requested (modify job statuses before resume)

        _apply_force_mode(runtime_yaml, force_errors, force_all, log)

        # Execute post_run to process remaining jobs
        log.log.info(f"Execute post run processes of queue {queue}")
        log.log.info(f"queue {PYPE_QUEUES}")

        post_run = get_module_method(PYPE_QUEUES, queue, "post_run")
        if post_run is not None:
            post_run(log)
            log.log.info("Pipeline resume completed")
            return True
        else:
            log.log.error(f"Queue module {queue} does not have post_run method")
            return False

    except Exception as e:
        print(f"Error resuming pipeline: {e}", file=sys.stderr)
        return False


def _cancel_running_jobs(runtime_yaml: str, queue_handler: Any, log: Any) -> None:
    """Cancel all running or submitted jobs before resuming.

    This prevents duplicate job execution when resuming after a crash.
    Only cancels if queue_handler is available.

    Args:
        runtime_yaml: Path to pipeline_runtime.yaml
        queue_handler: QueueCommandHandler instance (or None to skip)
        log: Logger instance
    """
    if not queue_handler:
        log.log.debug("No queue handler available - skipping job cancellation")
        return

    try:
        runtime_data = read_pipeline_runtime(runtime_yaml)
        cancelled_count = 0
        for job_id, job_data in runtime_data.items():
            if is_metadata_key(job_id):  # Skip metadata
                continue

            status = job_data.get("status")
            queue_id = job_data.get("queue_id")

            # Cancel jobs that are running, submitted, or pending (queued)
            if status in ("running", "submitted", "pending") and queue_id:
                try:
                    result = queue_handler.cancel({"queue_id": queue_id})
                    if result.get("success"):
                        log.log.info(f"Cancelled job {job_id} (queue_id: {queue_id})")
                        # Update status to 'cancelled' so it can be resumed with --force-errors
                        job_data["status"] = "cancelled"
                        cancelled_count += 1
                    else:
                        log.log.warning(
                            f"Failed to cancel job {job_id} (queue_id: {queue_id})"
                        )
                except Exception as e:
                    log.log.debug(f"Error cancelling job {job_id}: {e}")

        # Write back updated statuses if any jobs were cancelled
        if cancelled_count > 0:
            with open(runtime_yaml, "wt") as f:
                yaml.dump(runtime_data, f, default_flow_style=False, sort_keys=False)
            log.log.info(
                f"Successfully cancelled {cancelled_count} job(s) and marked as 'cancelled'"
            )

    except Exception as e:
        log.log.error(f"Error cancelling running jobs: {e}")


def _apply_force_mode(
    runtime_yaml: str, force_errors: bool, force_all: bool, log: Any
) -> None:
    """Apply force mode by resetting job statuses.

    Args:
        runtime_yaml: Path to pipeline_runtime.yaml
        force_errors: Reset failed and cancelled jobs to pending
        force_all: Reset all jobs to pending
        log: Logger instance
    """
    try:
        runtime_data = read_pipeline_runtime(runtime_yaml)
        modified = 0
        for job_id, job_data in runtime_data.items():
            if is_metadata_key(job_id):  # Skip metadata
                continue

            status = job_data.get("status")
            if status == "cancelled":
                # Reset failed and cancelled jobs (cancelled = jobs stopped during resume)
                job_data["status"] = "pending"
                modified += 1

            if force_all:
                # Reset everything to pending
                job_data["status"] = "pending"
                modified += 1
            elif force_errors and status == "failed":
                # Reset failed and cancelled jobs (cancelled = jobs stopped during resume)
                job_data["status"] = "pending"
                modified += 1

        if modified > 0:
            # Write back to file
            with open(runtime_yaml, "wt") as f:
                yaml.dump(runtime_data, f, default_flow_style=False, sort_keys=False)
            log.log.info(f"Reset {modified} job(s) to pending status")

    except Exception as e:
        log.log.error(f"Failed to apply force mode: {e}")


def add_parser(subparsers: _SubParsersAction, module_name: str) -> ArgumentParser:
    """Add resume command parser.

    Args:
        subparsers: Parent parser's subparsers
        module_name: Name of this module

    Returns:
        Parser for resume commands
    """
    # Create empty parser - arguments are added in resume_args()
    # This prevents parent parse_known_args() from consuming our arguments
    parser = create_module_parser(subparsers, module_name)
    return parser


def resume_args(parser: ArgumentParser, argv: list, profile: str) -> Optional[Any]:
    """Process resume command arguments.

    Args:
        parser: Command parser
        argv: Command line arguments
        profile: Profile name (not used for resume, kept for API compatibility)

    Returns:
        None if resume executed successfully, parser namespace otherwise
    """
    # Add arguments to parser (done here to prevent parent from consuming them)
    parser.add_argument(
        "runtime_yaml", type=str, help="Path to pipeline_runtime.yaml file"
    )

    parser.add_argument(
        "--queue",
        dest="queue",
        type=str,
        default=None,
        help="Override queue system (default: use original from metadata)",
    )

    parser.add_argument(
        "--status",
        dest="status",
        action="store_true",
        help="Print pipeline status and exit (no execution)",
    )

    parser.add_argument(
        "--force-errors",
        dest="force_errors",
        action="store_true",
        help="Re-run failed jobs",
    )

    parser.add_argument(
        "--force-all",
        dest="force_all",
        action="store_true",
        help="Re-run all jobs regardless of status",
    )

    # Parse arguments
    args = parser.parse_args(argv)

    # Restore environment FIRST (before importing queue modules)
    try:
        restored = _restore_environment_from_yaml(args.runtime_yaml)
        if restored > 0:
            print(f"Restored {restored} environment variable(s) from pipeline runtime")
    except Exception as e:
        print(f"Error restoring environment: {e}", file=sys.stderr)
        sys.exit(1)

    # Handle status-only mode
    if args.status:
        _print_pipeline_status(args.runtime_yaml)
        return None

    # Execute resume
    success = _execute_resume(
        args.runtime_yaml,
        args.queue,
        force_errors=args.force_errors,
        force_all=args.force_all,
    )

    if not success:
        sys.exit(1)

    return None


def resume(subparsers, module_name, argv, profile):
    """Resume command entry point.

    Args:
        subparsers: Parent parser's subparsers
        module_name: Name of this module
        argv: Command line arguments
        profile: Profile name

    Returns:
        Result of resume_args()
    """
    args = resume_args(add_parser(subparsers, module_name), argv, profile)
    return args
