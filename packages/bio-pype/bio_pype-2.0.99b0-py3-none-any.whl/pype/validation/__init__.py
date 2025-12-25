"""Bio_pype validation module.

This module provides a comprehensive validation suite for bio_pype snippets,
pipelines, and profiles. It offers:

- Structural validation (YAML/Markdown parsing)
- Semantic validation (cross-file references, variable tracking)
- Runtime validation (attempting to load modules with bio_pype API)
- CLI interface for validating modules
- LSP server integration for IDE support

Example usage:

    from pype.validation import (
        ValidationContext,
        SnippetValidator,
        ProfileValidator,
        PipelineValidator
    )

    # Create validation context (manages workspace discovery)
    context = ValidationContext()

    # Validate a snippet file
    validator = SnippetValidator(context)
    result = validator.validate(Path('path/to/snippet.md'))

    # Check results
    if result.is_valid:
        print(f"{result.file_path} is valid")
    else:
        for diagnostic in result.diagnostics:
            print(f"{diagnostic.severity.value}: {diagnostic.message}")

    # JSON export for tooling
    import json
    print(json.dumps(result.to_dict(), indent=2))
"""

from pype.validation.core import (
    Diagnostic,
    DiagnosticSeverity,
    Location,
    ParsedSection,
    ValidationContext,
    ValidationResult,
    VariableInfo,
)
from pype.validation.context import discover_modules, detect_module_root
from pype.validation.parsers import MarkdownSectionParser, VariableTracker
from pype.validation.snippet_validator import SnippetValidator
from pype.validation.profile_validator import ProfileValidator
from pype.validation.pipeline_validator import PipelineValidator

__all__ = [
    # Core types
    "Diagnostic",
    "DiagnosticSeverity",
    "Location",
    "ParsedSection",
    "ValidationContext",
    "ValidationResult",
    "VariableInfo",
    # Utilities
    "MarkdownSectionParser",
    "VariableTracker",
    "discover_modules",
    "detect_module_root",
    # Validators
    "SnippetValidator",
    "ProfileValidator",
    "PipelineValidator",
]

__version__ = "0.1.0"
