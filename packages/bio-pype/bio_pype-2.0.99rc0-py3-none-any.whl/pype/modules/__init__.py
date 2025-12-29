"""Pype modules package.

This package contains all command-line interface modules for pype:
- pipelines: Execute bioinformatics pipeline workflows
- snippets: Run individual snippet tasks
- profiles: Manage execution profiles and environments

Module Metadata
===============
Each module is registered with metadata (help text, description) in MODULE_METADATA.
This serves as the single source of truth for module documentation.

Module Registration
===================
The create_module_parser() factory function creates parser objects for modules
using the metadata registry. All modules use this function to maintain consistency
while preserving their distinctive argument structures.
"""

from typing import Dict

from pype.argparse import ArgumentParser, _SubParsersAction

# Module metadata registry - single source of truth for module documentation
MODULE_METADATA: Dict[str, Dict[str, str]] = {
    "pipelines": {
        "help": "Execute pipeline workflows",
        "description": "Run bioinformatics pipelines with queue system integration",
    },
    "snippets": {
        "help": "Execute individual snippet tasks",
        "description": "Run individual bioinformatics tasks as snippets",
    },
    "profiles": {
        "help": "Manage execution profiles",
        "description": "Configure and validate execution environments",
    },
    "resume": {
        "help": "Resume a previous pipeline run",
        "description": "Resume pipeline execution from runtime YAML with environment restoration",
    },
    "compute_bio": {
        "help": "Test and monitor compute.bio API integration",
        "description": "Test compute.bio credentials and run persistent listener daemon",
    },
    "validate": {
        "help": "Validate bio_pype modules (snippets, profiles, pipelines)",
        "description": "Validate snippets, profiles, and pipelines for correctness and compatibility",
    },
}


def create_module_parser(
    subparsers: _SubParsersAction, module_name: str
) -> ArgumentParser:
    """Create a module parser using metadata registry.

    This factory function creates parser objects for modules using metadata
    from MODULE_METADATA. It ensures consistency across all modules while
    allowing each module to add its own distinctive arguments.

    Args:
        subparsers: Parent parser's subparsers
        module_name: Name of the module

    Returns:
        Parser for the module

    Raises:
        KeyError: If module_name not in MODULE_METADATA
    """
    if module_name not in MODULE_METADATA:
        # Fallback for tests or edge cases where module_name is None or missing
        # Create a minimal parser without metadata
        return subparsers.add_parser(
            module_name,
            add_help=False,
        )

    metadata = MODULE_METADATA[module_name]
    return subparsers.add_parser(
        module_name,
        help=metadata["help"],
        description=metadata["description"],
        add_help=False,
    )


__all__ = ["MODULE_METADATA", "create_module_parser"]
