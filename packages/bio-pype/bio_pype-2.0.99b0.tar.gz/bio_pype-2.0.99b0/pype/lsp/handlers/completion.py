"""Autocomplete handler for LSP server.

Provides intelligent code completion for snippets, profiles, variables, and arguments.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional

from lsprotocol import types

from pype.utils.snippets import SnippetMd
from pype.validation import (
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

            validation_context = discover_modules(workspace_root)
            logger.debug(
                f"Completion context: {len(validation_context.snippet_paths)} snippets, {len(validation_context.profile_paths)} profiles, {len(validation_context.pipeline_paths)} pipelines"
            )

            lines = content.split("\n")

            # Get appropriate completions based on file type
            if file_path.suffix == ".md":
                # Store validation result in shared cache for other handlers to use
                validation_result = SnippetValidator(validation_context).validate(
                    file_path
                )
                self.server.validation_cache[uri] = validation_result

                return self._get_snippet_completions(
                    lines, position, validation_context, file_path
                )
            elif file_path.suffix in [".yaml"]:
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
                # Find the variable pattern context - match %(word (without $ anchor to work mid-typing)
                # Also handle case where user just typed %( with nothing after
                match = re.search(r"%\((\w*)", line[:char_pos])
                if match:
                    # User is typing a variable name
                    prefix = match.group(1)
                    # Pass the current snippet file path to extract real variables
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
                        validation_context=validation_context,
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
                    line, char_pos, validation_context
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
                    lines, line_num, char_pos, validation_context=validation_context
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

        # Check if we're in a pipeline (looking for 'name:' field)
        if "name:" in line and "items:" in "".join(lines[:line_num]):
            return "snippet_name"

        # Check if we're completing variables
        if "%" in line and "(" in line:
            return "variable"

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
        self, line: str, char_pos: int, validation_context
    ) -> List[types.CompletionItem]:
        """Get completion suggestions for snippet names.

        Args:
            line: Current line
            char_pos: Character position in line
            validation_context: ValidationContext with available snippets

        Returns:
            List of CompletionItem objects
        """
        suggestions = []

        # Extract what the user has typed so far
        prefix_match = re.search(r"name:\s*(\w*)$", line[:char_pos])
        if prefix_match:
            prefix = prefix_match.group(1).lower()

            # Get all available snippets
            for snippet_path in validation_context.snippet_paths:
                snippet_name = snippet_path.stem
                if snippet_name.lower().startswith(prefix):
                    # Try to get description
                    description = ""
                    try:
                        snippet = SnippetMd(
                            snippet_path.parent, snippet_name, str(snippet_path)
                        )
                        description = snippet.mod.get("description", "").strip()
                    except Exception:
                        pass

                    suggestions.append(
                        types.CompletionItem(
                            label=snippet_name,
                            kind=types.CompletionItemKind.Function,
                            detail=description,
                            documentation=description,
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
        self, lines: List[str], line_num: int, char_pos: int, validation_context=None
    ) -> List[types.CompletionItem]:
        """Get completion suggestions for variables in YAML files.

        Extracts variables from:
        - Pipeline arguments defined earlier
        - Snippet arguments and results
        - Profile variables

        Args:
            lines: File lines
            line_num: Current line number
            char_pos: Character position in line
            validation_context: ValidationContext for looking up snippets/profiles

        Returns:
            List of CompletionItem objects
        """
        suggestions = []
        variables = {}

        # Parse the YAML to find defined variables and snippet references
        in_arguments = False
        in_items = False
        defined_vars = set()
        snippet_names = set()

        for i, line in enumerate(lines[:line_num]):
            if "arguments:" in line:
                in_arguments = True
                in_items = False
            elif "items:" in line:
                in_items = True
                in_arguments = False
            elif line.strip() and not line.startswith(" "):
                in_arguments = False
                in_items = False

            # Collect argument-defined variables
            if in_arguments and "pipeline_arg" in line:
                # Extract variable from %(var)s pattern
                match = re.search(r"%\((\w+)\)s", line)
                if match:
                    defined_vars.add(match.group(1))

            # Collect snippet references in pipeline items
            if in_items and "name:" in line:
                match = re.search(r"name:\s*(\w+)", line)
                if match:
                    snippet_names.add(match.group(1))

        # Add defined variables
        for var in sorted(defined_vars):
            variables[var] = "Pipeline argument"

        # Extract variables from referenced snippets using validator
        if validation_context and snippet_names:
            try:
                for snippet_name in snippet_names:
                    # Find the snippet in validation context
                    for snippet_path in validation_context.snippet_paths:
                        if snippet_path.stem == snippet_name:
                            # Use validator to get parsed data
                            validator = SnippetValidator(validation_context)
                            result = validator.validate(snippet_path)
                            # Add arguments with help text
                            for arg_name, help_text in result.parsed_arguments.items():
                                if arg_name not in variables:
                                    variables[arg_name] = help_text
                            break
            except Exception as e:
                logger.debug(f"Could not get variables from snippet validator: {e}")

        # Get the prefix being typed - match %( followed by word chars
        line = lines[line_num]
        # Match %(word without requiring end-of-string
        prefix_match = re.search(r"%\((\w*)", line[:char_pos])
        if prefix_match:
            prefix = prefix_match.group(1).lower()

            # Add all extracted variables that match the prefix
            for var_name, description in variables.items():
                if var_name.lower().startswith(prefix):
                    suggestions.append(
                        types.CompletionItem(
                            label=var_name,
                            kind=types.CompletionItemKind.Variable,
                            detail=description,
                        )
                    )

            # Add common pipeline variables as fallback
            common_pipeline_vars = {
                "input_fa": "Input FASTA file",
                "output_fa": "Output FASTA file",
                "lower_fa": "Lowercased FASTA",
                "complement_fa": "Complement FASTA",
                "sample_id": "Sample identifier",
                "input": "Input file",
                "output": "Output file",
            }

            for var_name, description in common_pipeline_vars.items():
                if var_name.lower().startswith(prefix) and var_name not in variables:
                    suggestions.append(
                        types.CompletionItem(
                            label=var_name,
                            kind=types.CompletionItemKind.Variable,
                            detail=description,
                        )
                    )

            # Add profile variables for available profiles (use file paths as descriptions)
            if validation_context:
                for profile_path in validation_context.profile_paths:
                    profile_name = profile_path.stem
                    var_name = f"profile_{profile_name}"
                    if (
                        var_name.lower().startswith(prefix)
                        and var_name not in variables
                    ):
                        suggestions.append(
                            types.CompletionItem(
                                label=var_name,
                                kind=types.CompletionItemKind.Variable,
                                detail=str(profile_path),
                            )
                        )

        return suggestions
