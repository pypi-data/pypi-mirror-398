#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pype.modules
from pype.__config__ import PYPE_PROFILES
from pype.__version__ import AUTHOR, DATE, VERSION
from pype.exceptions import ProfileError
from pype.misc import DefaultHelpParser, SubcommandHelpFormatter, get_modules
from pype.utils.profiles import get_profiles


def main():
    """
    Execute the function with args
    """
    try:
        default_p = PYPE_PROFILES.default
    except AttributeError:
        profiles = get_profiles({})
        if "default" in profiles.keys():
            default_p = "default"
        else:
            if len(profiles) > 2:
                raise ProfileError(
                    'no "default" profile set in profiles/__init__.py '
                    "nor a profile named default.yaml was found"
                )
            try:
                default_p = list(profiles.keys())[0]
            except IndexError:
                default_p = None
    parser = DefaultHelpParser(
        prog="pype",
        formatter_class=lambda prog: SubcommandHelpFormatter(
            prog, max_help_position=20, width=75
        ),
        description=("A python pipeliens manager oriented for bioinformatics"),
        add_help=False,
        epilog="This is version %s - %s - %s" % (VERSION, AUTHOR, DATE),
    )
    parser.add_argument(
        "-p",
        "--profile",
        dest="profile",
        type=str,
        default=default_p,
        help=(
            "Choose the pype profile from "
            "the available options ("
            "see pype profiles). "
            "Default: %s"
        )
        % default_p,
    )
    subparsers = parser.add_subparsers(dest="module")

    modules = get_modules(pype.modules, subparsers, {})
    args, extra = parser.parse_known_args()
    try:
        use_module = args.module
        use_profile = args.profile
        if use_module in modules.keys():
            modules[use_module](subparsers, use_module, extra, use_profile)
            return None
        if args.module is None:
            return parser.print_help()
        return parser.parse_args(args)
    except IndexError:
        return parser.print_help()


if __name__ == "__main__":
    main()
