"""
ContractIQ Test Reporter
Generates Allure and HTML test reports with coverage analytics.
"""
from __future__ import annotations
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger

from core.test_runner import ExecutionResult, TestCase, TestStatus
from core.healer import HealingResult

class ContractIQReporter:
    """Generate test reports in multiple formats."""

    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, result: ExecutionResult, healing_results: Optional[List[HealingResult]] = None) -> Dict[str, str]:
        """Generate all report formats."""
        logger.info(f"Generating reports for suite: {result.suite_name}")
        report_files = {
            "json": self._generate_json_report(result, healing_results),
            "html": self._generate_html_report(result, healing_results),
            "allure": self._generate_allure_report(result, healing_results),
            "summary": self._generate_summary_report(result, healing_results)
        }
        logger.success(f"Reports generated in {self.output_dir}")
        return report_files

    def _generate_json_report(self, result: ExecutionResult, healing_results: Optional[List[HealingResult]]) -> str:
        """Generate JSON report."""
        output = {
            "suite": {
                "id": result.suite_id,
                "name": result.suite_name,
                "timestamp": result.timestamp,
                "duration_ms": result.duration_ms
            },
            "summary": {
                "total": result.total,
                "passed": result.passed,
                "failed": result.failed,
                "skipped": result.skipped,
                "errors": result.errors,
                "coverage_percent": result.coverage_percent
            },
            "tests": [asdict(tc) for tc in result.test_results]
        }
        if healing_results:
            output["healing"] = {
                "total_healed": len(healing_results),
                "successful": sum(1 for hr in healing_results if hr.success),
                "details": [asdict(hr) for hr in healing_results]
            }
        
        filepath = self.output_dir / f"report_{result.timestamp}.json"
        filepath.write_text(json.dumps(output, indent=2))
        logger.debug(f"JSON report: {filepath}")
        return str(filepath)

    def _generate_html_report(self, result: ExecutionResult, healing_results: Optional[List[HealingResult]]) -> str:
        """Generate HTML report with visual styling."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>ContractIQ Test Report - {result.suite_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .card {{ background: white; padding: 20px; border-radius: 5px; flex: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .passed {{ color: #27ae60; font-weight: bold; }}
        .failed {{ color: #e74c3c; font-weight: bold; }}
        .skipped {{ color: #f39c12; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; background: white; margin-top: 20px; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }}
        th {{ background: #34495e; color: white; }}
        .progress {{ height: 20px; background: #ecf0f1; border-radius: 10px; overflow: hidden; }}
        .progress-bar {{ height: 100%; background: #27ae60; transition: width 0.3s; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 ContractIQ Test Report</h1>
        <p>{result.suite_name}</p>
        <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(result.timestamp)))}</p>
    </div>
    <div class="summary">
        <div class="card">
            <h3>Total Tests</h3>
            <h1>{result.total}</h1>
        </div>
        <div class="card">
            <h3>Passed</h3>
            <h1 class="passed">{result.passed}</h1>
        </div>
        <div class="card">
            <h3>Failed</h3>
            <h1 class="failed">{result.failed}</h1>
        </div>
        <div class="card">
            <h3>Coverage</h3>
            <h1>{result.coverage_percent:.1f}%</h1>
        </div>
    </div>
    <div class="card">
        <h3>Coverage Progress</h3>
        <div class="progress">
            <div class="progress-bar" style="width: {result.coverage_percent}%"></div>
        </div>
        <p>{result.passed} / {result.total} tests passing</p>
    </div>
    <table>
        <thead>
            <tr>
                <th>Test Name</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Error</th>
            </tr>
        </thead>
        <tbody>
"""
        for tc in result.test_results:
            status_class = tc.status.value
            error_text = tc.error[:100] if tc.error else "-"
            html += f"""            <tr>
                <td>{tc.name}</td>
                <td class="{status_class}">{tc.status.value.upper()}</td>
                <td>{tc.duration_ms:.0f}ms</td>
                <td>{error_text}</td>
            </tr>
"""
        
        html += """        </tbody>
    </table>
</body>
</html>"""
        
        filepath = self.output_dir / f"report_{result.timestamp}.html"
        filepath.write_text(html)
        logger.debug(f"HTML report: {filepath}")
        return str(filepath)

    def _generate_allure_report(self, result: ExecutionResult, healing_results: Optional[List[HealingResult]]) -> str:
        """Generate Allure-compatible JSON results."""
        allure_dir = self.output_dir / "allure-results"
        allure_dir.mkdir(exist_ok=True)
        
        for tc in result.test_results:
            allure_result = {
                "uuid": tc.id,
                "historyId": tc.id,
                "testCaseId": tc.id,
                "name": tc.name,
                "fullName": f"{result.suite_name}.{tc.name}",
                "description": tc.description,
                "status": self._map_status_to_allure(tc.status),
                "stage": "finished",
                "start": int(result.timestamp) * 1000,
                "stop": int(result.timestamp) * 1000 + int(tc.duration_ms),
                "labels": [
                    {"name": "suite", "value": result.suite_name},
                    {"name": "testType", "value": tc.mode.value}
                ] + [{"name": "tag", "value": tag} for tag in tc.tags]
            }
            if tc.error:
                allure_result["statusDetails"] = {
                    "message": tc.error,
                    "trace": tc.error
                }
            
            allure_file = allure_dir / f"{tc.id}-result.json"
            allure_file.write_text(json.dumps(allure_result, indent=2))
        
        logger.debug(f"Allure results: {allure_dir}")
        return str(allure_dir)

    def _generate_summary_report(self, result: ExecutionResult, healing_results: Optional[List[HealingResult]]) -> str:
        """Generate a concise summary report."""
        summary = f"""ContractIQ Test Execution Summary
{'=' * 60}
Suite: {result.suite_name}
Duration: {result.duration_ms / 1000:.2f}s
Results:
  Total: {result.total}
  Passed: {result.passed} ({result.passed / result.total * 100 if result.total > 0 else 0:.1f}%)
  Failed: {result.failed}
  Skipped: {result.skipped}
  Errors: {result.errors}
Coverage: {result.coverage_percent:.1f}%
"""
        if healing_results:
            healed = sum(1 for hr in healing_results if hr.success)
            summary += f"""
Self-Healing:
  Total healing attempts: {len(healing_results)}
  Successfully healed: {healed}
  Healing success rate: {healed / len(healing_results) * 100 if healing_results else 0:.1f}%
"""
        filepath = self.output_dir / f"summary_{result.timestamp}.txt"
        filepath.write_text(summary)
        logger.debug(f"Summary report: {filepath}")
        return str(filepath)

    def _map_status_to_allure(self, status: TestStatus) -> str:
        """Map ContractIQ status to Allure status."""
        mapping = {
            TestStatus.PASSED: "passed",
            TestStatus.FAILED: "failed",
            TestStatus.SKIPPED: "skipped",
            TestStatus.ERROR: "broken"
        }
        return mapping.get(status, "unknown")

    def generate_coverage_report(self, endpoint_coverage: Dict[str, bool]) -> str:
        """Generate endpoint coverage report."""
        total = len(endpoint_coverage)
        covered = sum(1 for v in endpoint_coverage.values() if v)
        coverage_percent = (covered / total * 100) if total > 0 else 0.0
        
        report = f"""Endpoint Coverage Report
{'=' * 60}
Total Endpoints: {total}
Covered: {covered}
Coverage: {coverage_percent:.1f}%

Endpoint Details:
"""
        for endpoint, covered in sorted(endpoint_coverage.items()):
            status = "✓" if covered else "✗"
            report += f"  [{status}] {endpoint}
"
            
        filepath = self.output_dir / "coverage.txt"
        filepath.write_text(report)
        return str(filepath)
