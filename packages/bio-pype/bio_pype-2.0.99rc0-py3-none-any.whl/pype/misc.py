import datetime
import gzip
import os
import secrets
import string
import sys
import time
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TextIO, Union

from pype import argparse
from pype.exceptions import CommandError


def import_module(module_name: str, module_path: str) -> types.ModuleType:
    """Import a module from a specific path.

    Args:
        module_name: Name to give to the imported module
        module_path: Path to the module file

    Returns:
        Imported module object

    Raises:
        ImportError: If module cannot be loaded
    """
    spec = spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create module specification for {module_path}")

    module = module_from_spec(spec)
    sys.modules[module_name] = module  # Register the module in sys.modules
    spec.loader.exec_module(module)
    return module


def generate_uid(n: int = 4, timestamp: bool = True) -> str:
    """Generate a unique identifier with timestamp and random chars."""
    timestamp_str = datetime.datetime.now().strftime("%y%m%d%H%M%S.%f")
    random_str = "".join(
        [secrets.choice(string.ascii_uppercase + string.digits) for _ in range(n)]
    )
    if timestamp:
        return f"{timestamp_str}_{random_str}"
    else:
        return random_str


def package_modules(package: types.ModuleType) -> Set[str]:
    """Get all Python modules in a package directory."""
    modules = set()
    for path_str in package.__path__:
        path = Path(path_str)
        modules.update(
            {
                f"{package.__name__}.{module.stem}"
                for module in path.glob("*.py")
                if module.name != "__init__.py"
            }
        )
    return modules


def package_files(package: types.ModuleType, extension: str) -> Set[str]:
    """Get all files with specific extension in a package directory."""
    files = set()
    for path_dir in package.__path__:
        path = Path(path_dir)
        files.update({str(file.absolute()) for file in path.glob(f"*{extension}")})
    return files


def try_import(path: str, module_name: str) -> types.ModuleType:
    """Import a module, creating __init__.py if needed.

    Args:
        path: Directory path where the module should be located/created
        module_name: Name of the module to import

    Returns:
        Imported module object

    Raises:
        ImportError: If module cannot be created or loaded
    """
    module_path = Path(path) / module_name
    init_path = module_path / "__init__.py"

    try:
        # Ensure directory and init file exist
        module_path.mkdir(parents=True, exist_ok=True)
        if not init_path.exists():
            init_path.touch()

        # Create module spec and load module
        spec = spec_from_file_location(module_name, str(init_path))
        if spec is None or spec.loader is None:
            raise ImportError(
                f"Could not create module specification for {module_name}"
            )
        module = module_from_spec(spec)
        sys.modules[module_name] = module  # Register the module in sys.modules
        spec.loader.exec_module(module)
        return module

    except Exception as e:
        raise ImportError(
            f"Failed to import module '{module_name}' from path '{path}': {e}"
        ) from e


def get_modules(parent: types.ModuleType, subparsers: Any, progs: Dict) -> Dict:
    """Get all modules and their parsers."""
    for mod_path in sorted(package_modules(parent)):
        try:
            __import__(mod_path)
            mod_name = mod_path.split(".")[-1]
            module = getattr(parent, mod_name)
            module.add_parser(subparsers, mod_name)
            progs[mod_name] = getattr(module, mod_name)
        except AttributeError:
            pass
    return progs


def get_modules_names(parent: types.ModuleType) -> List[str]:
    """Get names of all valid modules in parent."""
    mods = package_modules(parent)
    modules = []

    for mod in mods:
        try:
            mod_name = mod.split(".")[-1]

            # Try to find the module file in parent's __path__
            for path_dir in parent.__path__:
                module_file = Path(path_dir) / f"{mod_name}.py"
                if module_file.exists():
                    # Load module directly from file
                    spec = spec_from_file_location(mod, str(module_file))
                    if spec and spec.loader:
                        loaded_mod = module_from_spec(spec)
                        sys.modules[mod] = loaded_mod
                        spec.loader.exec_module(loaded_mod)
                        # Cache in parent for easy access
                        setattr(parent, mod_name, loaded_mod)
                        modules.append(mod_name)
                    break
        except (ModuleNotFoundError, ImportError, AttributeError):
            pass

    return modules


def get_module_method(
    parent: types.ModuleType, module: str, method: str
) -> Optional[Any]:
    """Get a specific method from a module.

    Args:
        parent: Parent module package
        module: Name of submodule within parent
        method: Name of method/function to retrieve

    Returns:
        The method/function if found, None otherwise
    """
    try:
        # First try to get the submodule as an attribute (if already imported)
        mod = getattr(parent, module, None)

        # If not found, try to import it dynamically by searching parent.__path__
        # This respects the extended __path__ from import_and_default()
        if mod is None:
            # Search through parent's __path__ (includes both custom and default paths)
            print(
                f"DEBUG get_module_method: Looking for {module} in parent.__path__: {parent.__path__}"
            )
            for path_dir in parent.__path__:
                module_file = Path(path_dir) / f"{module}.py"
                print(f"DEBUG: Checking {module_file}, exists={module_file.exists()}")
                if module_file.exists():
                    print(f"DEBUG: Found {module_file}, attempting to load...")
                    # Load module directly from file
                    full_module_name = f"{parent.__name__}.{module}"
                    spec = spec_from_file_location(full_module_name, str(module_file))
                    print(
                        f"DEBUG: spec={spec}, spec.loader={spec.loader if spec else None}"
                    )
                    if spec and spec.loader:
                        mod = module_from_spec(spec)
                        sys.modules[full_module_name] = mod
                        spec.loader.exec_module(mod)
                        # Cache in parent for future access
                        setattr(parent, module, mod)
                        print(f"DEBUG: Successfully loaded {module}")
                        break

            # If still not found, return None
            if mod is None:
                return None

        return getattr(mod, method)
    except (AttributeError, ImportError, ModuleNotFoundError):
        return None


def xopen(filename: str, mode: str = "r") -> Any:
    """Smart file opener that handles gzip and stdin/stdout."""
    if not isinstance(filename, str):
        raise TypeError("Filename must be a string")
    if filename == "-":
        return sys.stdin if "r" in mode else sys.stdout
    opener = gzip.open if filename.endswith(".gz") else open
    return opener(filename, mode)


def check_exit_code(process, sting, results_dict, log):
    log.log.info("Checking exit code for process %s" % string)
    code = process.returncode
    info = "Process terminated, exit code: %s" % code
    if code == 0:
        log.log.info(info)
    else:
        log.log.error(info)
        log.log.warning("Removing results:")
        for result in results_dict:
            for res in results_dict[result]:
                try:
                    log.log.warning("Attempt to remove results: %s" % res)
                    os.remove(res)
                except OSError as e:
                    log.log.warning("Failed to remove results: %s; %s" % (res, e))
        log.log.warning("Terminate the process")
        raise CommandError(
            f"Process exited with code {code}", command=string, exit_code=code
        )


def human_format(num: Union[int, float], base: int = 1000) -> str:
    """Format numbers with human readable units."""
    prefixes = ["", "K", "M", "G", "T", "P", "E", "Z", "Y"]
    magnitude = 0

    while abs(num) >= base and magnitude < len(prefixes) - 1:
        magnitude += 1
        num /= base

    if isinstance(num, float):
        decimal_part = num - int(num)
        if decimal_part:
            decimal_str = human_format(int(decimal_part * base**magnitude))
            return f"{int(num)}{prefixes[magnitude]}{decimal_str}"

    return f"{int(num)}{prefixes[magnitude]}"


def bases_format(string_unit: str, base: int = 1000) -> int:
    """Convert string with units to number of bases."""
    if not string_unit:
        raise ValueError("Empty string provided")

    symbols = ["", "K", "M", "G", "T", "P", "E", "Z", "Y"]
    prefix_bytes = [f"{p}B" for p in symbols]

    # Split number and unit
    num = ""
    i = 0
    while i < len(string_unit) and (string_unit[i].isdigit() or string_unit[i] == "."):
        num += string_unit[i]
        i += 1

    if not num:
        raise ValueError("No number found in string")

    unit = string_unit[i:].strip().upper()

    if unit not in (symbols + prefix_bytes):
        raise ValueError(f"Invalid unit: {unit}")

    # Calculate multiplier
    multiplier = base ** (
        symbols.index(unit) if unit in symbols else prefix_bytes.index(unit)
    )

    return int(float(num) * multiplier)


def basename_no_extension(file_name: str) -> str:
    """Get basename without extension."""
    return Path(file_name).stem


class Tee:
    """File-like object that writes to two output streams simultaneously."""

    def __init__(self, f1: TextIO, f2: TextIO) -> None:
        """Initialize Tee with two output streams.

        Args:
            f1: First output stream
            f2: Second output stream
        """
        self.f1 = f1
        self.f2 = f2

    def write(self, msg: str) -> int:
        """Write message to both streams.

        Args:
            msg: Message string to write

        Returns:
            Number of characters written (from first stream)
        """
        self.f1.write(msg)
        return self.f2.write(msg)


class SubcommandHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter that suppresses subparser action help text headers."""

    def _format_action(self, action: argparse.Action) -> str:
        """Format action, skipping the first line for PARSER type actions.

        Args:
            action: ArgumentParser action to format

        Returns:
            Formatted action help text
        """
        parts = super()._format_action(action)
        if action.nargs == argparse.PARSER:
            parts = "\n".join(parts.split("\n")[1:])
        return parts


class DefaultHelpParser(argparse.ArgumentParser):
    """ArgumentParser that prints help before exiting on errors."""

    def error(self, message: str) -> None:
        """Handle parse errors by printing help and exiting.

        Args:
            message: Error message to display

        Raises:
            SystemExit: Always exits with code 2
        """
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


def responsive_sleep(stop_event, duration: int) -> None:
    """Sleep with immediate exit capability via stop_event.

    Sleeps for the specified duration in 1-second intervals, checking
    for stop event between each interval. Allows responsive shutdown
    in threading scenarios without waiting for the full duration.

    Args:
        stop_event: threading.Event that when set causes immediate return
        duration: Number of seconds to sleep
    """
    for _ in range(duration):
        if stop_event.is_set():
            break
        time.sleep(1)


def create_minimal_profile(name: str = "minimal") -> types.ModuleType:
    """Create a minimal profile object for use with PypeLogger.

    Used when a real profile object isn't available (e.g., in listener
    daemon or resume mode). Provides __name__ and __path__ attributes
    that PypeLogger expects.

    Args:
        name: Name for the profile (default: "minimal")

    Returns:
        Module-like object with __name__ and __path__ attributes
    """
    profile = types.ModuleType(name)
    profile.__path__ = "/dev/null"
    return profile
