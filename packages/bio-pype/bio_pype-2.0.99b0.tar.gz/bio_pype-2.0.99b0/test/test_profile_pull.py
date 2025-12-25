"""Unit tests for profile image pulling functionality.

Tests for:
- pull_singularity_image function
- pull_profile_images function
- Integration with container utilities
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from pype.logger import PypeLogger
from pype.process import Namespace
from pype.utils.profiles import (
    DockerConfig,
    pull_profile_images,
    pull_singularity_image,
)


class TestPullSingularityImage(unittest.TestCase):
    """Test pull_singularity_image function."""

    def setUp(self):
        """Create temporary cache directory for tests."""
        self.test_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.test_dir, "singularity")
        os.makedirs(self.cache_dir, exist_ok=True)

        # Create mock logger
        self.log = MagicMock()
        self.log.log = MagicMock()

        # Create mock profile with programs dict
        self.profile = MagicMock()
        self.profile.programs = {}

        # Create DockerConfig for testing
        self.docker = DockerConfig(
            exec_path=Path("singularity"),
            runtime="singularity",
            cache_dir=Path(self.cache_dir),
        )

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pull_invalid_namespace(self):
        """Test pulling with non-docker namespace."""
        program_dict = {
            "namespace": "env_module@gcc/9.3.0",
            "version": "9.3.0",
        }

        namespace = Namespace(program_dict, self.log.log, self.profile)
        result = pull_singularity_image(namespace, self.docker, self.log)

        self.assertFalse(result["success"])
        self.assertIn("Not a docker namespace", result["message"])
        self.assertIsNone(result["sif_path"])

    def test_pull_missing_version(self):
        """Test pulling without version specified."""
        program_dict = {
            "namespace": "docker@biocontainers/samtools",
            "version": None,
        }

        namespace = Namespace(program_dict, self.log.log, self.profile)
        result = pull_singularity_image(namespace, self.docker, self.log)

        self.assertFalse(result["success"])
        self.assertIn("version", result["message"].lower())

    def test_pull_existing_image(self):
        """Test pulling when image already exists."""
        # Create a fake SIF file
        sif_path = Path(self.cache_dir) / "docker" / "docker.io" / "ubuntu_22.04.sif"
        sif_path.parent.mkdir(parents=True, exist_ok=True)
        sif_path.touch()

        program_dict = {
            "namespace": "docker@ubuntu",
            "version": "22.04",
        }

        namespace = Namespace(program_dict, self.log.log, self.profile)
        result = pull_singularity_image(namespace, self.docker, self.log)

        self.assertTrue(result["success"])
        self.assertIn("already exists", result["message"].lower())
        self.assertEqual(result["sif_path"], str(sif_path))

    @patch("subprocess.run")
    def test_pull_new_image_success(self, mock_run):
        """Test successfully pulling a new image."""
        # Mock successful singularity pull
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        program_dict = {
            "namespace": "docker@biocontainers/samtools",
            "version": "1.15",
        }

        namespace = Namespace(program_dict, self.log.log, self.profile)
        result = pull_singularity_image(namespace, self.docker, self.log)

        self.assertTrue(result["success"])
        self.assertIn("successful", result["message"].lower())
        # Verify singularity pull was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        # Convert first element to string for comparison (can be Path or str)
        self.assertEqual(str(call_args[0]), "singularity")
        self.assertEqual(call_args[1], "pull")
        self.assertIn("docker://docker.io/biocontainers/samtools:1.15", call_args)

    @patch("subprocess.run")
    def test_pull_new_image_failure(self, mock_run):
        """Test handling of failed image pull."""
        # Mock failed singularity pull
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Image not found")

        program_dict = {
            "namespace": "docker@quay.io/biocontainers/samtools",
            "version": "1.15",
        }

        namespace = Namespace(program_dict, self.log.log, self.profile)
        result = pull_singularity_image(namespace, self.docker, self.log)

        self.assertFalse(result["success"])
        self.assertIn("failed", result["message"].lower())
        self.assertIn("Image not found", result["message"])

    @patch("subprocess.run")
    def test_pull_timeout(self, mock_run):
        """Test handling of pull timeout."""
        import subprocess

        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 600)

        program_dict = {
            "namespace": "docker@ubuntu",
            "version": "22.04",
        }

        namespace = Namespace(program_dict, self.log.log, self.profile)
        result = pull_singularity_image(namespace, self.docker, self.log)

        self.assertFalse(result["success"])
        self.assertIn("timed out", result["message"].lower())

    def test_pull_singularity_not_found(self):
        """Test when singularity command is not available."""
        program_dict = {
            "namespace": "docker@ubuntu",
            "version": "22.04",
        }

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("singularity not found")

            namespace = Namespace(program_dict, self.log.log, self.profile)
            result = pull_singularity_image(namespace, self.docker, self.log)

            self.assertFalse(result["success"])
            self.assertIn("not found", result["message"].lower())

    @patch("subprocess.run")
    def test_pull_with_logger(self, mock_run):
        """Test pulling with logger output."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        mock_log = Mock()
        mock_log.log = Mock()

        program_dict = {
            "namespace": "docker@ubuntu",
            "version": "22.04",
        }

        namespace = Namespace(program_dict, mock_log.log, self.profile)
        result = pull_singularity_image(namespace, self.docker, log=mock_log)

        # Logger should have been called
        self.assertTrue(mock_log.log.info.called)
        self.assertTrue(result["success"])


class TestPullProfileImages(unittest.TestCase):
    """Test pull_profile_images function."""

    def setUp(self):
        """Create temporary cache directory and mock profile."""
        self.test_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.test_dir, "singularity")
        os.makedirs(self.cache_dir, exist_ok=True)

        # Create a mock profile
        self.mock_profile = Mock()

        # Create mock logger
        self.log = MagicMock()
        self.log.log = MagicMock()

        # Docker exec path
        self.docker_exec = "singularity"

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pull_empty_profile(self):
        """Test pulling images from profile with no programs."""
        self.mock_profile.programs = {}

        results = pull_profile_images(
            self.mock_profile, self.cache_dir, self.docker_exec, self.log
        )

        self.assertEqual(results, {})

    def test_pull_profile_docker_only(self):
        """Test pulling profile with only docker programs."""
        self.mock_profile.programs = {
            "samtools": {
                "namespace": "docker@biocontainers/samtools",
                "version": "1.15",
            },
            "ubuntu": {
                "namespace": "docker@ubuntu",
                "version": "22.04",
            },
        }

        with patch("pype.utils.profiles.pull_singularity_image") as mock_pull:
            mock_pull.return_value = {
                "success": True,
                "sif_path": "/path/to/sif",
                "message": "Success",
            }

            results = pull_profile_images(
                self.mock_profile, self.cache_dir, self.docker_exec, self.log
            )

            # Should have called pull for both images
            self.assertEqual(len(results), 2)
            self.assertIn("samtools", results)
            self.assertIn("ubuntu", results)
            self.assertEqual(mock_pull.call_count, 2)

    def test_pull_profile_mixed_namespaces(self):
        """Test pulling profile with mixed namespace types."""
        self.mock_profile.programs = {
            "samtools": {
                "namespace": "docker@biocontainers/samtools",
                "version": "1.15",
            },
            "gcc": {
                "namespace": "env_module@gcc/9.3.0",
                "version": "9.3.0",
            },
            "custom_tool": {
                "namespace": "path@/usr/local/bin/custom",
                "version": "1.0",
            },
        }

        with patch("pype.utils.profiles.pull_singularity_image") as mock_pull:
            mock_pull.return_value = {
                "success": True,
                "sif_path": "/path/to/sif",
                "message": "Success",
            }

            results = pull_profile_images(
                self.mock_profile, self.cache_dir, self.docker_exec, self.log
            )

            # Should have results for all programs
            self.assertEqual(len(results), 3)

            # Only docker program should call pull_singularity_image
            mock_pull.assert_called_once()

            # Non-docker programs should be marked as skipped
            self.assertIn("env_module@gcc", results["gcc"]["message"])
            self.assertIn(
                "path@/usr/local/bin/custom", results["custom_tool"]["message"]
            )

    def test_pull_profile_with_failures(self):
        """Test pulling profile where some images fail."""
        self.mock_profile.programs = {
            "samtools": {
                "namespace": "docker@biocontainers/samtools",
                "version": "1.15",
            },
            "cuda": {
                "namespace": "docker@nvcr.io/nvidia/cuda",
                "version": "11.8",
            },
        }

        def pull_side_effect(namespace, docker, log=None):
            if "samtools" in namespace.str:
                return {
                    "success": True,
                    "sif_path": "/path/to/samtools.sif",
                    "message": "Success",
                }
            else:
                return {"success": False, "sif_path": None, "message": "Failed to pull"}

        with patch("pype.utils.profiles.pull_singularity_image") as mock_pull:
            mock_pull.side_effect = pull_side_effect

            results = pull_profile_images(
                self.mock_profile, self.cache_dir, self.docker_exec, self.log
            )

            self.assertTrue(results["samtools"]["success"])
            self.assertFalse(results["cuda"]["success"])

    def test_pull_profile_with_logger(self):
        """Test pulling with logger."""
        self.mock_profile.programs = {
            "ubuntu": {
                "namespace": "docker@ubuntu",
                "version": "22.04",
            },
        }

        mock_log = Mock()
        mock_log.log = Mock()

        with patch("pype.utils.profiles.pull_singularity_image") as mock_pull:
            mock_pull.return_value = {
                "success": True,
                "sif_path": "/path/to/sif",
                "message": "Success",
            }

            results = pull_profile_images(
                self.mock_profile, self.cache_dir, self.docker_exec, log=mock_log
            )

            # Logger should have been called
            self.assertTrue(mock_log.log.info.called)

    def test_pull_profile_returns_dict(self):
        """Test that function returns proper result dictionary."""
        self.mock_profile.programs = {
            "samtools": {
                "namespace": "docker@biocontainers/samtools",
                "version": "1.15",
            },
        }

        with patch("pype.utils.profiles.pull_singularity_image") as mock_pull:
            mock_pull.return_value = {
                "success": True,
                "sif_path": "/path/to/samtools.sif",
                "message": "Success",
            }

            results = pull_profile_images(
                self.mock_profile, self.cache_dir, self.docker_exec, self.log
            )

            # Check result structure
            self.assertIn("samtools", results)
            result = results["samtools"]
            self.assertIn("success", result)
            self.assertIn("sif_path", result)
            self.assertIn("message", result)


if __name__ == "__main__":
    unittest.main()
