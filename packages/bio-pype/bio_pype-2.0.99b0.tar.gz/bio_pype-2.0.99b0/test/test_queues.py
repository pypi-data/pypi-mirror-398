"""Unit tests for pype.utils.queues module.

Tests for YAML-based pipeline runtime tracking and SnippetRuntime helper:
- YAML runtime file management (get_job_status, update_job_status, etc.)
- Job grouping for array submissions
- Ready job selection
- Pipeline completion detection
- SnippetRuntime class for queue implementations
"""

import os
import shutil
import tempfile
import unittest

import yaml

from pype.utils.queues import (
    JobStatus,
    SnippetRuntime,
    get_job_status,
    get_ready_jobs,
    is_pipeline_complete,
    update_job_status,
)


class TestJobStatus(unittest.TestCase):
    """Test JobStatus enumeration."""

    def test_status_values(self):
        """Test all status enum values."""
        self.assertEqual(JobStatus.PENDING.value, "pending")
        self.assertEqual(JobStatus.SUBMITTED.value, "submitted")
        self.assertEqual(JobStatus.RUNNING.value, "running")
        self.assertEqual(JobStatus.COMPLETED.value, "completed")
        self.assertEqual(JobStatus.FAILED.value, "failed")
        self.assertEqual(JobStatus.CANCELLED.value, "cancelled")

    def test_status_string_comparison(self):
        """Test that JobStatus can be compared with strings."""
        self.assertEqual(JobStatus.PENDING, "pending")
        self.assertEqual(JobStatus.COMPLETED, "completed")


class TestYamlRuntimeTracking(unittest.TestCase):
    """Test YAML-based runtime status tracking functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.runtime_file = os.path.join(self.test_dir, "pipeline_runtime.yaml")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def _create_runtime(self, jobs):
        """Helper to create a runtime YAML file."""
        runtime = {}
        for job_id, job_data in jobs.items():
            runtime[job_id] = {
                "command": job_data.get("command", f"echo {job_id}"),
                "requirements": job_data.get("requirements", {}),
                "dependencies": job_data.get("dependencies", []),
                "status": job_data.get("status", JobStatus.PENDING.value),
            }
        with open(self.runtime_file, "wt") as f:
            yaml.dump(runtime, f, default_flow_style=False)
        return runtime

    def test_get_job_status(self):
        """Test getting job status from YAML."""
        self._create_runtime(
            {
                "job1": {"status": JobStatus.PENDING.value},
                "job2": {"status": JobStatus.COMPLETED.value},
            }
        )

        self.assertEqual(
            get_job_status(self.runtime_file, "job1"), JobStatus.PENDING.value
        )
        self.assertEqual(
            get_job_status(self.runtime_file, "job2"), JobStatus.COMPLETED.value
        )
        self.assertIsNone(get_job_status(self.runtime_file, "nonexistent"))

    def test_get_job_status_nonexistent_file(self):
        """Test getting status when runtime file doesn't exist."""
        result = get_job_status("/nonexistent/file.yaml", "job1")
        self.assertIsNone(result)

    def test_update_job_status(self):
        """Test updating job status in YAML."""
        self._create_runtime({"job1": {"status": JobStatus.PENDING.value}})

        update_job_status(self.runtime_file, "job1", JobStatus.SUBMITTED.value)

        with open(self.runtime_file, "rt") as f:
            runtime = yaml.safe_load(f)

        self.assertEqual(runtime["job1"]["status"], JobStatus.SUBMITTED.value)
        self.assertIn("submitted_at", runtime["job1"])

    def test_update_job_status_to_running(self):
        """Test that started_at timestamp is set when status changes to RUNNING."""
        self._create_runtime({"job1": {"status": JobStatus.PENDING.value}})

        # Update to submitted first
        update_job_status(self.runtime_file, "job1", JobStatus.SUBMITTED.value)

        with open(self.runtime_file, "rt") as f:
            runtime = yaml.safe_load(f)
        self.assertIn("submitted_at", runtime["job1"])
        submitted_at = runtime["job1"]["submitted_at"]

        # Now update to running
        update_job_status(self.runtime_file, "job1", JobStatus.RUNNING.value)

        with open(self.runtime_file, "rt") as f:
            runtime = yaml.safe_load(f)

        self.assertEqual(runtime["job1"]["status"], JobStatus.RUNNING.value)
        self.assertIn("started_at", runtime["job1"])
        self.assertIsNotNone(runtime["job1"]["started_at"])
        # submitted_at should still be there
        self.assertEqual(runtime["job1"]["submitted_at"], submitted_at)

    def test_update_job_status_with_error(self):
        """Test updating job status with error message."""
        self._create_runtime({"job1": {"status": JobStatus.RUNNING.value}})

        update_job_status(
            self.runtime_file, "job1", JobStatus.FAILED.value, error_msg="Test error"
        )

        with open(self.runtime_file, "rt") as f:
            runtime = yaml.safe_load(f)

        self.assertEqual(runtime["job1"]["status"], JobStatus.FAILED.value)
        self.assertEqual(runtime["job1"]["error_msg"], "Test error")
        self.assertIn("completed_at", runtime["job1"])

    def test_update_job_status_creates_file(self):
        """Test that updating status creates the file and job entry."""
        # File doesn't exist yet
        self.assertFalse(os.path.exists(self.runtime_file))

        # update_job_status creates file and job entry if needed
        # This ensures we can always record job status
        update_job_status(self.runtime_file, "job1", "submitted")

        # File should now exist
        self.assertTrue(os.path.exists(self.runtime_file))

        # Job entry should be created
        with open(self.runtime_file, "rt") as f:
            runtime = yaml.safe_load(f)
        self.assertIn("job1", runtime)
        self.assertEqual(runtime["job1"]["status"], "submitted")

    def test_get_ready_jobs(self):
        """Test getting ready jobs (pending with completed dependencies)."""
        self._create_runtime(
            {
                "job1": {"status": JobStatus.PENDING.value, "dependencies": []},
                "job2": {"status": JobStatus.PENDING.value, "dependencies": ["job1"]},
                "job3": {
                    "status": JobStatus.PENDING.value,
                    "dependencies": ["job1", "job2"],
                },
                "job4": {"status": JobStatus.COMPLETED.value, "dependencies": []},
            }
        )

        # Initially only job1 is ready
        ready = get_ready_jobs(self.runtime_file)
        self.assertEqual(ready, ["job1"])

        # Mark job1 as completed
        update_job_status(self.runtime_file, "job1", JobStatus.COMPLETED.value)

        # Now job2 is ready
        ready = get_ready_jobs(self.runtime_file)
        self.assertEqual(ready, ["job2"])

        # Mark job2 as completed
        update_job_status(self.runtime_file, "job2", JobStatus.COMPLETED.value)

        # Now job3 is ready
        ready = get_ready_jobs(self.runtime_file)
        self.assertEqual(ready, ["job3"])

    def test_get_ready_jobs_empty(self):
        """Test getting ready jobs when none are ready."""
        self._create_runtime(
            {
                "job1": {"status": JobStatus.RUNNING.value, "dependencies": []},
                "job2": {"status": JobStatus.PENDING.value, "dependencies": ["job1"]},
            }
        )

        ready = get_ready_jobs(self.runtime_file)
        self.assertEqual(len(ready), 0)

    def test_is_pipeline_complete(self):
        """Test checking if pipeline is complete."""
        self._create_runtime(
            {
                "job1": {"status": JobStatus.COMPLETED.value},
                "job2": {"status": JobStatus.COMPLETED.value},
            }
        )

        self.assertTrue(is_pipeline_complete(self.runtime_file))

        # Update one job to pending
        update_job_status(self.runtime_file, "job1", JobStatus.PENDING.value)
        self.assertFalse(is_pipeline_complete(self.runtime_file))

    def test_is_pipeline_complete_with_failures(self):
        """Test that pipeline with failures is not complete."""
        self._create_runtime(
            {
                "job1": {"status": JobStatus.COMPLETED.value},
                "job2": {"status": JobStatus.FAILED.value},
            }
        )

        self.assertFalse(is_pipeline_complete(self.runtime_file))

    def test_is_pipeline_complete_nonexistent_file(self):
        """Test pipeline complete check with non-existent file."""
        result = is_pipeline_complete("/nonexistent/file.yaml")
        self.assertFalse(result)


class TestSnippetRuntime(unittest.TestCase):
    """Test SnippetRuntime helper class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.runtime_file = os.path.join(self.test_dir, "pipeline_runtime.yaml")

        # Create a mock log object
        class MockLog:
            def __init__(self, path):
                self.__path__ = path

        self.log = MockLog(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_snippet_runtime_creation(self):
        """Test creating a SnippetRuntime."""
        runtime = SnippetRuntime("test_command", self.log, "test_profile")

        self.assertIsNotNone(runtime.command)
        self.assertIn("test_command", runtime.command)
        self.assertIsNotNone(runtime.run_id)
        # runtime_dir is the parent of log.__path__ (one level up)
        self.assertIsNotNone(runtime.runtime_dir)
        # runtime_file should be in the runtime_dir
        self.assertEqual(os.path.dirname(runtime.runtime_file), runtime.runtime_dir)
        self.assertTrue(runtime.runtime_file.endswith("pipeline_runtime.yaml"))

    def test_get_runtime(self):
        """Test initializing runtime."""
        runtime = SnippetRuntime("echo test", self.log, "test_profile")
        runtime.get_runtime(requirements={"ncpu": 4, "mem": "8gb"}, dependencies=[])
        runtime.commit_runtime()

        # Check YAML file was created
        self.assertTrue(os.path.exists(runtime.runtime_file))

        # Check runtime was stored correctly
        with open(runtime.runtime_file, "rt") as f:
            data = yaml.safe_load(f)

        self.assertIn(runtime.run_id, data)
        self.assertEqual(data[runtime.run_id]["requirements"]["ncpu"], 4)
        self.assertEqual(data[runtime.run_id]["status"], JobStatus.PENDING.value)

    def test_should_skip_completed_job(self):
        """Test should_skip for already completed job."""
        runtime = SnippetRuntime("echo test", self.log, "test_profile")
        runtime.get_runtime(requirements={}, dependencies=[])

        # Mark as completed
        runtime.runtime[runtime.run_id]["status"] = JobStatus.COMPLETED.value

        should_skip, reason = runtime.should_skip()
        self.assertTrue(should_skip)
        self.assertIn("completed", reason.lower())

    def test_should_skip_pending_job(self):
        """Test should_skip for pending job."""
        runtime = SnippetRuntime("echo test", self.log, "test_profile")
        runtime.get_runtime(requirements={}, dependencies=[])

        should_skip, reason = runtime.should_skip()
        self.assertFalse(should_skip)

    def test_mark_submitted(self):
        """Test marking job as submitted."""
        runtime = SnippetRuntime("echo test", self.log, "test_profile")
        runtime.get_runtime(requirements={}, dependencies=[])

        runtime.mark_submitted("queue_12345")

        self.assertEqual(runtime.runtime[runtime.run_id]["queue_id"], "queue_12345")
        self.assertEqual(
            runtime.runtime[runtime.run_id]["status"], JobStatus.SUBMITTED.value
        )
        self.assertIsNotNone(runtime.runtime[runtime.run_id]["submitted_at"])

    def test_mark_completed(self):
        """Test marking job as completed."""
        runtime = SnippetRuntime("echo test", self.log, "test_profile")
        runtime.get_runtime(requirements={}, dependencies=[])

        runtime.mark_completed()

        self.assertEqual(
            runtime.runtime[runtime.run_id]["status"], JobStatus.COMPLETED.value
        )
        self.assertIsNotNone(runtime.runtime[runtime.run_id]["completed_at"])

    def test_mark_failed(self):
        """Test marking job as failed."""
        runtime = SnippetRuntime("echo test", self.log, "test_profile")
        runtime.get_runtime(requirements={}, dependencies=[])

        runtime.mark_failed("Test failure")

        self.assertEqual(
            runtime.runtime[runtime.run_id]["status"], JobStatus.FAILED.value
        )
        self.assertEqual(runtime.runtime[runtime.run_id]["error_msg"], "Test failure")
        self.assertIsNotNone(runtime.runtime[runtime.run_id]["completed_at"])

    def test_add_queue_id(self):
        """Test adding queue ID."""
        runtime = SnippetRuntime("echo test", self.log, "test_profile")
        runtime.get_runtime(requirements={}, dependencies=[])

        runtime.add_queue_id("slurm_12345")

        self.assertEqual(runtime.runtime[runtime.run_id]["queue_id"], "slurm_12345")

    def test_resume_with_existing_completed_job(self):
        """Test resume logic skips already completed jobs."""
        # Create first runtime
        runtime1 = SnippetRuntime("echo test", self.log, "test_profile")
        # Manually set run_id to simulate resume
        runtime1.run_id = "custom_id"
        runtime1.get_runtime(requirements={}, dependencies=[])
        runtime1.runtime[runtime1.run_id]["status"] = JobStatus.COMPLETED.value
        runtime1.commit_runtime()

        # Create second runtime with same run_id (simulate resume)
        runtime2 = SnippetRuntime("echo test", self.log, "test_profile")
        runtime2.run_id = "custom_id"
        runtime2.get_runtime(requirements={}, dependencies=[])

        # Should not reinitialize since job is completed
        self.assertEqual(
            runtime2.runtime[runtime2.run_id]["status"], JobStatus.COMPLETED.value
        )


if __name__ == "__main__":
    unittest.main()
