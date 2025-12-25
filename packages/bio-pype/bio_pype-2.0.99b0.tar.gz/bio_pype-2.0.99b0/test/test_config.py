"""Tests for configuration and module fallback behavior."""

import os
import sys
import tempfile
import unittest


class TestModuleFallback(unittest.TestCase):
    """Test module fallback when custom PYPE_MODULES lacks subdirectories."""

    def test_queue_fallback_when_custom_missing(self):
        """Test that default queues are accessible when custom PYPE_MODULES lacks queues/."""
        # Create a temporary directory without queues subdirectory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create subdirectories that DO exist (to make PYPE_MODULES valid)
            os.makedirs(os.path.join(tmpdir, 'snippets'), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, 'profiles'), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, 'pipelines'), exist_ok=True)
            # Note: NOT creating queues/ subdirectory

            # Save original env var
            original_pype_modules = os.environ.get('PYPE_MODULES')

            try:
                # Set PYPE_MODULES to temp dir (no queues/ subdirectory)
                os.environ['PYPE_MODULES'] = tmpdir

                # Reload config to re-import modules with new env var
                # We need to reload the config module to apply the new env var
                import importlib
                import pype.__config__ as config_module
                importlib.reload(config_module)

                # Get the reloaded PYPE_QUEUES
                from pype.__config__ import PYPE_QUEUES
                from pype.misc import package_modules

                # Discover available queue modules
                queue_modules = package_modules(PYPE_QUEUES)
                queue_names = [m.split('.')[-1] for m in queue_modules]

                # Should have default queues - this verifies the fallback works
                # When custom PYPE_MODULES lacks queues/, defaults are still discoverable
                self.assertIn('dry_run', queue_names,
                             f"Default 'dry_run' queue not found. Available: {queue_names}")
                self.assertIn('parallel', queue_names,
                             f"Default 'parallel' queue not found. Available: {queue_names}")

                # Verify the full queue module names are present
                self.assertIn('queues.dry_run', queue_modules)
                self.assertIn('queues.parallel', queue_modules)

            finally:
                # Restore original env var and reload config
                if original_pype_modules is not None:
                    os.environ['PYPE_MODULES'] = original_pype_modules
                else:
                    os.environ.pop('PYPE_MODULES', None)

                # Reload config to restore original state
                import importlib
                import pype.__config__ as config_module
                importlib.reload(config_module)


if __name__ == '__main__':
    unittest.main()
