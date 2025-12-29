"""Snippet command-line interface module.

This module provides the command-line interface for snippet operations:
- Individual snippet execution
- Snippet discovery and listing
- Argument parsing and validation
- Logging configuration

The module serves as the entry point for the 'pype snippets' command.

Example:
    pype snippets reverse_fa -i input.fa -o reversed.fa
    pype snippets list
    pype snippets --help
"""

import os
import sys

from pype.__config__ import PYPE_LOGDIR
from pype.argparse import ArgumentParser, _SubParsersAction
from pype.exceptions import CommandError, SnippetExecutionError
from pype.logger import PypeLogger
from pype.modules import create_module_parser
from pype.modules.profiles import get_profiles
from pype.utils.snippets import snippets_modules_list

PYPE_SNIPPETS_MODULES = snippets_modules_list({})


def add_parser(parser: _SubParsersAction, module_name: str) -> ArgumentParser:
    """Add snippet command parser.

    Args:
        parser: Parent parser's subparsers
        module_name: Name of this module

    Returns:
        Parser for snippet commands
    """
    return create_module_parser(parser, module_name)


def snippets_args(parser, argv, profile):
    lastparsers = parser.add_subparsers(dest="snippet")
    parser.add_argument(
        "--log",
        dest="log",
        type=str,
        default=PYPE_LOGDIR,
        help=("Path used for the snippet logs. Default: %s" % PYPE_LOGDIR),
    )
    for snippet_name in PYPE_SNIPPETS_MODULES:
        PYPE_SNIPPETS_MODULES[snippet_name].add_parser(lastparsers)
    args, extra = parser.parse_known_args(argv)
    try:
        used_snippet = args.snippet
        if used_snippet in PYPE_SNIPPETS_MODULES.keys():
            profile = get_profiles({})[profile]
            log = PypeLogger(used_snippet, args.log, profile)
            log.log.info("Prepare snippet %s" % used_snippet)
            log.log.info("Attempt to execute snippet %s" % used_snippet)

            snippet_obj = PYPE_SNIPPETS_MODULES[used_snippet]

            try:
                # Execute the snippet
                snippet_obj.snippet(lastparsers, extra, profile, log)
                log.log.info("Snippet %s executed successfully" % used_snippet)

                # Validate expected result files if enabled (following pipeline.py pattern)
                # Parse arguments using snippet's own argparse to get arg_dict
                try:
                    # Check if result validation is enabled
                    if (
                        hasattr(snippet_obj, "check_results_enabled")
                        and not snippet_obj.check_results_enabled()
                    ):
                        log.log.debug(
                            f"Result file validation disabled for snippet {used_snippet}"
                        )
                    else:
                        # Try to parse arguments - use return_args if available for SnippetMd
                        if hasattr(snippet_obj, "return_args"):
                            # SnippetMd has return_args() which handles arg conversion
                            arg_dict = {}
                            for arg in extra:
                                if arg.startswith("--"):
                                    key = arg.lstrip("-")
                                    idx = extra.index(arg)
                                    if idx + 1 < len(extra) and not extra[
                                        idx + 1
                                    ].startswith("--"):
                                        arg_dict[key] = extra[idx + 1]
                            arg_dict = snippet_obj.return_args(arg_dict)
                        else:
                            # For regular Python snippets, try parsing with snippet's parser
                            snippet_subparser = snippet_obj.add_parser(lastparsers)
                            try:
                                parsed_args = snippet_subparser.parse_args(extra)
                                arg_dict = vars(parsed_args)
                            except SystemExit:
                                # Snippet has different args, can't validate - skip
                                log.log.debug(
                                    f"Could not parse args for results validation"
                                )
                                arg_dict = None

                        if arg_dict is not None:
                            results = snippet_obj.results(arg_dict)
                            # Flatten results dict values into list of file paths
                            if isinstance(results, dict):
                                result_files = []
                                for val in results.values():
                                    if isinstance(val, list):
                                        result_files.extend(val)
                                    else:
                                        result_files.append(val)
                            else:
                                result_files = []

                            if result_files:
                                log.log.info(
                                    "Checking result file(s): %s"
                                    % ", ".join(result_files)
                                )
                                missing_files = [
                                    f for f in result_files if not os.path.isfile(f)
                                ]

                                if missing_files:
                                    error_msg = (
                                        f"Snippet '{used_snippet}' completed but expected result "
                                        f"file(s) not found: {', '.join(missing_files)}"
                                    )
                                    log.log.error(error_msg)
                                    raise SnippetExecutionError(
                                        error_msg, snippet_name=used_snippet
                                    )

                                log.log.info(
                                    "All expected result files created successfully"
                                )
                except AttributeError:
                    # Snippet doesn't have results() method - skip validation
                    log.log.debug(f"Snippet {used_snippet} has no results() method")

            except (CommandError, SnippetExecutionError) as e:
                log.log.error(f"Snippet execution failed: {e}")
                sys.exit(1)
            except KeyboardInterrupt:
                log.log.info("Shutdown requested (Ctrl+C)")
                sys.exit(0)
            except Exception as e:
                log.log.error(f"Unexpected error during snippet execution: {e}")
                raise

            return None
        if args.snippet is None:
            return parser.print_help()
        return parser.parse_args(args)
    except IndexError:
        return parser.print_help()


def snippets(parser, module_name, argv, profile):
    args = snippets_args(add_parser(parser, module_name), argv, profile)
    return args
