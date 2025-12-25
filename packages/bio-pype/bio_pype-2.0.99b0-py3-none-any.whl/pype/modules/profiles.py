"""Profile command-line interface module.

This module provides the command-line interface for profile management:
- Profile validation and checking
- Software/tool version verification
- Resource path validation
- Profile information display

The module serves as the entry point for the 'pype profiles' command.

Example:
    pype profiles info
    pype profiles check my_profile
    pype profiles check my_profile --files
"""

from pype.__config__ import PYPE_LOGDIR, PYPE_SINGULARITY_CACHE, PYPE_DOCKER
from pype.argparse import ArgumentParser, _SubParsersAction
from pype.logger import PypeLogger
from pype.modules import create_module_parser
from pype.utils.profiles import (
    check_profile_files,
    get_profiles,
    print_checks,
    pull_profile_images,
    validate_all_programs,
)


def add_parser(subparsers: _SubParsersAction, module_name: str) -> ArgumentParser:
    """Add profile command parser.

    Args:
        subparsers: Parent parser's subparsers
        module_name: Name of this module

    Returns:
        Parser for profile commands
    """
    return create_module_parser(subparsers, module_name)


def profiles_args(parser, argv):
    lastparsers = parser.add_subparsers(dest="profile")
    lastparsers.add_parser(
        "info", add_help=False, help="Retrieve details from available profiles"
    )
    lastparsers.add_parser("check", add_help=False, help="Check if a profile is valid")
    lastparsers.add_parser(
        "pull", add_help=False, help="Pull Singularity images for a profile"
    )
    args, extra = parser.parse_known_args(argv)
    profiles_list = get_profiles({})
    if args.profile == "info":
        info_profiles(lastparsers, profiles_list, extra)
    elif args.profile == "check":
        check_profiles(lastparsers, profiles_list, extra)
    elif args.profile == "pull":
        pull_profiles(lastparsers, profiles_list, extra)
    else:
        parser.print_help()


def profiles(subparsers, module_name, argv, profile):
    profiles_args(add_parser(subparsers, module_name), argv)


def check_profiles(parser, profiles_list, argv):
    subparser = parser.add_parser("check", add_help=False)
    subparser.add_argument(
        "name",
        action="store",
        choices=profiles_list.keys(),
        help="Name of profile to check",
    )
    subparser.add_argument(
        "-f",
        "--files",
        dest="files",
        action="store_true",
        help="Check only the Profile files",
    )
    subparser.add_argument(
        "-p",
        "--programs",
        dest="programs",
        action="store_true",
        help="Check only the Profile programs",
    )
    subparser.add_argument(
        "--log",
        dest="log",
        type=str,
        default=PYPE_LOGDIR,
        help=("Path used to write the profile check logs. Default %s" % PYPE_LOGDIR),
    )
    args = subparser.parse_args(argv)
    profile = profiles_list[args.name]

    # Create logger for validation
    log = PypeLogger(f"{args.name}_profile_check", path=args.log, profile=profile)

    if args.files == args.programs:
        files = True
        programs = True
    else:
        files = args.files
        programs = args.programs
    if files is True:
        files_check = check_profile_files(profiles_list[args.name])
        print_checks(files_check, profile.files)
    if programs is True:
        programs_check = validate_all_programs(profile, log)
        print_checks(programs_check, profile.programs)


def info_profiles(parser, profiles_list, argv):
    subparser = parser.add_parser("info", add_help=False)
    subparser.add_argument(
        "-p",
        "--profile",
        dest="profile",
        action="store",
        choices=profiles_list.keys(),
        help="Print details of a selected profile",
    )
    subparser.add_argument(
        "-a", "--all", dest="all", action="store_true", help="List all profiles"
    )
    args = subparser.parse_known_args(argv)[0]
    if args.all:
        for profile in profiles_list:
            print("%s:\t%s" % (profile, profiles_list[profile].info["description"]))
    elif args.profile:
        used_profile = args.profile
        if used_profile in profiles_list.keys():
            profiles_list[used_profile].describe()
    else:
        subparser.print_help()


def pull_profiles(parser, profiles_list, argv):
    """Pull Singularity images for a profile.

    Fetches all docker-namespace container images in a profile to the
    Singularity cache directory. Images are stored using a consistent
    directory structure that matches the Namespace class path construction.

    Args:
        parser: Argument subparsers object
        profiles_list: Dict of available profiles
        argv: Command-line arguments
    """
    subparser = parser.add_parser("pull", add_help=False)
    subparser.add_argument(
        "name",
        action="store",
        choices=profiles_list.keys(),
        help="Name of profile to pull images for",
    )
    subparser.add_argument(
        "--force",
        dest="force",
        action="store_true",
        help="Re-pull images even if they already exist",
    )
    subparser.add_argument(
        "--cache",
        dest="cache",
        action="store",
        default=PYPE_SINGULARITY_CACHE,
        help=f"Singularity cache directory (default: {PYPE_SINGULARITY_CACHE})",
    )
    args = subparser.parse_args(argv)

    profile = profiles_list[args.name]

    # Create a simple logger
    class SimpleLogger:
        """Minimal logger for pull command output."""

        class Log:
            @staticmethod
            def info(msg):
                print(f"INFO: {msg}")

            @staticmethod
            def error(msg):
                print(f"ERROR: {msg}")

            @staticmethod
            def debug(msg):
                pass  # Suppress debug output for cleaner output

        log = Log()

    log = SimpleLogger()

    print(f"Profile: {args.name}")
    print(f"Cache: {args.cache}")
    print("=" * 80)

    # Pull images
    results = pull_profile_images(profile, args.cache, PYPE_DOCKER, log, force=args.force)

    # Display results
    print()
    print("Pull Results:")
    print("-" * 80)

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for program_name, result in results.items():
        status = (
            "✓"
            if result["success"]
            else "✗"
            if result["message"].startswith("Not a docker")
            else "✗"
        )

        if result["success"]:
            success_count += 1
        elif "skipped" in result["message"].lower():
            skipped_count += 1
        else:
            failed_count += 1

        print(f"  {status} {program_name:20} {result['message']}")

    print("-" * 80)
    print(
        f"Summary: {success_count} success, {failed_count} failed, {skipped_count} skipped"
    )

    if failed_count > 0:
        import sys

        sys.exit(1)
