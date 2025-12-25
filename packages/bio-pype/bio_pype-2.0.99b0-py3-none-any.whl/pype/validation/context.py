"""Validation context and workspace discovery.

Manages workspace discovery, module caching, and shared state
across validation operations.
"""

from pathlib import Path
from typing import Dict, Optional, Set

from pype.validation.core import ValidationContext


def detect_module_root(file_path: Path) -> Optional[Path]:
    """Auto-detect PYPE_MODULES root from a file path.

    Looks for a parent directory that contains snippets/, profiles/, pipelines/, queues/
    subdirectories. This allows validation without requiring environment variables.

    Args:
        file_path: Path to a snippet/profile/pipeline file

    Returns:
        Path to the module root (containing snippets/, profiles/, etc.) or None
    """
    path = file_path.resolve()

    # Walk up the directory tree looking for the module structure
    while path != path.parent:
        path = path.parent

        # Check if this directory contains expected subdirectories
        expected_dirs = {"snippets", "profiles", "pipelines", "queues"}
        found_dirs = {d.name for d in path.iterdir() if d.is_dir()} & expected_dirs

        # If we found at least some of the expected directories, this is likely the root
        if found_dirs:
            return path

    return None


def _discover_modules_in_dir(workspace_root: Path) -> tuple:
    """Internal function to discover modules without creating ValidationContext.

    Used to avoid infinite recursion in ValidationContext.__post_init__.

    Args:
        workspace_root: Root directory containing snippets/, profiles/, pipelines/

    Returns:
        Tuple of (snippet_paths, profile_paths, pipeline_paths)
    """
    snippet_paths = list(workspace_root.glob("snippets/*.md"))
    profile_paths = list(workspace_root.glob("profiles/*.yaml")) + list(
        workspace_root.glob("profiles/*.yml")
    )
    pipeline_paths = list(workspace_root.glob("pipelines/*.yaml")) + list(
        workspace_root.glob("pipelines/*.yml")
    )

    return sorted(snippet_paths), sorted(profile_paths), sorted(pipeline_paths)


def discover_modules(workspace_root: Optional[Path] = None) -> ValidationContext:
    """Discover all snippets, profiles, and pipelines in a workspace.

    Expects workspace_root to be a module folder with:
    - snippets/ subdirectory
    - profiles/ subdirectory
    - pipelines/ subdirectory

    Example: workspace_root=/Users/lgq442/src/pype_modules/qc

    Args:
        workspace_root: Root directory containing snippets/, profiles/, pipelines/
                       If None, will use current directory.

    Returns:
        ValidationContext with discovered module paths
    """
    if workspace_root is None:
        workspace_root = Path.cwd()

    workspace_root = workspace_root.resolve()

    # Discover modules using internal function (no ValidationContext creation)
    snippet_paths, profile_paths, pipeline_paths = _discover_modules_in_dir(
        workspace_root
    )

    # Create context with discovered paths (prevents auto-discovery in __post_init__)
    context = ValidationContext(
        workspace_root=workspace_root,
        snippet_paths=snippet_paths,
        profile_paths=profile_paths,
        pipeline_paths=pipeline_paths,
    )

    return context


class WorkspaceIndex:
    """Index of modules in a workspace for fast lookups.

    Caches module names and paths to avoid repeated filesystem scans.
    """

    def __init__(self, context: ValidationContext) -> None:
        """Initialize workspace index from validation context.

        Args:
            context: ValidationContext with discovered modules
        """
        self._snippet_map: Dict[str, Path] = {}
        self._profile_map: Dict[str, Path] = {}
        self._pipeline_map: Dict[str, Path] = {}

        # Build maps from paths
        for path in context.snippet_paths:
            name = path.stem
            self._snippet_map[name] = path

        for path in context.profile_paths:
            name = path.stem
            self._profile_map[name] = path

        for path in context.pipeline_paths:
            name = path.stem
            self._pipeline_map[name] = path

    def get_snippet_path(self, name: str) -> Optional[Path]:
        """Get path for snippet by name.

        Args:
            name: Snippet name (without .md extension)

        Returns:
            Path to snippet file, or None if not found
        """
        return self._snippet_map.get(name)

    def get_profile_path(self, name: str) -> Optional[Path]:
        """Get path for profile by name.

        Args:
            name: Profile name (without .yaml/.yml extension)

        Returns:
            Path to profile file, or None if not found
        """
        return self._profile_map.get(name)

    def get_pipeline_path(self, name: str) -> Optional[Path]:
        """Get path for pipeline by name.

        Args:
            name: Pipeline name (without .yaml/.yml extension)

        Returns:
            Path to pipeline file, or None if not found
        """
        return self._pipeline_map.get(name)

    def all_snippet_names(self) -> Set[str]:
        """Get all snippet names in workspace.

        Returns:
            Set of snippet names
        """
        return set(self._snippet_map.keys())

    def all_profile_names(self) -> Set[str]:
        """Get all profile names in workspace.

        Returns:
            Set of profile names
        """
        return set(self._profile_map.keys())

    def all_pipeline_names(self) -> Set[str]:
        """Get all pipeline names in workspace.

        Returns:
            Set of pipeline names
        """
        return set(self._pipeline_map.keys())
