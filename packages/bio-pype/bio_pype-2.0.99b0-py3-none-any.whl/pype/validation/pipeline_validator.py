"""Pipeline validation implementation.

Validates bio_pype YAML pipeline configurations (API 2.1.0 only).
Uses the Pipeline class for all structural validation via exceptions.

Structure follows the snippet validator pattern for consistency.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pype.__config__ import reload_pype_snippets
from pype.exceptions import (
    PipelineError,
    PipelineItemError,
    PipelineVersionError,
    SnippetNotFoundError,
    SnippetResultsArgumentError,
    SnippetResultsTemplateSobstitutionError,
)
from pype.utils.arguments import get_arg_from_string
from pype.utils.pipeline import Pipeline
from pype.utils.snippets import snippets_modules_list
from pype.validation.context import WorkspaceIndex
from pype.validation.core import (
    Diagnostic,
    DiagnosticSeverity,
    Location,
    ValidationContext,
    ValidationResult,
)


class _DummyLogger:
    """Dummy logger for snippet argument extraction."""

    def info(self, msg):
        pass

    def error(self, msg):
        pass

    def warning(self, msg):
        pass

    def debug(self, msg):
        pass


class _DummyLog:
    """Dummy log object for snippet argument extraction."""

    def __init__(self):
        self.log = _DummyLogger()
        self.__path__ = "/tmp"


class _DummyProfile:
    """Dummy profile for snippet argument extraction."""

    def __init__(self):
        self.files = {}
        self.genome_build = "unknown"
        self.programs = {}


class PipelineValidator:
    """Validator for bio_pype YAML pipelines (API 2.1.0 only).

    Validates:
    - YAML syntax and structure
    - API version (2.1.0 only)
    - Pipeline structure (steps, info section)
    - Item types and required fields
    - Snippet/pipeline references
    - All validation via Pipeline class exceptions

    Structure follows the snippet validator pattern for consistency.
    """

    VALID_APIS = {"2.1.0", "2.0.0"}

    def __init__(self, context: ValidationContext) -> None:
        """Initialize pipeline validator.

        Args:
            context: ValidationContext for workspace information
        """
        self.context = context
        self.diagnostics: List[Diagnostic] = []
        self.file_lines: List[str] = []
        self.pipeline: Optional[Pipeline] = None
        self.workspace_index = WorkspaceIndex(self.context)
        self.pype_snippets_modules: Optional[dict] = None

        # Caches for performance
        self._snippet_args_cache: Dict[str, Dict[str, Any]] = {}
        self._results_cache: Dict[str, Dict[str, Any]] = {}

        # Reusable dummy objects for argument extraction
        self._dummy_log = _DummyLog()
        self._dummy_profile = _DummyProfile()

    def _add_diagnostic(
        self,
        severity: DiagnosticSeverity,
        line: int,
        start_char: int,
        end_char: int,
        message: str,
        code: str,
    ) -> None:
        """Add a diagnostic to the list."""
        self.diagnostics.append(
            Diagnostic(
                severity=severity,
                location=Location(line, start_char, end_char),
                message=message,
                code=code,
            )
        )

    def _load_file_lines(self, file_path: Path) -> None:
        """Load file into memory for line number lookup."""
        if not self.file_lines:
            with open(file_path, "r") as f:
                self.file_lines = f.readlines()

    def _get_line_nr(
        self,
        search_str: str,
        context: Optional[str] = None,
        in_step: Optional[str] = None,
        in_arg: Optional[str] = None,
    ) -> int:
        """Find line number containing search string, optionally within a specific step/argument.

        Args:
            search_str: String to search for in file
            context: Optional prefix that should appear before search_str on the same line
                    (e.g., "name:" to find "name: my_snippet")
            in_step: Optional step_id to search within (e.g., "step_reverse_fa")
                    When provided, only searches within that step's YAML block
            in_arg: Optional argument key to search within (e.g., "--bam")
                    When provided along with in_step, narrows search to that argument's block

        Returns:
            Line number (0-based) or 0 if not found
        """
        if not search_str:
            return 0

        # Determine search range
        start_line = 0
        end_line = len(self.file_lines)

        if in_step:
            # Find the step block boundaries
            step_pattern = f"{in_step}:"
            step_found = False
            step_indent = 0

            for i, line in enumerate(self.file_lines):
                if step_pattern in line and not step_found:
                    start_line = i
                    step_found = True
                    # Get the indentation level of this step
                    step_indent = len(line) - len(line.lstrip())
                elif step_found:
                    # Check if we've exited the step block
                    # (another key at same or lower indent level)
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        current_indent = len(line) - len(line.lstrip())
                        if current_indent <= step_indent and ":" in stripped:
                            end_line = i
                            break

            if not step_found:
                # Step not found, fall back to full file search
                start_line = 0
                end_line = len(self.file_lines)

        # If in_arg is specified, further narrow to that argument's block
        if in_arg and start_line < end_line:
            arg_pattern = f"{in_arg}:"
            arg_found = False
            arg_indent = 0
            arg_start = start_line
            arg_end = end_line

            for i in range(start_line, end_line):
                line = self.file_lines[i]
                if arg_pattern in line and not arg_found:
                    arg_start = i
                    arg_found = True
                    arg_indent = len(line) - len(line.lstrip())
                elif arg_found:
                    # Check if we've exited the argument block
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        current_indent = len(line) - len(line.lstrip())
                        if current_indent <= arg_indent:
                            arg_end = i
                            break

            if arg_found:
                start_line = arg_start
                end_line = arg_end

        # Search within the range
        for line_nr in range(start_line, end_line):
            line = self.file_lines[line_nr]
            if context:
                if context in line and search_str in line:
                    return line_nr
            else:
                if search_str in line:
                    return line_nr

        return 0

    def _load_pipeline(self, file_path: Path) -> None:
        """Load pipeline using Pipeline class. Handles exceptions as diagnostics.

        Args:
            file_path: Path to pipeline file
        """
        # Set PYPE_MODULES environment variable for snippet loading
        os.environ["PYPE_MODULES"] = str(file_path.parents[1])
        pype_snippets = reload_pype_snippets()
        self.pype_snippets_modules = snippets_modules_list({}, pype_snippets)

        try:
            self.pipeline = Pipeline(
                str(file_path), file_path.stem, self.pype_snippets_modules
            )

        except PipelineVersionError as e:
            line = self._get_line_nr("api:")
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                line,
                0,
                10,
                f"Invalid or unsupported API version. Only API 2.1.0 is supported. {e}",
                "invalid-api-version",
            )

        except SnippetNotFoundError as e:
            snippet_name = e.context.get("snippet_name", "")
            line = self._get_line_nr(snippet_name, context="name:")
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                line,
                0,
                10,
                f"Snippet '{snippet_name}' not found: {e}",
                "missing-snippet",
            )

        except PipelineItemError as e:
            item_name = e.context.get("item_name", "")
            line = self._get_line_nr(item_name, context="name:")
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                line,
                0,
                10,
                f"Pipeline item error: {e}",
                "pipeline-item-error",
            )

        except PipelineError as e:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                0,
                0,
                10,
                f"Pipeline structure error: {e}",
                "pipeline-structure-error",
            )

        except Exception as e:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                0,
                0,
                10,
                f"Failed to load pipeline: {e}",
                "pipeline-load-error",
            )

    def _validate_pipeline_items(self) -> None:
        """Validate each pipeline item's arguments and composite_args."""
        if not self.pipeline:
            return

        for item in self.pipeline.pipelineitems:
            self._validate_item_arguments(item)

    def _validate_item_arguments(self, item: Any) -> None:
        """Validate a single pipeline item's arguments.

        Args:
            item: PipelineItem instance to validate

        Validates:
        - Arguments defined in pipeline match snippet's argparse interface
        - Composite arguments reference valid snippets
        - Composite arguments have valid result keys
        """
        item_type = getattr(item, "type", "unknown")

        # Only validate snippet and batch_snippet types (not pipeline types)
        if item_type in ("snippet", "batch_snippet"):
            self._validate_snippet_arguments(item)

        # Validate each argument
        for argument in item.arguments.arguments:
            # Recursively validate composite arguments
            if hasattr(argument, "type") and argument.type == "composite_arg":
                self._validate_composite_argument(argument, item)

    def _extract_snippet_arguments(
        self, snippet_module: Any, item_name: str
    ) -> Dict[str, Any]:
        """Extract expected arguments from a snippet by inspecting its parser.

        Results are cached by item_name for performance.

        Args:
            snippet_module: The snippet module (Snippet or SnippetMd instance)
            item_name: Name of the snippet

        Returns:
            Dictionary mapping argument strings (e.g., '-i', '--input') to their actions,
            or empty dict if extraction fails
        """
        # Check cache first
        if item_name in self._snippet_args_cache:
            return self._snippet_args_cache[item_name]

        import sys
        from io import StringIO

        from pype.argparse import ArgumentParser

        # Create a temporary parser
        temp_parser = ArgumentParser(add_help=False)
        temp_subparsers = temp_parser.add_subparsers()

        snippet_parser = None

        try:
            if hasattr(snippet_module, "argparse"):
                # SnippetMd: argparse() adds arguments to the parser
                snippet_parser = snippet_module.argparse(temp_subparsers)
            else:
                # Python Snippet: Try calling with --help and capture output
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = StringIO()
                sys.stderr = StringIO()

                try:
                    # Call snippet with --help to get argument info
                    # Uses pre-created dummy objects for performance
                    snippet_module.snippet(
                        temp_subparsers, ["--help"], self._dummy_profile, self._dummy_log
                    )
                except SystemExit:
                    # Expected when --help is used
                    pass
                finally:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr

                # Try the direct parser approach as well
                snippet_parser = snippet_module.add_parser(temp_subparsers)

        except Exception:
            # If anything fails, cache and return empty dict
            self._snippet_args_cache[item_name] = {}
            return {}

        # Extract arguments from parser's _actions
        snippet_expected_args = {}
        if snippet_parser and hasattr(snippet_parser, "_actions"):
            for action in snippet_parser._actions:
                if hasattr(action, "option_strings") and action.option_strings:
                    for opt_string in action.option_strings:
                        snippet_expected_args[opt_string] = action

        # Cache the result
        self._snippet_args_cache[item_name] = snippet_expected_args
        return snippet_expected_args

    def _validate_snippet_arguments(self, item: Any) -> None:
        """Validate pipeline item arguments against snippet's argparse interface.

        Args:
            item: PipelineItem instance (must be snippet or batch_snippet type)
        """
        if not self.pype_snippets_modules:
            return

        item_name = getattr(item, "name", "unknown")
        step_id = getattr(item, "step_id", None)

        # Check if snippet exists in loaded modules
        if item_name not in self.pype_snippets_modules:
            # Already caught during Pipeline construction, skip
            return

        try:
            snippet_module = self.pype_snippets_modules[item_name]

            # Extract expected arguments from snippet
            snippet_expected_args = self._extract_snippet_arguments(
                snippet_module, item_name
            )

            # Get the argument keys defined in pipeline item
            pipeline_arg_keys = set()
            for argument in item.arguments.arguments:
                if hasattr(argument, "key"):
                    pipeline_arg_keys.add(argument.key)

            # Build set of required arguments
            required_args = set()
            for opt_string, action in snippet_expected_args.items():
                if getattr(action, "required", False):
                    required_args.add(opt_string)

            # Check if pipeline arguments are recognized by snippet
            for pipeline_key in pipeline_arg_keys:
                if pipeline_key not in snippet_expected_args:
                    # Search for the argument within this step's block
                    line = self._get_line_nr(pipeline_key, in_step=step_id)
                    self._add_diagnostic(
                        DiagnosticSeverity.ERROR,
                        line,
                        0,
                        10,
                        f"Argument '{pipeline_key}' in item '{item_name}' not recognized by snippet. "
                        f"Expected arguments: {sorted(snippet_expected_args.keys())}",
                        "unknown-argument",
                    )

            # Check if required arguments are provided
            for req_arg in required_args:
                action = snippet_expected_args[req_arg]
                option_strings = set(action.option_strings)

                # Check if any variant is provided in pipeline
                if not pipeline_arg_keys.intersection(option_strings):
                    # Report at the step's name line
                    line = self._get_line_nr(item_name, context="name:", in_step=step_id)
                    self._add_diagnostic(
                        DiagnosticSeverity.ERROR,
                        line,
                        0,
                        10,
                        f"Required argument missing in item '{item_name}': {option_strings}",
                        "missing-required-argument",
                    )

        except Exception as e:
            line = self._get_line_nr(item_name, context="name:", in_step=step_id)
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                line,
                0,
                10,
                f"Failed to validate arguments for snippet '{item_name}': {e}",
                "snippet-argument-validation-error",
            )

    def _validate_composite_argument(self, argument: Any, item: Any) -> None:
        """Validate a composite argument's internal structure.

        Args:
            argument: CompositeArgument instance
            item: Parent PipelineItem

        Validates:
        - Snippet referenced in composite_arg exists
        - Result key exists in snippet's results() method
        - Nested result_arguments are valid
        """
        from copy import copy

        item_name = getattr(item, "name", "unknown")
        step_id = getattr(item, "step_id", None)
        arg_key = getattr(argument, "key", "unknown")

        if not self.pype_snippets_modules:
            return

        try:
            # Get snippet name and result key from the composite argument definition
            if (
                not hasattr(argument, "argument")
                or "pipeline_arg" not in argument.argument
            ):
                return

            composite_def = argument.argument["pipeline_arg"]
            if not isinstance(composite_def, dict):
                return

            snippet_name = composite_def.get("snippet_name")
            result_key = composite_def.get("result_key")

            if not snippet_name or not result_key:
                return

            # Check if snippet exists in the properly loaded modules
            if snippet_name not in self.pype_snippets_modules:
                # Search within the specific argument block for more accurate line
                line = self._get_line_nr(snippet_name, in_step=step_id, in_arg=arg_key)
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    line,
                    0,
                    10,
                    f"Snippet '{snippet_name}' not found (referenced in composite argument '{arg_key}')",
                    "missing-snippet-composite",
                )
                return

            # Validate that result_key exists by calling results() with mock data
            try:
                # Build minimal mock arguments from result_arguments
                mock_args = {}
                if hasattr(argument, "arguments"):
                    for arg_i in argument.arguments.arguments:
                        arg_info = get_arg_from_string(arg_i.value)
                        if arg_info["arg"]:
                            mock_args[arg_i.key] = arg_info["arg"].upper()

                # Try to get results - this will fail if result_key doesn't exist
                if mock_args:
                    # Use cached results if available
                    cache_key = f"{snippet_name}:{sorted(mock_args.items())}"
                    if cache_key in self._results_cache:
                        results_dict = self._results_cache[cache_key]
                    else:
                        snippet_module = copy(self.pype_snippets_modules[snippet_name])
                        results_dict = snippet_module.results(mock_args)
                        self._results_cache[cache_key] = results_dict

                    if result_key not in results_dict:
                        # Search within the specific argument block
                        line = self._get_line_nr(result_key, in_step=step_id, in_arg=arg_key)
                        self._add_diagnostic(
                            DiagnosticSeverity.ERROR,
                            line,
                            0,
                            10,
                            f"Result key '{result_key}' not found in snippet '{snippet_name}'. "
                            f"Available keys: {list(results_dict.keys())} (in composite argument '{arg_key}')",
                            "invalid-result-key",
                        )

            except SnippetResultsTemplateSobstitutionError as e:
                line = self._get_line_nr(snippet_name, in_step=step_id, in_arg=arg_key)
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    line,
                    0,
                    10,
                    f"Template substitution error in composite argument '{arg_key}': {e}",
                    "snippet-template-error",
                )

            except SnippetResultsArgumentError as e:
                line = self._get_line_nr(snippet_name, in_step=step_id, in_arg=arg_key)
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    line,
                    0,
                    10,
                    f"Argument error in composite argument '{arg_key}': {e}",
                    "snippet-results-error",
                )

            except Exception as e:
                line = self._get_line_nr(snippet_name, in_step=step_id, in_arg=arg_key)
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    line,
                    0,
                    10,
                    f"Failed to parse the composite arguments: {e}",
                    "composite-argument-error",
                )

        except Exception as e:
            line = self._get_line_nr(arg_key, in_step=step_id)
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                line,
                0,
                10,
                f"Error validating composite argument '{arg_key}' in item '{item_name}': {e}",
                "composite-arg-validation-error",
            )

    def validate(self, file_path: Path) -> ValidationResult:
        """Validate a pipeline file.

        Args:
            file_path: Path to the pipeline file to validate

        Returns:
            ValidationResult with diagnostics
        """
        # Reset state for fresh validation
        self.diagnostics = []
        self.file_lines = []
        self.pipeline = None
        self.pype_snippets_modules = None
        self._snippet_args_cache = {}
        self._results_cache = {}

        # Load file for line number lookup
        try:
            self._load_file_lines(file_path)
        except IOError as e:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                0,
                0,
                10,
                f"Failed to read file: {e}",
                "file-read-error",
            )
            return ValidationResult(file_path, "pipeline", self.diagnostics, False)

        # Load pipeline (handles exceptions internally)
        self._load_pipeline(file_path)

        # Validate pipeline items if loaded successfully
        self._validate_pipeline_items()

        is_valid = not any(
            d.severity == DiagnosticSeverity.ERROR for d in self.diagnostics
        )
        return ValidationResult(file_path, "pipeline", self.diagnostics, is_valid)
