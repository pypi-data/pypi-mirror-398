"""Unit tests for container utilities.

Tests for:
- Container reference parsing (multiple registries)
- Singularity SIF path construction
- Docker URI generation
"""

import unittest
from pathlib import Path

from pype.utils.containers import (
    get_docker_uri,
    get_singularity_image_path,
    parse_container_reference,
)


class TestParseContainerReference(unittest.TestCase):
    """Test container reference parsing."""

    def test_parse_docker_hub_default(self):
        """Test parsing Docker Hub reference without registry."""
        registry, image_path = parse_container_reference("biocontainers/samtools")
        self.assertEqual(registry, "docker.io")
        self.assertEqual(image_path, "biocontainers/samtools")

    def test_parse_quay_io(self):
        """Test parsing Quay.io reference."""
        registry, image_path = parse_container_reference(
            "quay.io/biocontainers/samtools"
        )
        self.assertEqual(registry, "quay.io")
        self.assertEqual(image_path, "biocontainers/samtools")

    def test_parse_nvcr_io(self):
        """Test parsing NVCR.io reference."""
        registry, image_path = parse_container_reference("nvcr.io/nvidia/cuda")
        self.assertEqual(registry, "nvcr.io")
        self.assertEqual(image_path, "nvidia/cuda")

    def test_parse_github_container_registry(self):
        """Test parsing GitHub Container Registry reference."""
        registry, image_path = parse_container_reference("ghcr.io/username/myimage")
        self.assertEqual(registry, "ghcr.io")
        self.assertEqual(image_path, "username/myimage")

    def test_parse_private_registry_with_port(self):
        """Test parsing private registry with port."""
        registry, image_path = parse_container_reference("localhost:5000/myimage")
        self.assertEqual(registry, "localhost:5000")
        self.assertEqual(image_path, "myimage")

    def test_parse_private_registry_with_port_multipart(self):
        """Test parsing private registry with port and multi-level path."""
        registry, image_path = parse_container_reference(
            "registry.example.com:5000/myorg/myimage"
        )
        self.assertEqual(registry, "registry.example.com:5000")
        self.assertEqual(image_path, "myorg/myimage")

    def test_parse_single_component(self):
        """Test parsing single image name (no namespace)."""
        registry, image_path = parse_container_reference("ubuntu")
        self.assertEqual(registry, "docker.io")
        self.assertEqual(image_path, "ubuntu")


class TestGetSingularityImagePath(unittest.TestCase):
    """Test Singularity SIF path construction."""

    def test_path_docker_io(self):
        """Test SIF path for Docker Hub image."""
        sif_path = get_singularity_image_path(
            "biocontainers/samtools", "1.15", "/cache"
        )
        expected = Path("/cache/docker/docker.io/biocontainers_samtools_1.15.sif")
        self.assertEqual(sif_path, expected)

    def test_path_quay_io(self):
        """Test SIF path for Quay.io image."""
        sif_path = get_singularity_image_path(
            "quay.io/biocontainers/samtools", "1.15", "/cache"
        )
        expected = Path("/cache/docker/quay.io/biocontainers_samtools_1.15.sif")
        self.assertEqual(sif_path, expected)

    def test_path_nvcr_io(self):
        """Test SIF path for NVCR.io image."""
        sif_path = get_singularity_image_path("nvcr.io/nvidia/cuda", "11.8", "/cache")
        expected = Path("/cache/docker/nvcr.io/nvidia_cuda_11.8.sif")
        self.assertEqual(sif_path, expected)

    def test_path_deep_namespace(self):
        """Test SIF path with deep image namespace."""
        sif_path = get_singularity_image_path(
            "ghcr.io/org/project/image", "latest", "/singularity"
        )
        expected = Path("/singularity/docker/ghcr.io/org_project_image_latest.sif")
        self.assertEqual(sif_path, expected)

    def test_path_private_registry_with_port(self):
        """Test SIF path for private registry with port."""
        sif_path = get_singularity_image_path("localhost:5000/myimage", "dev", "/cache")
        expected = Path("/cache/docker/localhost:5000/myimage_dev.sif")
        self.assertEqual(sif_path, expected)

    def test_path_returns_pathlib_path(self):
        """Test that function returns Path object."""
        sif_path = get_singularity_image_path("ubuntu", "22.04", "/cache")
        self.assertIsInstance(sif_path, Path)


class TestGetDockerUri(unittest.TestCase):
    """Test Docker URI generation."""

    def test_uri_docker_io_default(self):
        """Test docker:// URI for Docker Hub image."""
        uri = get_docker_uri("biocontainers/samtools", "1.15")
        self.assertEqual(uri, "docker://docker.io/biocontainers/samtools:1.15")

    def test_uri_quay_io(self):
        """Test docker:// URI for Quay.io image."""
        uri = get_docker_uri("quay.io/biocontainers/samtools", "1.15")
        self.assertEqual(uri, "docker://quay.io/biocontainers/samtools:1.15")

    def test_uri_nvcr_io(self):
        """Test docker:// URI for NVCR.io image."""
        uri = get_docker_uri("nvcr.io/nvidia/cuda", "11.8")
        self.assertEqual(uri, "docker://nvcr.io/nvidia/cuda:11.8")

    def test_uri_github_container_registry(self):
        """Test docker:// URI for GitHub Container Registry."""
        uri = get_docker_uri("ghcr.io/org/image", "main")
        self.assertEqual(uri, "docker://ghcr.io/org/image:main")

    def test_uri_single_image(self):
        """Test docker:// URI for single image name."""
        uri = get_docker_uri("ubuntu", "22.04")
        self.assertEqual(uri, "docker://docker.io/ubuntu:22.04")

    def test_uri_has_docker_scheme(self):
        """Test that URI has docker:// scheme."""
        uri = get_docker_uri("biocontainers/samtools", "1.15")
        self.assertTrue(uri.startswith("docker://"))

    def test_uri_has_version_tag(self):
        """Test that URI includes version as tag."""
        uri = get_docker_uri("ubuntu", "20.04")
        self.assertIn(":20.04", uri)


class TestConsistencyBetweenPathAndUri(unittest.TestCase):
    """Test that path and URI construction are consistent."""

    def test_docker_hub_consistency(self):
        """Test path and URI use same registry for Docker Hub."""
        namespace = "biocontainers/samtools"
        version = "1.15"

        sif_path = get_singularity_image_path(namespace, version, "/cache")
        docker_uri = get_docker_uri(namespace, version)

        # Both should reference docker.io
        self.assertIn("docker.io", str(sif_path))
        self.assertIn("docker.io", docker_uri)

    def test_quay_io_consistency(self):
        """Test path and URI use same registry for Quay.io."""
        namespace = "quay.io/biocontainers/samtools"
        version = "1.15"

        sif_path = get_singularity_image_path(namespace, version, "/cache")
        docker_uri = get_docker_uri(namespace, version)

        # Both should reference quay.io
        self.assertIn("quay.io", str(sif_path))
        self.assertIn("quay.io", docker_uri)

    def test_nvcr_io_consistency(self):
        """Test path and URI use same registry for NVCR.io."""
        namespace = "nvcr.io/nvidia/cuda"
        version = "11.8"

        sif_path = get_singularity_image_path(namespace, version, "/cache")
        docker_uri = get_docker_uri(namespace, version)

        # Both should reference nvcr.io
        self.assertIn("nvcr.io", str(sif_path))
        self.assertIn("nvcr.io", docker_uri)

    def test_version_in_both(self):
        """Test that version appears in both path and URI."""
        namespace = "ubuntu"
        version = "22.04"

        sif_path = get_singularity_image_path(namespace, version, "/cache")
        docker_uri = get_docker_uri(namespace, version)

        # Version should be in both
        self.assertIn("22.04", str(sif_path))
        self.assertIn("22.04", docker_uri)


if __name__ == "__main__":
    unittest.main()
