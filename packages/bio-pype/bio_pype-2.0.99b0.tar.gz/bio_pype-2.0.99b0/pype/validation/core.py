"""Core validation data structures and types.

This module defines the fundamental data structures used throughout the validation system:
- Diagnostic: Individual validation errors/warnings/infos with location information
- ValidationResult: Result of validating a single file
- DiagnosticSeverity: Severity levels for diagnostics
- Location: Line and character position information
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class DiagnosticSeverity(Enum):
    """Severity levels for validation diagnostics."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Location:
    """Location information for a diagnostic.

    Attributes:
        line: 0-based line number in the file
        start_char: Character position in line where diagnostic starts
        end_char: Character position in line where diagnostic ends
    """

    line: int
    start_char: int
    end_char: int


@dataclass
class Diagnostic:
    """Validation diagnostic (error/warning/info).

    Represents a single validation issue found during validation.

    Attributes:
        severity: DiagnosticSeverity level (ERROR, WARNING, INFO)
        location: Location object with line and character positions
        message: Human-readable error/warning/info message
        code: Optional error code for categorization (e.g., "missing-section")
        suggestion: Optional suggestion for fixing the issue
    """

    severity: DiagnosticSeverity
    location: Location
    message: str
    code: Optional[str] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert diagnostic to dictionary for JSON serialization."""
        return {
            "severity": self.severity.value,
            "line": self.location.line,
            "start_char": self.location.start_char,
            "end_char": self.location.end_char,
            "message": self.message,
            "code": self.code,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationResult:
    """Result of validating a single file.

    Attributes:
        file_path: Path to the validated file
        file_type: Type of file ('snippet', 'profile', 'pipeline')
        diagnostics: List of Diagnostic objects found during validation
        is_valid: True if no errors found (warnings/info are acceptable)
        parsed_arguments: Dict mapping argument names to their help text (for snippets)
        parsed_results: Dict mapping result names to descriptions (for snippets)
        parsed_requirements: Dict mapping requirement keys to values (for snippets)
        available_profiles: List of available profile names from validation context
        profile_files: Dict mapping file keys to "profile_name: path" descriptions (for profile_* completions)
        profile_programs: Dict mapping program names to namespace strings (for namespace= completions)
        friendly_name: str snippet friendly name (for snippet)
    """

    file_path: Path
    file_type: str
    diagnostics: List[Diagnostic] = field(default_factory=list)
    is_valid: bool = True
    parsed_arguments: Dict[str, str] = field(default_factory=dict)
    parsed_results: Dict[str, str] = field(default_factory=dict)
    parsed_requirements: Dict[str, Any] = field(default_factory=dict)
    available_profiles: List[str] = field(default_factory=list)
    profile_files: Dict[str, str] = field(default_factory=dict)
    profile_programs: Dict[str, str] = field(default_factory=dict)
    friendly_name: Optional[str] = None

    def __post_init__(self) -> None:
        """Update is_valid based on presence of errors."""
        self.is_valid = not any(
            d.severity == DiagnosticSeverity.ERROR for d in self.diagnostics
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary for JSON serialization."""
        return {
            "file_path": str(self.file_path),
            "file_type": self.file_type,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "is_valid": self.is_valid,
            "parsed_arguments": self.parsed_arguments,
            "parsed_results": self.parsed_results,
            "parsed_requirements": self.parsed_requirements,
            "available_profiles": self.available_profiles,
        }


@dataclass
class ParsedSection:
    """Parsed section from a Markdown file.

    Attributes:
        name: Section name (lowercase, from ## header)
        content: Raw content of the section
        start_line: 0-based line number where section starts
        end_line: 0-based line number where section ends
    """

    name: str
    content: str
    start_line: int
    end_line: int


@dataclass
class VariableInfo:
    """Information about a variable usage.

    Attributes:
        name: Variable name (e.g., 'input_file')
        locations: List of Location objects where variable is used
    """

    name: str
    locations: List[Location] = field(default_factory=list)


@dataclass
class ValidationContext:
    """Context for validation operations.

    Manages workspace discovery, module caching, and shared state
    across multiple validation operations.

    Attributes:
        workspace_root: Root directory of the workspace (default: current directory)
        snippet_paths: Paths to snippet files discovered in workspace
        profile_paths: Paths to profile files discovered in workspace
        pipeline_paths: Paths to pipeline files discovered in workspace
        loaded_profiles: Cache of loaded Profile objects (name -> Profile)
        loaded_snippets: Cache of loaded Snippet/SnippetMd objects (name -> Snippet)
    """

    workspace_root: Optional[Path] = None
    snippet_paths: List[Path] = field(default_factory=list)
    profile_paths: List[Path] = field(default_factory=list)
    pipeline_paths: List[Path] = field(default_factory=list)
    loaded_profiles: Dict[str, Any] = field(default_factory=dict)
    loaded_snippets: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize workspace_root and discover modules if not already populated."""
        if self.workspace_root is None:
            self.workspace_root = Path.cwd()

        # Auto-discover modules if paths are not populated
        if self.workspace_root and not self.snippet_paths:
            # Import here to avoid circular imports
            from pype.validation.context import _discover_modules_in_dir

            snippet_paths, profile_paths, pipeline_paths = _discover_modules_in_dir(
                self.workspace_root
            )
            self.snippet_paths = snippet_paths
            self.profile_paths = profile_paths
            self.pipeline_paths = pipeline_paths

    def get_available_profile_names(self) -> Set[str]:
        """Get names of all available profiles."""
        return set(self.loaded_profiles.keys())

    def get_available_snippet_names(self) -> Set[str]:
        """Get names of all available snippets."""
        return set(self.loaded_snippets.keys())

    def clear_cache(self) -> None:
        """Clear all cached modules."""
        self.loaded_profiles.clear()
        self.loaded_snippets.clear()
