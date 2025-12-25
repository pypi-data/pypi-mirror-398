from pype import __config__
import contextlib
import yaml
import os
import sys
from io import BytesIO
import tarfile
from urllib.request import urlopen
from pype.exceptions import PypeError


def add_parser(subparsers, module_name):
    return subparsers.add_parser(
        module_name, help=("Manage pype modules"), add_help=False
    )


def repos_args(parser, argv):
    lastparsers = parser.add_subparsers(dest="repos")
    parser.add_argument(
        "-r",
        "--repo",
        dest="repo_list",
        default=__config__.PYPE_REPOS,
        help="Repository list. Default: %s" % __config__.PYPE_REPOS,
    )
    lastparsers.add_parser(
        "list", add_help=False, help="List the available repositories"
    )
    lastparsers.add_parser(
        "install", add_help=False, help="Install modules from selected repository"
    )
    lastparsers.add_parser("init", add_help=False, help="Initiate an empty repository")
    lastparsers.add_parser("clean", add_help=False, help=("Cleanup all module folders"))
    lastparsers.add_parser(
        "info",
        add_help=False,
        help=("Print location of the modules " "currently in use"),
    )
    args, extra = parser.parse_known_args(argv)
    if args.repos == "list":
        list_repos(args.repo_list)
        return None
    if args.repos == "install":
        install(lastparsers, extra, args.repo_list, __config__)
        return None
    if args.repos == "info":
        info(__config__)
        return None
    if args.repos == "init":
        init(lastparsers, extra)
        return None
    if args.repos == "clean":
        cleanup_dirs(lastparsers, extra, __config__)
        return None
    return parser.print_help()


def repos(subparsers, module_name, argv, profile):
    args = repos_args(add_parser(subparsers, module_name), argv)
    return args


def load_repos(repo_list):
    if len(repo_list.split("://")) < 2:
        repo_list = "file://%s" % repo_list
    with contextlib.closing(urlopen(repo_list)) as repo_yaml:
        try:
            repo = yaml.safe_load(repo_yaml.read())
        except yaml.scanner.ScannerError:
            raise PypeError("No repo file available or not in YAML format")
    return repo


def list_repos(repo_list):
    repo = load_repos(repo_list)
    for rec in repo["repositories"]:
        bullet = "-"
        print(
            "%s %s\n\t%s\n\thomepage: %s\n\tsource: %s"
            % (bullet, rec["name"], rec["description"], rec["homepage"], rec["source"])
        )


def info(config):
    paths = config_paths(config)
    print_info("Profiles", paths["profiles"], "PYPE_PROFILES")
    print_info("Pipelines", paths["pipelines"], "PYPE_PIPELINES")
    print_info("Snippets", paths["snippets"], "PYPE_SNIPPETS")
    print_info("Queues", paths["queues"], "PYPE_QUEUES")


def print_info(mod_name, mod_path, env_module):
    greencol = "\033[92m"
    redcol = "\033[91m"
    endcol = "\033[0m"
    print(
        (
            "- %s\n\t* modules path in use: %s%s%s\n"
            "\t tip: Adjust the env. variable %s%s%s for"
            " a different module path"
        )
        % (
            mod_name,
            greencol,
            os.path.abspath(mod_path),
            endcol,
            redcol,
            env_module,
            endcol,
        )
    )


def config_paths(config):
    modules_dirs = {
        "profiles": config.PYPE_PROFILES.__path__[0],
        "pipelines": config.PYPE_PIPELINES.__path__[0],
        "queues": config.PYPE_QUEUES.__path__[0],
        "snippets": config.PYPE_SNIPPETS.__path__[0],
    }
    return modules_dirs


def install(parser, extra, repo_list, config):
    subparser = parser.add_parser("install", add_help=False)
    subparser.add_argument(
        "name",
        help=(
            "Repository name to be installed, see repos " "list for repository names"
        ),
    )
    subparser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        help="Overwrite files if present",
    )
    args = subparser.parse_args(extra)
    repo_meta = None
    repo = load_repos(repo_list)
    for rec in repo["repositories"]:
        if rec["name"] == args.name:
            repo_meta = rec
    if repo_meta is None:
        print("The repository %s is not in the repository list" % args.name)
        sys.exit()
    try:
        subproject = repo_meta["subproject"]
    except KeyError:
        subproject = None
    modules_paths = config_paths(config)
    source = download_tar_archive(repo_meta["source"])
    install_tar_archive(source, modules_paths, args.force, subproject)


def init(parser, extra):
    subparser = parser.add_parser("init repository", add_help=False)
    subparser.add_argument(
        "path",
        help=(
            "path of the repository to init. "
            "This will create snippets/pipelines/profiles/queue "
            "modules in the specified path"
        ),
    )
    args = subparser.parse_args(extra)
    module_path = os.path.realpath(args.path)
    if not os.path.isdir(module_path):
        if os.path.exists(module_path):
            raise PypeError(f"{module_path} is not a folder")
        os.makedirs(module_path)
    for module in ("profiles", "pipelines", "snippets", "queues"):
        module_dir = os.path.join(module_path, module)
        module_init_file = os.path.join(module_dir, "__init__.py")
        os.mkdir(module_dir)
        print("Creating __init__.py in %s" % module_init_file)
        open(module_init_file, "ab").close()


def download_tar_archive(url):
    print("Downloading source at %s" % url)
    response = urlopen(url)
    results = tarfile.open(fileobj=BytesIO(response.read()))
    print("Source downloaded")
    return results


def install_tar_archive(tar, paths, force, subproject):
    for element in tar.getmembers():
        write = False
        base, file_source = os.path.split(element.name)
        root, module = os.path.split(base)
        if subproject is None:
            pass
        else:
            sub = os.path.basename(root)
            if sub != subproject:
                continue
        if module in paths.keys():
            outfile = os.path.join(paths[module], file_source)
            if force is True:
                write = True
            else:
                if os.path.isfile(outfile):
                    write = False
                else:
                    write = True
            if write is True:
                with open(outfile, "wb") as install_file:
                    print("Installing source %s into file %s" % (element.name, outfile))
                    for content in tar.extractfile(element):
                        install_file.write(content)
            else:
                print(
                    ("Skip installation of %s, " "file already exists") % element.name
                )
    print("Installation completed")


def cleanup_dirs(parser, extra, config):
    subparser = parser.add_parser("clean", add_help=False)
    subparser.add_argument(
        "-y",
        "--yes",
        dest="yes",
        action="store_true",
        help=("Imply yes, avoiding all " "interactive questions"),
    )
    args = subparser.parse_args(extra)
    answered = args.yes
    paths = config_paths(config)
    question = ("Do you really want to delete " "all files in %s? (Y/N)") % ", ".join(
        paths.values()
    )
    while answered is False:
        print(question)
        answer = input("--> ")
        if answer == "Y":
            answered = True
        elif answer == "N":
            answered = True
            print("Stop cleaning process")
            sys.exit()
    for module in paths:
        print("Deleting file in folder %s" % paths[module])
        path = paths[module]
        for file_name in os.listdir(path):
            file_path = os.path.join(path, file_name)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)
        init_file = os.path.join(path, "__init__.py")
        if os.path.isfile(init_file):
            pass
        else:
            print("Creating __init__.py in %s" % init_file)
            with open(init_file, "wb") as module_init:
                module_init.write(str())
