"""ContractIQ Documentation Agent - Layer 1

Auto-generates living documentation and coverage reports.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class DocumentationAgent:
    """
    Layer 1 Orchestrator: Documentation Agent
    
    Responsibilities:
    - Generate living test documentation
    - Create coverage reports
    - Update API documentation from test results
    - Generate test execution reports
    - Maintain always up-to-date documentation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.docs_generated = []
        
    def generate_documentation(self, test_results: Dict[str, Any], 
                              analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive documentation from test results.
        
        Args:
            test_results: Test execution results
            analysis: Analysis from AnalysisAgent
            
        Returns:
            Generated documentation with multiple formats
        """
        markdown_doc = self._generate_markdown(test_results, analysis)
        html_doc = self._generate_html_report(test_results, analysis)
        coverage_report = self._generate_coverage_report(analysis)
        
        doc_package = {
            'markdown': markdown_doc,
            'html': html_doc,
            'coverage_report': coverage_report,
            'timestamp': datetime.now().isoformat(),
            'agent_type': 'DocumentationAgent',
            'layer': 1
        }
        
        self.docs_generated.append(doc_package)
        return doc_package
    
    def _generate_markdown(self, results: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """
        Generate Markdown documentation.
        """
        stats = results.get('statistics', {})
        insights = analysis.get('insights', [])
        
        markdown = f"""# Test Execution Report

## Summary
- **Total Tests**: {stats.get('total', 0)}
- **Passed**: {stats.get('passed', 0)}
- **Failed**: {stats.get('failed', 0)}
- **Skipped**: {stats.get('skipped', 0)}
- **Overall Score**: {analysis.get('overall_score', 0)}%

## Insights
"""        
        for insight in insights:
            markdown += f"- {insight}\n"
        
        markdown += f"\n## Coverage\n"
        coverage = analysis.get('coverage', {})
        markdown += f"- API Tests: {coverage.get('api_tests', 0)} ({coverage.get('api_coverage_percentage', 0)}%)\n"
        markdown += f"- UI Tests: {coverage.get('ui_tests', 0)} ({coverage.get('ui_coverage_percentage', 0)}%)\n"
        
        return markdown
    
    def _generate_html_report(self, results: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """
        Generate HTML report.
        """
        stats = results.get('statistics', {})
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>SPECTRA Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
    </style>
</head>
<body>
    <h1>SPECTRA Test Execution Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Total: {stats.get('total', 0)}</p>
        <p class="passed">Passed: {stats.get('passed', 0)}</p>
        <p class="failed">Failed: {stats.get('failed', 0)}</p>
        <p>Score: {analysis.get('overall_score', 0)}%</p>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_coverage_report(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate detailed coverage report.
        """
        coverage = analysis.get('coverage', {})
        performance = analysis.get('performance', {})
        
        return {
            'test_coverage': coverage,
            'performance_metrics': performance,
            'generated_at': datetime.now().isoformat()
        }
    
    def get_documentation_stats(self) -> Dict[str, Any]:
        """Get documentation generation statistics."""
        return {
            'total_docs_generated': len(self.docs_generated),
            'agent_type': 'DocumentationAgent',
            'layer': 1
        }


if __name__ == '__main__':
    agent = DocumentationAgent()
    
    test_results = {
        'statistics': {'total': 10, 'passed': 8, 'failed': 2, 'skipped': 0}
    }
    
    analysis = {
        'overall_score': 80.0,
        'insights': ['Good test pass rate'],
        'coverage': {'api_tests': 6, 'ui_tests': 4, 'api_coverage_percentage': 60, 'ui_coverage_percentage': 40}
    }
    
    docs = agent.generate_documentation(test_results, analysis)
    print(docs['markdown'])
