"""Central exception handling for bio_pype.

Provides a hierarchy of custom exceptions for better error context and handling.
Each exception type includes contextual information specific to its domain.
"""

from typing import Dict, Optional


class PypeError(Exception):
    """Base exception for all pype errors."""

    def __init__(self, message: str, context: Optional[Dict] = None):
        self.context = context or {}
        super().__init__(message)


class PipelineError(PypeError):
    """Base class for pipeline-related errors."""

    def __init__(self, message: str, pipeline_name: Optional[str] = None, **kwargs):
        context = {"pipeline_name": pipeline_name, **kwargs}
        super().__init__(f"Pipeline error: {message}", context)


class PipelineVersionError(PipelineError):
    """Raised when pipeline version is incompatible."""

    def __init__(
        self, current_version: str, required_version: str, pipeline_name: Optional[str]
    ):
        super().__init__(
            f"Version mismatch: {current_version} != {required_version}",
            pipeline_name,
            current_version=current_version,
            required_version=required_version,
        )


class PipelineItemError(PipelineError):
    """Error in a specific pipeline item."""

    def __init__(
        self,
        message: str,
        item_name: str,
        item_type: str,
        pipeline_name: Optional[str] = None,
    ):
        super().__init__(
            f"Error in {item_type} '{item_name}': {message}",
            pipeline_name,
            item_name=item_name,
            item_type=item_type,
        )


class SnippetError(PypeError):
    """Base class for snippet-related errors."""

    def __init__(self, message: str, snippet_name: Optional[str] = None, **kwargs):
        context = {"snippet_name": snippet_name, **kwargs}
        super().__init__(f"Snippet error: {message}", context)


class SnippetNotFoundError(SnippetError):
    """Raised when a snippet cannot be found."""

    def __init__(self, snippet_name: str):
        super().__init__(f"Snippet '{snippet_name}' not found", snippet_name)


class SnippetResultsTemplateSobstitutionError(SnippetError):
    """Raised when a snippet results template sobstritution reports an error."""

    def __init__(
        self,
        snippet_name: str,
        chunk_id: str,
        missing_key: str,
        template_vars: set[str],
        available_keys: set[str],
        missing_keys: set[str],
    ):
        super().__init__(
            f"Template substitution failed in snippet '{snippet_name}', chunk '{chunk_id}':\n"
            f"  Missing variable: '{missing_key}'\n"
            f"  Required variables: {sorted(template_vars)}\n"
            f"  Provided variables: {sorted(available_keys)}\n"
            f"  Missing variables: {sorted(missing_keys)}"
        )


class SnippetResultsArgumentError(SnippetError):
    """Raised when a snippet results from non-md snippet gives an error."""

    def __init__(
        self,
        snippet_name: str,
        missing_key: str,
        available_keys: set[str],
    ):
        super().__init__(
            f"Error in executing the Results method for '{snippet_name}':\n"
            f"  Missing variable: '{missing_key}'\n"
            f"  Provided variables: {sorted(available_keys)}."
        )


class SnippetExecutionError(SnippetError):
    """Raised when snippet execution fails."""

    def __init__(
        self, message: str, snippet_name: str, exit_code: Optional[int] = None
    ):
        super().__init__(message, snippet_name, exit_code=exit_code)


class ArgumentError(PypeError):
    """Base class for argument-related errors."""

    def __init__(self, message: str, argument: Optional[str] = None, **kwargs):
        context = {"argument": argument, **kwargs}
        super().__init__(f"Argument error: {message}", context)


class BatchArgumentError(ArgumentError):
    """Error in batch argument processing."""

    def __init__(self, message: str, batch_file: Optional[str]):
        super().__init__(message, batch_file=batch_file)


class ProfileError(PypeError):
    """Base class for profile-related errors."""

    def __init__(self, message: str, profile_name: Optional[str] = None, **kwargs):
        context = {"profile_name": profile_name, **kwargs}
        super().__init__(f"Profile error: {message}", context)


class CommandError(PypeError):
    """Base class for command execution errors."""

    def __init__(
        self,
        message: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None,
    ):
        context = {"command": command, "exit_code": exit_code}
        super().__init__(f"Command error: {message}", context)


class CommandNamespaceError(CommandError):
    """Error in command namespace."""

    pass


class EnvModulesError(PypeError):
    """Error in environment modules."""

    def __init__(self, message: str, module_name: Optional[str] = None):
        super().__init__(
            f"Environment module error: {message}", {"module_name": module_name}
        )
