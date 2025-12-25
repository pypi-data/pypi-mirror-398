import os
import shlex
import subprocess
import tempfile
from copy import copy
from dataclasses import dataclass
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pype.__config__ import PYPE_DOCKER, PYPE_SINGULARITY_CACHE, PYPE_TMP
from pype.exceptions import CommandNamespaceError, EnvModulesError
from pype.misc import generate_uid
from pype.utils.containers import get_singularity_image_path, parse_container_reference


@dataclass
class DockerConfig:
    """Configuration for Docker and container runtime environments.

    This class manages container runtime configuration and provides properties
    to identify the runtime type (Docker, Singularity, uDocker).

    Attributes:
        exec_path: Path to the container runtime executable
        runtime: Name of the container runtime ('docker', 'singularity', 'udocker')
        cache_dir: Optional cache directory, required for Singularity containers
    """

    exec_path: Path
    runtime: str
    cache_dir: Optional[Path] = None

    @property
    def is_singularity(self) -> bool:
        """Check if runtime is Singularity."""
        return self.runtime == "singularity"

    @property
    def is_udocker(self) -> bool:
        """Check if runtime is uDocker."""
        return self.runtime == "udocker"


def get_module_cmd():
    """Get the environment modules command interface."""
    try:
        modules_home = os.environ.get("MODULESHOME")
        if not modules_home:
            raise EnvModulesError("No MODULESHOME variable found in the environment")

        modules_path = Path(modules_home) / "init/python.py"
        if not modules_path.exists():
            raise EnvModulesError(f"No python script {modules_path}")

        modules = {}
        exec(modules_path.read_bytes(), modules)

        return modules["module"]
    except KeyError as e:
        raise EnvModulesError(f"Module command not found: {e}")


def program_string(program_dict: Dict[str, str]) -> str:
    """Format program string from dictionary."""
    try:
        return f"{program_dict['path']}/{program_dict['version']}"
    except KeyError:
        return f"{program_dict['namespace']}/{program_dict['version']}"


@dataclass
class Volume:
    """Volume binding configuration for containerized environments.

    Handles the mounting of files and directories between host and container
    environments, managing read-only and read-write access modes.

    Attributes:
        path: Path to the file or directory on the host system
        output: If True, mount as read-write; if False, mount as read-only
        bind_prefix: Base path in the container where volumes will be mounted
    """

    path: str
    output: bool = False
    bind_prefix: str = "/var/lib/pype"

    def __post_init__(self):
        """Initialize volume configuration after instance creation.

        Sets up volume string templates and generates unique binding paths
        to avoid conflicts between multiple volumes.
        """
        self.path = str(Path(self.path))

        self.volume_str = "--volume=%(host_file)s:%(docker_file)s:%(mode)s"
        self.mode = "rw" if self.output else "ro"
        self.to_bind = os.path.dirname(self.path) if self.output else self.path

        # Generate random subfolder for binding
        random_str = generate_uid(12, False)
        bind_base = Path(self.bind_prefix) / random_str / Path(self.to_bind).name

        self.bind_volume = str(bind_base)
        self.bind_file = (
            str(bind_base / Path(self.path).name) if self.output else self.bind_volume
        )

    def remove_mode(self) -> None:
        """Remove mode specifier for udocker compatibility."""
        self.mode = ""
        self.volume_str = "--volume=%(host_file)s:%(docker_file)s"

    def singularity_volume(self) -> None:
        """Format for Singularity binding syntax."""
        self.volume_str = "--bind %(host_file)s:%(docker_file)s:%(mode)s"

    def replace_bind_volume(self, bind_path):
        """
        Replaces the bind volume in the container environment
        with the specified `bind path`.

        This is useful to manage binding point to multiple
        paths (defined in multiple `Volume` classes) that
        are subfolders of another bind volume in the host system.

        :param bind_path: Binding point to replace instead of the
            current one randomly generated  by the class.
        :type bind_path: str
        """

        bind_file_i = os.path.join(bind_path, os.path.basename(self.bind_file))
        self.bind_file = bind_file_i
        if self.mode == "rw":
            self.bind_volume = os.path.dirname(bind_file_i)
        else:
            self.bind_volume = bind_file_i

    def replace_bind_dirname(self, bind_path):
        """
        Replaces the bind volume in the container environment
        with the `dirname` of the specified `bind path`.

        This is useful to give the same binding point to multiple
        paths (defined in multiple `Volume` classes) that
        are in the same folder in the host system.

        :param bind_path: Binding point to replace instead of the
            current one randomly generated  by the class.
        :type bind_path: str
        """

        bind_file_i = os.path.join(
            os.path.dirname(bind_path), os.path.basename(self.bind_file)
        )
        self.bind_file = bind_file_i
        if self.mode == "rw":
            self.bind_volume = os.path.dirname(bind_file_i)
        else:
            self.bind_volume = bind_file_i

    def to_str(self) -> str:
        """Get formatted volume string."""
        return self.volume_str % {
            "host_file": self.to_bind,
            "docker_file": self.bind_volume,
            "mode": self.mode,
        }


class Command:
    """High-level interface for executing commands with container support.

    This class provides a unified interface for running commands locally or
    within containers (Docker, Singularity, uDocker). It handles:
    - Command execution and piping
    - Volume mounting and file access
    - Container runtime configuration
    - Environment modules integration
    - Input/output file tracking

    Attributes:
        cmd: Command to execute as list of arguments
        name: Identifier for the command (used in logs)
        profile: Configuration profile for the environment
        log: Logger instance for command execution tracking
        docker: Container runtime configuration
        inputs: List of input files required by the command
        outputs: List of output files produced by the command
        volumes: List of volumes to mount in container environments
    """

    def __init__(self, cmd: str, log: Any, profile: Any, name: str = ""):
        """Initialize command execution environment.

        Args:
            cmd: Command string to execute
            log: Logger instance for command output
            profile: Environment profile configuration
            name: Optional identifier for the command
        """
        self.cmd = shlex.split(cmd)
        self.name = name
        self.profile = profile
        self.log = log.log

        # Initialize container configuration
        self.docker = DockerConfig(
            exec_path=Path(PYPE_DOCKER),
            runtime=Path(PYPE_DOCKER).name,
            cache_dir=(
                Path(PYPE_SINGULARITY_CACHE)
                if Path(PYPE_DOCKER).name == "singularity"
                else None
            ),
        )

        # Process configuration
        self.stdin = subprocess.PIPE
        self.stdout = subprocess.PIPE
        self.procin: Optional[Command] = None

        # File tracking
        self.inputs: List[str] = []
        self.outputs: List[str] = []
        self.volumes: List[Volume] = []

        # Runtime configuration
        self.uid = os.geteuid
        self.gid = os.getegid
        self.random_work_dir = Path("/") / generate_uid(6, False)
        self.tmp = Path(PYPE_TMP)

        if not name:
            self.log.warning("Proceeding with unnamed Command")

    def add_output(self, out_file: str) -> None:
        """Add output file to track."""
        if out_file not in self.outputs:
            self.outputs.append(out_file)

    def add_input(self, in_file: str, match: str = "exact") -> None:
        """Add input file(s) to track."""
        if match == "recursive":
            for file_in in glob(f"{in_file}*"):
                self.add_input(file_in, "exact")
        elif in_file not in self.inputs:
            self.inputs.append(in_file)

    def add_volume(self, path: str, output: bool = False) -> None:
        """Add volume to track."""
        n_volumes = len(self.volumes)
        volume = Volume(path, output=output)
        for i in range(n_volumes):
            path_i = self.volumes[i].to_bind
            mode_i = self.volumes[i].mode
            has_same_mode = mode_i == volume.mode
            if is_direct_child_of(path_i, path) and has_same_mode:
                self.volumes[i].replace_bind_volume(volume.bind_volume)
            elif is_direct_child_of(path, path_i) and has_same_mode:
                volume.replace_bind_volume(self.volumes[i].bind_volume)
            elif has_same_basedir(path, path_i) and has_same_mode:
                volume.replace_bind_dirname(self.volumes[i].bind_volume)
        self.volumes.append(volume)

    def normalize_volumes(self) -> None:
        """Normalize volumes to avoid duplicates."""
        _unique_volumes_list_ = []
        _to_bind_ = []
        _bind_volumes_ = []
        for volume in self.volumes:
            if (
                volume.bind_volume not in _bind_volumes_
                and volume.to_bind not in _to_bind_
            ):
                _unique_volumes_list_.append(volume)
                _to_bind_.append(volume.to_bind)
                _bind_volumes_.append(volume.bind_volume)
        self.volumes = _unique_volumes_list_

    def add_namespace(self, namespace: Union[Dict[str, Any], Any]) -> None:
        """Add namespace to command.

        Args:
            namespace: Program configuration as dict or ProfileProgram object
        """
        self.namespace = Namespace(namespace, self.log, self.profile)

    def run(self, local_script: bool = False, capture_stderr: bool = False) -> None:
        """Execute the command.

        Args:
            local_script: If True, execute as local script
            capture_stderr: If True, capture stderr output (default False to maintain current behavior)
        """
        try:
            if hasattr(self, "namespace") and self.namespace.type == "docker":
                self.docker_run(local_script)
            elif hasattr(self, "namespace") and self.namespace.type == "env_module":
                self.module_run(capture_stderr=capture_stderr)
            else:
                self.local_run(capture_stderr=capture_stderr)
        except Exception as e:
            self.log.error(f"Command execution failed: {e}")
            raise

    def docker_run(self, local_script: bool) -> None:
        """Execute command within a container environment.

        Handles the complexities of running commands in containers including:
        - Volume mounting and path translation
        - User permissions
        - Working directory setup
        - Container-specific command modifications

        Args:
            local_script: If True, indicates the command is a local script that
                         needs to be mounted in the container
        """
        docker_cwd = tempfile.mkdtemp(dir=self.tmp)
        docker_data = {
            "user": self.uid(),
            "group": self.gid(),
            "random_dir": self.random_work_dir,
            "docker": self.docker.exec_path,
            "cwd": docker_cwd,
        }

        cmd = copy(self.cmd)

        # Handle container command based on runtime
        if self.docker.is_udocker:
            docker_cmd = (
                f"{docker_data['docker']} --quiet run -i --rm "
                f"{self.namespace.docker_extra_args} "
                f"--user={docker_data['user']}:{docker_data['group']} "
                f"--workdir=/var/spool/pype "
                f"--volume={docker_data['cwd']}:/var/spool/pype"
            )
        elif self.docker.is_singularity:
            docker_cmd = (
                f"{docker_data['docker']} --quiet exec "
                f"{self.namespace.docker_extra_args} --contain "
                f"--pid --ipc --pwd {docker_data['random_dir']} "
                f"--home {docker_data['cwd']}:{docker_data['random_dir']}"
            )
        else:
            docker_cmd = (
                f"{docker_data['docker']} run -i --rm "
                f"{self.namespace.docker_extra_args} "
                f"--user={docker_data['user']}:{docker_data['group']} "
                f"--workdir=/var/spool/pype "
                f"--volume={docker_data['cwd']}:/var/spool/pype:rw"
            )

        # Handle volumes
        for in_file in self.inputs:
            self.add_volume(in_file)
        for out_file in self.outputs:
            self.add_volume(out_file, output=True)

        volumes_files = []
        if local_script:
            exec_file = self.cmd[0]
            self.add_volume(exec_file)
            self.replace_values_in_code(exec_file)

        self.normalize_volumes()

        for volume in self.volumes:
            # Update command arguments if they match volume paths
            for i in range(len(cmd)):
                if volume.path == self.cmd[i]:
                    cmd[i] = volume.bind_file

            # Adjust volume string based on container runtime
            if self.docker.is_udocker:
                volume.remove_mode()
            elif self.docker.is_singularity:
                volume.singularity_volume()
            volumes_files.append(volume.to_str())

        try:
            docker_image = self.namespace.first()
        except AttributeError:
            self.log.error("A namespace is required before executing a Docker command")
            raise Exception("A namespace is required before executing a Docker command")

        # Construct final docker command
        volumes_files = " ".join(volumes_files)
        docker_cmd = f"{docker_cmd} {volumes_files}"
        docker_cmd = f"{docker_cmd} {docker_image}"
        docker_cmd = shlex.split(docker_cmd)
        docker_cmd.extend(cmd)

        self.log.info(f"Prepare Docker command {' '.join(docker_cmd)}")
        self.log.info(f"Replace {' '.join(self.cmd)} with Docker command")
        self.cmd = docker_cmd
        self.local_run()

    def local_run(self, capture_stderr: bool = False) -> None:
        """Execute command locally.

        Args:
            capture_stderr: If True, capture stderr output (default False to maintain current behavior)
        """
        self.log.info(f"Prepare {self.name} command line")
        self.log.info(" ".join(map(str, self.cmd)))
        self.log.info(f"Execute {self.name} with python subprocess.Popen")
        stderr_pipe = subprocess.PIPE if capture_stderr else None
        self.proc = subprocess.Popen(
            self.cmd, stdin=self.stdin, stdout=self.stdout, stderr=stderr_pipe
        )
        self.stdout = self.proc.stdout

    def module_run(self, capture_stderr: bool = False) -> None:
        """Execute command with environment modules.

        Args:
            capture_stderr: If True, capture stderr output
        """
        module = get_module_cmd()
        self.log.info(f"Purge the module env before loading {self.namespace.namespace}")
        module("purge")
        for nm in self.namespace.list:
            self.log.info(f"Add env_module {nm}")
            module("add", nm)
        self.local_run(capture_stderr=capture_stderr)

    def pipe_in(self, command: "Command", local_script: bool = False) -> None:
        """Pipe input from another command."""
        self.log.info(f"Pipe in {command.name} in {self.name} command")
        self.procin = command
        self.procin.run(local_script)
        self.stdin = self.procin.stdout

    def release_stdout(self) -> None:
        """Release stdout to terminal (for final commands in execution).

        Use this for terminal commands where output should be visible to the user.
        """
        self.stdout = None

    def capture_stdout(self) -> None:
        """Capture stdout for piping (for intermediate commands).

        Use this to ensure stdout is captured in subprocess.PIPE for piping to another command.
        """
        self.stdout = subprocess.PIPE

    def child_close(self) -> None:
        """Close child process."""
        try:
            self.procin.stdout.close()
            self.log.info(f"Close {self.procin.name} stdout stream")
        except AttributeError:
            pass

    def close(self, ignore_returncode: bool = False) -> Tuple[Any, int]:
        """Close command and return result with exit code.

        Args:
            ignore_returncode: If False (default), raise exception on non-zero exit.
                             If True, ignore exit code (legacy behavior).

        Returns:
            Tuple of (communicate_result, returncode)

        Raises:
            CommandError: If returncode != 0 and ignore_returncode is False
        """
        from pype.exceptions import CommandError

        if self.procin is not None:
            self.child_close()
        res = self.proc.communicate()
        returncode = self.proc.returncode

        self.log.info(f"Terminate {self.name} (exit code: {returncode})")

        if not ignore_returncode and returncode != 0:
            self.log.error(f"{self.name} failed with exit code {returncode}")
            raise CommandError(
                f"Command '{self.name}' failed with exit code {returncode}",
                command=" ".join(map(str, self.cmd)),
                exit_code=returncode,
            )

        return res, returncode

    def replace_values_in_code(self, code_file: str) -> None:
        """Replace values in code file with bind volumes."""
        code_lines = ""
        with open(code_file, "rt") as code:
            for line in code:
                for volume in self.volumes:
                    line = line.replace(volume.path, volume.bind_file)
                code_lines += line
        with open(code_file, "wt") as code:
            code.write(code_lines)
        os.chmod(code_file, 0o760)


def is_direct_child_of(x: str, y: str) -> bool:
    """Check if x is a direct child of directory y."""
    path_a = Path(x).resolve()
    path_b = Path(y).resolve()
    return path_a.parent == path_b


def has_same_basedir(x: str, y: str) -> bool:
    """Check if x and y have the same base directory."""
    path_a = Path(x).resolve().parent
    path_b = Path(y).resolve().parent
    return path_a == path_b


class Namespace:
    """Environment and dependency management system.

    Manages different execution environments (path-based, environment modules,
    containers) and their dependencies. Supports:
    - Path-based program execution
    - Environment modules loading
    - Container image specification
    - Dependency resolution

    The namespace format is 'type@item' where:
    - type: One of 'path', 'env_module', or 'docker'
    - item: The specific program/container/module to use

    For example:
    - 'docker@ubuntu:latest'
    - 'env_module@gcc/9.3.0'
    - 'path@/usr/local/bin/python'
    """

    def __init__(
        self,
        program_dict: Union[Dict[str, Any], Any],
        log: Any,
        profile: Any,
    ):
        """Initialize namespace configuration.

        Parses a program configuration and sets up namespace properties for command execution.
        Supports both dict and ProfileProgram object inputs.

        Args:
            program_dict: Program configuration as dict or ProfileProgram object with keys:
                - namespace: String in format 'type@item' where type is one of:
                  'docker', 'env_module', or 'path'
                - version: Program version (optional for path type)
                - dependencies: Optional list of dependent program names
            log: Logger instance for namespace operations
            profile: Environment profile containing program configurations

        Attributes set:
            type: Namespace type ('docker', 'env_module', or 'path')
            namespace: Original namespace string (e.g., 'docker@ubuntu')
            str: Parsed namespace item (e.g., 'ubuntu')
            version: Program version string
            list: List of resolved namespace items (empty until processing)
            docker_extra_args: Extra arguments for docker/singularity commands

        Raises:
            CommandNamespaceError: For invalid namespace format or unsupported types
        """
        self.type: Optional[str] = None
        self.list: List[str] = []
        self.docker_extra_args = ""
        self.version = None
        self.namespace = None
        self.str = None
        self.log = log

        # Extract values from either ProfileProgram object or dict
        # Use duck typing to avoid circular imports - check for namespace attribute
        if hasattr(program_dict, "namespace") and not isinstance(program_dict, dict):
            # It's a ProfileProgram object
            namespace_str = program_dict.namespace
            version_str = program_dict.version
            deps_list = program_dict.dependencies or []
        else:
            # It's a dict
            namespace_str = program_dict["namespace"]
            version_str = program_dict["version"]
            deps_list = program_dict.get("dependencies", [])
        self.namespace = namespace_str
        self.version = version_str

        namespace_list = namespace_str.split("@")
        if len(namespace_list) == 2:
            self.type = namespace_list[0]
            self.log.info(f"Set namespace to {self.type}")
            namespace_item = namespace_list[1]
        elif len(namespace_list) == 1:
            self.type = "path"
            self.log.info(f"Set namespace to {self.type}")
            namespace_item = namespace_list[0]
        else:
            self.log.error("Wrong Namespace format")
            raise CommandNamespaceError("Wrong Namespace format")
        self.str = namespace_item
        supported_namespaces = ("path", "env_module", "docker")
        if self.type not in supported_namespaces:
            self.log.error(f"Not supported namespace names {self.type}")
            raise CommandNamespaceError(f"Not supported namespace {self.type}")
        if self.type == "env_module":
            for dep in deps_list:
                dep_dict = profile.programs[dep]
                dep_nm = Namespace(dep_dict, self.log, profile)
                if dep_nm.type != "env_module":
                    self.log.error("All dependencies must be type env_module")
                    raise CommandNamespaceError(
                        "All dependencies must be type env_module"
                    )
                self.list += dep_nm.list
            self.list.append(
                program_string({"namespace": namespace_item, "version": version_str})
            )
        elif self.type == "docker":
            docker_cmd = PYPE_DOCKER
            docker_runtime = Path(docker_cmd).name
            # Extract extra_args from either ProfileProgram object or dict
            if hasattr(program_dict, "extra_args"):
                # ProfileProgram object
                extra_args = program_dict.extra_args
            else:
                # Dict
                extra_args = program_dict.get("extra_args")
            if extra_args:
                self.docker_extra_args = extra_args
            if docker_runtime == "singularity":
                # Use shared container utilities for consistent path construction
                # Extract version from either ProfileProgram object or dict
                version = (
                    program_dict.version
                    if hasattr(program_dict, "version")
                    else program_dict["version"]
                )
                nm = get_singularity_image_path(
                    namespace_item,
                    version,
                    PYPE_SINGULARITY_CACHE,
                )
            else:
                # Docker/uDocker - use standard image:tag format with full registry
                # Extract version from either ProfileProgram object or dict
                version = (
                    program_dict.version
                    if hasattr(program_dict, "version")
                    else program_dict["version"]
                )
                registry, image_path = parse_container_reference(namespace_item)
                nm = f"{registry}/{image_path}:{version}"
            self.list.append(str(nm))
        elif self.type == "path":
            self.list.append(namespace_item)

    def first(self) -> str:
        return self.list[0]
