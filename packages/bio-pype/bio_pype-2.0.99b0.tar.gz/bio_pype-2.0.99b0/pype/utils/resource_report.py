"""HTML report generation for resource analysis data.

Generates interactive HTML reports with plots and visualizations
from resource_analysis.yaml/json files using Chart.js.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml


class ResourceReportGenerator:
    """Generate interactive HTML reports from resource analysis data."""

    def __init__(self):
        """Initialize report generator."""
        self.analysis = {}

    def load_analysis(self, analysis_file: str) -> bool:
        """Load resource analysis from YAML or JSON file.

        Args:
            analysis_file: Path to resource_analysis.yaml or .json

        Returns:
            True if loaded successfully, False otherwise
        """
        if not os.path.exists(analysis_file):
            return False

        try:
            if analysis_file.endswith(".json"):
                with open(analysis_file, "r") as f:
                    self.analysis = json.load(f)
            else:
                with open(analysis_file, "r") as f:
                    self.analysis = yaml.safe_load(f)
            return True
        except Exception as e:
            print(f"Error loading analysis file: {e}")
            return False

    def generate_report(self, output_file: str) -> None:
        """Generate HTML report with interactive plots.

        Args:
            output_file: Path to save HTML report
        """
        if not self.analysis:
            print("No analysis data loaded")
            return

        html = self._build_html()

        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        with open(output_file, "w") as f:
            f.write(html)

        print(f"Report generated: {output_file}")

    def _build_html(self) -> str:
        """Build complete HTML document with plots and styling."""
        jobs = self.analysis.get("jobs", {})
        by_batch = self.analysis.get("by_batch", {})
        summary = self.analysis.get("summary", {})
        generated_at = self.analysis.get("generated_at", "Unknown")

        # Prepare data for charts
        job_names = list(jobs.keys())
        mem_requested = [jobs[jid]["requested"]["mem_gb"] for jid in job_names]
        mem_used = [jobs[jid]["actual"]["mem_gb"] for jid in job_names]
        mem_efficiency = [jobs[jid]["efficiency"]["mem_percent"] for jid in job_names]
        cpu_efficiency = [jobs[jid]["efficiency"]["cpu_percent"] for jid in job_names]

        # Batch efficiency data
        batch_names = list(by_batch.keys())
        batch_mem_eff = [
            by_batch[bid]["metrics"]["avg_mem_efficiency"] for bid in batch_names
        ]
        batch_cpu_eff = [
            by_batch[bid]["metrics"]["avg_cpu_efficiency"] for bid in batch_names
        ]

        # Generate chart data as JSON
        mem_comparison_data = json.dumps(
            {
                "labels": job_names,
                "datasets": [
                    {
                        "label": "Requested (GB)",
                        "data": mem_requested,
                        "backgroundColor": "rgba(54, 162, 235, 0.6)",
                        "borderColor": "rgba(54, 162, 235, 1)",
                        "borderWidth": 1,
                    },
                    {
                        "label": "Used (GB)",
                        "data": mem_used,
                        "backgroundColor": "rgba(75, 192, 192, 0.6)",
                        "borderColor": "rgba(75, 192, 192, 1)",
                        "borderWidth": 1,
                    },
                ],
            }
        )

        mem_eff_data = json.dumps(
            {
                "labels": job_names,
                "datasets": [
                    {
                        "label": "Memory Efficiency (%)",
                        "data": mem_efficiency,
                        "backgroundColor": [
                            "rgba(255, 99, 132, 0.6)"
                            if e < 25
                            else "rgba(255, 193, 7, 0.6)"
                            if e < 50
                            else "rgba(76, 175, 80, 0.6)"
                            for e in mem_efficiency
                        ],
                        "borderColor": [
                            "rgba(255, 99, 132, 1)"
                            if e < 25
                            else "rgba(255, 193, 7, 1)"
                            if e < 50
                            else "rgba(76, 175, 80, 1)"
                            for e in mem_efficiency
                        ],
                        "borderWidth": 1,
                    },
                ],
            }
        )

        cpu_eff_data = json.dumps(
            {
                "labels": job_names,
                "datasets": [
                    {
                        "label": "CPU Efficiency (%)",
                        "data": cpu_efficiency,
                        "backgroundColor": [
                            "rgba(255, 99, 132, 0.6)"
                            if e < 25
                            else "rgba(255, 193, 7, 0.6)"
                            if e < 50
                            else "rgba(76, 175, 80, 0.6)"
                            for e in cpu_efficiency
                        ],
                        "borderColor": [
                            "rgba(255, 99, 132, 1)"
                            if e < 25
                            else "rgba(255, 193, 7, 1)"
                            if e < 50
                            else "rgba(76, 175, 80, 1)"
                            for e in cpu_efficiency
                        ],
                        "borderWidth": 1,
                    },
                ],
            }
        )

        batch_eff_data = json.dumps(
            {
                "labels": batch_names,
                "datasets": [
                    {
                        "label": "Memory Efficiency (%)",
                        "data": batch_mem_eff,
                        "backgroundColor": "rgba(54, 162, 235, 0.6)",
                        "borderColor": "rgba(54, 162, 235, 1)",
                        "borderWidth": 1,
                    },
                    {
                        "label": "CPU Efficiency (%)",
                        "data": batch_cpu_eff,
                        "backgroundColor": "rgba(75, 192, 192, 0.6)",
                        "borderColor": "rgba(75, 192, 192, 1)",
                        "borderWidth": 1,
                    },
                ],
            }
        )

        summary_data = json.dumps(
            {
                "labels": ["Completed", "Failed/Timeout", "Pending"],
                "datasets": [
                    {
                        "data": [
                            summary.get("completed", 0),
                            summary.get("failed_or_timeout", 0),
                            summary.get("pending", 0),
                        ],
                        "backgroundColor": [
                            "rgba(76, 175, 80, 0.6)",
                            "rgba(255, 99, 132, 0.6)",
                            "rgba(255, 193, 7, 0.6)",
                        ],
                        "borderColor": [
                            "rgba(76, 175, 80, 1)",
                            "rgba(255, 99, 132, 1)",
                            "rgba(255, 193, 7, 1)",
                        ],
                        "borderWidth": 1,
                    },
                ],
            }
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pipeline Resource Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 50px;
        }}

        .section h2 {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        .metrics-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}

        .metric-card .value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}

        .metric-card .label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}

        .chart-container {{
            position: relative;
            height: 400px;
            margin-bottom: 40px;
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #eee;
        }}

        .two-column {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }}

        @media (max-width: 1200px) {{
            .two-column {{
                grid-template-columns: 1fr;
            }}
        }}

        .table-container {{
            overflow-x: auto;
            background: #f9f9f9;
            border-radius: 8px;
            padding: 20px;
            border: 1px solid #eee;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}

        tr:hover {{
            background: #f0f0f0;
        }}

        .low-efficiency {{
            color: #d32f2f;
            font-weight: 600;
        }}

        .medium-efficiency {{
            color: #f57c00;
            font-weight: 600;
        }}

        .high-efficiency {{
            color: #388e3c;
            font-weight: 600;
        }}

        .footer {{
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Pipeline Resource Analysis Report</h1>
            <p>Generated: {generated_at}</p>
        </div>

        <div class="content">
            <!-- Summary Section -->
            <div class="section">
                <h2>Summary</h2>
                <div class="metrics-summary">
                    <div class="metric-card">
                        <div class="label">Total Jobs</div>
                        <div class="value">{self.analysis.get("total_jobs", 0)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Completed</div>
                        <div class="value">{summary.get("completed", 0)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Failed/Timeout</div>
                        <div class="value">{summary.get("failed_or_timeout", 0)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Pending</div>
                        <div class="value">{summary.get("pending", 0)}</div>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="summaryChart"></canvas>
                </div>
            </div>

            <!-- Memory Analysis -->
            <div class="section">
                <h2>Memory Analysis</h2>
                <div class="two-column">
                    <div class="chart-container">
                        <canvas id="memComparisonChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <canvas id="memEfficiencyChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- CPU Analysis -->
            <div class="section">
                <h2>CPU Analysis</h2>
                <div class="chart-container">
                    <canvas id="cpuEfficiencyChart"></canvas>
                </div>
            </div>

            <!-- Batch Analysis -->
            <div class="section">
                <h2>Batch Efficiency</h2>
                <div class="chart-container">
                    <canvas id="batchEfficiencyChart"></canvas>
                </div>
            </div>

            <!-- Detailed Job Table -->
            <div class="section">
                <h2>Detailed Job Analysis</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Job Name</th>
                                <th>Batch ID</th>
                                <th>Queue ID</th>
                                <th>Mem Requested (GB)</th>
                                <th>Mem Used (GB)</th>
                                <th>Mem Efficiency</th>
                                <th>CPU Efficiency</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._generate_table_rows(jobs)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Resource analysis report | Pipeline optimization insights</p>
        </div>
    </div>

    <script>
        // Chart.js configuration
        const chartOptions = {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    display: true,
                    position: 'top',
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                }}
            }}
        }};

        // Summary Chart
        const summaryCtx = document.getElementById('summaryChart').getContext('2d');
        new Chart(summaryCtx, {{
            type: 'doughnut',
            data: {summary_data},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                    }}
                }}
            }}
        }});

        // Memory Comparison Chart
        const memComparisonCtx = document.getElementById('memComparisonChart').getContext('2d');
        new Chart(memComparisonCtx, {{
            type: 'bar',
            data: {mem_comparison_data},
            options: chartOptions
        }});

        // Memory Efficiency Chart
        const memEfficiencyCtx = document.getElementById('memEfficiencyChart').getContext('2d');
        new Chart(memEfficiencyCtx, {{
            type: 'bar',
            data: {mem_eff_data},
            options: {{
                ...chartOptions,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                    }}
                }}
            }}
        }});

        // CPU Efficiency Chart
        const cpuEfficiencyCtx = document.getElementById('cpuEfficiencyChart').getContext('2d');
        new Chart(cpuEfficiencyCtx, {{
            type: 'bar',
            data: {cpu_eff_data},
            options: {{
                ...chartOptions,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                    }}
                }}
            }}
        }});

        // Batch Efficiency Chart
        const batchEfficiencyCtx = document.getElementById('batchEfficiencyChart').getContext('2d');
        new Chart(batchEfficiencyCtx, {{
            type: 'bar',
            data: {batch_eff_data},
            options: {{
                ...chartOptions,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        return html

    def _generate_table_rows(self, jobs: Dict[str, Any]) -> str:
        """Generate table rows for detailed job analysis.

        Args:
            jobs: Dictionary of job analyses

        Returns:
            HTML table rows
        """
        rows = []
        for run_id, job in jobs.items():
            name = job.get("name", run_id)
            batch_id = job.get("batch_id", "-")
            queue_id = job.get("queue_id", "-")
            mem_req = f"{job['requested']['mem_gb']:.2f}"
            mem_used = f"{job['actual']['mem_gb']:.2f}"
            mem_eff = job["efficiency"]["mem_percent"]
            cpu_eff = job["efficiency"]["cpu_percent"]

            mem_class = self._get_efficiency_class(mem_eff)
            cpu_class = self._get_efficiency_class(cpu_eff)

            rows.append(
                f"""
                        <tr>
                            <td><code>{name}</code></td>
                            <td><code>{batch_id}</code></td>
                            <td><code>{queue_id}</code></td>
                            <td>{mem_req}</td>
                            <td>{mem_used}</td>
                            <td class="{mem_class}">{mem_eff:.1f}%</td>
                            <td class="{cpu_class}">{cpu_eff:.1f}%</td>
                        </tr>
                """
            )
        return "".join(rows)

    @staticmethod
    def _get_efficiency_class(efficiency: float) -> str:
        """Get CSS class for efficiency level.

        Args:
            efficiency: Efficiency percentage

        Returns:
            CSS class name
        """
        if efficiency < 25:
            return "low-efficiency"
        elif efficiency < 50:
            return "medium-efficiency"
        else:
            return "high-efficiency"


def generate_html_report(analysis_file: str, output_file: Optional[str] = None) -> None:
    """Convenience function to generate HTML report from analysis file.

    Args:
        analysis_file: Path to resource_analysis.yaml or .json
        output_file: Path to save HTML report (defaults to .html version of input)
    """
    if output_file is None:
        base = os.path.splitext(analysis_file)[0]
        output_file = f"{base}.html"

    generator = ResourceReportGenerator()
    if generator.load_analysis(analysis_file):
        generator.generate_report(output_file)
    else:
        print(f"Failed to load analysis from {analysis_file}")
