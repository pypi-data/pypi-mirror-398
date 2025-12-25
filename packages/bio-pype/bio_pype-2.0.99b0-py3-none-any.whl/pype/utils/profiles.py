"""Profile management system for bio_pype.

Profiles define the execution environment and resource configuration:
- Software installation paths and versions
- Reference data locations
- Environment module configurations
- System resources (memory, CPU, etc)

Key functions:
    check_profile_files: Validate all file paths
    get_profiles: Load available profile configurations
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from sys import version
from typing import Any, Dict, Optional, Tuple, Union

import yaml

from pype.__config__ import PYPE_PROFILES
from pype.exceptions import ProfileError
from pype.misc import package_files
from pype.process import Command, DockerConfig, Namespace
from pype.utils.containers import (
    get_docker_uri,
    get_singularity_image_path,
    parse_container_reference,
)


@dataclass
class ProfileInfo:
    """Profile metadata."""

    description: str
    date: str
    version: str = "1.0.0"


@dataclass
class ProfileProgram:
    """Software program configuration for profile execution.

    Represents a program entry in a profile YAML with all necessary configuration
    for namespace setup and execution via the Command class.

    Attributes:
        namespace: Namespace format string 'type@item' where type is one of:
            - 'docker': Docker/Singularity image (format: docker@image_name)
            - 'env_module': HPC environment module (format: env_module@module_name)
            - 'path': Direct filesystem path (format: path@/absolute/path)
        version: Program version tag or identifier
        path: Alternative path to executable (rarely used with namespace)
        modulepath: Custom module search path for env_module type
        dependencies: List of dependent program names that must be loaded first
        extra_args: Extra command-line arguments for container runtimes
            (e.g., '--nv' for Singularity GPU support, '--gpus all' for Docker)
    """

    namespace: str
    version: Optional[str] = None
    path: Optional[str] = None
    modulepath: Optional[str] = None
    dependencies: Optional[list] = None
    extra_args: Optional[str] = None


def check_profile_files(profile: "Profile") -> Dict[str, Dict[str, Any]]:
    """Validate all file paths in profile.

    Args:
        profile: Profile to validate

    Returns:
        Dict mapping file keys to validation result dicts with keys:
        - success: bool indicating if file exists
        - message: str with file path or error message
    """
    check_dict = {}
    for key in profile.files:
        resource = profile.files[key]
        if os.path.isfile(resource) or os.path.isdir(resource):
            check_dict[key] = {"success": True, "message": resource}
        else:
            check_dict[key] = {"success": False, "message": resource}
    return check_dict


def validate_program(
    program: ProfileProgram, profile: "Profile", log: Any = None
) -> Tuple[bool, str]:
    """Validate a program by executing it with the 'echo' command.

    Uses Command class which handles all namespace setup and validation:
    - env_module: loads the modules and their dependencies
    - docker: sets up container access
    - path: validates executable location and availability

    This is a real validation that catches actual runtime issues, not just
    YAML structure validation.

    Args:
        program: ProfileProgram to validate
        profile: Profile context
        log: Optional logger instance for validation

    Returns:
        Tuple of (success: bool, message: str)
    """
    namespace_str = f"{program.namespace}/{program.version}"
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as stderr_file:
        stderr_path = stderr_file.name

    original_stderr = os.dup(2)
    stderr_output = None
    error_status = True
    with open(stderr_path, "wt") as fd:
        os.dup2(fd.fileno(), 2)

    try:
        # Create command with minimal 'echo' script
        # The namespace setup/validation happens when run() is called
        cmd = Command(cmd="echo validation", name="validate", log=log, profile=profile)
        cmd.add_namespace(program)
        cmd.run(capture_stderr=True)
        cmd.proc.wait()
        return_code = cmd.proc.returncode

        with open(stderr_path, "rt") as f:
            stderr_output = f.read()

        # Log all stderr for debugging (helps identify validation issues)

        if return_code != 0 and log:
            log.log.error(f"[validate_program exited with] {return_code}")
            return (False, f"{namespace_str} failed with return code {return_code}")
        # Check stderr for module loading errors
        if stderr_output:
            # Parse stderr for error messages
            error_lines = []
            for line in stderr_output.split("\n"):
                line = line.strip()
                # Capture lines with ERROR or common error patterns
                if line and (
                    "ERROR" in line
                    or "Unable to locate" in line
                    or "command not found" in line
                    or "No such file" in line
                ):
                    if log:
                        log.log.error(line)
                    error_lines.append(line)

            if error_lines:
                # Return the first meaningful error message
                error_msg = "\n".join(error_lines)
                return (False, f"{namespace_str}: {error_msg}")

        # If we get here, validation passed
        error_status = False
        return (True, f"{namespace_str}: Program validated successfully")

    except Exception as e:
        error_msg = str(e)
        if log:
            log.log.error(f"Exception during validation: {error_msg}")
        return (False, f"{namespace_str}: {error_msg}")
    finally:
        os.dup2(original_stderr, 2)
        os.close(original_stderr)
        os.unlink(stderr_path)
        if error_status:
            log.log.error(f"{namespace_str} failed with error: {stderr_output}")


def validate_all_programs(
    profile: "Profile", log: Any = None
) -> Dict[str, Dict[str, Any]]:
    """Validate all programs in profile.

    Uses Command class to validate each program's namespace setup and availability:
    - env_module: Validates by attempting to load the module
    - docker: Validates container image availability
    - path: Validates if executable exists

    Args:
        profile: Profile to validate
        log: Optional logger instance for validation

    Returns:
        Dict mapping program keys to validation result dicts with keys:
        - success: bool indicating if program is valid
        - message: str with error message if validation failed
    """
    check_dict = {}
    for program_name, program in profile.programs.items():
        success, message = validate_program(program, profile, log)
        check_dict[program_name] = {"success": success, "message": message}

    return check_dict


def print_checks(check: Dict[str, Any], profile_dict: Dict[str, Any]) -> None:
    """Print the results of profile checks.

    Args:
        check: Dict of check results with {success: bool, message: str}
        profile_dict: Profile data
    """
    greencol = "\033[92m"
    redcol = "\033[91m"
    endcol = "\033[0m"

    for key, value in check.items():
        item = profile_dict[key]
        # Determine if it's a program (ProfileProgram object) or file (string)
        if isinstance(item, ProfileProgram):
            type_check = "Program"
            type_str = "namespace"
        else:
            # It's a file path (string or dict)
            type_check = "File"
            type_str = "path"

        # Get status and message from value dict
        is_success = value.get("success", value) if isinstance(value, dict) else value
        message = value.get("message", "") if isinstance(value, dict) else str(value)

        if is_success is True:
            print(f"{greencol}{type_check} OK{endcol} - {key} {type_str}: {message}")
        else:
            print(f"{redcol}{type_check} ERROR{endcol} - {key} {type_str}: {message}")


def get_profiles(profs: Dict[str, "Profile"]) -> Dict[str, "Profile"]:
    """Load available profile configurations.

    Args:
        profs: Dict to store loaded profiles

    Returns:
        Dict of loaded profiles
    """
    profiles = package_files(PYPE_PROFILES, ".yaml")
    for profile in sorted(profiles):
        try:
            prof_name = os.path.basename(os.path.splitext(profile)[0])
            profs[prof_name] = Profile(profile, prof_name)
        except AttributeError:
            pass
    return profs


class Profile:
    """Profile configuration container.

    Attributes:
        files: Dict of file/directory paths
        programs: Dict of program configurations
        info: Profile metadata
        build: Genome build info
    """

    def __init__(self, path: Union[str, Path], name: str):
        """Initialize profile from YAML file.

        Args:
            path: Path to profile YAML file
            name: Profile name

        Raises:
            ProfileError: If profile is invalid
        """
        self.__path__ = path
        self.__name__ = name
        self.files: Dict[str, str] = {}
        self.programs: Dict[str, ProfileProgram] = {}
        self.info: ProfileInfo

        try:
            with open(self.__path__, "rb") as f:
                profile = yaml.safe_load(f)
                for key, value in profile.items():
                    setattr(self, key, value)

                # Convert program dicts to ProfileProgram objects
                if isinstance(self.programs, dict):
                    for prog_name, prog_data in self.programs.items():
                        if isinstance(prog_data, dict):
                            self.programs[prog_name] = ProfileProgram(**prog_data)
        except Exception as e:
            raise ProfileError(
                f"Failed to load profile {name}", profile_name=name
            ) from e

    def describe(self) -> None:
        """Print human readable profile description."""
        print("Name       : %s" % self.__name__)
        print("Description: %s" % self.info["description"])
        print("Date       : %s" % self.info["date"])
        print("Files      :")
        for file in self.files:
            print("\tID: %s" % file)
            print("\t\tpath: %s" % self.files[file])
        print("Programs   :")
        for program in self.programs:
            prog_obj = self.programs[program]
            print("\tID: %s" % program)
            print("\t\tnamespace: %s" % prog_obj.namespace)
            print("\t\tversion: %s" % prog_obj.version)
        print("File Path  : %s" % self.__path__)


def pull_singularity_image(
    namespace: Namespace, docker: DockerConfig, log: Any = None
) -> Dict[str, Any]:
    """Pull a Singularity image for a docker-namespace program.

    Converts Docker namespace format to proper singularity pull command using
    the docker:// URI scheme. Only processes docker-type namespaces; other types
    return success with no action.

    Uses shared container utilities to ensure path construction is consistent
    with Namespace class behavior.

    Args:
        namespace: Namespace object containing parsed program configuration
            - namespace.type: Must be 'docker' to trigger pull
            - namespace.str: Docker image name (e.g., 'biocontainers/samtools')
            - namespace.version: Image version tag
        docker: DockerConfig object containing:
            - exec_path: Path to singularity executable
            - runtime: Runtime type (should be 'singularity')
            - cache_dir: Path to PYPE_SINGULARITY_CACHE
        log: Optional logger instance for info/error messages

    Returns:
        Dict with keys:
            - success: bool indicating if pull succeeded or was skipped
            - sif_path: str path to SIF file, or None if not a docker namespace
            - message: str status/error message

    Examples:
        >>> # Create namespace from program dict
        >>> ns = Namespace(
        ...     {"namespace": "docker@biocontainers/samtools", "version": "1.15"},
        ...     logger,
        ...     profile
        ... )
        >>> docker_config = DockerConfig(
        ...     exec_path=Path("singularity"),
        ...     runtime="singularity",
        ...     cache_dir=Path("/singularity/cache")
        ... )
        >>> result = pull_singularity_image(ns, docker_config, logger)
        >>> result["success"]  # True if pull succeeded
    """

    try:
        # Extract namespace and version
        if namespace.type != "docker":
            return {
                "success": False,
                "sif_path": None,
                "message": f"Not a docker namespace: {namespace.namespace}",
            }

        namespace_item = namespace.str
        version = namespace.version

        if not version:
            return {
                "success": False,
                "sif_path": None,
                "message": "No version specified for program",
            }

        # Use shared function to get target path
        sif_path = get_singularity_image_path(namespace_item, version, docker.cache_dir)

        # Check if already exists
        if sif_path.exists():
            if log:
                log.log.info(f"Image already exists: {sif_path}")
            return {
                "success": True,
                "sif_path": str(sif_path),
                "message": "Image already exists",
            }

        # Create parent directory
        sif_path.parent.mkdir(parents=True, exist_ok=True)

        # Construct docker:// URI
        docker_uri = get_docker_uri(namespace_item, version)

        if log:
            log.log.info(f"Pulling {docker_uri} to {sif_path}")

        # Run singularity pull
        cmd = [docker.exec_path, "pull", str(sif_path), docker_uri]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            if log:
                log.log.info(f"Successfully pulled image to {sif_path}")
            return {
                "success": True,
                "sif_path": str(sif_path),
                "message": "Pull successful",
            }
        else:
            error_msg = result.stderr or result.stdout
            if log:
                log.log.error(f"Pull failed: {error_msg}")
            return {
                "success": False,
                "sif_path": str(sif_path),
                "message": f"Pull failed: {error_msg[:200]}",
            }

    except FileNotFoundError:
        return {
            "success": False,
            "sif_path": None,
            "message": "singularity command not found in PATH",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "sif_path": str(sif_path) if "sif_path" in locals() else None,
            "message": "Pull timed out (10 minutes)",
        }
    except Exception as e:
        return {
            "success": False,
            "sif_path": None,
            "message": f"Error: {str(e)[:200]}",
        }


def pull_docker_image(
    namespace: Namespace, docker: DockerConfig, log: Any = None
) -> Dict[str, Any]:
    """Pull a Docker image for a docker-namespace program.

    Pulls Docker images directly using the docker or podman runtime. Only processes
    docker-type namespaces; other types return success with no action.

    Args:
        namespace: Namespace object containing parsed program configuration
            - namespace.type: Must be 'docker' to trigger pull
            - namespace.str: Docker image name (e.g., 'biocontainers/samtools')
            - namespace.version: Image version tag
        docker: DockerConfig object containing:
            - exec_path: Path to docker/podman executable
            - runtime: Runtime type (should be 'docker' or 'podman')
            - cache_dir: Not used for docker pull (included for API consistency)
        log: Optional logger instance for info/error messages

    Returns:
        Dict with keys:
            - success: bool indicating if pull succeeded or was skipped
            - image_name: str full image name with tag, or None if not a docker namespace
            - message: str status message or error details

    Examples:
        >>> # Create namespace from program dict
        >>> ns = Namespace(
        ...     {"namespace": "docker@biocontainers/samtools", "version": "1.15"},
        ...     logger,
        ...     profile
        ... )
        >>> docker_config = DockerConfig(
        ...     exec_path=Path("docker"),
        ...     runtime="docker",
        ...     cache_dir=None
        ... )
        >>> result = pull_docker_image(ns, docker_config, logger)
        >>> result["success"]  # True if pull succeeded
    """
    try:
        # Extract namespace and version
        if namespace.type != "docker":
            return {
                "success": False,
                "image_name": None,
                "message": f"Not a docker namespace: {namespace.namespace}",
            }

        namespace_item = namespace.str
        version = namespace.version

        if not version:
            return {
                "success": False,
                "image_name": None,
                "message": "No version specified for program",
            }

        # Construct image name with registry
        registry, image_path = parse_container_reference(namespace_item)
        image_name = f"{registry}/{image_path}:{version}"

        if log:
            log.log.info(f"Pulling Docker image {image_name}")

        # Run docker pull
        cmd = [str(docker.exec_path), "pull", image_name]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            if log:
                log.log.info(f"Successfully pulled image {image_name}")
            return {
                "success": True,
                "image_name": image_name,
                "message": "Pull successful",
            }
        else:
            error_msg = result.stderr or result.stdout
            if log:
                log.log.error(f"Pull failed: {error_msg}")
            return {
                "success": False,
                "image_name": image_name,
                "message": f"Pull failed: {error_msg[:200]}",
            }

    except FileNotFoundError:
        return {
            "success": False,
            "image_name": None,
            "message": f"{docker.exec_path} command not found in PATH",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "image_name": f"{registry}/{image_path}:{version}"
            if "registry" in locals()
            else None,
            "message": "Pull timed out (10 minutes)",
        }
    except Exception as e:
        return {
            "success": False,
            "image_name": None,
            "message": f"Error: {str(e)[:200]}",
        }


def pull_profile_images(
    profile: Profile,
    cache_dir: str,
    docker_exec: str,
    log: Any = None,
    force: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """Pull all Singularity images for docker-namespace programs in a profile.

    Iterates through all programs in the profile and pulls docker-namespace
    images to the Singularity cache. Non-docker programs are skipped with
    success=True status. Uses Namespace class for consistent namespace parsing
    and DockerConfig for consistent container runtime configuration.

    Args:
        profile: Profile object containing programs dict with ProfileProgram objects
        cache_dir: PYPE_SINGULARITY_CACHE path for storing .sif files
        docker_exec: Path to container runtime executable (usually 'singularity')
        log: Optional logger instance for info/error messages
        force: Re-pull images even if they already exist (currently ignored)

    Returns:
        Dict mapping program names to result dicts, each containing:
            - success: bool indicating pull succeeded or was skipped
            - sif_path: str path to pulled SIF file, or None if skipped
            - message: str status message or error details

    Examples:
        >>> from pype.utils.profiles import Profile
        >>> profile = Profile("/path/to/profile.yaml", "hg38")
        >>> results = pull_profile_images(
        ...     profile,
        ...     "/singularity/cache",
        ...     "singularity",
        ...     log=logger
        ... )
        >>> for program, result in results.items():
        ...     status = "OK" if result['success'] else "ERROR"
        ...     print(f"{program}: {status} - {result['message']}")
    """
    results = {}

    docker = DockerConfig(
        exec_path=Path(docker_exec),
        runtime=Path(docker_exec).name,
        cache_dir=(
            Path(cache_dir) if Path(docker_exec).name == "singularity" else None
        ),
    )

    for program_name, program_dict in profile.programs.items():
        namespace = Namespace(program_dict, log.log, profile)

        # Only pull docker-namespace programs
        if namespace.type != "docker":
            results[program_name] = {
                "success": True,
                "sif_path": None,
                "message": f"Not a docker namespace ({namespace.namespace}), skipped",
            }
            continue

        if log:
            log.log.info(f"Pulling image for {program_name}...")
        if docker.is_singularity:
            result = pull_singularity_image(namespace, docker, log)

        else:
            result = pull_docker_image(namespace, docker, log)
        results[program_name] = result

    return results
