"""Pipeline command builder for hover information.

Generates actual command lines from pipeline steps for display in hover tooltips.
This is a special feature that shows users what command will be executed.
"""

import logging
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

from pype.utils.snippets import SnippetMd


logger = logging.getLogger("bio_pype_lsp.command_builder")


class PipelineCommandBuilder:
    """Builds command lines from pipeline steps.

    Generates the actual bash commands that will be executed for a pipeline step,
    including variable substitution.
    """

    def __init__(self, validation_context):
        """Initialize command builder.

        Args:
            validation_context: ValidationContext with module paths
        """
        self.validation_context = validation_context
        self.snippet_cache = {}

    def build_step_command(
        self, step_name: str, step_args: Dict[str, str], pipeline_args: Dict[str, str]
    ) -> Optional[str]:
        """Build command line for a pipeline step.

        Args:
            step_name: Name of the snippet to execute
            step_args: Arguments from the pipeline step
            pipeline_args: Pipeline-level arguments (variables)

        Returns:
            Formatted command line or None if step not found
        """
        try:
            # Find the snippet
            snippet = self._get_snippet(step_name)
            if not snippet:
                return None

            # Substitute variables in step arguments
            substituted_args = self._substitute_variables(
                step_args, pipeline_args
            )

            # Extract snippet code chunks
            command_parts = []

            # Get the snippet chunks with their IO headers
            if hasattr(snippet, "snippet_chunks"):
                try:
                    snippet.parse_snippet_chunks("/tmp")
                except Exception:
                    pass

                if hasattr(snippet, "snippet_chunks"):
                    for i, chunk in enumerate(snippet.snippet_chunks):
                        # Get chunk code
                        if hasattr(chunk, "code"):
                            code = chunk.code
                        else:
                            code = ""

                        # Substitute variables in the code
                        substituted_code = self._substitute_variables_in_text(
                            code, pipeline_args
                        )

                        if substituted_code:
                            if i == 0:
                                # First chunk - add shebang/header
                                command_parts.append(
                                    f"# Snippet: {step_name}\n{substituted_code}"
                                )
                            else:
                                command_parts.append(substituted_code)

            if command_parts:
                return "\n".join(command_parts)

            # Fallback: show the step configuration
            args_str = " ".join(
                [f"{k}={v}" for k, v in substituted_args.items()]
            )
            return f"# Snippet: {step_name}\n# Arguments: {args_str}"

        except Exception as e:
            logger.debug(f"Error building command for step {step_name}: {e}")
            return None

    def get_step_preview(
        self, step_name: str, step_args: Dict[str, str]
    ) -> Optional[str]:
        """Get a short preview of what a step does.

        Args:
            step_name: Name of the snippet
            step_args: Arguments from the pipeline step

        Returns:
            Short description of the step
        """
        try:
            snippet = self._get_snippet(step_name)
            if not snippet:
                return None

            # Get snippet description
            description = snippet.mod.get("description", "").strip()

            # Get requirements
            requirements = None
            try:
                requirements = snippet.requirements()
            except Exception:
                pass

            preview_parts = [f"**{step_name}**: {description}"]

            if requirements:
                preview_parts.append("\n**Requirements**:")
                if isinstance(requirements, dict):
                    for key, value in requirements.items():
                        preview_parts.append(f"- {key}: {value}")

            return "\n".join(preview_parts)

        except Exception as e:
            logger.debug(f"Error getting step preview for {step_name}: {e}")
            return None

    def _get_snippet(self, snippet_name: str) -> Optional[SnippetMd]:
        """Get snippet by name with caching.

        Args:
            snippet_name: Name of the snippet

        Returns:
            SnippetMd instance or None if not found
        """
        if snippet_name in self.snippet_cache:
            return self.snippet_cache[snippet_name]

        try:
            for snippet_path in self.validation_context.snippet_paths:
                if snippet_path.stem == snippet_name:
                    snippet = SnippetMd(
                        snippet_path.parent, snippet_name, str(snippet_path)
                    )
                    self.snippet_cache[snippet_name] = snippet
                    return snippet
        except Exception as e:
            logger.debug(f"Error loading snippet {snippet_name}: {e}")

        return None

    def _substitute_variables(
        self, args: Dict[str, str], pipeline_args: Dict[str, str]
    ) -> Dict[str, str]:
        """Substitute variables in arguments.

        Replaces %(var)s patterns with actual values from pipeline_args.

        Args:
            args: Arguments with potential variables
            pipeline_args: Available variable values

        Returns:
            Arguments with variables substituted
        """
        substituted = {}
        for key, value in args.items():
            if isinstance(value, str):
                substituted[key] = self._substitute_variables_in_text(
                    value, pipeline_args
                )
            else:
                substituted[key] = value
        return substituted

    def _substitute_variables_in_text(
        self, text: str, pipeline_args: Dict[str, str]
    ) -> str:
        """Substitute variables in text.

        Args:
            text: Text potentially containing %(var)s patterns
            pipeline_args: Available variable values

        Returns:
            Text with variables substituted
        """
        def replacer(match):
            var_name = match.group(1)
            if var_name in pipeline_args:
                value = pipeline_args[var_name]
                # Quote file paths
                if isinstance(value, str) and "/" in value:
                    return f'"{value}"'
                return str(value)
            return match.group(0)  # Keep original if not found

        return re.sub(r"%\((\w+)\)s", replacer, text)
