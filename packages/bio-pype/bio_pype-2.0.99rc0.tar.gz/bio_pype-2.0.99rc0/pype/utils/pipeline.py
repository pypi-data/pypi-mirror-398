"""Pipeline configuration and execution system.

This module manages the complete pipeline lifecycle:
- Loading pipeline definitions from YAML
- Validating pipeline configurations
- Resolving dependencies between components
- Processing pipeline arguments
- Executing pipeline components
- Managing job submission and tracking

Key classes:
- Pipeline: Main pipeline configuration container
- PipelineItem: Individual executable pipeline component
- PipelineConfig: Configuration validation and loading
- JobState: Pipeline execution state tracking
"""

import os
import re
import shlex
from copy import copy
from pathlib import Path
from pydoc import locate
from typing import Any, Dict, List, Optional

import yaml

from pype.__config__ import PYPE_PIPELINES, PYPE_QUEUES
from pype.__version__ import PIPELINES_API
from pype.argparse import ArgumentParser, RawTextHelpFormatter
from pype.exceptions import (
    ArgumentError,
    PipelineError,
    PipelineItemError,
    PipelineVersionError,
    SnippetNotFoundError,
)
from pype.misc import generate_uid, get_module_method, package_files
from pype.modules.snippets import PYPE_SNIPPETS_MODULES
from pype.utils.arguments import (
    PipelineItemArguments,
    compose_batch_description,
    get_arg_from_string,
)
from pype.utils.snippets import Snippet


def get_visible_pipelines() -> List[str]:
    """Get list of available pipeline names.

    Returns:
        List of pipeline names, excluding those starting with __

    Raises:
        PipelineError: If pipeline directory cannot be read
    """
    try:
        visible_pipelines = []
        pipelines = package_files(PYPE_PIPELINES, ".yaml")
        for pipeline in sorted(pipelines):
            pipe_name = Path(pipeline).stem
            if not pipe_name.startswith("__"):
                visible_pipelines.append(pipe_name)
        return visible_pipelines
    except Exception as e:
        # Catches FileNotFoundError, PermissionError, and other I/O errors
        # when accessing pipeline package files
        raise PipelineError(f"Failed to list pipelines: {str(e)}") from e


def get_pipelines(subparsers, pipes: Dict[str, Any]) -> Dict[str, Any]:
    """Get all available pipelines and add them to parser."""
    pipelines = package_files(PYPE_PIPELINES, ".yaml")
    for pipeline in sorted(pipelines):
        try:
            with open(pipeline, "rb") as pipe:
                pipe_dict = yaml.safe_load(pipe)
                pipe_name = os.path.basename(os.path.splitext(pipeline)[0])
                if subparsers:
                    if pipe_name.startswith("__"):
                        subparsers.add_parser(pipe_name, add_help=False)
                    else:
                        help_parser = pipe_dict["info"]["description"]
                        subparsers.add_parser(
                            pipe_name, help=help_parser, add_help=False
                        )
                pipes[pipe_name] = Pipeline(pipeline, pipe_name)
        except AttributeError:
            pass
        except Exception as e:
            raise PipelineError(
                "Failed to load pipelines", context={"error": str(e)}
            ) from e
    return pipes


def cmp(a: Any, b: Any) -> int:
    return (a > b) - (a < b)


def compare_version(version1: str, version2: str) -> int:
    def normalize(v: str) -> List[int]:
        return [int(x) for x in re.sub(r"(\.0+)*$", "", v).split(".")]

    return cmp(normalize(version1), normalize(version2))


def normalize_arguments(arg_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert compact arguments format into 2.0.0 API compatible
    list of objects. Supports recursive composite arguments.
    """
    result = []
    for prefix, value in arg_dict.items():
        # Case 1: simple string/number
        if isinstance(value, str):
            result.append({"prefix": prefix, "pipeline_arg": value})
        elif isinstance(value, int):
            result.append({"prefix": prefix, "pipeline_arg": str(value)})
        elif isinstance(value, float):
            result.append({"prefix": prefix, "pipeline_arg": str(value)})
        # Case 2: list of values (multiple same-prefix args)
        # Can contain strings, numbers, or composite arguments (dicts)
        elif isinstance(value, list):
            for v in value:
                # Handle dict items in list (composite arguments)
                if isinstance(v, dict):
                    entry = {"prefix": prefix}

                    # composite arguments
                    if v.get("type") == "composite_arg" and isinstance(
                        v.get("value"), dict
                    ):
                        composite = v["value"].copy()
                        if "result_arguments" in composite:
                            composite["result_arguments"] = normalize_arguments(
                                composite["result_arguments"]
                            )
                        entry["pipeline_arg"] = composite
                    elif "value" in v:
                        entry["pipeline_arg"] = v["value"]
                    else:
                        raise ValueError(
                            f"Invalid argument object in list for {prefix}: {v}"
                        )

                    # copy over extra metadata (e.g., type, required)
                    entry.update({k: val for k, val in v.items() if k not in ("value")})
                    result.append(entry)
                # Handle simple values in list (strings, numbers)
                else:
                    result.append({"prefix": prefix, "pipeline_arg": v})

        # Case 3: dictionary with metadata (extended form)
        elif isinstance(value, dict):
            entry = {"prefix": prefix}

            # composite arguments
            if value.get("type") == "composite_arg" and isinstance(
                value.get("value"), dict
            ):
                composite = value["value"].copy()
                if "result_arguments" in composite:
                    composite["result_arguments"] = normalize_arguments(
                        composite["result_arguments"]
                    )
                entry["pipeline_arg"] = composite
            elif "value" in value:
                entry["pipeline_arg"] = value["value"]
            else:
                raise ValueError(f"Invalid argument object for {prefix}: {value}")

            # copy over extra metadata (e.g., type, required)
            entry.update({k: v for k, v in value.items() if k not in ("value")})
            result.append(entry)

        else:
            raise ValueError(f"Unsupported argument format for {prefix}: {value}")

    return result


def topological_sort(steps_dict: Dict[str, Any]) -> List[str]:
    """Perform topological sort on pipeline steps.

    Args:
        steps_dict: Dictionary of step_id -> step definition

    Returns:
        List of step IDs in execution order (dependencies before dependents)
    """
    # Build adjacency list and in-degree map
    graph = {step_id: [] for step_id in steps_dict}
    in_degree = {step_id: 0 for step_id in steps_dict}

    for step_id, step_def in steps_dict.items():
        for dep_id in step_def.get("depends_on", []):
            if dep_id in graph:
                graph[dep_id].append(step_id)
                in_degree[step_id] += 1

    # Kahn's algorithm
    queue = [step_id for step_id in steps_dict if in_degree[step_id] == 0]
    sorted_steps = []

    while queue:
        current = queue.pop(0)
        sorted_steps.append(current)

        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_steps) != len(steps_dict):
        raise ValueError("Circular dependency detected in pipeline")

    return sorted_steps


def build_dag_structure(steps: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build flat DAG structure for pipeline execution.

    Instead of nested dependencies, creates a flat list of steps
    with explicit dependency tracking. Each step appears exactly once.

    Args:
        steps: Dictionary of step_id -> step definition from YAML

    Returns:
        List of step items in topological order (ready for execution)
    """
    step_map = {k: v for k, v in steps.items()}
    sorted_steps = topological_sort(step_map)

    items = []
    for step_id in sorted_steps:
        step = step_map[step_id]
        item = {
            "step_id": step_id,  # Track original step ID
            "name": step["name"],
            "type": step["type"],
            "arguments": normalize_arguments(step.get("arguments", {})),
            "depends_on": step.get("depends_on", []),  # Store as flat list
        }
        # Copy optional fields
        if "requirements" in step:
            item["requirements"] = step["requirements"]
        if "mute" in step:
            item["mute"] = step["mute"]

        items.append(item)

    return items


def build_nested_structure(steps):
    """
    DEPRECATED: Convert flattened steps into the API 2.0.0 nested structure.
    Kept for backwards compatibility, but build_dag_structure is preferred.
    Each step lists the steps it *depends on* as nested dependencies.
    """
    step_map = {k: v for k, v in steps.items()}

    # Identify which steps are depended upon by others
    all_steps = set(step_map.keys())
    depended_on = {
        dep for step in step_map.values() for dep in step.get("depends_on", [])
    }
    roots = list(all_steps - depended_on)  # top-level (final output) steps

    def build_item(step_id):
        step = step_map[step_id]
        item = {
            "name": step["name"],
            "type": step["type"],
            "arguments": normalize_arguments(step.get("arguments", {})),
        }

        # Steps it depends on should appear as nested dependencies
        if step.get("depends_on"):
            item["dependencies"] = {
                "items": [build_item(dep) for dep in step["depends_on"]]
            }

        return item

    return {"items": [build_item(r) for r in roots]}


def dump_arguments(
    item_arguments: PipelineItemArguments, pipeline_item: Optional[Any] = None
) -> List[Any]:
    """Extract all arguments from pipeline items recursively.

    Args:
        item_arguments: Arguments container to process
        pipeline_item: Optional parent pipeline item for dependency processing

    Returns:
        List of processed arguments

    Raises:
        PipelineError: If argument processing fails
    """
    try:
        arguments = []
        for argument in item_arguments.arguments:
            # Skip composite arguments - their internal arguments shouldn't be
            # extracted to pipeline level (they may contain literals or embedded defs)
            if hasattr(argument, "type") and argument.type == "composite_arg":
                arguments.append(argument)
                continue

            try:
                arguments += dump_arguments(argument.arguments)
            except AttributeError:
                arguments.append(argument)
            if pipeline_item is not None:
                try:
                    for dep in pipeline_item.deps:
                        arguments += dump_arguments(dep.arguments, dep)
                except AttributeError:
                    pass
        return arguments
    except Exception as e:
        # Catches KeyError, ValueError, TypeError, and other processing errors
        # during argument extraction and normalization
        raise PipelineError(f"Failed to process arguments: {str(e)}") from e


class PipelineItem:
    def __init__(
        self,
        item: Dict[str, Any],
        pype_snippets_modules: Dict = PYPE_SNIPPETS_MODULES,
    ):
        self.name = item["name"]
        self.step_id = item.get("step_id")  # For DAG execution tracking
        self.arguments = PipelineItemArguments()
        self.batch_id = None
        for argument in item["arguments"]:
            try:
                arg_type = argument["type"]
            except KeyError:
                arg_type = "argv_arg"
            self.arguments.add_argument(argument, arg_type)

        self.type = item["type"]
        self.jobs = []
        self.requirements = {}
        self.depends_on = item.get("depends_on", [])
        self.snippet: Optional[Snippet] = None  # Flat list of dependency step IDs

        try:
            self.requirements = item["requirements"]
        except KeyError:
            if self.type == "snippet" or self.type == "batch_snippet":
                # At least print the missing snippet to
                # be fixed within issue #3
                try:
                    self.snippet = copy(pype_snippets_modules[self.name])
                    self.requirements = self.snippet.requirements()
                except KeyError:
                    raise SnippetNotFoundError(self.name)

        # Support deprecated nested dependencies (for backwards compatibility)
        self.deps = []
        try:
            self.deps = [PipelineItem(x) for x in item["dependencies"]["items"]]
        except KeyError:
            pass

        try:
            self.mute = item["mute"]
            if not self.mute:
                self.mute = False
        except KeyError:
            self.mute = False

    def generate_batch_id(
        self,
    ):
        self.batch_id = generate_uid(10)[-10:]

    def run(
        self,
        argv: List[str],
        queue: str,
        profile: str,
        log: Any,
        jobs: List[Any],
        progress: Optional[Any] = None,
    ) -> Optional[List[Any]]:
        """Run pipeline item (without recursively running dependencies).

        In DAG execution model, dependencies are handled by Pipeline.submit(),
        so this method just executes the current step.

        For backwards compatibility, still supports deprecated nested deps.

        Args:
            argv: Command line arguments
            queue: Queue system to use
            profile: Profile name
            log: Logger instance
            jobs: List of submitted jobs (job IDs of dependencies)
            progress: Optional Progress tracker for resumable execution

        Returns:
            List of job results
        """
        self.jobs: List = []
        item_run: Optional[list[Any]] = None

        # Support deprecated nested dependencies (for backwards compatibility)
        try:
            for dep in self.deps:
                res = dep.run(argv, queue, profile, log, jobs, progress)
                if res:
                    self.jobs += res
        except AttributeError:
            pass

        # jobs parameter contains dependency job IDs from DAG execution
        self.jobs += jobs

        possible_types = ("snippet", "pipeline", "batch_snippet", "batch_pipeline")
        if self.type in possible_types:
            if self.type == "snippet":
                item_run = exec_snippet(self, argv, queue, profile, log, progress)
            elif self.type == "pipeline":
                item_run = exec_pipeline(self, argv, queue, profile, log, progress)
            elif self.type == "batch_snippet":
                item_run = batch_exec_unit(
                    self, argv, queue, profile, log, exec_snippet_unit, progress
                )
            elif self.type == "batch_pipeline":
                self.batch_id = None
                item_run = batch_exec_unit(
                    self, argv, queue, profile, log, exec_pipeline_unit, progress
                )
            if self.mute:
                return self.jobs
            return item_run
        raise PipelineItemError(
            f"Item type '{self.type}' is not in the possible types {possible_types}",
            self.name,
            self.type,
        )


class Pipeline:
    def __init__(
        self, path: str, name: str, pype_snippets_module: Dict = PYPE_SNIPPETS_MODULES
    ):
        self.__path__ = path
        self.__name__ = name
        self.__results__ = []
        with open(self.__path__, "rb") as file:
            pipeline = yaml.safe_load(file)
            for key in pipeline:
                setattr(self, key, pipeline[key])
        try:
            api_version = self.info["api"]
        except KeyError:
            raise PipelineVersionError("unknown", PIPELINES_API[0], self.__name__)
        version_diffs = map(
            compare_version,
            PIPELINES_API,
            [api_version for i in range(len(PIPELINES_API))],
        )
        if all([version_diff != 0 for version_diff in version_diffs]):
            raise PipelineVersionError(api_version, PIPELINES_API[0], self.__name__)
        self.pipelineitems = []
        self.step_map = {}  # Map of step_id -> PipelineItem for DAG execution

        # Handle both API 2.1.0 (steps with depends_on) and API 2.0.0 (items with nested dependencies)
        if hasattr(self, "steps"):
            # API 2.1.0: Use DAG structure for proper execution ordering
            self.items = build_dag_structure(self.steps)
        elif hasattr(self, "items"):
            # API 2.0.0: items are already in the correct nested structure, keep as-is
            pass  # self.items is already set from YAML loading
        else:
            raise PipelineError(
                "Pipeline must have either 'steps' (API 2.1.0) or 'items' (API 2.0.0)",
                self.__name__,
            )

        for x in self.items:
            item = PipelineItem(x, pype_snippets_module)
            self.pipelineitems.append(item)
            # Track by step_id for DAG dependency resolution
            if hasattr(item, "step_id") and item.step_id:
                self.step_map[item.step_id] = item

    def submit(
        self,
        parser: ArgumentParser,
        argv: List[str],
        queue: str,
        profile: str,
        log: Any,
        progress: Optional[Any] = None,
        jobs: Optional[List[Any]] = None,
    ):
        """Submit pipeline for execution using DAG-based dependency ordering.

        Args:
            parser: Argument parser
            argv: Command line arguments
            queue: Queue system to use
            profile: Profile name
            log: Logger instance
            progress: Optional Progress tracker for resumable execution
            jobs: Optional list of jobs
        """
        if jobs is None:
            jobs = []

        log.log.info("Prepare argument parser for pipeline")
        parse_snippets = pipeline_argparse_ui(self, parser, log)
        log.log.info("Parse arguments %s" % ", ".join(argv))
        args = parse_snippets.parse_args(argv)
        args = vars(args)
        log.log.info("Run all snippets with arguments %s" % args)

        # DAG-based execution: execute items in order with proper dependency tracking
        step_results = {}  # Map of step_id -> job_ids
        for item in self.pipelineitems:
            # Collect job IDs from dependencies
            dep_jobs = []
            if hasattr(item, "depends_on") and item.depends_on:
                for dep_step_id in item.depends_on:
                    if dep_step_id in step_results:
                        # dep_results could be a list of job IDs
                        dep_job_ids = step_results[dep_step_id]
                        if isinstance(dep_job_ids, list):
                            dep_jobs.extend(dep_job_ids)
                        else:
                            dep_jobs.append(dep_job_ids)
            else:
                # If this item has no internal dependencies (root item in this pipeline),
                # inherit external dependencies from parent pipeline (if nested)
                if jobs:
                    if isinstance(jobs, list):
                        dep_jobs.extend(jobs)
                    else:
                        dep_jobs.append(jobs)

            # Execute step with dependency job IDs
            results = item.run(args, queue, profile, log, dep_jobs, progress)

            # Track results for this step
            if hasattr(item, "step_id") and item.step_id:
                step_results[item.step_id] = results if results else []

            self.__results__ += results if results else []


def pipeline_argparse_ui(
    pipeline: Pipeline, parser: ArgumentParser, log: Any
) -> ArgumentParser:
    parse_snippets = parser.add_parser(
        pipeline.__name__,
        help=pipeline.info["description"],
        add_help=False,
        formatter_class=RawTextHelpFormatter,
    )
    log.log.info("Retrieve all arguments required in the pipeline snippets")
    arguments = []
    arguments_items = []
    arguments_values = []
    parser_batch = None
    parser_opt = None
    for item in pipeline.pipelineitems:
        arguments_items += dump_arguments(item.arguments)
        try:
            for dep in item.deps:
                arguments_items += dump_arguments(dep.arguments, dep)
        except AttributeError:
            pass
    for arg in arguments_items:
        # Skip composite arguments (they have value=None and shouldn't be counted as pipeline args)
        if hasattr(arg, "type") and arg.type == "composite_arg":
            continue
        if arg.value not in arguments_values:
            arguments_values.append(arg.value)
            arguments.append(arg)
    log.log.info(
        ("Use unique tags %s with specified type to the pipeline argument parser")
        % ", ".join([a.value for a in arguments])
    )
    parser_req = parse_snippets.add_argument_group(
        title="Required", description="Required pipeline arguments"
    )
    try:
        batch_args = len(pipeline.info["batches"].keys())
        if batch_args >= 1:
            parser_batch = parse_snippets.add_argument_group(
                title="Batches", description=("Arguments requiring a batch file")
            )
    except KeyError:
        pass
    try:
        default_args = len(pipeline.info["defaults"].keys())
        if default_args >= 1:
            parser_opt = parse_snippets.add_argument_group(
                title="Optional", description=("Optional pipeline arguments")
            )
    except KeyError:
        pass

    for arg_obj in arguments:
        arg = arg_obj.value
        nargs = arg_obj.nargs
        arg_str_dict = get_arg_from_string(arg)
        arg = arg_str_dict["arg"]
        arg_type = arg_str_dict["arg_type"]
        if arg is not None:
            try:
                description = "%s, type: %s" % (
                    pipeline.info["arguments"][arg],
                    arg_type,
                )
            except KeyError:
                description = "%s, type: %s" % (arg, arg_type)
            try:
                default_val = pipeline.info["defaults"][arg]
                description = "%s. Default: %s" % (description, default_val)
            except KeyError:
                default_val = False
            try:
                batch_description = pipeline.info["batches"][arg]
                description = compose_batch_description(batch_description, description)
            except KeyError:
                batch_description = False
            if arg_obj.action in ["store_true", "store_false"]:
                parser_req.add_argument(
                    "--%s" % arg, dest=arg, help=description, action=arg_obj.action
                )
            elif not default_val:
                if not batch_description:
                    parser_req.add_argument(
                        "--%s" % arg,
                        dest=arg,
                        help=description,
                        type=locate(arg_type),
                        nargs=nargs,
                        action=arg_obj.action,
                        required=True,
                    )
                else:
                    parser_batch.add_argument(
                        "--%s" % arg,
                        dest=arg,
                        help=description,
                        type=locate(arg_type),
                        required=True,
                    )
            else:
                parser_opt.add_argument(
                    "--%s" % arg,
                    dest=arg,
                    help=description,
                    type=locate(arg_type),
                    nargs=nargs,
                    action=arg_obj.action,
                    default=default_val,
                )
    return parse_snippets


def flat_list(S: List[Any]) -> List[Any]:
    """Flatten a nested list structure into a single-level list.

    Recursively flattens lists that may contain nested lists, returning
    a single flat list containing all non-list elements.

    Args:
        S: A list that may contain nested lists and other elements.

    Returns:
        A flattened list with all nested lists expanded into a single level.

    Example:
        >>> flat_list([[1, 2], 3, [4, [5, 6]]])
        [1, 2, 3, 4, 5, 6]
    """
    if S == []:
        return S
    if isinstance(S[0], list):
        return flat_list(S[0]) + flat_list(S[1:])
    return S[:1] + flat_list(S[1:])


def arg_dict_to_str(arg_dict: Dict[str, Any], arg_str: List[str]) -> List[str]:
    """Convert an argument dictionary to command-line argument list.

    Transforms a dictionary of arguments into a flat list suitable for shell
    command execution. Handles various argument types including booleans,
    strings, numbers, and lists. Boolean values are handled specially:
    - False values are skipped entirely
    - True values are added as flags (key only, no value)
    - Other values are added as key-value pairs

    Args:
        arg_dict: Dictionary where keys are argument names (e.g., '-o', '--param')
            and values can be strings, numbers, booleans, or lists.
        arg_str: Existing argument list to append to (typically starts as []).

    Returns:
        The modified arg_str list with all arguments appended.

    Example:
        >>> arg_dict = {'-o': 'output.txt', '-v': True, '--skip': False}
        >>> arg_dict_to_str(arg_dict, [])
        ['-o', 'output.txt', '-v']
    """
    for key in arg_dict:
        if isinstance(arg_dict[key], list):
            # Only join if all items are strings/numbers (not dicts/composite args)
            if all(isinstance(item, (str, int, float)) for item in arg_dict[key]):
                arg_dict[key] = " ".join(str(item) for item in arg_dict[key])
            # Otherwise keep as list (for composite arguments or other complex types)
    for key in arg_dict:
        if arg_dict[key] is not False:
            arg_str.append(key)
            if arg_dict[key] is not True:
                # Handle both string values and lists (for repeated args)
                if isinstance(arg_dict[key], list):
                    arg_str.extend(arg_dict[key])
                else:
                    arg_str.append(arg_dict[key])
    return arg_str


def exec_snippet_unit(
    item: PipelineItem,
    arg_dict: Dict[str, Any],
    queue: str,
    profile: str,
    log: Any,
    progress: Optional[Any] = None,
) -> List[Any]:
    """Execute a single snippet with two-layer skip strategy.

    Two-layer skip strategy:
    1. Layer 1 (Progress): Check if snippet completed in previous run
    2. Layer 2 (Files): Check if result files exist

    Args:
        item: Pipeline item to execute
        arg_dict: Argument dictionary
        queue: Queue system
        profile: Profile name
        log: Logger instance
        progress: Optional Progress tracker

    Returns:
        List of job results
    """
    arg_str = []
    results = None

    if not isinstance(arg_dict, dict):
        raise ArgumentError(
            f"Argument must be a dictionary, got {type(arg_dict).__name__}",
            argument="arg_dict",
        )

    arg_str = arg_dict_to_str(arg_dict, arg_str)
    log.log.info("Snippet %s relevant item.arguments: %s" % (item.name, arg_dict))
    snippet = item.snippet
    friendly_name = snippet.friendly_name(arg_dict)

    # Generate unique job ID for this snippet execution
    # job_id = "%s_%s" % (item.name, generate_uid(10)[-10:])

    try:
        results = snippet.results(arg_dict)
        results = flat_list(list(results.values()))
        log.log.info(
            "Results file(s) for snippet %s: %s" % (item.name, ", ".join(results))
        )
    except AttributeError:
        results = []

    # NOTE: Progress tracking is deprecated and no longer supported
    # Job resumption and state tracking is now handled by queue modules via pipeline_runtime.yaml
    # The progress parameter is kept for backwards compatibility but not used

    # LAYER 2: Check if result files exist
    files_exist = all(os.path.isfile(x) for x in results) if results else False
    if files_exist:
        log.log.info(
            ("Found results file(s) %s: skipping execution of snippet %s")
            % (", ".join(results), item.name)
        )

        # Files exist - skip execution
        return []

    # Neither layer says skip - execute the snippet
    log.log.info("Submit Snippet %s with queue : %s" % (item.name, queue))
    queue_name = "%s_%s_%s" % (generate_uid(), friendly_name, queue)
    log.add_log(queue_name)
    queuelog = log.programs_logs[queue_name]
    log.log.info(
        ("Add log information for snippets %s (for results %s) to folder %s")
        % (item.name, ", ".join(results), queuelog.__path__)
    )
    queuelog.log.info("Execute snippet %s with queue %s" % (item.name, queue))
    queue_exec = get_module_method(PYPE_QUEUES, queue, "submit")
    if item.jobs:
        log.log.info(
            "Snippets %s on queue %s depends on jobs: %s"
            % (item.name, queue, ", ".join(map(str, item.jobs)))
        )
    try:
        res_queue = queue_exec(
            item.name + " " + " ".join(shlex.quote(str(arg)) for arg in arg_str),
            friendly_name,
            item.requirements,
            item.jobs,
            queuelog,
            profile,
            batch_id=item.batch_id,
        )
    except TypeError as e:
        if "batch_id" in str(e):
            # Old queue module without batch_id support
            log.log.warning(
                f"Queue module doesn't support batch_id, retrying without it"
            )
            res_queue = queue_exec(
                item.name + " " + " ".join(shlex.quote(str(arg)) for arg in arg_str),
                friendly_name,
                item.requirements,
                item.jobs,
                queuelog,
                profile,
            )
        else:
            raise
    log.log.info("Snippets %s returned %s" % (item.name, res_queue))

    return [res_queue]


def exec_pipeline_unit(
    item: PipelineItem,
    arg_dict: Dict[str, Any],
    queue: str,
    profile: str,
    log: Any,
    progress: Optional[Any] = None,
) -> List[Any]:
    """Execute sub-pipeline unit.

    Args:
        item: Pipeline item
        arg_dict: Argument dictionary
        queue: Queue system
        profile: Profile name
        log: Logger
        progress: Optional Progress tracker

    Returns:
        List of pipeline results
    """
    parser = ArgumentParser(prog="pype", description="exec_pipeline")
    subparsers = parser.add_subparsers(dest="modules")
    this_pipeline = get_pipelines(subparsers, {})[item.name]
    arg_str = []

    if not isinstance(arg_dict, dict):
        raise ArgumentError(
            f"Argument must be a dictionary, got {type(arg_dict).__name__}",
            argument="arg_dict",
        )

    arg_str = arg_dict_to_str(arg_dict, arg_str)
    # may as well try to change pype.utils.arguments.Argument.to_argv
    # return in case of store_true/false
    log.log.info("Pipeline %s relevant item.arguments: %s" % (item.name, arg_dict))
    this_pipeline.submit(subparsers, arg_str, queue, profile, log, progress, item.jobs)
    return this_pipeline.__results__


def exec_snippet(
    item: PipelineItem,
    argv: List[str],
    queue: str,
    profile: str,
    log: Any,
    progress: Optional[Any] = None,
) -> List[Any]:
    """Execute snippet with Progress tracking.

    Args:
        item: Pipeline item
        argv: Arguments
        queue: Queue system
        profile: Profile name
        log: Logger
        progress: Optional Progress tracker

    Returns:
        List of job results
    """
    arg_dict = item.arguments.to_dict(argv)
    results = exec_snippet_unit(item, arg_dict, queue, profile, log, progress)
    return results


def exec_pipeline(
    item: PipelineItem,
    argv: List[str],
    queue: str,
    profile: str,
    log: Any,
    progress: Optional[Any] = None,
) -> List[Any]:
    """Execute sub-pipeline with Progress tracking.

    Args:
        item: Pipeline item
        argv: Arguments
        queue: Queue system
        profile: Profile name
        log: Logger
        progress: Optional Progress tracker

    Returns:
        List of pipeline results
    """
    arg_dict = item.arguments.to_dict(argv)
    results = exec_pipeline_unit(item, arg_dict, queue, profile, log, progress)
    return results


def batch_exec_unit(
    item: PipelineItem,
    argv: List[str],
    queue: str,
    profile: str,
    log: Any,
    exec_unit: Any,
    progress: Optional[Any] = None,
) -> List[Any]:
    """Execute batch unit.

    Args:
        item: Pipeline item
        argv: Arguments
        queue: Queue system
        profile: Profile name
        log: Logger
        exec_unit: Execution function
        progress: Optional Progress tracker

    Returns:
        List of results
    """
    results = []
    arg_dict = item.arguments.to_dict(argv)
    item.generate_batch_id()
    for tmp_argv in arg_dict:
        results += exec_unit(item, tmp_argv, queue, profile, log, progress)
    return results
