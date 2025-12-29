"""Integration tests for parallel queue graceful shutdown."""

import os
import sys
import tempfile
import unittest
import logging
from io import StringIO
import yaml

from pype.utils.queues import TaskScheduler, JobStatus, check_for_blocked_jobs
from pype.pype_modules.queues.parallel import LocalResourceManager


class TestGracefulShutdownDetection(unittest.TestCase):
    """Test graceful shutdown detection for blocked jobs."""

    def setUp(self):
        """Set up test fixtures."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.runtime_file = os.path.join(self.tmp_dir.name, 'pipeline_runtime.yaml')
        # Create a simple logger for tests
        self.log = logging.getLogger('test')

    def tearDown(self):
        """Clean up test fixtures."""
        self.tmp_dir.cleanup()

    def _create_runtime(self, jobs):
        """Create a test runtime YAML file.

        Args:
            jobs: List of dict with job definitions
        """
        runtime = {}
        for job in jobs:
            runtime[job['run_id']] = {
                'command': job.get('command', 'echo test'),
                'status': job.get('status', JobStatus.PENDING.value),
                'name': job.get('name', job['run_id']),
                'requirements': job.get('requirements', {'ncpu': 1, 'mem': '1gb'}),
                'dependencies': job.get('dependencies', []),
            }

        with open(self.runtime_file, 'wt') as f:
            yaml.dump(runtime, f)

        return runtime

    def test_blocked_by_failed_dependency(self):
        """Test detection of jobs blocked by failed dependencies."""
        # Create runtime with one failed job and one pending job that depends on it
        runtime = self._create_runtime([
            {
                'run_id': 'job1',
                'name': 'failing_job',
                'status': JobStatus.FAILED.value,
                'dependencies': [],
            },
            {
                'run_id': 'job2',
                'name': 'blocked_job',
                'status': JobStatus.PENDING.value,
                'dependencies': ['job1'],
            },
        ])

        # Load scheduler
        scheduler = TaskScheduler(self.runtime_file, None, None)

        # Check for blocked jobs
        blocked = scheduler.get_blocked_by_failed_deps()

        # Verify job2 is blocked by job1
        self.assertEqual(len(blocked), 1)
        run_id, job_data, failed_deps = blocked[0]
        self.assertEqual(run_id, 'job2')
        self.assertIn('job1', failed_deps)

    def test_candidate_job_detection(self):
        """Test candidate job calculation for stall detection."""
        # Create runtime with:
        # - 1 running job
        # - 1 ready job
        # - 2 pending jobs blocked by failed dependencies
        runtime = self._create_runtime([
            {
                'run_id': 'job1',
                'name': 'running',
                'status': JobStatus.RUNNING.value,
            },
            {
                'run_id': 'job2',
                'name': 'ready',
                'status': JobStatus.PENDING.value,
                'dependencies': [],
            },
            {
                'run_id': 'job3',
                'name': 'blocked1',
                'status': JobStatus.PENDING.value,
                'dependencies': ['job_failed'],
            },
            {
                'run_id': 'job4',
                'name': 'blocked2',
                'status': JobStatus.PENDING.value,
                'dependencies': ['job_failed'],
            },
            {
                'run_id': 'job_failed',
                'name': 'failed',
                'status': JobStatus.FAILED.value,
            },
        ])

        scheduler = TaskScheduler(self.runtime_file, None, None)
        resources = LocalResourceManager(4, 1024**3)

        # Check for blocked jobs using check_for_blocked_jobs
        has_blocked, reason, blocked_ids = check_for_blocked_jobs(
            scheduler, self.log, resources
        )

        # Verify blocked jobs detected
        self.assertTrue(has_blocked)
        self.assertIsNotNone(reason)
        self.assertEqual(len(blocked_ids), 2)
        self.assertIn('job3', blocked_ids)
        self.assertIn('job4', blocked_ids)

    def test_no_blocked_when_all_ready(self):
        """Test that no jobs are blocked when all pending jobs are ready."""
        # Create runtime with pending jobs that can run
        runtime = self._create_runtime([
            {
                'run_id': 'job1',
                'name': 'completed',
                'status': JobStatus.COMPLETED.value,
            },
            {
                'run_id': 'job2',
                'name': 'ready1',
                'status': JobStatus.PENDING.value,
                'dependencies': ['job1'],
            },
            {
                'run_id': 'job3',
                'name': 'ready2',
                'status': JobStatus.PENDING.value,
                'dependencies': [],
            },
        ])

        scheduler = TaskScheduler(self.runtime_file, None, None)
        resources = LocalResourceManager(4, 1024**3)

        # Check for blocked jobs
        has_blocked, reason, blocked_ids = check_for_blocked_jobs(
            scheduler, self.log, resources
        )

        # No jobs should be blocked
        self.assertFalse(has_blocked)
        self.assertIsNone(reason)
        self.assertIsNone(blocked_ids)

    def test_resource_exhaustion_not_candidate_blocking(self):
        """Verify resource limits don't trigger candidate job detection.

        Resource-based blocking (job requires more CPU/memory than available)
        is different from candidate job detection. A job that's ready but can't
        run due to resource limits is still a "candidate" for blocking purposes.
        This is expected - the scheduler should attempt to run it.
        """
        # Create job requiring more memory than available
        runtime = self._create_runtime([
            {
                'run_id': 'job1',
                'name': 'too_much_memory',
                'status': JobStatus.PENDING.value,
                'requirements': {'ncpu': 1, 'mem': '2gb'},
            },
        ])

        scheduler = TaskScheduler(self.runtime_file, None, None)
        resources = LocalResourceManager(4, 1024**3)  # 1GB max

        # Check for blocked jobs (dependency-based, not resource-based)
        has_blocked, reason, blocked_ids = check_for_blocked_jobs(
            scheduler, self.log, resources
        )

        # Should NOT be blocked from candidate perspective (job is ready)
        # even though it can't actually run due to resource limits
        self.assertFalse(has_blocked)
        self.assertIsNone(reason)
        self.assertIsNone(blocked_ids)

        # Verify scheduler correctly identifies the resource issue
        blocked_by_res = scheduler.get_blocked_by_resources(resources)
        self.assertEqual(len(blocked_by_res), 1)
        self.assertEqual(blocked_by_res[0][0], 'job1')

    def test_cancelled_status_is_terminal(self):
        """Test that CANCELLED status is treated as terminal."""
        runtime = self._create_runtime([
            {
                'run_id': 'job1',
                'status': JobStatus.COMPLETED.value,
            },
            {
                'run_id': 'job2',
                'status': JobStatus.FAILED.value,
            },
            {
                'run_id': 'job3',
                'status': JobStatus.CANCELLED.value,
            },
        ])

        scheduler = TaskScheduler(self.runtime_file, None, None)

        # Pipeline should be complete when all jobs are in terminal state
        self.assertTrue(scheduler.is_complete())

        # Stats should include cancelled count
        stats = scheduler.get_stats()
        self.assertEqual(stats['cancelled'], 1)
        self.assertEqual(stats['completed'], 1)
        self.assertEqual(stats['failed'], 1)

    def test_graceful_shutdown_updates_cancelled_status(self):
        """Test that update_job_status can set jobs to CANCELLED."""
        from pype.utils.queues import update_job_status

        # Create initial runtime with pending job
        runtime = self._create_runtime([
            {
                'run_id': 'job1',
                'status': JobStatus.PENDING.value,
            },
        ])

        # Update status to CANCELLED
        update_job_status(
            self.runtime_file,
            'job1',
            JobStatus.CANCELLED.value,
            error_msg='Blocked by pipeline stall'
        )

        # Verify status was updated
        with open(self.runtime_file, 'rt') as f:
            updated_runtime = yaml.safe_load(f)

        self.assertEqual(
            updated_runtime['job1']['status'],
            JobStatus.CANCELLED.value
        )
        self.assertIn('error_msg', updated_runtime['job1'])


if __name__ == '__main__':
    unittest.main()
