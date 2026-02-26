"""SPECTRA Execution Agent - Layer 1

Orchestrates parallel test execution with 100+ concurrent threads.
Supports API and UI test execution with intelligent resource management.
"""

import asyncio
import concurrent.futures
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import time
import json


class ExecutionAgent:
    """
    Layer 1 Orchestrator: Execution Agent
    
    Responsibilities:
    - Parallel test execution with configurable thread pools
    - Support for both API and UI test types
    - Real-time execution monitoring and progress tracking
    - Resource management and load balancing
    - Test retry logic for flaky tests
    - Result aggregation and status tracking
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_workers = self.config.get('max_workers', 100)
        self.retry_count = self.config.get('retry_count', 2)
        self.timeout = self.config.get('timeout_seconds', 300)
        self.execution_results = []
        self.execution_stats = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0
        }
        
    def execute_tests(self, test_cases: List[Dict[str, Any]], 
                     mode: str = 'parallel') -> Dict[str, Any]:
        """
        Execute a list of test cases.
        
        Args:
            test_cases: List of test case definitions
            mode: 'parallel' or 'sequential'
            
        Returns:
            Execution results with statistics
        """
        self.execution_results = []
        self.execution_stats = {
            'total': len(test_cases),
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0
        }
        
        start_time = time.time()
        
        if mode == 'parallel':
            results = self._execute_parallel(test_cases)
        else:
            results = self._execute_sequential(test_cases)
            
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            'results': results,
            'statistics': self.execution_stats,
            'duration_seconds': round(duration, 2),
            'tests_per_second': round(len(test_cases) / duration, 2) if duration > 0 else 0
        }
    
    def _execute_parallel(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute test cases in parallel using thread pool.
        """
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._execute_single_test, test_case): test_case 
                for test_case in test_cases
            }
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=self.timeout)
                    results.append(result)
                    self._update_stats(result['status'])
                except concurrent.futures.TimeoutError:
                    test_case = futures[future]
                    result = self._create_timeout_result(test_case)
                    results.append(result)
                    self._update_stats('failed')
                except Exception as e:
                    test_case = futures[future]
                    result = self._create_error_result(test_case, str(e))
                    results.append(result)
                    self._update_stats('errors')
                    
        return results
    
    def _execute_sequential(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute test cases sequentially.
        """
        results = []
        
        for test_case in test_cases:
            try:
                result = self._execute_single_test(test_case)
                results.append(result)
                self._update_stats(result['status'])
            except Exception as e:
                result = self._create_error_result(test_case, str(e))
                results.append(result)
                self._update_stats('errors')
                
        return results
    
    def _execute_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single test case with retry logic.
        """
        test_type = test_case.get('type', 'api')
        retries_remaining = self.retry_count
        last_error = None
        
        while retries_remaining >= 0:
            try:
                start_time = time.time()
                
                if test_type == 'api':
                    result = self._execute_api_test(test_case)
                elif test_type == 'ui':
                    result = self._execute_ui_test(test_case)
                else:
                    raise ValueError(f"Unknown test type: {test_type}")
                
                end_time = time.time()
                
                return {
                    'test_id': test_case.get('id', 'unknown'),
                    'test_name': test_case.get('name', 'Unknown Test'),
                    'status': result.get('status', 'passed'),
                    'duration_ms': round((end_time - start_time) * 1000, 2),
                    'type': test_type,
                    'retry_count': self.retry_count - retries_remaining,
                    'timestamp': datetime.now().isoformat(),
                    'details': result.get('details', {})
                }
                
            except Exception as e:
                last_error = str(e)
                retries_remaining -= 1
                
                if retries_remaining < 0:
                    return self._create_failed_result(test_case, last_error)
                    
                time.sleep(1)  # Wait before retry
        
        return self._create_failed_result(test_case, last_error)
    
    def _execute_api_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an API test case.
        """
        # Placeholder for actual API test execution
        # In real implementation, this would make HTTP requests
        endpoint = test_case.get('endpoint', '/')
        method = test_case.get('method', 'GET')
        
        # Simulate test execution
        time.sleep(0.1)
        
        # For demonstration, randomly pass/fail based on test config
        expected_status = test_case.get('expected_status', 200)
        
        return {
            'status': 'passed',
            'details': {
                'endpoint': endpoint,
                'method': method,
                'expected_status': expected_status,
                'actual_status': 200
            }
        }
    
    def _execute_ui_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a UI test case.
        """
        # Placeholder for actual UI test execution
        # In real implementation, this would use Playwright
        url = test_case.get('url', 'https://example.com')
        actions = test_case.get('actions', [])
        
        # Simulate test execution
        time.sleep(0.2)
        
        return {
            'status': 'passed',
            'details': {
                'url': url,
                'actions_count': len(actions),
                'screenshots_captured': 0
            }
        }
    
    def _update_stats(self, status: str):
        """Update execution statistics."""
        status_map = {
            'passed': 'passed',
            'failed': 'failed',
            'skipped': 'skipped',
            'error': 'errors'
        }
        
        stat_key = status_map.get(status, 'errors')
        self.execution_stats[stat_key] += 1
    
    def _create_timeout_result(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Create result for timed out test."""
        return {
            'test_id': test_case.get('id', 'unknown'),
            'test_name': test_case.get('name', 'Unknown Test'),
            'status': 'failed',
            'duration_ms': self.timeout * 1000,
            'type': test_case.get('type', 'api'),
            'retry_count': 0,
            'timestamp': datetime.now().isoformat(),
            'error': f"Test execution timed out after {self.timeout} seconds"
        }
    
    def _create_error_result(self, test_case: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create result for test with error."""
        return {
            'test_id': test_case.get('id', 'unknown'),
            'test_name': test_case.get('name', 'Unknown Test'),
            'status': 'error',
            'duration_ms': 0,
            'type': test_case.get('type', 'api'),
            'retry_count': 0,
            'timestamp': datetime.now().isoformat(),
            'error': error
        }
    
    def _create_failed_result(self, test_case: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create result for failed test."""
        return {
            'test_id': test_case.get('id', 'unknown'),
            'test_name': test_case.get('name', 'Unknown Test'),
            'status': 'failed',
            'duration_ms': 0,
            'type': test_case.get('type', 'api'),
            'retry_count': self.retry_count,
            'timestamp': datetime.now().isoformat(),
            'error': error
        }
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of test execution."""
        total = self.execution_stats['total']
        passed = self.execution_stats['passed']
        
        return {
            'statistics': self.execution_stats,
            'pass_rate': round((passed / total * 100), 2) if total > 0 else 0,
            'agent_type': 'ExecutionAgent',
            'layer': 1
        }


if __name__ == '__main__':
    # Example usage
    agent = ExecutionAgent({'max_workers': 10})
    
    # Example test cases
    test_cases = [
        {
            'id': 'test_001',
            'name': 'Get User API Test',
            'type': 'api',
            'endpoint': '/api/users/1',
            'method': 'GET',
            'expected_status': 200
        },
        {
            'id': 'test_002',
            'name': 'Login Page UI Test',
            'type': 'ui',
            'url': 'https://example.com/login',
            'actions': ['click_login', 'enter_credentials']
        }
    ]
    
    # Execute tests
    results = agent.execute_tests(test_cases, mode='parallel')
    print(json.dumps(results, indent=2))
