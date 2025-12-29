"""compute.bio API testing and listener module.

This module provides CLI commands for:
- Testing compute.bio API connectivity and credentials (--test)
- Running a persistent listener daemon that polls for commands (--run)

Example:
    pype compute-bio --test              # Test API connectivity
    pype compute-bio --run               # Run listener daemon
"""

import importlib
import json
import os
import socket
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

import pype.__config__
from pype.__config__ import (
    COMPUTE_BIO_API_URL,
    COMPUTE_BIO_TOKEN,
    PYPE_LOGDIR,
    reload_pype_queues,
)
from pype.argparse import ArgumentParser, _SubParsersAction
from pype.logger import PypeLogger
from pype.misc import create_minimal_profile, responsive_sleep
from pype.modules import create_module_parser
from pype.utils.compute_bio_api import create_api_client
from pype.utils.queue_commands import execute_command
from pype.utils.queues import _restore_environment_from_yaml, load_queue_handler


def add_parser(parser: _SubParsersAction, module_name: str) -> ArgumentParser:
    """Add compute-bio command parser.

    Args:
        parser: Parent parser's subparsers
        module_name: Name of this module

    Returns:
        Parser for compute-bio commands
    """
    return create_module_parser(parser, module_name)


def compute_bio_args(parser, argv, profile):
    """Parse and handle compute-bio arguments.

    Args:
        parser: ArgumentParser instance
        argv: Command line arguments
        profile: Profile name
    """
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test API connectivity and credentials",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run persistent listener daemon",
    )
    parser.add_argument(
        "--log",
        dest="log",
        type=str,
        default=PYPE_LOGDIR,
        help=f"Path for logs. Default: {PYPE_LOGDIR}",
    )

    args = parser.parse_args(argv)

    # Setup logging with minimal profile if not provided or if profile is just a string
    # (profile parameter is a string like 'default', not a profile object)
    if profile and hasattr(profile, '__path__') and hasattr(profile, '__name__'):
        log_profile = profile
    else:
        log_profile = create_minimal_profile("compute-bio")
    log = PypeLogger("compute_bio", args.log, log_profile)
    # Note: PypeLogger already creates the main logger, use it directly
    cblog = log

    if args.test:
        test_api_connection(cblog)
    elif args.run:
        run_listener_daemon(cblog)
    else:
        parser.print_help()


def compute_bio(subparsers, module_name, argv, profile):
    """Main compute_bio command entry point.

    Args:
        subparsers: Parent parser's subparsers
        module_name: Name of this module
        argv: Command line arguments
        profile: Profile name
    """
    args = compute_bio_args(add_parser(subparsers, module_name), argv, profile)
    return args


def test_api_connection(queuelog):
    """Test compute.bio API connectivity and credentials (handshake only).

    This performs a simple connectivity test without creating any pipelines
    or permanent records in the database. It's just a "hello" handshake.

    Args:
        queuelog: Logger object
    """
    queuelog.log.info("=" * 80)
    queuelog.log.info("Testing compute.bio API Connection (Handshake)")
    queuelog.log.info("=" * 80)

    # Check environment variables
    if not COMPUTE_BIO_API_URL:
        queuelog.log.error("COMPUTE_BIO_API_URL not set")
        queuelog.log.error(
            "Please set: export COMPUTE_BIO_API_URL=http://app.compute.bio"
        )
        sys.exit(1)

    if not COMPUTE_BIO_TOKEN:
        queuelog.log.error("COMPUTE_BIO_TOKEN not set")
        queuelog.log.error("Please set: export COMPUTE_BIO_TOKEN=your_token_here")
        sys.exit(1)

    queuelog.log.info(f"API URL: {COMPUTE_BIO_API_URL}")
    queuelog.log.info(
        f"Token: {COMPUTE_BIO_TOKEN[:10]}..."
        if len(COMPUTE_BIO_TOKEN) > 10
        else f"Token: {COMPUTE_BIO_TOKEN}"
    )

    # Initialize API client
    api_client = create_api_client("compute-bio-handshake", queuelog)
    if not api_client:
        queuelog.log.error("API client not configured")
        return

    # Test simple connectivity using the health check endpoint (no auth required)
    queuelog.log.info("\nTesting API connectivity (simple handshake)...")
    try:
        # Use the health check endpoint which doesn't require authentication
        url = f"{api_client.api_url}/health/"
        request = Request(url, method="GET")

        try:
            with urlopen(request, timeout=10) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                queuelog.log.info("Handshake successful - API is responsive")
                queuelog.log.info(f"  Status: {response_data.get('status')}")
                queuelog.log.info(f"  Message: {response_data.get('message')}")
                queuelog.log.info("\n" + "=" * 80)
                queuelog.log.info(
                    "Handshake complete! compute.bio API is accessible and responding."
                )
                queuelog.log.info("=" * 80)
                sys.exit(0)
        except HTTPError as e:
            if e.code == 404:
                queuelog.log.error(
                    "Health check endpoint not found (API version mismatch?)"
                )
                sys.exit(1)
            else:
                queuelog.log.error(f"HTTP {e.code}: {e.reason}")
                sys.exit(1)

    except URLError as e:
        queuelog.log.error(f"Cannot reach API at {api_client.api_url}: {e.reason}")
        sys.exit(1)
    except Exception as e:
        queuelog.log.error(f"Handshake failed: {e}")
        sys.exit(1)


def _process_worker_command(
    api_client, queuelog, worker_id, cmd_id, cmd_type, cmd, yaml_path
):
    """Process a command from a worker through the queue handler.

    Executes commands by delegating to the queue handler's execute_command()
    method, so all queue types get the same command support without duplication.

    Args:
        api_client: ComputeBioAPIClient instance
        queuelog: Logger object
        worker_id: Worker ID
        cmd_id: Command ID
        cmd_type: Type of command (e.g., 'get_logs', 'cancel_job')
        cmd: Full command data dict from API
        yaml_path: Path to pipeline_runtime.yaml (if available)
    """
    # Save current environment to restore after command
    saved_env = os.environ.copy()

    try:
        if not yaml_path or not Path(yaml_path).exists():
            queuelog.log.debug(f"        Runtime file not found: {yaml_path}")
            return

        # Restore pipeline environment from YAML
        restored = _restore_environment_from_yaml(yaml_path)
        if restored > 0:
            queuelog.log.info(
                f"Restored {restored} environment variable(s) from pipeline runtime"
            )

        # Reload pype config with pipeline environment
        importlib.reload(pype.__config__)
        PYPE_QUEUES = reload_pype_queues()

        # Load runtime to get queue type and metadata

        with open(yaml_path, "r") as f:
            runtime_data = yaml.safe_load(f) or {}

        metadata = runtime_data.get("__pipeline_metadata__", {})
        queue_type = metadata.get("queue_system", "parallel")

        # Load the handler from the active queue module
        handler = load_queue_handler(PYPE_QUEUES, queue_type, runtime_data)
        if not handler:
            queuelog.log.error(f"        Queue module '{queue_type}' not found")
            return

        # Execute command through shared function
        queuelog.log.debug(
            f"        → Processing {cmd_type} via {handler.__class__.__name__}"
        )
        result = execute_command(handler, cmd, yaml_path)

        # Send result back to API
        complete_payload = {
            "success": result.get("success", False),
            "result": result,
        }
        api_client._make_request(
            "POST",
            f"workers/{worker_id}/commands/{cmd_id}/complete/",
            complete_payload,
        )

        if result.get("success"):
            queuelog.log.info(f"        Processed {cmd_type} successfully")
        else:
            queuelog.log.warning(
                f"        Command failed: {result.get('error', 'unknown error')}"
            )

    except Exception as e:
        queuelog.log.error(f"        Error processing command: {str(e)[:200]}")

    finally:
        # Always restore original environment
        os.environ.clear()
        os.environ.update(saved_env)


def run_listener_daemon(queuelog):
    """Run persistent listener daemon that monitors compute.bio for commands.

    NOTE: This daemon is meant to run on the same system where bio_pype pipelines
    are executed. It doesn't create fake pipelines. Instead:

    1. When a real pipeline runs and registers with compute.bio, it gets a worker_id
    2. The daemon monitors compute.bio for any commands sent to pipelines on this system
    3. Commands are handled automatically (log requests, etc.)

    The daemon will show 404 errors until actual pipelines register and send commands.
    This is normal and expected behavior.

    What happens in the UI:
    ========================
    When you send a command from the UI (e.g., "Get Logs" for a completed pipeline):

    1. UI creates a WorkerCommand with status=PENDING in the database
    2. Daemon polls /api/v1/inactive-workers/commands/ every 10 seconds
    3. Daemon receives the command, logs it, and:
       - Acknowledges it (status → ACKNOWLEDGED) so it won't be polled again
       - Processes it based on command type (get_snippet_logs, cancel, etc.)
       - Marks it COMPLETED (or FAILED) with results/status
    4. UI can poll /api/v1/pipelines/<id>/commands/<cmd_id>/ to get the result
    5. Once COMPLETED, the command is no longer in the queue

    To see this in action:
    - Watch daemon logs: tail -f ~/.bio_pype/logs/compute_bio/compute_bio.log
    - Send a command from compute.bio UI
    - Daemon should log: "Command X: <type>" and "Poll N complete: Processed X command(s)"

    Args:
        queuelog: Logger object
    """

    queuelog.log.info("=" * 80)
    queuelog.log.info("Starting compute.bio Listener Daemon")
    queuelog.log.info("=" * 80)

    # Check if another daemon is already running on this machine
    # This prevents accidental double-running which could cause race conditions
    hostname = socket.gethostname()
    lock_file = f"/tmp/pype_compute_bio_daemon_{hostname}.lock"
    try:
        lock_fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(lock_fd)
        queuelog.log.info(f"Daemon lock acquired for {hostname}")
    except FileExistsError:
        queuelog.log.error(f"ERROR: Another daemon already running on {hostname}")
        queuelog.log.error(f"Lock file: {lock_file}")
        queuelog.log.error("Only one daemon should run per machine")
        sys.exit(1)

    def cleanup_lock(lock_file):
        # Ensure lock file is cleaned up on exit
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
                queuelog.log.info(f"Removed lock file: {lock_file}")
        except Exception as e:
            queuelog.log.warning(f"Failed to remove lock file: {e}")

    # Check environment variables
    if not COMPUTE_BIO_API_URL or not COMPUTE_BIO_TOKEN:
        queuelog.log.error("COMPUTE_BIO_API_URL or COMPUTE_BIO_TOKEN not set")
        queuelog.log.error("Please set environment variables to enable API integration")
        sys.exit(1)

    queuelog.log.info(f"API URL: {COMPUTE_BIO_API_URL}")
    queuelog.log.info(
        "\nNOTE: This daemon monitors for commands from registered pipelines."
    )
    queuelog.log.info(
        "It will start handling commands once pipelines register with compute.bio."
    )
    queuelog.log.info("Press Ctrl+C to stop.\n")
    queuelog.log.info("=" * 80 + "\n")

    # Initialize API client
    api_client = create_api_client("compute-bio-listener", queuelog)
    if not api_client:
        queuelog.log.error("Failed to initialize API client")
        cleanup_lock(lock_file)
        sys.exit(1)

    # This daemon actively monitors for commands from registered pipelines
    # It polls the API periodically and logs any activity

    queuelog.log.info(
        "Daemon is running and monitoring for commands from registered pipelines."
    )
    queuelog.log.info("Polling every 10 seconds for activity.")
    queuelog.log.info("Waiting for pipelines to register with compute.bio API...\n")
    queuelog.log.info("=" * 80)
    queuelog.log.info("Command Processing Flow:")
    queuelog.log.info(
        "  1. Poll /api/v1/inactive-workers/commands/ for PENDING commands"
    )
    queuelog.log.info("  2. For each command: ACK → PROCESS → COMPLETE")
    queuelog.log.info("  3. Acknowledged commands won't appear on next poll")
    queuelog.log.info("  4. Completed commands are removed from the queue")
    queuelog.log.info("=" * 80 + "\n")

    poll_interval = 10  # Poll more frequently so you see activity
    iteration = 0

    try:
        while True:
            iteration += 1

            try:
                # Log every poll so you can see daemon is active
                queuelog.log.info(
                    f"[Poll {iteration}] Checking for inactive workers with commands..."
                )

                # Query for inactive workers that have pending commands
                # Active workers will poll for their own commands
                # This daemon handles commands for workers that are no longer actively polling
                try:
                    response = api_client._make_request(
                        "GET", "inactive-workers/commands/"
                    )
                    if response is not None:
                        inactive_workers = response.get("inactive_workers", [])
                        count = response.get("count", 0)
                        queuelog.log.debug(
                            f"  API Response: count={count}, inactive_workers={len(inactive_workers)}"
                        )

                        if count > 0:
                            queuelog.log.info(
                                f"  Found {count} inactive worker(s) with pending commands:"
                            )
                            processed_count = 0
                            for worker in inactive_workers:
                                worker_id = worker.get("worker_id")
                                pipeline_id = worker.get("pipeline_id")
                                commands_count = len(worker.get("commands", []))
                                queuelog.log.info(
                                    f"    - Worker {worker_id} (Pipeline {pipeline_id}): {commands_count} command(s)"
                                )

                                # Get yaml_path from worker data for log processing
                                yaml_path = worker.get("yaml_path")

                                # Process each command
                                for cmd in worker.get("commands", []):
                                    cmd_type = cmd.get("command_type")
                                    cmd_id = cmd.get("id")
                                    queuelog.log.info(
                                        f"      Command {cmd_id}: {cmd_type}"
                                    )

                                    # Acknowledge so it won't be re-polled on next cycle
                                    try:
                                        api_client._make_request(
                                            "POST",
                                            f"workers/{worker_id}/commands/{cmd_id}/ack/",
                                        )
                                        queuelog.log.debug("        Acknowledged")
                                    except Exception as e:
                                        queuelog.log.error(
                                            f"        Failed to acknowledge: {str(e)[:100]}"
                                        )

                                    # Execute command through the queue handler
                                    _process_worker_command(
                                        api_client,
                                        queuelog,
                                        worker_id,
                                        cmd_id,
                                        cmd_type,
                                        cmd,
                                        yaml_path,
                                    )

                                    processed_count += 1

                            # Summary of this poll
                            queuelog.log.info(
                                f"  Poll {iteration} complete: Processed {processed_count} command(s)"
                            )
                        else:
                            queuelog.log.debug(
                                "  (No inactive workers with pending commands)"
                            )
                    else:
                        queuelog.log.info(
                            "  API returned None (auth error or endpoint not found)"
                        )
                except Exception as e:
                    queuelog.log.info(
                        f"  Error querying inactive workers: {str(e)[:200]}"
                    )

            except Exception as e:
                queuelog.log.error(f"Error during monitoring: {e}")

            # Sleep in small increments for responsive shutdown
            for _ in range(poll_interval):
                time.sleep(1)

    except KeyboardInterrupt:
        queuelog.log.info("\n" + "=" * 80)
        queuelog.log.info("Shutdown requested (Ctrl+C)")
        queuelog.log.info("Listener daemon stopped")
        queuelog.log.info("=" * 80)
        cleanup_lock(lock_file)
        sys.exit(0)
    except Exception as e:
        queuelog.log.error(f"Fatal error: {e}")
        cleanup_lock(lock_file)
        sys.exit(1)
