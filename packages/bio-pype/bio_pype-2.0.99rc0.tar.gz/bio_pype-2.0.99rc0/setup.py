import os
from setuptools import setup
from importlib.util import spec_from_file_location, module_from_spec

def get_version():
    """Import version from __version__.py using importlib."""
    version_file = os.path.join(os.path.dirname(__file__), 'pype', '__version__.py')
    spec = spec_from_file_location('__version__', version_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load __version__.py from {version_file}")
        
    version_module = module_from_spec(spec)
    spec.loader.exec_module(version_module)
    return version_module.VERSION

setup(
    version=get_version(),
    packages=['pype'],
    # Rest of configuration comes from pyproject.toml
)
