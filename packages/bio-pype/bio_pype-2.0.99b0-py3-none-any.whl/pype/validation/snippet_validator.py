"""Snippet validation implementation.

Validates bio_pype Markdown snippets for structural and semantic correctness.
Ports validation logic from VSCode plugin while using bio_pype API for runtime validation.

This module serves as the reference implementation for the validation pattern.
Other validators (profile, pipeline) follow the same structure.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from pype.utils.snippets import ArgumentList, SnippetMd
from pype.validation.context import WorkspaceIndex
from pype.validation.core import (
    Diagnostic,
    DiagnosticSeverity,
    Location,
    ValidationContext,
    ValidationResult,
)
from pype.validation.parsers import (
    CodeChunkHeaderParser,
    IODeclarationParser,
    MarkdownSectionParser,
    VariableTracker,
)
from pype.validation.profile_validator import ProfileValidator

logger = logging.getLogger(__name__)


class SnippetValidator:
    """Validator for bio_pype Markdown snippets.

    Validates:
    - Required sections (description, requirements, results, arguments, snippet)
    - Requirements format (ncpu, time, mem)
    - Arguments structure (sequential numbering, types, options)
    - Code chunk headers and format
    - Variable definitions and usage
    - I/O declarations
    - Namespace references to profiles
    - Runtime validation (attempting to load with SnippetMd)
    """

    # Required sections for all snippets
    REQUIRED_SECTIONS = {
        "description",
        "requirements",
        "results",
        "arguments",
        "snippet",
    }

    # All valid section names (required + optional like "name")
    VALID_SECTIONS = REQUIRED_SECTIONS | {"name"}

    # Valid argument types
    VALID_ARG_TYPES = {"str", "int", "float", "bool"}

    # Valid argument options
    VALID_ARG_OPTIONS = {
        "help",
        "type",
        "required",
        "default",
        "nargs",
        "action",
        "choices",
    }

    # Valid actions for arguments
    VALID_ACTIONS = {"store_true", "store_false"}

    def __init__(self, context: ValidationContext) -> None:
        """Initialize snippet validator.

        Args:
            context: ValidationContext for workspace information
        """
        self.context = context
        self.diagnostics: List[Diagnostic] = []
        self.snippet: Optional[SnippetMd] = None
        self.results_dict: Dict = {}
        self.requirements_dict: Dict = {}
        self.arguments_dict: Dict = {}
        self.arguments_long_names: Set[str] = (
            set()
        )  # Only long names for snippet template validation
        self.friendly_name: str = ""
        self.profile_files_dict: Dict = {}
        self.profile_programs_dict: Dict = {}

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

    def _load_snippet(self, file_path: Path) -> None:
        if self.snippet is None:
            try:
                snippet_name = file_path.stem
                parent = type("TempModule", (), {})()
                self.snippet = SnippetMd(parent, snippet_name, str(file_path))
            except Exception as e:
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    0,
                    0,
                    10,
                    f"Could not create SnippetMd for bio_pype API calls: {e}",
                    "snippet-md-error",
                )
                logger.debug(f"Could not create SnippetMd for bio_pype API calls: {e}")

    def validate(self, file_path: Path) -> ValidationResult:
        """Validate a snippet file.

        Args:
            file_path: Path to the snippet file to validate

        Returns:
            ValidationResult with diagnostics
        """
        # Reset state for fresh validation
        self.diagnostics = []
        self.snippet = None
        self.results_dict = {}
        self.requirements_dict = {}
        self.arguments_dict = {}
        self.arguments_long_names = set()
        self.friendly_name = ""
        self.profile_files_dict = {}
        self.profile_programs_dict = {}

        # Read file content
        try:
            with open(file_path, "r") as f:
                content = f.read()
        except IOError as e:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                0,
                0,
                10,
                f"Failed to read file: {e}",
                "file-read-error",
            )
            return ValidationResult(
                file_path,
                "snippet",
                self.diagnostics,
            )

        # Parse sections
        sections = MarkdownSectionParser.parse_sections(content)

        # Create single SnippetMd instance early for reuse (efficient bio_pype API access)
        self._load_snippet(file_path)

        # 0. Validate section headers (must be before other validation)
        self._validate_section_headers(content)

        # 1. Validate required sections
        self._validate_required_sections(sections)

        # 2. Validate requirements section (use SnippetMd to avoid YAML re-parsing)
        if "requirements" in sections:
            self._validate_requirements(sections["requirements"])

        # 3. Validate arguments section
        if "arguments" in sections:
            self._validate_arguments(sections["arguments"])

        # 4. Validate results section
        if "results" in sections:
            self._validate_results(sections["results"])
        # 4. Validate results section
        if "name" in sections:
            self._validate_name(sections["name"])
        # 5. Validate code chunks
        if "snippet" in sections:
            self._validate_code_chunks(sections["snippet"])

        # 6. Cross-file validation (profiles, pipelines) - must be before variables validation
        # so that profile files are available for I/O declaration validation
        self._validate_cross_references(content, sections)

        # 7. Validate variables and I/O declarations (uses profile_files_dict from step 6)
        self._validate_variables(content, sections)

        available_profiles = [p.stem for p in self.context.profile_paths]

        is_valid = not any(
            d.severity == DiagnosticSeverity.ERROR for d in self.diagnostics
        )
        return ValidationResult(
            file_path,
            "snippet",
            self.diagnostics,
            is_valid,
            parsed_arguments=self.arguments_dict,
            parsed_results=self.results_dict,
            parsed_requirements=self.requirements_dict,
            available_profiles=available_profiles,
            profile_files=self.profile_files_dict,
            profile_programs=self.profile_programs_dict,
            friendly_name=self.friendly_name,
        )

    def _validate_required_sections(self, sections: Dict) -> None:
        """Validate that all required sections are present."""
        for required in self.REQUIRED_SECTIONS:
            if required not in sections:
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    0,
                    0,
                    10,
                    f"Missing required section: ## {required}",
                    f"missing-section-{required}",
                )

    def _validate_section_headers(self, content: str) -> None:
        """Validate that all ## headers are valid section names."""
        in_code_block = False

        for line_num, line in enumerate(content.split("\n")):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block

            if line.startswith("## "):
                section_name = line[3:].strip().lower()
                if in_code_block:
                    self._add_diagnostic(
                        DiagnosticSeverity.ERROR,
                        line_num,
                        0,
                        len(line),
                        f"Invalid '## {section_name}' inside code block. Double hashes break chunk parsing - everything after this line is lost. Use '#' for comments instead.",
                        "invalid-section-in-code",
                    )
                elif section_name and section_name not in self.VALID_SECTIONS:
                    self._add_diagnostic(
                        DiagnosticSeverity.ERROR,
                        line_num,
                        0,
                        len(line),
                        f"Invalid section header: '## {section_name}'. Valid sections are: {', '.join(sorted(self.VALID_SECTIONS))}",
                        "invalid-section-header",
                    )

    def _validate_requirements(self, section) -> None:
        """Validate requirements section using SnippetMd API."""
        required_fields = {"ncpu", "time", "mem"}
        try:
            reqs = self.snippet.requirements()
            if not isinstance(reqs, dict):
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    section.start_line,
                    0,
                    10,
                    "Requirements must be a YAML object (key: value pairs)",
                    "invalid-requirements-format",
                )
                return

            for field in required_fields:
                if field not in reqs:
                    self._add_diagnostic(
                        DiagnosticSeverity.ERROR,
                        section.start_line,
                        0,
                        10,
                        f"Missing required field in requirements: {field}",
                        f"missing-requirement-{field}",
                    )
            self.requirements_dict = reqs

        except Exception as e:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                section.start_line,
                0,
                10,
                f"Failed to parse requirements: {e}",
                "requirements-parse-error",
            )

    def _validate_results(self, section) -> None:
        """Validate results section.

        Should contain a code chunk with header: @interpreter, parser_format

        Args:
            section: ParsedSection object
        """
        content = section.content.strip()

        if not content:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                section.start_line,
                0,
                10,
                "Results section cannot be empty",
                "empty-results-section",
            )
            return

        # Look for code chunk
        if "```" not in content:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                section.start_line,
                0,
                10,
                "Results section must contain a code chunk (``` ... ```)",
                "missing-results-code-chunk",
            )
            return

        # Extract header (first line after ```)
        lines = content.split("\n")
        header_line = None
        for i, line in enumerate(lines):
            if line.startswith("```"):
                if i + 1 < len(lines):
                    header_line = lines[i + 1]
                break

        if not header_line or not header_line.startswith("@"):
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                section.start_line,
                0,
                10,
                "Results code chunk must have header: @interpreter, parser_format",
                "missing-results-header",
            )

        # Parse and validate header
        header_info = CodeChunkHeaderParser.parse_results_chunk_header(header_line)
        if not header_info["is_valid"]:
            for error in header_info["errors"]:
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    section.start_line,
                    0,
                    50,
                    f"Invalid results chunk header: {error}",
                    "invalid-results-header",
                )
        try:
            # Extract argument names from snippet's arguments using ArgumentList
            dummy_args = {}
            # Create dummy values using UPPERCASE argument names
            # This ensures results chunk runs with meaningful values
            for arg_name in self.arguments_dict.keys():
                arg_name = arg_name.strip()
                if arg_name:
                    dummy_args[arg_name] = arg_name.upper()
            # Call results() method to get the dictionary
            self.results_dict = self.snippet.results(dummy_args)
            if not isinstance(self.results_dict, dict):
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    section.start_line,
                    0,
                    10,
                    "Results output are not a valid dictionary",
                    "invalid-results-output",
                )
        except FileNotFoundError:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                section.start_line,
                0,
                10,
                "Results chunk could not execute.\n"
                "Check for shebang line or syntax errors in the code.",
                "missing-results-output",
            )
        except KeyError:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                section.start_line,
                0,
                10,
                "Results chunk could not execute.\n"
                "There are no corresponding arguments to replace in the chunk",
                "wrong-results-argument",
            )
        except Exception as e:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                section.start_line,
                0,
                10,
                "Results chunk could not execute.\nOr has an empty output",
                "results-chunk-error",
            )

    def _validate_name(self, section) -> None:
        """Validate name optional section.

        Should contain a code chunk with header: @interpreter

        Args:
            section: ParsedSection object
        """
        content = section.content.strip()

        if not content:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                section.start_line,
                0,
                10,
                "Name section, if included, cannot be empty",
                "empty-name-section",
            )
            return

        # Look for code chunk
        if "```" not in content:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                section.start_line,
                0,
                10,
                "Name section, if included, must contain a code chunk (``` ... ```)",
                "missing-name-code-chunk",
            )
            return

        # Extract header (first line after ```)
        lines = content.split("\n")
        header_line = None
        for i, line in enumerate(lines):
            if line.startswith("```"):
                if i + 1 < len(lines):
                    header_line = lines[i + 1]
                break

        if not header_line or not header_line.startswith("@"):
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                section.start_line,
                0,
                10,
                "Name code chunk, if included, must have header: @interpretert",
                "missing-name-header",
            )

        # Parse and validate header
        header_info = CodeChunkHeaderParser.parse_name_chunk_header(header_line)
        if not header_info["is_valid"]:
            for error in header_info["errors"]:
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    section.start_line,
                    0,
                    50,
                    f"Invalid name chunk header: {error}",
                    "invalid-name-header",
                )
        try:
            # Extract argument names from snippet's arguments using ArgumentList
            dummy_args = {}
            # Create dummy values using UPPERCASE argument names
            # This ensures results chunk runs with meaningful values
            for arg_name in self.arguments_dict.keys():
                arg_name = arg_name.strip()
                if arg_name:
                    dummy_args[arg_name] = arg_name.upper()
            # Call results() method to get the dictionary
            self.friendly_name = self.snippet.friendly_name(dummy_args)
            if not isinstance(self.friendly_name, str):
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    section.start_line,
                    0,
                    10,
                    "Name output must be a string",
                    "invalid-name-output",
                )
        except FileNotFoundError:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                section.start_line,
                0,
                10,
                "Name chunk could not execute.\n"
                "Check for shebang line or syntax errors in the code.",
                "missing-name-output",
            )
        except KeyError:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                section.start_line,
                0,
                10,
                "Name chunk could not execute.\n"
                "There are no corresponding arguments to replace in the chunk",
                "wrong-name-argument",
            )

    def _validate_arguments(self, section) -> None:
        """Validate arguments section using bio_pype ArgumentList.

        Args should be numbered sequentially (1, 2, 3, ...) with:
        - argument: name
        - help: description (required)
        - type: str/int/float/bool (required)
        - required: true/false (optional)
        - default: value (optional)
        - nargs: * + ? number (optional)
        - action: store_true/store_false (optional)
        - choices: comma/space separated list (optional)

        Args:
            section: ParsedSection object
        """
        content = section.content.strip()

        try:
            # Use ArgumentList from bio_pype API (same parser as snippet execution)
            arg_list = ArgumentList("snippet", content)
            arguments = arg_list.arguments

            # Validate sequential numbering (ArgumentList is 0-indexed)
            for i, arg_dict in enumerate(arguments):
                expected = i + 1
                if expected > len(arguments):
                    break
                # Note: ArgumentList doesn't track numbers, so we assume sequential parsing
                # Convert to our format for validation
                arg_num_data = {
                    "number": i + 1,
                    "names": arg_dict.get("argument", "").split("/"),
                    "line": section.start_line + i,  # Approximate line number
                    "options": arg_dict.get("options", {}),
                }
                self._validate_argument(arg_num_data)
                help_text = arg_dict.get("options", {}).get("help", "")
                # Extract all argument name variants (e.g., "bam/b" -> ["bam", "b"])
                # Both long and short versions go into arguments_dict for pipeline use
                arg_names = arg_dict.get("argument", "").split("/")
                for name in arg_names:
                    name = name.strip()
                    if name:
                        self.arguments_dict[name] = help_text
                # But only long version (first) is valid for snippet template replacement
                # e.g., "bam/b" -> only "bam" is valid in %(bam)s, not %(b)s
                if arg_names:
                    long_name = arg_names[0].strip()
                    if long_name:
                        self.arguments_long_names.add(long_name)

        except Exception as e:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                0,
                0,
                50,
                f"Arguments section can't be properly parsed {e}",
                "error-argument-parsing",
            )
            logger.debug(f"Could not validate arguments using ArgumentList: {e}")

    def _validate_argument(self, arg: Dict) -> None:
        """Validate a single argument.

        Args:
            arg: Argument dict with keys: number, names, line, options
        """
        options = arg.get("options", {})

        # Check required fields
        if "help" not in options:
            self._add_diagnostic(
                DiagnosticSeverity.WARNING,
                arg["line"],
                0,
                50,
                f"Argument '{arg['names'][0]}' missing 'help' field",
                "missing-argument-help",
            )

        if "type" not in options:
            if "action" not in options:
                self._add_diagnostic(
                    DiagnosticSeverity.WARNING,
                    arg["line"],
                    0,
                    50,
                    f"Argument '{arg['names'][0]}' missing 'type' field",
                    "missing-argument-type",
                )
        else:
            arg_type = options["type"]
            if arg_type not in self.VALID_ARG_TYPES:
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    arg["line"],
                    0,
                    50,
                    f"Invalid type '{arg_type}' for argument '{arg['names'][0]}'. "
                    f"Must be one of: {', '.join(self.VALID_ARG_TYPES)}",
                    "invalid-argument-type",
                )

        # Validate option names
        for opt_key in options.keys():
            if opt_key not in self.VALID_ARG_OPTIONS:
                self._add_diagnostic(
                    DiagnosticSeverity.WARNING,
                    arg["line"],
                    0,
                    50,
                    f"Unknown option '{opt_key}' for argument '{arg['names'][0]}'",
                    "unknown-argument-option",
                )

        # Validate action if present
        if "action" in options:
            action = options["action"]
            if action not in self.VALID_ACTIONS:
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    arg["line"],
                    0,
                    50,
                    f"Invalid action '{action}'. Must be one of: {', '.join(self.VALID_ACTIONS)}",
                    "invalid-argument-action",
                )

        # Validate required field
        if "required" in options:
            req_val = options["required"].lower()
            if req_val not in ("true", "false"):
                self._add_diagnostic(
                    DiagnosticSeverity.ERROR,
                    arg["line"],
                    0,
                    50,
                    f"Invalid 'required' value: '{options['required']}'. Must be 'true' or 'false'",
                    "invalid-required-value",
                )

    def _validate_code_chunks(self, section) -> None:
        """Validate code chunks in snippet section."""
        content = section.content.strip()

        if "```" not in content:
            self._add_diagnostic(
                DiagnosticSeverity.ERROR,
                section.start_line,
                0,
                10,
                "Snippet section must contain at least one code chunk",
                "missing-snippet-chunks",
            )
            return

        # Parse code chunks inline
        chunks = []
        lines = content.split("\n")
        in_chunk = False
        chunk_start = 0
        chunk_header = ""
        chunk_code = []

        for i, line in enumerate(lines):
            if line.startswith("```") and not in_chunk:
                in_chunk = True
                chunk_start = i
                chunk_header = ""
                chunk_code = []
            elif line.startswith("```") and in_chunk:
                in_chunk = False
                chunks.append(
                    {
                        "header": chunk_header,
                        "code": "\n".join(chunk_code),
                        "start_line": chunk_start,
                        "end_line": i,
                    }
                )
            elif in_chunk and chunk_header == "":
                chunk_header = line
            elif in_chunk:
                chunk_code.append(line)

        # Validate chunks
        for chunk in chunks:
            header_info = CodeChunkHeaderParser.parse_snippet_chunk_header(
                chunk["header"]
            )
            if not header_info["is_valid"]:
                for error in header_info["errors"]:
                    self._add_diagnostic(
                        DiagnosticSeverity.ERROR,
                        chunk["start_line"] + section.start_line,
                        0,
                        50,
                        f"Invalid snippet chunk header: {error}",
                        "invalid-chunk-header",
                    )

    def _validate_variables(self, content: str, sections: Dict) -> None:
        """Validate variable definitions and usage.

        Args:
            content: Full file content
            sections: Parsed sections
        """
        # Find all variables used in content
        used_variables = VariableTracker.find_variables(content)

        # Find defined variables (from arguments section)
        # Use only long argument names for snippet template validation
        defined_variables = set(self.arguments_long_names)

        # Check for undefined variables
        for var_name, var_info in used_variables.items():
            # Special handling for profile variables
            if var_name.startswith("profile_"):
                # Profile variables are ok as long as profile is loaded
                pass
            # Special handling for results variables
            elif var_name.startswith("results_"):
                # Validate that the results variable key exists in extracted results
                key = var_name[len("results_") :]
                if key not in self.results_dict.keys():
                    for loc in var_info.locations:
                        available = (
                            ", ".join(sorted(self.results_dict.keys()))
                            if self.results_dict
                            else "none"
                        )
                        self._add_diagnostic(
                            DiagnosticSeverity.ERROR,
                            loc.line,
                            loc.start_char,
                            loc.end_char,
                            f"Undefined results variable '{var_name}'. Available results variables: {available}",
                            "undefined-results-variable",
                        )

            # Special handling for requirements variables
            elif var_name.startswith("requirements_"):
                # Validate that the requirements variable key exists in extracted requirements
                key = var_name[len("requirements_") :]
                if key not in self.requirements_dict.keys():
                    for loc in var_info.locations:
                        available = (
                            ", ".join(sorted(self.requirements_dict.keys()))
                            if self.requirements_dict
                            else "none"
                        )
                        self._add_diagnostic(
                            DiagnosticSeverity.ERROR,
                            loc.line,
                            loc.start_char,
                            loc.end_char,
                            f"Undefined results requirements variable '{var_name}'. Available requirements variables: {available}",
                            "undefined-requirements-variable",
                        )

            # Regular argument variables
            elif var_name not in defined_variables:
                for loc in var_info.locations:
                    self._add_diagnostic(
                        DiagnosticSeverity.ERROR,
                        loc.line,
                        loc.start_char,
                        loc.end_char,
                        f"Undefined variable '{var_name}', Available variables: {', '.join(defined_variables)}",
                        "undefined-variable",
                    )

        # Validate I/O declarations
        if "snippet" in sections:
            self._validate_io_declarations(
                sections["snippet"].content, defined_variables, sections["snippet"]
            )

    def _validate_cross_references(self, content: str, sections: Dict) -> None:
        """Validate cross-references to profiles (namespaces and profile variables).

        Args:
            content: Full file content
            sections: Parsed sections
        """

        workspace_index = WorkspaceIndex(self.context)

        # Extract @profile directive inline
        profile_directive = None
        pattern = r"#\s+@profile\s*:?\s*(\w+)"
        for line in content.split("\n"):
            match = re.search(pattern, line)
            if match:
                profile_directive = match.group(1)
                break

        # Determine which profile to use
        profile_name = profile_directive
        if not profile_name:
            available_profiles = workspace_index.all_profile_names()
            if not available_profiles:
                return
            profile_name = sorted(available_profiles)[0]

        # Load the profile
        profile_path = workspace_index.get_profile_path(profile_name)
        if not profile_path:
            if profile_directive:
                self._add_diagnostic(
                    DiagnosticSeverity.WARNING,
                    0,
                    0,
                    10,
                    f"Profile '{profile_directive}' not found in workspace",
                    "missing-profile-directive",
                )
            return

        # Load profile and extract data
        profile_validator = ProfileValidator(self.context)
        profile, profile_diagnostics = profile_validator.load_profile(profile_path)

        # Reset the error position in the profile_diagnostics
        for diag_indx, profile_diagnostic in enumerate(profile_diagnostics):
            profile_diagnostic.location = Location(0, 0, 10)
            profile_diagnostics[diag_indx] = profile_diagnostic

        self.diagnostics.extend(profile_diagnostics)
        self.profile_files_dict = profile_validator.extract_profile_files(profile_path)
        self.profile_programs_dict = profile_validator.extract_profile_programs(
            profile_path
        )

        if not profile:
            return

        # Validate namespace references in code chunks
        if "snippet" in sections:
            self._validate_namespace_references(
                sections["snippet"], sections["snippet"].content
            )
        # Validate profile variables

        self._validate_profile_variable_usage(content)

    def _validate_namespace_references(self, section, snippet_content: str) -> None:
        """Validate that namespace references exist in profile.

        Args:
            section: ParsedSection object
            snippet_content: Content of snippet section
        """

        available_programs = set(self.profile_programs_dict.keys())

        if not available_programs:
            return

        # Find all code chunks with namespace options
        lines = snippet_content.split("\n")
        for line_num, line in enumerate(lines):
            if line.startswith("@") and "namespace=" in line:
                # Parse namespace reference
                match = re.search(r"namespace=([\w-]+)", line)
                if match:
                    namespace_ref = match.group(1)
                    if namespace_ref not in available_programs:
                        self._add_diagnostic(
                            DiagnosticSeverity.ERROR,
                            section.start_line + line_num,
                            0,
                            50,
                            f"Namespace reference '{namespace_ref}' not found in profile. "
                            f"Available programs: {', '.join(sorted(available_programs))}",
                            "missing-namespace-reference",
                        )

    def _validate_profile_variable_usage(self, content: str) -> None:
        """Validate that profile_ variables reference existing profile files.

        Args:
            content: Full file content
            available_profile_files: Set of available file variable names from profile
        """
        available_profile_files = set(self.profile_files_dict.keys())

        # Find all profile_ variables
        profile_var_pattern = re.compile(r"%\(profile_(\w+)\)[sif]")

        for line_num, line in enumerate(content.split("\n")):
            for match in profile_var_pattern.finditer(line):
                file_key = match.group(1)
                if file_key not in available_profile_files:
                    self._add_diagnostic(
                        DiagnosticSeverity.ERROR,
                        line_num,
                        match.start(),
                        match.end(),
                        f"Profile file variable 'profile_{file_key}' not found in profile. "
                        f"Available files: {', '.join(sorted(available_profile_files))}",
                        "missing-profile-variable",
                    )

    def _validate_io_declarations(
        self, snippet_content: str, defined_variables: Set[str], section
    ) -> None:
        """Validate I/O declarations against defined variables.

        Args:
            snippet_content: Content of snippet section
            defined_variables: Set of defined argument variables
            section: ParsedSection object containing start_line offset
        """

        # Parse I/O declarations
        input_vars, output_vars = IODeclarationParser.parse_io_declarations(
            snippet_content
        )

        # Convert to list and add profile variables
        defined_vars_list = list(defined_variables)
        defined_vars_list.extend(
            f"profile_{var}" for var in self.profile_files_dict.keys()
        )

        # Find line numbers for I/O declarations to report accurate errors
        lines = snippet_content.split("\n")
        input_pattern = re.compile(r"_input_\s*:\s*(.+)")
        output_pattern = re.compile(r"_output_\s*:\s*(.+)")

        # Validate input variables with correct line numbers
        for line_num, line in enumerate(lines):
            match = input_pattern.search(line)
            if match:
                vars_str = match.group(1)
                for var in vars_str.split():
                    # Remove wildcards (*, ~, ..)
                    clean_var = var.rstrip("*~.")
                    if clean_var and clean_var not in defined_vars_list:
                        self._add_diagnostic(
                            DiagnosticSeverity.ERROR,
                            line_num + section.start_line + 1,
                            match.start(1),
                            match.end(1),
                            f"I/O declaration references undefined input variable '{clean_var}'. "
                            f"Available variables: {', '.join(sorted(defined_vars_list))}",
                            "missing-input-variable",
                        )

        # Validate output variables with correct line numbers
        for line_num, line in enumerate(lines):
            match = output_pattern.search(line)
            if match:
                vars_str = match.group(1)
                for var in vars_str.split():
                    # Remove wildcards (*, ~, ..)
                    clean_var = var.rstrip("*~.")
                    if clean_var and clean_var not in defined_vars_list:
                        self._add_diagnostic(
                            DiagnosticSeverity.ERROR,
                            line_num + section.start_line + 1,
                            match.start(1),
                            match.end(1),
                            f"I/O declaration references undefined output variable '{clean_var}'. "
                            f"Available variables: {', '.join(sorted(defined_vars_list))}",
                            "missing-output-variable",
                        )
