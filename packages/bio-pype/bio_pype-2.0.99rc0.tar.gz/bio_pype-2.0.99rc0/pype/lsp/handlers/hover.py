"""Hover information handler for LSP server.

Provides contextual information when hovering over elements in code.
Handles snippet descriptions, section headers, variables, and YAML keys.
"""

import logging
import re
from pathlib import Path
from typing import Optional

from lsprotocol import types

from pype.validation.core import ValidationResult

logger = logging.getLogger("bio_pype_lsp.hover")


class HoverHandler:
    """Manages hover information for different file types."""

    def __init__(self, server):
        """Initialize hover handler.

        Args:
            server: BioPypeLspServer instance
        """
        self.server = server

    def get_hover_info(
        self, uri: str, position: types.Position
    ) -> Optional[types.Hover]:
        """Get hover information at a specific position.

        Args:
            uri: Document URI (file:// format)
            position: Position in document (line, character)

        Returns:
            Hover information or None if not available
        """
        try:
            file_path = Path(uri.replace("file://", ""))

            if not self.server.validation_context:
                return None

            # Get document content from workspace
            try:
                text_document = self.server.workspace.get_text_document(uri)
                content = text_document.source
                logger.debug(f"Using workspace content for hover: {file_path.name}")
            except Exception as e:
                logger.debug(f"Could not get text document from workspace: {e}")
                # Fall back to disk
                if file_path.exists():
                    content = file_path.read_text()
                    logger.debug(f"Reading hover content from disk: {file_path.name}")
                else:
                    logger.debug(f"No content available for hover: {file_path.name}")
                    return None

            # Get appropriate handler based on file type
            if file_path.suffix == ".md":
                return self._get_snippet_hover(file_path, position, content, uri)
            elif file_path.suffix in [".yaml", ".yml"]:
                return self._get_yaml_hover(file_path, position, content)

        except Exception as e:
            logger.error(f"Error getting hover info for {uri}: {e}", exc_info=True)

        return None

    def _get_snippet_hover(
        self, file_path: Path, position: types.Position, content: str, uri: str = None
    ) -> Optional[types.Hover]:
        """Get hover information for snippet (.md) files.

        Args:
            file_path: Path to snippet file
            position: Position in document
            content: File content
            uri: Document URI (for accessing cached validation results)

        Returns:
            Hover information with basic details
        """
        if file_path and file_path.exists():
            uri = self.server.path_to_uri(file_path)

        # If no cached validation, run validation now
        if uri not in self.server.validation_cache:
            try:
                from pype.validation import SnippetValidator, detect_module_root, discover_modules

                workspace_root = detect_module_root(file_path)
                if not workspace_root:
                    workspace_root = file_path.parent.parent.parent

                validation_context = discover_modules(workspace_root)
                validator = SnippetValidator(validation_context)
                result = validator.validate(file_path)
                self.server.validation_cache[uri] = result
                logger.debug(f"On-demand validation for hover: {file_path.name}")
            except Exception as e:
                logger.debug(f"Could not validate for hover: {e}")
                return None

        validation_results: ValidationResult = self.server.validation_cache[uri]
        try:
            lines = content.split("\n")
            if position.line >= len(lines):
                return None

            line = lines[position.line]
            char_pos = position.character

            # Check if hovering over a section header
            if line.strip().startswith("##"):
                section = line.strip().replace("##", "").strip()
                if section == "name":
                    validation_results.friendly_name
                    hover_text = f"**Section:** `{section}`\n\n_{validation_results.friendly_name}_"
                    return types.Hover(
                        contents=types.MarkupContent(
                            kind=types.MarkupKind.Markdown, value=hover_text
                        )
                    )
                else:
                    hover_text = f"**Section:** `{section}`"
                    return types.Hover(
                        contents=types.MarkupContent(
                            kind=types.MarkupKind.Markdown, value=hover_text
                        )
                    )

            # Check if hovering over a variable reference
            if "%" in line and "(" in line:
                # Extract variable name at cursor
                var_match = self._extract_variable_at_position(line, char_pos)
                if var_match:
                    var_name = var_match
                    if var_name.startswith("results_"):
                        var_name = var_name.replace("results_", "")
                        hover_text = f"**Results:** `{var_name}`"
                        try:
                            var_text = validation_results.parsed_results[var_name]
                            hover_text = f"{hover_text}\n\n{var_text}"
                        except KeyError:
                            pass

                    elif var_name.startswith("requirements_"):
                        var_name = var_name.replace("requirements_", "")
                        hover_text = f"**Resource requirements:** `{var_name}`"
                        try:
                            logger.info(
                                "req: ".join(
                                    validation_results.parsed_requirements.keys()
                                )
                            )
                            var_text = validation_results.parsed_requirements[var_name]
                            hover_text = f"{hover_text}\n\n{var_text}"
                        except KeyError:
                            pass
                    elif var_name.startswith("profile_"):
                        hover_text = f"**Profile files:** `{var_name}`"
                        try:
                            var_text = validation_results.profile_files[
                                var_name.replace("profile_", "")
                            ]
                            hover_text = f"{hover_text}\n\n{var_text}"
                        except KeyError:
                            pass
                    else:
                        hover_text = f"**Arguments:** `{var_name}`"
                        try:
                            var_text = validation_results.parsed_arguments[var_name]
                            hover_text = f"{hover_text}\n\n{var_text}"
                        except KeyError:
                            pass

                    return types.Hover(
                        contents=types.MarkupContent(
                            kind=types.MarkupKind.Markdown, value=hover_text
                        )
                    )
            elif line.startswith("@") and "namespace" in line:
                # extract namespace
                var_match = self._extract_namespace_at_position(line, char_pos)
                if var_match:
                    var_name = var_match
                    hover_text = f"**Namespace:** `{var_name}`"
                    try:
                        var_text = validation_results.profile_programs[var_name]
                        hover_text = f"{hover_text}\n\n{var_text}"
                    except KeyError:
                        pass
                    return types.Hover(
                        contents=types.MarkupContent(
                            kind=types.MarkupKind.Markdown, value=hover_text
                        )
                    )

        except Exception as e:
            logger.debug(f"Error getting snippet hover: {e}")

        return None

    def _extract_namespace_at_position(self, line: str, char_pos: int) -> Optional[str]:
        """Extract namespace name at cursor position.

        Handles patterns like namespace=fastqc in code chunk headers.
        Example: @/bin/sh, fastqc, namespace=fastqc

        Args:
            line: Current line text
            char_pos: Character position in line

        Returns:
            Namespace name or None
        """
        # Match namespace=<name> where name is alphanumeric or underscore
        for match in re.finditer(r"namespace=(\w+)", line):
            start, end = match.span()
            if start <= char_pos <= end:
                return match.group(1)
        return None

    def _extract_variable_at_position(self, line: str, char_pos: int) -> Optional[str]:
        """Extract variable name at cursor position.

        Handles patterns like %(variable_name)s, %(count)d, %(value)f, etc.

        Args:
            line: Current line text
            char_pos: Character position in line

        Returns:
            Variable name or None
        """
        # Find all variables in the line - matches format specifiers %i, %s, %f
        for match in re.finditer(r"%\(([a-zA-Z_][a-zA-Z0-9_]*)\)[isf]", line):
            start, end = match.span()
            if start <= char_pos <= end:
                return match.group(1)

        return None

    def _get_yaml_hover(
        self, file_path: Path, position: types.Position, content: str
    ) -> Optional[types.Hover]:
        """Get hover information for YAML files (profiles/pipelines).

        Args:
            file_path: Path to YAML file
            position: Position in document
            content: File content

        Returns:
            Hover information with context
        """
        try:
            # Determine if profile or pipeline based on content or directory
            if "programs:" in content:
                # Likely a profile
                return self._get_profile_hover(file_path, position, content)
            else:
                # Likely a pipeline
                return self._get_pipeline_hover(file_path, position, content)

        except Exception as e:
            logger.debug(f"Error getting YAML hover: {e}")

        return None

    def _get_profile_hover(
        self, file_path: Path, position: types.Position, content: str
    ) -> Optional[types.Hover]:
        """Get hover information for profile YAML files.

        Args:
            file_path: Path to profile file
            position: Position in document
            content: File content

        Returns:
            Hover information with basic key details
        """
        try:
            lines = content.split("\n")
            line_num = position.line

            if line_num >= len(lines):
                return None

            line = lines[line_num]

            # Extract the key being hovered over
            if ":" in line:
                key = line.split(":")[0].strip()
                if key and not key.startswith("#"):
                    hover_text = f"**Key:** `{key}`"
                    return types.Hover(
                        contents=types.MarkupContent(
                            kind=types.MarkupKind.Markdown,
                            value=hover_text,
                        )
                    )

        except Exception as e:
            logger.debug(f"Error getting profile hover: {e}")

        return None

    def _get_pipeline_hover(
        self, file_path: Path, position: types.Position, content: str
    ) -> Optional[types.Hover]:
        """Get hover information for pipeline YAML files.

        Args:
            file_path: Path to pipeline file
            position: Position in document
            content: File content

        Returns:
            Hover information with basic key details
        """
        try:
            lines = content.split("\n")
            line_num = position.line

            if line_num >= len(lines):
                return None

            line = lines[line_num]

            # Extract the key being hovered over
            if ":" in line:
                key = line.split(":")[0].strip()
                if key and not key.startswith("#"):
                    hover_text = f"**Key:** `{key}`"
                    return types.Hover(
                        contents=types.MarkupContent(
                            kind=types.MarkupKind.Markdown,
                            value=hover_text,
                        )
                    )

        except Exception as e:
            logger.debug(f"Error getting pipeline hover: {e}")

        return None
