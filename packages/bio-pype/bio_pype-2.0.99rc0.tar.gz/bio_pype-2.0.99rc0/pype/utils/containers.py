"""Container image utilities for Docker, Singularity, and other runtimes.

Provides standardized functions for:
- Parsing container references (registry/image:tag)
- Constructing Singularity SIF file paths
- Building docker:// URIs for singularity pull

All functions ensure consistent behavior across Docker and Singularity,
enabling portable profiles that work on any system.
"""

from pathlib import Path
from typing import Tuple


def parse_container_reference(namespace_item: str) -> Tuple[str, str]:
    """Parse container reference into registry and image path.

    Handles various container reference formats:
    - "biocontainers/samtools" → default to docker.io
    - "quay.io/biocontainers/samtools" → use specified registry
    - "nvcr.io/nvidia/cuda" → registry with multi-level path
    - "localhost:5000/myimage" → private registry with port

    Args:
        namespace_item: Container reference string (no scheme like docker://)

    Returns:
        Tuple of (registry, image_path):
            - registry: Full registry hostname or "docker.io" default
            - image_path: Image path without registry or version

    Examples:
        >>> parse_container_reference("biocontainers/samtools")
        ('docker.io', 'biocontainers/samtools')

        >>> parse_container_reference("quay.io/biocontainers/samtools")
        ('quay.io', 'biocontainers/samtools')

        >>> parse_container_reference("nvcr.io/nvidia/cuda")
        ('nvcr.io', 'nvidia/cuda')

        >>> parse_container_reference("localhost:5000/myimage")
        ('localhost:5000', 'myimage')
    """
    parts = namespace_item.split("/")

    # Check if first component is a registry (contains . or :)
    # Registries have domain names (docker.io, quay.io) or ports (localhost:5000)
    if len(parts) > 1 and ("." in parts[0] or ":" in parts[0]):
        registry = parts[0]
        image_path = "/".join(parts[1:])
    else:
        # No registry specified - default to Docker Hub
        registry = "docker.io"
        image_path = namespace_item

    return registry, image_path


def get_singularity_image_path(
    namespace_item: str, version: str, cache_dir: str
) -> Path:
    """Convert Docker namespace to Singularity SIF file path.

    Creates consistent directory structure in Singularity cache:
    {cache_dir}/docker/{registry}/{image_path}_{version}.sif

    This allows:
    1. Multiple registries to coexist (docker.io, quay.io, etc.)
    2. Multi-level image paths to be preserved
    3. Version tracking in filename
    4. Easy discovery of available images

    Args:
        namespace_item: Container reference (e.g., "biocontainers/samtools")
        version: Image version/tag (e.g., "1.15")
        cache_dir: Singularity cache directory path

    Returns:
        Path object pointing to SIF file location

    Examples:
        >>> get_singularity_image_path("biocontainers/samtools", "1.15", "/cache")
        PosixPath('/cache/docker/docker.io/biocontainers/samtools_1.15.sif')

        >>> get_singularity_image_path("quay.io/biocontainers/samtools", "1.15", "/cache")
        PosixPath('/cache/docker/quay.io/biocontainers/samtools_1.15.sif')

        >>> get_singularity_image_path("nvcr.io/nvidia/cuda", "11.8", "/cache")
        PosixPath('/cache/docker/nvcr.io/nvidia/cuda_11.8.sif')
    """
    registry, image_path = parse_container_reference(namespace_item)

    # Build path: {cache}/docker/{registry}/{image}_{version}.sif
    # Replace slashes in image_path with underscores for valid filename
    sif_filename = f"{image_path.replace('/', '_')}_{version}.sif"

    sif_path = Path(cache_dir) / "docker" / registry / sif_filename

    return sif_path


def get_docker_uri(namespace_item: str, version: str) -> str:
    """Build docker:// URI for singularity pull command.

    Converts namespace format to full docker:// URI that singularity can pull.

    Args:
        namespace_item: Container reference (e.g., "biocontainers/samtools")
        version: Image version/tag (e.g., "1.15")

    Returns:
        Full docker:// URI suitable for `singularity pull` command

    Examples:
        >>> get_docker_uri("biocontainers/samtools", "1.15")
        'docker://docker.io/biocontainers/samtools:1.15'

        >>> get_docker_uri("quay.io/biocontainers/samtools", "1.15")
        'docker://quay.io/biocontainers/samtools:1.15'

        >>> get_docker_uri("nvcr.io/nvidia/cuda", "11.8")
        'docker://nvcr.io/nvidia/cuda:11.8'
    """
    registry, image_path = parse_container_reference(namespace_item)

    # Build: docker://{registry}/{image}:{version}
    docker_uri = f"docker://{registry}/{image_path}:{version}"

    return docker_uri
