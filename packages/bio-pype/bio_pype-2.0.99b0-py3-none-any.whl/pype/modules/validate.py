"""Validation command-line interface module.

This module provides validation commands for bio_pype modules (snippets, profiles, pipelines).

Example:
    pype validate snippet /path/to/snippet.md
    pype validate profile /path/to/profile.yaml
    pype validate all --workspace /Users/lgq442/src/pype_modules
    pype validate snippet /path/to/snippets/ --recursive --format json
"""

import json
import sys
from pathlib import Path
from typing import List

from pype.argparse import ArgumentParser, _SubParsersAction
from pype.logger import PypeLogger
from pype.modules import create_module_parser
from pype.validation import (
    ValidationContext,
    SnippetValidator,
    ProfileValidator,
    PipelineValidator,
    discover_modules,
    detect_module_root,
)


def add_parser(subparsers: _SubParsersAction, module_name: str) -> ArgumentParser:
    """Add validate command parser.

    Args:
        subparsers: Parent parser's subparsers
        module_name: Name of this module

    Returns:
        Parser for validate commands
    """
    return create_module_parser(subparsers, module_name)


def validate_args(parser: ArgumentParser, argv: List[str]) -> None:
    """Add validate subcommands and handle dispatch.

    Args:
        parser: Parent parser
        argv: Command-line arguments
    """
    subparsers = parser.add_subparsers(dest="validate_cmd", help="Validation target")

    # validate snippet
    snippet_parser = subparsers.add_parser("snippet", add_help=False, help="Validate snippet file(s)")
    snippet_parser.add_argument("path", help="Path to snippet file or directory")
    snippet_parser.add_argument(
        "-r", "--recursive", action="store_true", help="Recursively validate all snippets in directory"
    )
    snippet_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    snippet_parser.add_argument(
        "--no-warnings", action="store_true", help="Only show errors, hide warnings"
    )

    # validate profile
    profile_parser = subparsers.add_parser("profile", add_help=False, help="Validate profile file(s)")
    profile_parser.add_argument("path", help="Path to profile file or directory")
    profile_parser.add_argument(
        "-r", "--recursive", action="store_true", help="Recursively validate all profiles in directory"
    )
    profile_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    profile_parser.add_argument(
        "--no-warnings", action="store_true", help="Only show errors, hide warnings"
    )

    # validate pipeline
    pipeline_parser = subparsers.add_parser("pipeline", add_help=False, help="Validate pipeline file(s)")
    pipeline_parser.add_argument("path", help="Path to pipeline file or directory")
    pipeline_parser.add_argument(
        "-r", "--recursive", action="store_true", help="Recursively validate all pipelines in directory"
    )
    pipeline_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    pipeline_parser.add_argument(
        "--no-warnings", action="store_true", help="Only show errors, hide warnings"
    )

    # validate all (workspace)
    all_parser = subparsers.add_parser("all", add_help=False, help="Validate entire workspace")
    all_parser.add_argument(
        "--workspace", default=".", help="Workspace root directory (default: current directory)"
    )
    all_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    all_parser.add_argument(
        "--no-warnings", action="store_true", help="Only show errors, hide warnings"
    )

    # validate lsp (start LSP server)
    lsp_parser = subparsers.add_parser("lsp", add_help=False, help="Start LSP server for editor integration")
    lsp_parser.add_argument(
        "--stdio", action="store_true", default=True, help="Use stdio for communication (default)"
    )
    lsp_parser.add_argument(
        "--tcp", type=int, metavar="PORT", help="Use TCP on specified port (for debugging)"
    )
    lsp_parser.add_argument(
        "--log-file", type=str, help="Log file for debugging (default: /tmp/bio_pype_lsp.log)"
    )

    # Parse arguments
    args, extra = parser.parse_known_args(argv)

    # Dispatch to handler
    if not hasattr(args, "validate_cmd") or args.validate_cmd is None:
        parser.print_help()
        return

    _handle_validation(args, extra)


def validate(subparsers: _SubParsersAction, module_name: str, argv: List[str], profile: str) -> None:
    """Main validate command entry point.

    Args:
        subparsers: Parent subparsers
        module_name: Name of this module
        argv: Command-line arguments
        profile: Profile name (not used for validation)
    """
    validate_args(add_parser(subparsers, module_name), argv)


def _handle_validation(args, extra: List[str]) -> None:
    """Handle validation dispatch based on command.

    Args:
        args: Parsed arguments
        extra: Extra arguments
    """
    validate_cmd = args.validate_cmd

    if validate_cmd == "snippet":
        _validate_snippets(args)
    elif validate_cmd == "profile":
        _validate_profiles(args)
    elif validate_cmd == "pipeline":
        _validate_pipelines(args)
    elif validate_cmd == "all":
        _validate_all(args)
    elif validate_cmd == "lsp":
        _start_lsp_server(args)
    else:
        print(f"Unknown validation command: {validate_cmd}")
        sys.exit(1)


def _validate_snippets(args) -> None:
    """Validate snippet file(s).

    Args:
        args: Parsed arguments with path, recursive, format, no_warnings
    """
    path = Path(args.path)

    # Auto-detect workspace root from file structure
    workspace_root = detect_module_root(path)
    if not workspace_root:
        # Fallback: assume current directory or parent structure
        workspace_root = path.parent if path.is_dir() else path.parent.parent.parent

    context = discover_modules(workspace_root)
    validator = SnippetValidator(context)

    results = []

    if path.is_file():
        # Single file
        result = validator.validate(path)
        results.append(result)
    elif path.is_dir() and args.recursive:
        # Directory - recursive
        for snippet_file in sorted(path.glob("**/*.md")):
            result = validator.validate(snippet_file)
            results.append(result)
    elif path.is_dir():
        # Directory - non-recursive
        for snippet_file in sorted(path.glob("*.md")):
            result = validator.validate(snippet_file)
            results.append(result)
    else:
        print(f"Error: Path does not exist: {path}")
        sys.exit(1)

    _print_results(results, args.format, args.no_warnings)

    # Exit code
    has_errors = any(not r.is_valid for r in results)
    sys.exit(1 if has_errors else 0)


def _validate_profiles(args) -> None:
    """Validate profile file(s).

    Args:
        args: Parsed arguments with path, recursive, format, no_warnings
    """
    path = Path(args.path)

    # Auto-detect workspace root from file structure
    workspace_root = detect_module_root(path)
    if not workspace_root:
        # Fallback: assume current directory or parent structure
        workspace_root = path.parent if path.is_dir() else path.parent.parent.parent

    context = discover_modules(workspace_root)
    validator = ProfileValidator(context)

    results = []

    if path.is_file():
        # Single file
        result = validator.validate(path)
        results.append(result)
    elif path.is_dir() and args.recursive:
        # Directory - recursive
        for profile_file in sorted(path.glob("**/*.yaml")) + sorted(path.glob("**/*.yml")):
            result = validator.validate(profile_file)
            results.append(result)
    elif path.is_dir():
        # Directory - non-recursive
        for profile_file in sorted(path.glob("*.yaml")) + sorted(path.glob("*.yml")):
            result = validator.validate(profile_file)
            results.append(result)
    else:
        print(f"Error: Path does not exist: {path}")
        sys.exit(1)

    _print_results(results, args.format, args.no_warnings)

    # Exit code
    has_errors = any(not r.is_valid for r in results)
    sys.exit(1 if has_errors else 0)


def _validate_pipelines(args) -> None:
    """Validate pipeline file(s).

    Args:
        args: Parsed arguments with path, recursive, format, no_warnings
    """
    path = Path(args.path)

    # Auto-detect workspace root from file structure
    workspace_root = detect_module_root(path)
    if not workspace_root:
        # Fallback: assume current directory or parent structure
        workspace_root = path.parent if path.is_dir() else path.parent.parent.parent

    context = discover_modules(workspace_root)
    validator = PipelineValidator(context)

    results = []

    if path.is_file():
        # Single file
        result = validator.validate(path)
        results.append(result)
    elif path.is_dir() and args.recursive:
        # Directory - recursive
        for pipeline_file in sorted(path.glob("**/*.yaml")) + sorted(path.glob("**/*.yml")):
            result = validator.validate(pipeline_file)
            results.append(result)
    elif path.is_dir():
        # Directory - non-recursive
        for pipeline_file in sorted(path.glob("*.yaml")) + sorted(path.glob("*.yml")):
            result = validator.validate(pipeline_file)
            results.append(result)
    else:
        print(f"Error: Path does not exist: {path}")
        sys.exit(1)

    _print_results(results, args.format, args.no_warnings)

    # Exit code
    has_errors = any(not r.is_valid for r in results)
    sys.exit(1 if has_errors else 0)


def _validate_all(args) -> None:
    """Validate entire workspace.

    Args:
        args: Parsed arguments with workspace, format, no_warnings
    """
    workspace = Path(args.workspace)
    context = discover_modules(workspace)

    results = []

    # Validate snippets
    snippet_validator = SnippetValidator(context)
    for snippet_file in context.snippet_paths:
        result = snippet_validator.validate(snippet_file)
        results.append(result)

    # Validate profiles
    profile_validator = ProfileValidator(context)
    for profile_file in context.profile_paths:
        result = profile_validator.validate(profile_file)
        results.append(result)

    # Validate pipelines
    pipeline_validator = PipelineValidator(context)
    for pipeline_file in context.pipeline_paths:
        result = pipeline_validator.validate(pipeline_file)
        results.append(result)

    _print_results(results, args.format, args.no_warnings)

    # Exit code
    has_errors = any(not r.is_valid for r in results)
    sys.exit(1 if has_errors else 0)


def _start_lsp_server(args) -> None:
    """Start the LSP server.

    Args:
        args: Parsed arguments with stdio, tcp, log_file
    """
    from pype.lsp import start_server

    log_file = args.log_file or "/tmp/bio_pype_lsp.log"

    # Determine transport mode
    if args.tcp:
        print(f"Starting LSP server on TCP port {args.tcp}")
        start_server(use_stdio=False, tcp_port=args.tcp, log_file=log_file)
    else:
        print("Starting LSP server on stdio")
        start_server(use_stdio=True, log_file=log_file)


def _print_results(results: List, format_type: str, no_warnings: bool = False) -> None:
    """Print validation results.

    Args:
        results: List of ValidationResult objects
        format_type: Output format ('text' or 'json')
        no_warnings: Hide warning messages
    """
    if format_type == "json":
        output = [r.to_dict() for r in results]
        print(json.dumps(output, indent=2))
    else:
        _print_text_results(results, no_warnings)


def _print_text_results(results: List, no_warnings: bool = False) -> None:
    """Print validation results in human-readable text format.

    Args:
        results: List of ValidationResult objects
        no_warnings: Hide warning messages
    """
    # Color codes
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"

    total_files = len(results)
    valid_files = sum(1 for r in results if r.is_valid)
    error_count = sum(len([d for d in r.diagnostics if d.severity.value == "error"]) for r in results)
    warning_count = sum(len([d for d in r.diagnostics if d.severity.value == "warning"]) for r in results)

    # Print summary header
    print(f"\n{BLUE}Validation Results{END}")
    print(f"{'='*60}")

    # Print details for each file
    for result in results:
        status_symbol = f"{GREEN}✓{END}" if result.is_valid else f"{RED}✗{END}"
        print(f"\n{status_symbol} {result.file_path}")

        if not result.diagnostics:
            print(f"  {GREEN}No issues found{END}")
            continue

        for diag in result.diagnostics:
            severity_str = diag.severity.value
            if diag.severity.value == "error":
                severity_color = RED
            elif diag.severity.value == "warning":
                severity_color = YELLOW
            else:
                severity_color = BLUE

            # Skip warnings if no_warnings flag is set
            if no_warnings and diag.severity.value == "warning":
                continue

            line_info = f":{diag.location.line+1}"
            print(f"  {severity_color}[{severity_str.upper()}]{END} {line_info} {diag.message}")
            if diag.code:
                print(f"            ({diag.code})")
            if diag.suggestion:
                print(f"            {GREEN}→ {diag.suggestion}{END}")

    # Print summary
    print(f"\n{'='*60}")
    print(
        f"Files: {valid_files}/{total_files} valid | "
        f"Errors: {RED}{error_count}{END} | "
        f"Warnings: {YELLOW}{warning_count}{END}"
    )
    print()
