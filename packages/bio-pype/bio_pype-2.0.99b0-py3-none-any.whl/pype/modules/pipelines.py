"""Pipeline command-line interface module.

This module provides the command-line interface for pipeline operations:
- Pipeline listing and discovery
- Pipeline execution and monitoring
- Queue system integration
- Logging configuration

The module serves as the entry point for the 'pype pipelines' command.

Example:
    pype pipelines rev_compl_low_fa --input_fa input.fasta
    pype pipelines --queue slurm complex_pipeline --batch_file samples.txt
"""

import os
import sys
from datetime import datetime
from typing import Any, List, Optional

import yaml

from pype.__config__ import PYPE_LOGDIR, PYPE_QUEUES
from pype.argparse import ArgumentParser, _SubParsersAction
from pype.exceptions import PypeError
from pype.logger import PypeLogger
from pype.misc import generate_uid, get_module_method, get_modules_names
from pype.modules import create_module_parser
from pype.modules.profiles import get_profiles
from pype.utils.pipeline import get_pipelines, get_visible_pipelines


def _write_pipeline_environment(log: Any) -> None:
    """Write pipeline environment variables to runtime YAML.

    Appends __pipeline_environment__ section to existing pipeline_runtime.yaml
    with all PYPE_* environment variables. This ensures reproducibility when
    resuming pipelines or debugging issues, especially important for PBS and
    other queue systems that don't share environment by default.

    Args:
        log: PypeLogger instance
    """
    runtime_file = os.path.join(log.__path__, "pipeline_runtime.yaml")

    try:
        # Read existing runtime YAML
        if os.path.isfile(runtime_file):
            with open(runtime_file, "rt") as f:
                runtime = yaml.safe_load(f) or {}
        else:
            runtime = {}

        # Capture PYPE_* environment variables (following pattern from pbs_runtime.py)
        pype_env = [x for x in os.environ.keys() if x.startswith("PYPE")]

        # Create environment dictionary
        environment = {k: os.environ[k] for k in pype_env}

        runtime["__pipeline_environment__"] = environment

        # Write back to file
        with open(runtime_file, "wt") as f:
            yaml.dump(runtime, f, default_flow_style=False, sort_keys=False)

        log.log.info(f"Pipeline environment written: {len(environment)} variables")

    except Exception as e:
        log.log.warning(f"Failed to write pipeline environment: {e}")


def _write_pipeline_metadata(
    log: Any,
    used_pipeline: str,
    run_name: Optional[str],
    args: Any,
    queue: str,
    profile_name: str,
    pipeline_obj: Optional[Any] = None,
    run_id: Optional[int] = None,
    run_hash: Optional[str] = None,
) -> None:
    """Write pipeline metadata to runtime YAML.

    Appends __pipeline_metadata__ section to existing pipeline_runtime.yaml
    with pipeline identification and execution context information.

    Args:
        log: PypeLogger instance
        used_pipeline: Pipeline template name from YAML definition
        run_name: Optional user-provided display name for this run
        args: Parsed arguments dict
        queue: Queue system name
        profile_name: Profile name
        pipeline_obj: Optional Pipeline object (to extract description and YAML path)
        run_id: Optional compute.bio run ID (saved after API registration)
        run_hash: Optional compute.bio run hash (saved after API registration)
    """
    runtime_file = os.path.join(log.__path__, "pipeline_runtime.yaml")

    try:
        # Read existing runtime YAML
        if os.path.isfile(runtime_file):
            with open(runtime_file, "rt") as f:
                runtime = yaml.safe_load(f) or {}
        else:
            runtime = {}

        # Get existing metadata to preserve run_id/run_hash if already set
        existing_metadata = runtime.get("__pipeline_metadata__", {})

        # Create metadata section
        metadata = {
            "pipeline_name": used_pipeline,  # Actual pipeline template name
            "run_name": run_name or used_pipeline,  # User-friendly run name
            "submission_time": datetime.now().isoformat(),
            "queue_system": queue,
            "profile": profile_name,
            "log_directory": os.path.abspath(log.__path__),
            "pipeline_runtime_yaml_path": os.path.abspath(runtime_file),
        }

        # Add compute.bio IDs if provided (or preserve existing ones)
        if run_id is not None:
            metadata["run_id"] = run_id
        elif "run_id" in existing_metadata:
            metadata["run_id"] = existing_metadata["run_id"]

        if run_hash is not None:
            metadata["run_hash"] = run_hash
        elif "run_hash" in existing_metadata:
            metadata["run_hash"] = existing_metadata["run_hash"]

        # Add pipeline description if available from Pipeline object
        if pipeline_obj and hasattr(pipeline_obj, "info"):
            description = pipeline_obj.info.get("description", "")
            if description:
                metadata["pipeline_description"] = description

        # Add pipeline YAML path if available from pipeline object
        if pipeline_obj and hasattr(pipeline_obj, "__path__"):
            metadata["pipeline_yaml_path"] = os.path.abspath(pipeline_obj.__path__)

        runtime["__pipeline_metadata__"] = metadata

        # Write back to file
        with open(runtime_file, "wt") as f:
            yaml.dump(runtime, f, default_flow_style=False, sort_keys=False)

        log.log.info(f"Pipeline metadata written: {metadata['run_name']}")

    except Exception as e:
        log.log.warning(f"Failed to write pipeline metadata: {e}")


def add_parser(subparsers: _SubParsersAction, module_name: str) -> ArgumentParser:
    """Add pipeline command parser.

    Args:
        subparsers: Parent parser's subparsers
        module_name: Name of this module

    Returns:
        Parser for pipeline commands
    """
    return create_module_parser(subparsers, module_name)


def pipelines_args(
    parser: ArgumentParser, argv: List[str], profile: str
) -> Optional[Any]:
    """Process pipeline command arguments.

    Args:
        parser: Command parser
        argv: Command line arguments
        profile: Profile name to use

    Returns:
        None if pipeline executed successfully, parser namespace otherwise

    Raises:
        Exception: If no queue systems are available
    """
    queues = get_modules_names(PYPE_QUEUES)
    if len(queues) < 1:
        raise PypeError(
            f"There are no queues in {PYPE_QUEUES.__path__[0]} to run a pipeline!!"
        )
    try:
        default_q = PYPE_QUEUES.default
    except AttributeError:
        default_q = queues[0]
    metavar_str = "{%s}" % ",".join(get_visible_pipelines())
    lastparsers = parser.add_subparsers(dest="pipeline", metavar=metavar_str)

    parser.add_argument(
        "--queue",
        dest="queue",
        action="store",
        choices=queues,
        default=default_q,
        help=("Select the queuing system to run the pipeline. Default %s" % default_q),
    )
    parser.add_argument(
        "--log",
        dest="log",
        type=str,
        default=PYPE_LOGDIR,
        help=("Path used to write the pipeline logs. Default %s" % PYPE_LOGDIR),
    )
    parser.add_argument(
        "--run-name",
        dest="run_name",
        type=str,
        default=None,
        help=(
            "Display name for this pipeline run (for tracking/reporting in compute.bio). "
            "If not specified, the pipeline name from the definition will be used. "
            "Example: --run-name 'Alignment Sample GBM00409N'"
        ),
    )
    pipelines_list = get_pipelines(lastparsers, {})
    args, extra = parser.parse_known_args(argv)
    try:
        used_pipeline = args.pipeline
        if used_pipeline in pipelines_list.keys():
            profile_dict = get_profiles({})
            try:
                profile = profile_dict[profile]
            except KeyError:
                profile = profile_dict[profile_dict.keys()[0]]

            log = PypeLogger(
                "%s_%s" % (generate_uid(), used_pipeline), args.log, profile
            )
            try:
                # The pipeline/queue system uses YAML-based progress tracking
                # Progress is tracked in pipeline_runtime.yaml in the log directory
                # Resume from previous runs is supported via --resume flag (see above)

                log.log.info(
                    f"Starting new pipeline run with progress tracking in: {log.__path__}"
                )

                pipelines_list[used_pipeline].submit(
                    lastparsers, extra, args.queue, profile.__name__, log
                )
                log.log.info("Pipeline %s terminated" % log.__name__)

                # Write pipeline metadata to runtime YAML before post_run
                # Note: run_id and run_hash will be added by post_run() after API registration
                _write_pipeline_metadata(
                    log,
                    used_pipeline,
                    args.run_name,  # This becomes run_name
                    vars(args),
                    args.queue,
                    profile.__name__,
                    pipeline_obj=pipelines_list[used_pipeline],
                )

                # Write pipeline environment variables to runtime YAML
                _write_pipeline_environment(log)

                log.log.info(
                    "Execute post run processes of queue %s, if any" % args.queue
                )
                post_run = get_module_method(PYPE_QUEUES, args.queue, "post_run")
                if post_run is not None:
                    post_run(log)
            except KeyboardInterrupt:
                log.log.info("Shutdown requested (Ctrl+C)")
                sys.exit(0)
            return
        try:
            if args.pipeline is None:
                return parser.print_help()
            return parser.parse_args(args)
        except AttributeError:
            return parser.print_help()
    except IndexError:
        return parser.print_help()


def pipelines(subparsers, module_name, argv, profile):
    args = pipelines_args(add_parser(subparsers, module_name), argv, profile)
    return args
