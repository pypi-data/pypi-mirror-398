import os

from pype.exceptions import ProfileError
from pype.misc import try_import


def load_config(config_file):
    res = {}
    if os.path.isfile(config_file):
        with open(config_file, "rt") as config:
            for line_num, line in enumerate(config, 1):
                # Remove inline comments (# at end of line)
                # But preserve # inside quoted strings
                if "#" in line:
                    # Check if # is inside quotes
                    in_quote = False
                    quote_char = None
                    for i, char in enumerate(line):
                        if char in ('"', "'"):
                            if not in_quote:
                                in_quote = True
                                quote_char = char
                            elif char == quote_char:
                                in_quote = False
                        elif char == "#" and not in_quote:
                            line = line[:i]
                            break

                # Skip full-line comments and empty lines
                if line.startswith("#"):
                    continue
                if not line.strip():
                    continue

                # Parse key=value (handle values with = in them)
                if "=" not in line:
                    continue

                key, val = line.split("=", 1)  # maxsplit=1 to handle = in values

                # Strip whitespace and quotes from value
                val = val.strip()
                val = val.strip('"').strip("'")

                res[key.strip()] = val
    return res


home_dir = os.path.expanduser("~")
PYPE_HOME = os.path.join(home_dir, ".bio_pype")
pype_config = os.path.join(PYPE_HOME, "config")

try:
    conf_dict = load_config(pype_config)
except Exception:
    conf_dict = {}

env_vars = [
    "PYPE_MODULES",
    "PYPE_SNIPPETS",
    "PYPE_PROFILES",
    "PYPE_PIPELINES",
    "PYPE_QUEUES",
    "PYPE_REPOS",
    "PYPE_NCPU",
    "PYPE_MEM",
    "PYPE_TMP",
    "PYPE_LOGDIR",
    "PYPE_DOCKER",
    "PYPE_SINGULARITY_CACHE",
    "COMPUTE_BIO_API_URL",
    "COMPUTE_BIO_TOKEN",
]
env_dict = {}

for env_var in env_vars:
    env_dict[env_var] = os.environ.get(env_var)
    if env_dict[env_var] is None and env_var in conf_dict.keys():
        env_dict[env_var] = conf_dict[env_var]


PYPE_SNIPPETS = None
PYPE_PROFILES = None
PYPE_PIPELINES = None
PYPE_QUEUES = None
PYPE_REPOS = None


def get_default_base():
    base = os.path.dirname(os.path.abspath(__file__))
    return base


DEFAULT_PYPE_MODULES_PATH = os.path.join(get_default_base(), "pype_modules")


def import_and_default(module_path, module_name, default_base):
    """Import module with fallback to default.

    If module_path doesn't exist, returns default module directly.
    If module_path exists, extends its __path__ with default paths
    to allow fallback module discovery.

    Args:
        module_path: Path to custom module (e.g., /path/to/queues)
        module_name: Name of module to import (e.g., 'queues')
        default_base: Path to default modules (e.g., pype/pype_modules)

    Returns:
        Imported module with fallback paths configured
    """
    mod_default = try_import(default_base, module_name)

    if module_path:
        # Only load custom module if the path actually exists
        # This prevents creating empty directories that shadow defaults
        if os.path.exists(module_path):
            base, name = os.path.split(os.path.abspath(module_path))
            mod = try_import(base, name)
            # Extend module search path with default paths for fallback discovery
            mod.__path__.extend(mod_default.__path__)
            return mod
        # Custom path doesn't exist, use default only

    return mod_default


if env_dict["PYPE_MODULES"]:
    PYPE_SNIPPETS = import_and_default(
        os.path.join(env_dict["PYPE_MODULES"], "snippets"),
        "snippets",
        DEFAULT_PYPE_MODULES_PATH,
    )
    PYPE_PROFILES = import_and_default(
        os.path.join(env_dict["PYPE_MODULES"], "profiles"),
        "profiles",
        DEFAULT_PYPE_MODULES_PATH,
    )
    PYPE_PIPELINES = import_and_default(
        os.path.join(env_dict["PYPE_MODULES"], "pipelines"),
        "pipelines",
        DEFAULT_PYPE_MODULES_PATH,
    )
    PYPE_QUEUES = import_and_default(
        os.path.join(env_dict["PYPE_MODULES"], "queues"),
        "queues",
        DEFAULT_PYPE_MODULES_PATH,
    )
else:
    PYPE_SNIPPETS = import_and_default(
        env_dict["PYPE_SNIPPETS"], "snippets", DEFAULT_PYPE_MODULES_PATH
    )
    PYPE_PROFILES = import_and_default(
        env_dict["PYPE_PROFILES"], "profiles", DEFAULT_PYPE_MODULES_PATH
    )
    PYPE_PIPELINES = import_and_default(
        env_dict["PYPE_PIPELINES"], "pipelines", DEFAULT_PYPE_MODULES_PATH
    )
    PYPE_QUEUES = import_and_default(
        env_dict["PYPE_QUEUES"], "queues", DEFAULT_PYPE_MODULES_PATH
    )

if env_dict["PYPE_TMP"] is None:
    PYPE_TMP = "/tmp"
else:
    PYPE_TMP = env_dict["PYPE_TMP"]

if env_dict["PYPE_LOGDIR"] is None:
    PYPE_LOGDIR = os.path.join(PYPE_HOME, "logs")
else:
    PYPE_LOGDIR = env_dict["PYPE_LOGDIR"]


if env_dict["PYPE_REPOS"] is None:
    PYPE_REPOS = os.path.join(DEFAULT_PYPE_MODULES_PATH, "repos.yaml")
else:
    PYPE_REPOS = env_dict["PYPE_REPOS"]
    if not os.path.isfile(PYPE_REPOS):
        raise ProfileError(f"Repository file {PYPE_REPOS} does not exist")

if env_dict["PYPE_DOCKER"] is None:
    PYPE_DOCKER = "docker"
else:
    PYPE_DOCKER = env_dict["PYPE_DOCKER"]

if env_dict["PYPE_SINGULARITY_CACHE"] is None:
    PYPE_SINGULARITY_CACHE = os.getcwd()
else:
    PYPE_SINGULARITY_CACHE = env_dict["PYPE_SINGULARITY_CACHE"]

PYPE_MEM = env_dict["PYPE_MEM"]
PYPE_NCPU = env_dict["PYPE_NCPU"]

# compute.bio API integration (optional)
# Set these environment variables or add to ~/.bio_pype/config to enable API monitoring
COMPUTE_BIO_API_URL = env_dict["COMPUTE_BIO_API_URL"]
COMPUTE_BIO_TOKEN = env_dict["COMPUTE_BIO_TOKEN"]


def reload_pype_queues():
    """Reload PYPE_QUEUES module after environment variable changes.

    This is useful when environment variables (like PYPE_MODULES) are changed
    after initial import, such as during pipeline resume operations.

    Returns:
        Reloaded PYPE_QUEUES module
    """
    global PYPE_QUEUES

    pype_modules = os.environ.get("PYPE_MODULES")

    if pype_modules:
        PYPE_QUEUES = import_and_default(
            os.path.join(pype_modules, "queues"),
            "queues",
            DEFAULT_PYPE_MODULES_PATH,
        )
    else:
        PYPE_QUEUES = import_and_default(
            os.environ.get("PYPE_QUEUES"), "queues", DEFAULT_PYPE_MODULES_PATH
        )

    return PYPE_QUEUES


def reload_pype_snippets():
    """Reload PYPE_SNIPPETS module after environment variable changes.

    This is useful when environment variables (like PYPE_MODULES) are changed
    after initial import, such as during pipeline resume operations.

    Returns:
        Reloaded PYPE_SNIPPETS module
    """
    global PYPE_SNIPPETS

    pype_modules = os.environ.get("PYPE_MODULES")

    if pype_modules:
        PYPE_SNIPPETS = import_and_default(
            os.path.join(pype_modules, "snippets"),
            "snippets",
            DEFAULT_PYPE_MODULES_PATH,
        )
    else:
        PYPE_SNIPPETS = import_and_default(
            os.environ.get("PYPE_SNIPPETS"), "snippets", DEFAULT_PYPE_MODULES_PATH
        )

    return PYPE_SNIPPETS
