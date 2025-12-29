"""Autocomplete handler for LSP server.

Provides intelligent code completion for snippets, profiles, variables, and arguments.
"""

import logging
import re
from ast import Return
from pathlib import Path
from typing import List, Optional

from lsprotocol import types

from pype.utils.snippets import SnippetMd
from pype.validation import (
    PipelineValidator,
    SnippetValidator,
    detect_module_root,
    discover_modules,
)

logger = logging.getLogger("bio_pype_lsp.completion")


class CompletionHandler:
    """Manages code completion suggestions."""

    def __init__(self, server):
        """Initialize completion handler.

        Args:
            server: BioPypeLspServer instance
        """
        self.server = server

    def get_completions(
        self, uri: str, position: types.Position
    ) -> Optional[types.CompletionList]:
        """Get completion suggestions at a specific position.

        Args:
            uri: Document URI (file:// format)
            position: Position in document (line, character)

        Returns:
            CompletionList with suggestions or None
        """
        try:
            file_path = Path(uri.replace("file://", ""))
            logger.info(
                f"Completion requested at {file_path.name}:{position.line}:{position.character}"
            )

            # Get file content from workspace
            try:
                text_document = self.server.workspace.get_text_document(uri)
                content = text_document.source
            except Exception as e:
                logger.debug(f"Could not get text document from workspace: {e}")
                # Fall back to disk
                if file_path.exists():
                    content = file_path.read_text()
                else:
                    logger.debug(f"File not found: {file_path}")
                    return None

            # Auto-detect module root and get validation context (like diagnostics does)

            workspace_root = detect_module_root(file_path)
            if not workspace_root:
                # Fallback: same as diagnostics
                workspace_root = file_path.parent.parent.parent
                logger.debug(f"Using fallback workspace root: {workspace_root}")
            else:
                logger.debug(f"Auto-detected module root: {workspace_root}")

            # Check validation context cache first to avoid repeated module discovery
            if workspace_root in self.server.validation_context_cache:
                validation_context = self.server.validation_context_cache[
                    workspace_root
                ]
                logger.debug(f"Using cached validation context for {workspace_root}")
            else:
                validation_context = discover_modules(workspace_root)
                self.server.validation_context_cache[workspace_root] = (
                    validation_context
                )
                logger.debug(f"Discovered and cached modules for {workspace_root}")

            logger.debug(
                f"Completion context: {len(validation_context.snippet_paths)} snippets, {len(validation_context.profile_paths)} profiles, {len(validation_context.pipeline_paths)} pipelines"
            )

            lines = content.split("\n")

            # Get appropriate completions based on file type
            if file_path.suffix == ".md":
                # Check cache first - only validate if not already cached
                if uri not in self.server.validation_cache:
                    validation_result = SnippetValidator(validation_context).validate(
                        file_path
                    )
                    self.server.validation_cache[uri] = validation_result
                    logger.debug(f"Validated and cached snippet: {file_path.name}")
                else:
                    logger.debug(
                        f"Using cached validation for snippet: {file_path.name}"
                    )

                return self._get_snippet_completions(
                    lines, position, validation_context, file_path
                )
            elif file_path.suffix in [".yaml"]:
                # Check cache first - only validate if not already cached
                if uri not in self.server.validation_cache:
                    validation_result = PipelineValidator(
                        validation_context,
                        server_caches={
                            "snippet_modules": self.server.snippet_modules_cache,
                            "snippet_args": self.server.snippet_args_cache,
                        },
                    ).validate(file_path)
                    self.server.validation_cache[uri] = validation_result
                    logger.debug(f"Validated and cached pipeline: {file_path.name}")
                else:
                    logger.debug(
                        f"Using cached validation for pipeline: {file_path.name}"
                    )

                return self._get_yaml_completions(
                    lines, position, validation_context, file_path
                )

        except Exception as e:
            logger.error(f"Error getting completions for {uri}: {e}", exc_info=True)

        return None

    def _get_snippet_completions(
        self,
        lines: List[str],
        position: types.Position,
        validation_context,
        file_path: Path,
    ) -> Optional[types.CompletionList]:
        """Get completions for snippet (.md) files.

        Args:
            lines: File lines
            position: Cursor position
            validation_context: ValidationContext with available snippets/profiles
            file_path: Path to the snippet file being edited

        Returns:
            CompletionList with variable or profile suggestions
        """
        try:
            line_num = position.line
            if line_num >= len(lines):
                logger.debug(f"Line {line_num} beyond file length {len(lines)}")
                return None

            line = lines[line_num]
            char_pos = position.character
            logger.debug(f"Snippet completion: line='{line}' char_pos={char_pos}")

            # Check if we're inside a %(...)s pattern (variables)
            if "%" in line:
                # Find which %(...)s pattern the cursor is inside of
                # Look for all %( patterns and check which one we're currently inside
                matches = list(re.finditer(r"%\((\w*?)(?:\)s)?", line))
                current_match = None

                for match in matches:
                    # Check if cursor is within this %(... pattern
                    # Find the closing )s or assume it continues to the next pattern/end
                    start = match.start()
                    # Look for closing )s after the match
                    closing = line.find(")s", match.end())
                    if closing == -1:
                        closing = len(line)  # No closing found, assume open pattern
                    else:
                        closing += 2  # Include the )s

                    if start <= char_pos <= closing:
                        current_match = match
                        break

                if current_match:
                    prefix = current_match.group(1)
                    suggestions = self._get_variable_completions(
                        prefix,
                        snippet_path=file_path,
                    )
                    logger.info(
                        f"Returning {len(suggestions)} variable completions for prefix '{prefix}'"
                    )
                    return types.CompletionList(is_incomplete=False, items=suggestions)

                # Also check if cursor is right after %(
                if line[:char_pos].rstrip().endswith("%("):
                    suggestions = self._get_variable_completions(
                        "",
                        snippet_path=file_path,
                    )  # Show all variables
                    logger.info(
                        f"Cursor after %(, returning {len(suggestions)} variable completions"
                    )
                    return types.CompletionList(is_incomplete=False, items=suggestions)

            # Check if we're inside an _input_ or _output_ declaration
            if "_input_:" in line or "_output_:" in line:
                # Extract what's being typed after _input_: or _output_:
                input_match = re.search(r"_input_:\s+(.*)$", line[:char_pos])
                output_match = re.search(r"_output_:\s+(.*)$", line[:char_pos])

                if input_match or output_match:
                    # Get the partial word being typed
                    partial_text = (input_match or output_match).group(1)
                    # Get the last word being typed (after the last space)
                    prefix = partial_text.split()[-1] if partial_text else ""

                    suggestions = self._get_io_variable_completions(
                        prefix,
                        snippet_path=file_path,
                    )
                    logger.info(
                        f"Returning {len(suggestions)} I/O variable completions for prefix '{prefix}'"
                    )
                    return types.CompletionList(is_incomplete=False, items=suggestions)

            # Check if we're inside a namespace= pattern in code chunk header
            if "namespace=" in line and line.lstrip().startswith("@"):
                # Code chunk header with namespace parameter - match namespace=word
                match = re.search(r"namespace=(\w*)", line[:char_pos])
                if match:
                    prefix = match.group(1)
                    suggestions = self._get_namespace_completions(
                        prefix,
                        snippet_path=file_path,
                    )
                    logger.info(
                        f"Returning {len(suggestions)} namespace completions for prefix '{prefix}'"
                    )
                    return types.CompletionList(is_incomplete=False, items=suggestions)

                # Also check if cursor is right after namespace=
                if line[:char_pos].rstrip().endswith("namespace="):
                    suggestions = self._get_namespace_completions(
                        "",
                        snippet_path=file_path,
                    )  # Show all namespaces
                    logger.info(
                        f"Cursor after namespace=, returning {len(suggestions)} namespace completions"
                    )
                    return types.CompletionList(is_incomplete=False, items=suggestions)

            # Check if we're inside a @profile pattern
            if "@" in line:
                # Find the profile pattern context - match @word (without $ anchor to work mid-typing)
                match = re.search(r"@(\w*)", line[:char_pos])
                if match:
                    # User is typing a profile name
                    prefix = match.group(1)
                    suggestions = self._get_profile_name_completions(
                        line, char_pos, validation_context
                    )
                    logger.info(
                        f"Returning {len(suggestions)} profile completions for prefix '{prefix}'"
                    )
                    return types.CompletionList(is_incomplete=False, items=suggestions)

                # Also check if cursor is right after @
                if line[:char_pos].rstrip().endswith("@"):
                    suggestions = self._get_profile_name_completions(
                        line, char_pos, validation_context
                    )
                    logger.info(
                        f"Cursor after @, returning {len(suggestions)} profile completions"
                    )
                    return types.CompletionList(is_incomplete=False, items=suggestions)

        except Exception as e:
            logger.debug(f"Error getting snippet completions: {e}")

        return None

    def _get_yaml_completions(
        self,
        lines: List[str],
        position: types.Position,
        validation_context,
        file_path: Path,
    ) -> Optional[types.CompletionList]:
        """Get completions for YAML files (profiles/pipelines).

        Args:
            lines: File lines
            position: Cursor position
            validation_context: ValidationContext with available snippets/profiles
            file_path: Path to the YAML file being edited

        Returns:
            CompletionList with appropriate suggestions
        """
        try:
            line_num = position.line
            if line_num >= len(lines):
                logger.debug(f"YAML: Line {line_num} beyond file length {len(lines)}")
                return None

            line = lines[line_num]
            char_pos = position.character
            logger.debug(f"YAML completion: line='{line}' char_pos={char_pos}")

            # Detect context from current line and surrounding context
            context = self._detect_yaml_context(lines, line_num)
            logger.debug(f"YAML context detected: {context}")

            if context == "snippet_name":
                # Completing snippet names in pipeline
                suggestions = self._get_snippet_name_completions(
                    line, char_pos, validation_context, file_path=file_path
                )
                return types.CompletionList(is_incomplete=False, items=suggestions)

            elif context == "profile_name":
                # Completing profile names
                suggestions = self._get_profile_name_completions(
                    line, char_pos, validation_context
                )
                return types.CompletionList(is_incomplete=False, items=suggestions)

            elif context == "variable":
                # Completing variables in %(...)s patterns
                suggestions = self._get_variable_completions_for_yaml(
                    lines,
                    line_num,
                    char_pos,
                    validation_context=validation_context,
                    file_path=file_path,
                )
                return types.CompletionList(is_incomplete=False, items=suggestions)

            elif context == "argument_key":
                # Completing argument keys (prefixes like -i, -o, etc)
                # This would need snippet context parsing
                pass

        except Exception as e:
            logger.debug(f"Error getting YAML completions: {e}")

        return None

    def _detect_yaml_context(self, lines: List[str], line_num: int) -> Optional[str]:
        """Detect what kind of completion is needed based on context.

        Args:
            lines: File lines
            line_num: Current line number

        Returns:
            Context type: 'snippet_name', 'profile_name', 'variable', 'argument_key', etc
        """
        if line_num >= len(lines):
            return None

        line = lines[line_num]

        is_argument_line = line.strip().startswith("-")

        # Check if we're completing variables
        if "%" in line and "(" in line and is_argument_line:
            return "variable"
        # Check if we're completing snippet names
        # Either in pipeline items (name:) or in composite arguments (snippet_name:)
        elif "snippet_name:" in line:
            return "snippet_name"
        # For pipeline items, check if "name:" is in the line and we're under a "steps:" section
        elif "name:" in line and "steps:" in "".join(lines[:line_num]):
            return "snippet_name"

        # Check if in arguments section
        if "arguments:" in line or (
            line_num > 0 and "arguments:" in lines[line_num - 1]
        ):
            return "argument_key"

        # Check for profile section (simplified)
        content = "".join(lines)
        if "programs:" in content or "files:" in content:
            # Likely a profile file
            if "namespace:" in line or "version:" in line:
                return "profile_name"

        return None

    def _get_snippet_name_completions(
        self,
        line: str,
        char_pos: int,
        validation_context,
        file_path: Optional[Path] = None,
    ) -> List[types.CompletionItem]:
        """Get completion suggestions for snippet names.

        Handles both:
        - Pipeline items: name: snippet_name
        - Composite arguments: snippet_name: snippet_name

        Args:
            line: Current line
            char_pos: Character position in line
            validation_context: ValidationContext with available snippets
            file_path: Path to the YAML file being edited (for cache lookup)

        Returns:
            List of CompletionItem objects
        """
        suggestions = []

        # Extract what the user has typed so far
        # Handle both "name:" and "snippet_name:" patterns
        prefix_match = re.search(r"(?:name|snippet_name):\s*(\w*)$", line[:char_pos])
        if prefix_match:
            prefix = prefix_match.group(1).lower()

            # Try to get snippets from validation cache first
            available_snippets = {}
            if file_path:
                try:
                    uri = f"file://{file_path}"
                    if uri in self.server.validation_cache:
                        result = self.server.validation_cache[uri]
                        if (
                            hasattr(result, "available_snippets")
                            and result.available_snippets
                        ):
                            available_snippets = result.available_snippets
                            logger.debug(
                                f"Using {len(available_snippets)} snippets from validation cache"
                            )
                except Exception as e:
                    logger.debug(f"Could not get snippets from validation cache: {e}")

            # If cache is empty, fall back to filesystem paths
            if not available_snippets:
                return suggestions

            # Create completion items
            for snippet_name, description in available_snippets.items():
                if snippet_name.lower().startswith(prefix):
                    suggestions.append(
                        types.CompletionItem(
                            label=snippet_name,
                            kind=types.CompletionItemKind.Function,
                            detail=description,
                        )
                    )

        return suggestions

    def _get_profile_name_completions(
        self, line: str, char_pos: int, validation_context
    ) -> List[types.CompletionItem]:
        """Get completion suggestions for profile names.

        Args:
            line: Current line
            char_pos: Character position in line
            validation_context: ValidationContext with available profiles

        Returns:
            List of CompletionItem objects
        """
        suggestions = []

        # Extract what the user has typed
        prefix_match = re.search(r"@(\w*)$", line[:char_pos])

        if prefix_match:
            prefix = prefix_match.group(1).lower()

            # Get all available profiles
            for profile_path in validation_context.profile_paths:
                profile_name = profile_path.stem
                if profile_name.lower().startswith(prefix):
                    suggestions.append(
                        types.CompletionItem(
                            label=profile_name,
                            kind=types.CompletionItemKind.Variable,
                            detail="Profile",
                        )
                    )

        return suggestions

    def _get_namespace_completions(
        self, prefix: str, snippet_path=None
    ) -> List[types.CompletionItem]:
        """Get completion suggestions for namespace= parameter in code chunk headers.

        Args:
            prefix: Partial namespace name being typed
            snippet_path: Path to current snippet file (to get available namespaces)

        Returns:
            List of CompletionItem objects
        """
        suggestions = []

        # If we have a snippet path, get available namespaces from the validator
        if snippet_path and snippet_path.exists():
            uri = self.server.path_to_uri(snippet_path)
            if uri not in self.server.validation_cache:
                return suggestions

            try:
                # Run validator to get parsed data including profile_programs_dict

                result = self.server.validation_cache[uri]

                # Get available programs (namespaces) from the profile
                # profile_programs is Dict[str, str] where keys are program names
                # and values are namespace strings (e.g., "command-line-args")
                if result.profile_programs:
                    for (
                        program_name,
                        namespace_string,
                    ) in result.profile_programs.items():
                        if program_name.lower().startswith(prefix.lower()):
                            suggestions.append(
                                types.CompletionItem(
                                    label=program_name,
                                    kind=types.CompletionItemKind.Value,
                                    detail=f"Namespace: {namespace_string}",
                                    documentation=f"Program: {program_name}\nNamespace: {namespace_string}",
                                )
                            )

                    logger.debug(
                        f"Extracted {len(suggestions)} namespace suggestions from profile for {snippet_path.name}"
                    )
            except Exception as e:
                logger.debug(f"Could not get namespaces from validator: {e}")

        return suggestions

    def _get_io_variable_completions(
        self, prefix: str, snippet_path=None
    ) -> List[types.CompletionItem]:
        """Get completion suggestions for variables in _input_ and _output_ declarations.

        Args:
            prefix: Partial variable name being typed
            validation_context: ValidationContext for looking up snippets
            snippet_path: Path to current snippet file (to get available I/O variables)

        Returns:
            List of CompletionItem objects
        """
        suggestions = []
        variables = {}

        # If we have a snippet path, get available variables from the validator
        if snippet_path and snippet_path.exists():
            uri = self.server.path_to_uri(snippet_path)
            if uri not in self.server.validation_cache:
                return suggestions
            try:
                # Run validator to get parsed data
                result = self.server.validation_cache[uri]
                # Valid variables for I/O declarations are:
                # 1. All argument names (long names only)
                for arg_name, help_text in result.parsed_arguments.items():
                    variables[arg_name] = f"Argument: {help_text}"

                # 2. Profile variables (profile_<key> for each file in profile)
                for profile_key, profile_value in result.profile_files.items():
                    variables[f"profile_{profile_key}"] = f"Profile: {profile_value}"

                logger.debug(
                    f"Extracted {len(variables)} I/O variables from validator for {snippet_path.name}"
                )
            except Exception as e:
                logger.debug(f"Could not get I/O variables from validator: {e}")

        # Filter by prefix and create completion items
        for var_name, description in variables.items():
            if var_name.lower().startswith(prefix.lower()):
                suggestions.append(
                    types.CompletionItem(
                        label=var_name,
                        kind=types.CompletionItemKind.Variable,
                        detail=description,
                    )
                )

        return suggestions

    def _get_variable_completions(
        self, prefix: str, snippet_path=None
    ) -> List[types.CompletionItem]:
        """Get completion suggestions for variables in snippets.

        Uses parsed data from validator (already extracted, no re-parsing).

        Args:
            prefix: Partial variable name being typed
            validation_context: ValidationContext for looking up snippets
            snippet_path: Path to current snippet file (to get actual variables)

        Returns:
            List of CompletionItem objects
        """
        suggestions = []
        variables = {}

        # If we have a snippet path, get variables from validator's parsed data
        if snippet_path and snippet_path.exists():
            uri = self.server.path_to_uri(snippet_path)
            if uri not in self.server.validation_cache:
                return suggestions
            try:
                # Run validator to get parsed data
                result = self.server.validation_cache[uri]

                # Use validator's extracted data (no re-parsing!)
                variables.update(result.parsed_arguments)

                # Add results with results_ prefix
                # Use the actual result values as descriptions
                for result_name, result_value in result.parsed_results.items():
                    variables[f"results_{result_name}"] = str(result_value)

                # Add requirements with requirements_ prefix
                # Use the actual requirement values as descriptions
                for req_key, req_value in result.parsed_requirements.items():
                    variables[f"requirements_{req_key}"] = str(req_value)

                # Add available profiles with profile_ prefix (use file paths as descriptions)
                for prof_key, prof_value in result.profile_files.items():
                    variables[f"profile_{prof_key}"] = str(prof_value)

                # Add available profiles with profile_ prefix (use file paths as descriptions)
                # for profile_path in validation_context.profile_paths:
                #     profile_name = profile_path.stem
                #     variables[f"profile_{profile_name}"] = str(profile_path)

                logger.debug(
                    f"Extracted {len(variables)} variables from validator for {snippet_path.name}"
                )
            except Exception as e:
                logger.debug(f"Could not get variables from validator: {e}")
                # Fall back to common variables

        # Filter by prefix and create completion items
        for var_name, description in variables.items():
            if var_name.lower().startswith(prefix.lower()):
                suggestions.append(
                    types.CompletionItem(
                        label=var_name,
                        kind=types.CompletionItemKind.Variable,
                        detail=description,
                    )
                )

        return suggestions

    def _get_variable_completions_for_yaml(
        self,
        lines: List[str],
        line_num: int,
        char_pos: int,
        validation_context=None,
        file_path: Path = None,
    ) -> List[types.CompletionItem]:
        """Get completion suggestions for variables in YAML files.

        For pipeline files, uses the validation cache to get all parsed arguments.
        Supports multiple variables on the same line by finding which pattern
        the cursor is currently inside.

        Args:
            lines: File lines
            line_num: Current line number
            char_pos: Character position in line
            validation_context: ValidationContext for looking up snippets/profiles
            file_path: Path to the YAML file being edited

        Returns:
            List of CompletionItem objects
        """
        suggestions = []
        variables = {}

        # Try to get variables from validation cache (for pipelines)
        if file_path:
            try:
                uri = f"file://{file_path}"
                if uri in self.server.validation_cache:
                    result = self.server.validation_cache[uri]
                    # Use pipeline arguments if available
                    if (
                        result.file_type == "pipeline"
                        and result.parsed_pipeline_arguments
                    ):
                        variables.update(result.parsed_pipeline_arguments)
                        logger.debug(
                            f"Using {len(variables)} pipeline arguments from validation cache"
                        )
            except Exception as e:
                logger.debug(f"Could not get variables from validation cache: {e}")

        # Find which %(...)s pattern the cursor is inside of
        line = lines[line_num]
        # Find all %( patterns in the line
        matches = list(re.finditer(r"%\((\w*?)(?:\)s)?", line))
        current_match = None

        for match in matches:
            # Check if cursor is within this %(... pattern
            start = match.start()
            # Look for closing )s after the match
            closing = line.find(")s", match.end())
            if closing == -1:
                closing = len(line)  # No closing found, assume open pattern
            else:
                closing += 2  # Include the )s

            if start <= char_pos <= closing:
                current_match = match
                break

        # If we found the pattern containing the cursor, get the prefix
        prefix = ""
        if current_match:
            prefix = current_match.group(1).lower()
        elif line[:char_pos].rstrip().endswith("%("):
            # Cursor is right after %(
            prefix = ""
        else:
            # No variable pattern found
            return suggestions

        # Filter variables by prefix and create completion items
        for var_name, description in variables.items():
            if var_name.lower().startswith(prefix):
                suggestions.append(
                    types.CompletionItem(
                        label=var_name,
                        kind=types.CompletionItemKind.Variable,
                        detail=description,
                    )
                )

        return suggestions
