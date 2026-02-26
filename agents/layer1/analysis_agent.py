"""ContractIQ Analysis Agent - Layer 1

Coverage analysis and AI-powered insights from test execution results.
"""

from typing import Dict, List, Any, Optional
import json


class AnalysisAgent:
    """
    Layer 1 Orchestrator: Analysis Agent
    
    Responsibilities:
    - Calculate test coverage metrics
    - Identify trends and patterns in test results
    - Generate AI-powered insights and recommendations
    - Track flaky tests and failure rates
    - Provide actionable test quality metrics
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.analysis_history = []
        
    def analyze_results(self, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze test execution results and generate insights.
        
        Args:
            execution_results: Results from ExecutionAgent
            
        Returns:
            Analysis report with metrics and insights
        """
        results = execution_results.get('results', [])
        stats = execution_results.get('statistics', {})
        
        coverage_analysis = self._analyze_coverage(results)
        failure_analysis = self._analyze_failures(results)
        performance_analysis = self._analyze_performance(results)
        insights = self._generate_insights(stats, results)
        
        return {
            'coverage': coverage_analysis,
            'failures': failure_analysis,
            'performance': performance_analysis,
            'insights': insights,
            'overall_score': self._calculate_quality_score(stats)
        }
    
    def _analyze_coverage(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze test coverage."""
        total_tests = len(results)
        api_tests = sum(1 for r in results if r.get('type') == 'api')
        ui_tests = sum(1 for r in results if r.get('type') == 'ui')
        
        return {
            'total_tests': total_tests,
            'api_tests': api_tests,
            'ui_tests': ui_tests,
            'api_coverage_percentage': round((api_tests / total_tests * 100), 2) if total_tests > 0 else 0,
            'ui_coverage_percentage': round((ui_tests / total_tests * 100), 2) if total_tests > 0 else 0
        }
    
    def _analyze_failures(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze test failures."""
        failed_tests = [r for r in results if r.get('status') == 'failed']
        
        failure_reasons = {}
        for test in failed_tests:
            error = test.get('error', 'unknown')
            failure_reasons[error] = failure_reasons.get(error, 0) + 1
        
        return {
            'total_failures': len(failed_tests),
            'failure_reasons': failure_reasons,
            'most_common_failure': max(failure_reasons.items(), key=lambda x: x[1])[0] if failure_reasons else None
        }
    
    def _analyze_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze test performance."""
        durations = [r.get('duration_ms', 0) for r in results]
        
        if not durations:
            return {'avg_duration_ms': 0, 'max_duration_ms': 0, 'min_duration_ms': 0}
        
        return {
            'avg_duration_ms': round(sum(durations) / len(durations), 2),
            'max_duration_ms': max(durations),
            'min_duration_ms': min(durations),
            'total_execution_time_ms': sum(durations)
        }
    
    def _generate_insights(self, stats: Dict[str, Any], results: List[Dict[str, Any]]) -> List[str]:
        """Generate AI-powered insights."""
        insights = []
        
        total = stats.get('total', 0)
        passed = stats.get('passed', 0)
        failed = stats.get('failed', 0)
        
        if total == 0:
            return ['No tests executed']
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        if pass_rate >= 95:
            insights.append('Excellent test pass rate - Test suite is stable')
        elif pass_rate >= 80:
            insights.append('Good test pass rate - Minor issues to address')
        else:
            insights.append('Low test pass rate - Significant issues detected')
        
        if failed > 0:
            insights.append(f'{failed} tests failing - Review and fix required')
        
        # Check for slow tests
        slow_tests = [r for r in results if r.get('duration_ms', 0) > 5000]
        if slow_tests:
            insights.append(f'{len(slow_tests)} slow tests detected (>5s) - Consider optimization')
        
        return insights
    
    def _calculate_quality_score(self, stats: Dict[str, Any]) -> float:
        """Calculate overall test quality score (0-100)."""
        total = stats.get('total', 0)
        passed = stats.get('passed', 0)
        
        if total == 0:
            return 0.0
        
        pass_rate = (passed / total * 100)
        return round(pass_rate, 2)
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get analysis summary."""
        return {
            'total_analyses': len(self.analysis_history),
            'agent_type': 'AnalysisAgent',
            'layer': 1
        }


if __name__ == '__main__':
    # Example usage
    agent = AnalysisAgent()
    
    # Example execution results
    execution_results = {
        'results': [
            {'test_id': 'test_001', 'type': 'api', 'status': 'passed', 'duration_ms': 150},
            {'test_id': 'test_002', 'type': 'ui', 'status': 'failed', 'duration_ms': 2000, 'error': 'Selector not found'},
            {'test_id': 'test_003', 'type': 'api', 'status': 'passed', 'duration_ms': 100}
        ],
        'statistics': {
            'total': 3,
            'passed': 2,
            'failed': 1,
            'skipped': 0,
            'errors': 0
        }
    }
    
    # Analyze results
    analysis = agent.analyze_results(execution_results)
    print(json.dumps(analysis, indent=2))
