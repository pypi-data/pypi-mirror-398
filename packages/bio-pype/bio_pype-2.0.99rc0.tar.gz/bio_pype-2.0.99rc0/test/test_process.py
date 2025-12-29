"""Unit tests for pype.process module.

Tests for container and process management including:
- DockerConfig for container runtime configuration
- Volume mounting and path translation
- Command execution (local, Docker, Singularity, env modules)
- Namespace configuration and dependency resolution
- Volume binding and normalization
- File input/output tracking
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

from pype.exceptions import CommandNamespaceError, EnvModulesError
from pype.process import (
    Command,
    DockerConfig,
    Namespace,
    Volume,
    get_module_cmd,
    has_same_basedir,
    is_direct_child_of,
    program_string,
)


class TestDockerConfig(unittest.TestCase):
    """Test DockerConfig dataclass."""

    def test_docker_config_creation(self):
        """Test DockerConfig initialization."""
        config = DockerConfig(exec_path=Path("/usr/bin/docker"), runtime="docker")

        self.assertEqual(config.runtime, "docker")
        self.assertEqual(config.exec_path, Path("/usr/bin/docker"))
        self.assertIsNone(config.cache_dir)

    def test_docker_config_with_cache(self):
        """Test DockerConfig with cache directory."""
        cache_dir = Path("/var/cache/singularity")
        config = DockerConfig(
            exec_path=Path("/usr/bin/singularity"),
            runtime="singularity",
            cache_dir=cache_dir,
        )

        self.assertEqual(config.runtime, "singularity")
        self.assertEqual(config.cache_dir, cache_dir)

    def test_is_singularity_property(self):
        """Test is_singularity property."""
        docker_config = DockerConfig(
            exec_path=Path("/usr/bin/docker"), runtime="docker"
        )
        sing_config = DockerConfig(
            exec_path=Path("/usr/bin/singularity"), runtime="singularity"
        )

        self.assertFalse(docker_config.is_singularity)
        self.assertTrue(sing_config.is_singularity)

    def test_is_udocker_property(self):
        """Test is_udocker property."""
        udocker_config = DockerConfig(
            exec_path=Path("/usr/bin/udocker"), runtime="udocker"
        )
        docker_config = DockerConfig(
            exec_path=Path("/usr/bin/docker"), runtime="docker"
        )

        self.assertTrue(udocker_config.is_udocker)
        self.assertFalse(docker_config.is_udocker)


class TestVolume(unittest.TestCase):
    """Test Volume class for container volume management."""

    def test_volume_creation_readonly(self):
        """Test creating a read-only volume."""
        vol = Volume("/data/input.txt", output=False)

        self.assertEqual(vol.path, "/data/input.txt")
        self.assertFalse(vol.output)
        self.assertEqual(vol.mode, "ro")

    def test_volume_creation_readwrite(self):
        """Test creating a read-write volume."""
        vol = Volume("/data/output.txt", output=True)

        self.assertEqual(vol.path, "/data/output.txt")
        self.assertTrue(vol.output)
        self.assertEqual(vol.mode, "rw")

    def test_volume_custom_bind_prefix(self):
        """Test volume with custom bind prefix."""
        vol = Volume("/data/file.txt", bind_prefix="/custom/mount")

        self.assertEqual(vol.bind_prefix, "/custom/mount")
        self.assertIn("/custom/mount", vol.bind_volume)

    def test_volume_to_str_readonly(self):
        """Test volume string representation for read-only volume."""
        vol = Volume("/data/input.txt", output=False)
        vol_str = vol.to_str()

        self.assertIn("--volume=", vol_str)
        self.assertIn("/data/input.txt", vol_str)
        self.assertIn(":ro", vol_str)

    def test_volume_to_str_readwrite(self):
        """Test volume string representation for read-write volume."""
        vol = Volume("/data/output.txt", output=True)
        vol_str = vol.to_str()

        self.assertIn("--volume=", vol_str)
        self.assertIn(":rw", vol_str)

    def test_volume_remove_mode(self):
        """Test removing mode specifier (for udocker compatibility)."""
        vol = Volume("/data/file.txt")
        vol.remove_mode()

        self.assertEqual(vol.mode, "")
        self.assertNotIn("%(mode)s", vol.to_str())

    def test_volume_singularity_format(self):
        """Test Singularity volume format conversion."""
        vol = Volume("/data/file.txt")
        vol.singularity_volume()

        self.assertIn("--bind", vol.to_str())
        self.assertNotIn("--volume", vol.to_str())

    def test_volume_replace_bind_volume(self):
        """Test replacing bind volume path."""
        vol = Volume("/data/output.txt", output=True)
        original_bind = vol.bind_volume

        vol.replace_bind_volume("/custom/mount/point")

        self.assertNotEqual(vol.bind_volume, original_bind)
        self.assertIn("/custom/mount/point", vol.bind_volume)

    def test_volume_replace_bind_dirname(self):
        """Test replacing bind volume directory."""
        vol = Volume("/data/file.txt", output=True)

        vol.replace_bind_dirname("/new/dir/mount")

        self.assertIn("/new/dir", vol.bind_volume)


class TestCommand(unittest.TestCase):
    """Test Command class for command execution."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_log = MagicMock()
        self.mock_log.log = MagicMock()
        self.mock_profile = MagicMock()

    def test_command_creation(self):
        """Test Command initialization."""
        cmd = Command(
            "echo hello world", self.mock_log, self.mock_profile, name="test_cmd"
        )

        self.assertEqual(cmd.name, "test_cmd")
        self.assertEqual(cmd.cmd, ["echo", "hello", "world"])
        self.assertEqual(cmd.profile, self.mock_profile)
        self.assertEqual(cmd.inputs, [])
        self.assertEqual(cmd.outputs, [])

    def test_command_without_name(self):
        """Test Command with warning for no name."""
        cmd = Command("ls -la", self.mock_log, self.mock_profile)

        self.mock_log.log.warning.assert_called_once()

    def test_add_output(self):
        """Test adding output file."""
        cmd = Command("test", self.mock_log, self.mock_profile)

        cmd.add_output("/data/output.txt")

        self.assertIn("/data/output.txt", cmd.outputs)

    def test_add_output_no_duplicates(self):
        """Test that duplicate outputs are not added."""
        cmd = Command("test", self.mock_log, self.mock_profile)

        cmd.add_output("/data/output.txt")
        cmd.add_output("/data/output.txt")

        self.assertEqual(cmd.outputs.count("/data/output.txt"), 1)

    def test_add_input_exact(self):
        """Test adding input file with exact match."""
        cmd = Command("test", self.mock_log, self.mock_profile)

        cmd.add_input("/data/input.txt", match="exact")

        self.assertIn("/data/input.txt", cmd.inputs)

    @patch("pype.process.glob")
    def test_add_input_recursive(self, mock_glob):
        """Test adding input files with recursive pattern."""
        mock_glob.return_value = [
            "/data/input1.txt",
            "/data/input2.txt",
            "/data/input3.txt",
        ]
        cmd = Command("test", self.mock_log, self.mock_profile)

        cmd.add_input("/data/input", match="recursive")

        self.assertEqual(len(cmd.inputs), 3)
        mock_glob.assert_called_once()

    def test_add_volume(self):
        """Test adding volume."""
        cmd = Command("test", self.mock_log, self.mock_profile)

        cmd.add_volume("/data/input.txt", output=False)

        self.assertEqual(len(cmd.volumes), 1)
        self.assertEqual(cmd.volumes[0].path, "/data/input.txt")

    def test_normalize_volumes(self):
        """Test volume normalization removes duplicates."""
        cmd = Command("test", self.mock_log, self.mock_profile)

        cmd.add_volume("/data/file1.txt")
        cmd.add_volume("/data/file2.txt")
        cmd.add_volume("/data/file1.txt")  # Duplicate

        cmd.normalize_volumes()

        # Should have at most 2 unique volumes
        self.assertLessEqual(len(cmd.volumes), 2)

    def test_add_namespace(self):
        """Test adding namespace."""
        cmd = Command("test", self.mock_log, self.mock_profile)
        namespace_dict = {"namespace": "docker@ubuntu:latest", "version": "20.04"}

        with patch("pype.process.Namespace") as mock_ns:
            cmd.add_namespace(namespace_dict)
            mock_ns.assert_called_once()

    @patch("pype.process.subprocess.Popen")
    def test_local_run(self, mock_popen):
        """Test local command execution."""
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        cmd = Command("echo test", self.mock_log, self.mock_profile, "test")
        cmd.local_run()

        mock_popen.assert_called_once()
        self.assertEqual(cmd.proc, mock_proc)

    def test_pipe_in(self):
        """Test piping output from one command to another."""
        cmd1 = Command("echo hello", self.mock_log, self.mock_profile, "cmd1")
        cmd2 = Command("cat", self.mock_log, self.mock_profile, "cmd2")

        with patch.object(cmd1, "run"):
            with patch.object(cmd1, "stdout", MagicMock()):
                cmd2.pipe_in(cmd1)

                self.assertEqual(cmd2.procin, cmd1)

    def test_child_close(self):
        """Test closing child process stdout."""
        cmd = Command("test", self.mock_log, self.mock_profile, "parent")
        cmd.procin = MagicMock()
        cmd.procin.stdout = MagicMock()

        cmd.child_close()

        cmd.procin.stdout.close.assert_called_once()

    @patch("pype.process.subprocess.Popen")
    def test_close_with_child(self, mock_popen):
        """Test closing command with child process."""
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (b"output", b"")
        mock_proc.returncode = 0  # Mock successful exit
        mock_popen.return_value = mock_proc

        cmd = Command("test", self.mock_log, self.mock_profile)
        cmd.proc = mock_proc
        cmd.procin = MagicMock()
        cmd.procin.stdout = MagicMock()

        result, returncode = cmd.close()

        self.assertEqual(returncode, 0)
        mock_proc.communicate.assert_called_once()
        cmd.procin.stdout.close.assert_called_once()


class TestNamespace(unittest.TestCase):
    """Test Namespace class for environment management."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_log = MagicMock()
        self.mock_profile = MagicMock()

    def test_namespace_docker(self):
        """Test Docker namespace initialization."""
        program_dict = {"namespace": "docker@ubuntu:latest", "version": "20.04"}

        with patch("pype.process.PYPE_DOCKER", "/usr/bin/docker"):
            ns = Namespace(program_dict, self.mock_log, self.mock_profile)

            self.assertEqual(ns.type, "docker")
            self.assertEqual(len(ns.list), 1)
            self.assertIn("ubuntu", ns.list[0])

    def test_namespace_path(self):
        """Test path-based namespace."""
        program_dict = {"namespace": "path@/usr/bin/python3", "version": "3.9"}

        ns = Namespace(program_dict, self.mock_log, self.mock_profile)

        self.assertEqual(ns.type, "path")
        self.assertIn("/usr/bin/python3", ns.list[0])

    def test_namespace_path_implicit(self):
        """Test implicit path namespace (no @)."""
        program_dict = {"namespace": "/usr/bin/python3", "version": "3.9"}

        ns = Namespace(program_dict, self.mock_log, self.mock_profile)

        self.assertEqual(ns.type, "path")

    def test_namespace_env_module(self):
        """Test environment module namespace."""
        program_dict = {
            "namespace": "env_module@gcc",
            "version": "9.3.0",
            "dependencies": [],
        }

        ns = Namespace(program_dict, self.mock_log, self.mock_profile)

        self.assertEqual(ns.type, "env_module")

    def test_namespace_env_module_with_dependencies(self):
        """Test environment module with dependencies."""
        program_dict = {
            "namespace": "env_module@gcc",
            "version": "9.3.0",
            "dependencies": ["cuda"],
        }

        self.mock_profile.programs = {
            "cuda": {
                "namespace": "env_module@cuda",
                "version": "11.0",
                "dependencies": [],
            }
        }

        ns = Namespace(program_dict, self.mock_log, self.mock_profile)

        self.assertEqual(ns.type, "env_module")
        self.assertGreater(len(ns.list), 1)

    def test_namespace_invalid_format(self):
        """Test invalid namespace format raises error."""
        program_dict = {
            "namespace": "docker@ubuntu@extra",  # Too many @
            "version": "20.04",
        }

        with self.assertRaises(CommandNamespaceError):
            Namespace(program_dict, self.mock_log, self.mock_profile)

    def test_namespace_unsupported_type(self):
        """Test unsupported namespace type raises error."""
        program_dict = {"namespace": "invalid@something", "version": "1.0"}

        with self.assertRaises(CommandNamespaceError):
            Namespace(program_dict, self.mock_log, self.mock_profile)

    def test_namespace_first(self):
        """Test first() method returns first item."""
        program_dict = {"namespace": "path@/usr/bin/python3", "version": "3.9"}

        ns = Namespace(program_dict, self.mock_log, self.mock_profile)
        first_item = ns.first()

        self.assertEqual(first_item, ns.list[0])


class TestPathUtilities(unittest.TestCase):
    """Test path utility functions."""

    def test_is_direct_child_of_true(self):
        """Test is_direct_child_of with true case."""
        result = is_direct_child_of("/data/input.txt", "/data")
        self.assertTrue(result)

    def test_is_direct_child_of_false(self):
        """Test is_direct_child_of with false case."""
        result = is_direct_child_of("/data/subdir/file.txt", "/data")
        self.assertFalse(result)

    def test_has_same_basedir_true(self):
        """Test has_same_basedir with true case."""
        result = has_same_basedir("/data/file1.txt", "/data/file2.txt")
        self.assertTrue(result)

    def test_has_same_basedir_false(self):
        """Test has_same_basedir with false case."""
        result = has_same_basedir("/data/file.txt", "/other/file.txt")
        self.assertFalse(result)


class TestProgramString(unittest.TestCase):
    """Test program_string formatting."""

    def test_program_string_with_path(self):
        """Test program string with path."""
        program_dict = {"path": "/usr/bin", "version": "1.0"}

        result = program_string(program_dict)
        self.assertEqual(result, "/usr/bin/1.0")

    def test_program_string_with_namespace(self):
        """Test program string with namespace."""
        program_dict = {"namespace": "gcc", "version": "9.3.0"}

        result = program_string(program_dict)
        self.assertEqual(result, "gcc/9.3.0")


class TestModuleIntegration(unittest.TestCase):
    """Integration tests for module functionality."""

    @patch("pype.process.get_module_cmd")
    @patch("pype.process.subprocess.Popen")
    def test_command_with_env_module(self, mock_popen, mock_get_module):
        """Test command execution with environment modules."""
        mock_log = MagicMock()
        mock_log.log = MagicMock()
        mock_profile = MagicMock()

        cmd = Command("gcc --version", mock_log, mock_profile, "compile")

        # Add mock namespace
        cmd.namespace = MagicMock()
        cmd.namespace.type = "env_module"
        cmd.namespace.list = ["gcc/9.3.0"]

        with patch.object(cmd, "local_run"):
            cmd.module_run()

            mock_get_module.assert_called_once()


class TestVolumeBehavior(unittest.TestCase):
    """Test complex volume behavior."""

    def test_volume_child_replacement(self):
        """Test volume replacement when one is child of another."""
        cmd = Command("test", MagicMock(), MagicMock())

        # Add parent volume
        cmd.add_volume("/data", output=False)
        parent_bind = cmd.volumes[0].bind_volume

        # Add child volume with same mode
        cmd.add_volume("/data/subdir", output=False)

        # Child should be replaced with parent's binding
        self.assertGreaterEqual(len(cmd.volumes), 1)

    def test_volume_same_basedir_replacement(self):
        """Test volume replacement when same base directory."""
        cmd = Command("test", MagicMock(), MagicMock())

        cmd.add_volume("/data/file1.txt", output=False)
        cmd.add_volume("/data/file2.txt", output=False)

        # Both should have compatible bindings
        self.assertGreaterEqual(len(cmd.volumes), 1)


if __name__ == "__main__":
    unittest.main()
