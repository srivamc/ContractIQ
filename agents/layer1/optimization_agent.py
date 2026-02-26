"""ContractIQ Optimization Agent - Layer 1

Intelligent test suite optimization for faster execution and better coverage.
"""

from typing import Dict, List, Any, Optional
import json


class OptimizationAgent:
    """
    Layer 1 Orchestrator: Optimization Agent
    
    Responsibilities:
    - Identify redundant tests
    - Optimize test execution order
    - Suggest test suite improvements
    - Reduce overall execution time
    - Improve test coverage efficiency
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.optimization_history = []
        
    def optimize_test_suite(self, test_results: Dict[str, Any], 
                           analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize test suite based on execution results and analysis.
        
        Args:
            test_results: Test execution results
            analysis: Analysis from AnalysisAgent
            
        Returns:
            Optimization recommendations
        """
        results = test_results.get('results', [])
        
        redundant_tests = self._identify_redundant_tests(results)
        slow_tests = self._identify_slow_tests(results)
        execution_order = self._optimize_execution_order(results)
        recommendations = self._generate_recommendations(redundant_tests, slow_tests)
        
        optimization_report = {
            'redundant_tests': redundant_tests,
            'slow_tests': slow_tests,
            'optimized_execution_order': execution_order,
            'recommendations': recommendations,
            'estimated_time_savings': self._calculate_time_savings(redundant_tests, slow_tests),
            'agent_type': 'OptimizationAgent',
            'layer': 1
        }
        
        self.optimization_history.append(optimization_report)
        return optimization_report
    
    def _identify_redundant_tests(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify potentially redundant tests.
        """
        redundant = []
        
        # Simple heuristic: tests with same endpoint and method
        endpoint_map = {}
        for result in results:
            if result.get('type') == 'api':
                endpoint = result.get('details', {}).get('endpoint', '')
                method = result.get('details', {}).get('method', '')
                key = f"{method}:{endpoint}"
                
                if key in endpoint_map:
                    redundant.append({
                        'test_id': result.get('test_id'),
                        'reason': f'Duplicate of {endpoint_map[key]}',
                        'endpoint': endpoint,
                        'method': method
                    })
                else:
                    endpoint_map[key] = result.get('test_id')
        
        return redundant
    
    def _identify_slow_tests(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify slow tests that need optimization.
        """
        slow_threshold_ms = 5000  # 5 seconds
        
        slow_tests = [
            {
                'test_id': r.get('test_id'),
                'test_name': r.get('test_name'),
                'duration_ms': r.get('duration_ms', 0),
                'type': r.get('type')
            }
            for r in results
            if r.get('duration_ms', 0) > slow_threshold_ms
        ]
        
        return sorted(slow_tests, key=lambda x: x['duration_ms'], reverse=True)
    
    def _optimize_execution_order(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Optimize test execution order for faster feedback.
        Strategy: Fast tests first, critical tests prioritized
        """
        # Sort by duration (fast tests first)
        sorted_tests = sorted(results, key=lambda x: x.get('duration_ms', 0))
        
        return [test.get('test_id') for test in sorted_tests]
    
    def _generate_recommendations(self, redundant: List[Dict[str, Any]], 
                                 slow: List[Dict[str, Any]]) -> List[str]:
        """
        Generate optimization recommendations.
        """
        recommendations = []
        
        if redundant:
            recommendations.append(
                f"Remove {len(redundant)} redundant tests to reduce execution time"
            )
        
        if slow:
            recommendations.append(
                f"Optimize {len(slow)} slow tests (>5s) to improve performance"
            )
        
        if not redundant and not slow:
            recommendations.append(
                "Test suite is well-optimized - no major improvements needed"
            )
        
        return recommendations
    
    def _calculate_time_savings(self, redundant: List[Dict[str, Any]], 
                               slow: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate potential time savings from optimizations.
        """
        # Assume removing redundant tests saves their full duration
        redundant_savings = len(redundant) * 1000  # Assume avg 1s per test
        
        # Assume optimizing slow tests reduces them by 50%
        slow_savings = sum(t.get('duration_ms', 0) for t in slow) * 0.5
        
        total_savings_ms = redundant_savings + slow_savings
        
        return {
            'total_savings_ms': round(total_savings_ms, 2),
            'total_savings_minutes': round(total_savings_ms / 60000, 2)
        }
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        return {
            'total_optimizations': len(self.optimization_history),
            'agent_type': 'OptimizationAgent',
            'layer': 1
        }


if __name__ == '__main__':
    agent = OptimizationAgent()
    
    test_results = {
        'results': [
            {'test_id': 'test_001', 'type': 'api', 'duration_ms': 150, 'details': {'endpoint': '/api/users', 'method': 'GET'}},
            {'test_id': 'test_002', 'type': 'api', 'duration_ms': 6000, 'details': {'endpoint': '/api/orders', 'method': 'GET'}},
            {'test_id': 'test_003', 'type': 'api', 'duration_ms': 200, 'details': {'endpoint': '/api/users', 'method': 'GET'}}
        ]
    }
    
    analysis = {'overall_score': 85.0}
    
    optimization = agent.optimize_test_suite(test_results, analysis)
    print(json.dumps(optimization, indent=2))
