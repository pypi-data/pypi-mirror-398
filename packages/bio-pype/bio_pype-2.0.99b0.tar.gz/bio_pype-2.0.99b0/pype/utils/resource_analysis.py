"""Resource usage analysis for pipeline jobs.

Provides queue-agnostic abstraction for analyzing actual vs. requested
resource usage after jobs complete. Each queue system implements its own
analyzer with system-specific resource query methods.
"""

import json
import os
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml

from pype.utils.queues import _read_runtime_file_locked


class ResourceAnalyzer(ABC):
    """Abstract base class for queue-specific resource analysis.

    Each queue module (SLURM, PBS, SGE) implements its own analyzer
    to query actual resource usage from the queue system.
    """

    @abstractmethod
    def query_job_resources(self, queue_id: str) -> Optional[Dict[str, Any]]:
        """Query actual resource usage for a completed job.

        Args:
            queue_id: Queue system job ID (e.g., SLURM job ID)

        Returns:
            Dict with actual usage metrics:
            {
                'status': 'COMPLETED',
                'mem_used_gb': 1.0,
                'cpu_used': 0.5,
                'time_elapsed': '00:10:30',
                'mem_efficiency': 50.0,  # percentage
                'cpu_efficiency': 25.0,  # percentage
            }
            or None if job not found or error querying
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement query_job_resources()"
        )

    def analyze_and_save(
        self,
        runtime_file: str,
        output_file: str,
    ) -> None:
        """Analyze resource usage and save report to file.

        Loads completed jobs from runtime.yaml, queries actual usage,
        calculates efficiency metrics, and saves report.

        Args:
            runtime_file: Path to pipeline_runtime.yaml
            output_file: Path to save analysis report (YAML or JSON)
        """
        runtime = _read_runtime_file_locked(runtime_file)

        if not runtime:
            return

        # Collect analysis by batch and individual jobs
        analysis = {
            "generated_at": datetime.now().isoformat(),
            "total_jobs": len(runtime),
            "jobs": {},
            "by_batch": defaultdict(
                lambda: {
                    "jobs": [],
                    "metrics": {
                        "avg_mem_efficiency": 0.0,
                        "avg_cpu_efficiency": 0.0,
                        "avg_time_efficiency": 0.0,
                        "count": 0,
                    },
                }
            ),
            "summary": {
                "completed": 0,
                "failed_or_timeout": 0,
                "pending": 0,
            },
        }

        # Analyze each job
        for run_id, job_data in runtime.items():
            status = job_data.get("status", "pending")
            queue_id = job_data.get("queue_id")
            batch_id = job_data.get("batch_id", "no_batch")

            # Skip non-completed jobs
            if status != "completed":
                analysis["summary"][
                    status if status in analysis["summary"] else "pending"
                ] += 1
                continue

            # Query actual usage
            if not queue_id:
                continue

            actual = self.query_job_resources(queue_id)
            if not actual:
                continue

            # Get requested resources
            requirements = job_data.get("requirements", {})

            # Build job analysis entry
            job_analysis = {
                "run_id": run_id,
                "name": job_data.get("name", run_id),
                "batch_id": batch_id,
                "queue_id": queue_id,
                "status": actual.get("status", "UNKNOWN"),
                "requested": {
                    "mem_gb": float(requirements.get("mem", "0").replace("gb", ""))
                    if isinstance(requirements.get("mem"), str)
                    else requirements.get("mem", 0),
                    "ncpu": int(requirements.get("ncpu", 0)),
                    "time": requirements.get("time", "00:00:00"),
                },
                "actual": {
                    "mem_gb": actual.get("mem_used_gb", 0.0),
                    "cpu": actual.get("cpu_used", 0.0),
                    "time_elapsed": actual.get("time_elapsed", ""),
                },
                "efficiency": {
                    "mem_percent": actual.get("mem_efficiency", 0.0),
                    "cpu_percent": actual.get("cpu_efficiency", 0.0),
                    "notes": actual.get("notes", ""),
                },
            }

            analysis["jobs"][run_id] = job_analysis
            analysis["by_batch"][batch_id]["jobs"].append(run_id)
            analysis["summary"]["completed"] += 1

        # Calculate batch statistics
        for batch_id, batch_data in analysis["by_batch"].items():
            jobs = batch_data["jobs"]
            if not jobs:
                continue

            mem_effs = []
            cpu_effs = []

            for run_id in jobs:
                job = analysis["jobs"][run_id]
                mem_effs.append(job["efficiency"]["mem_percent"])
                cpu_effs.append(job["efficiency"]["cpu_percent"])

            if mem_effs:
                batch_data["metrics"]["avg_mem_efficiency"] = sum(mem_effs) / len(
                    mem_effs
                )
            if cpu_effs:
                batch_data["metrics"]["avg_cpu_efficiency"] = sum(cpu_effs) / len(
                    cpu_effs
                )
            batch_data["metrics"]["count"] = len(jobs)

        # Convert defaultdict for serialization
        analysis["by_batch"] = dict(analysis["by_batch"])

        # Save report
        self._save_report(analysis, output_file)

    def _save_report(self, analysis: Dict[str, Any], output_file: str) -> None:
        """Save analysis report to YAML or JSON.

        Args:
            analysis: Analysis data dictionary
            output_file: Output file path (extension determines format)
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

        if output_file.endswith(".json"):
            with open(output_file, "w") as f:
                json.dump(analysis, f, indent=2, default=str)
        else:
            # Default to YAML
            with open(output_file, "w") as f:
                yaml.dump(analysis, f, default_flow_style=False, sort_keys=False)
