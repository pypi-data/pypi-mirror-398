"""Sample data factories for testing HTML export functionality."""

from typing import List, Tuple

from django_mercury.monitor import MonitorResult
from django_mercury.n_plus_one import N1Pattern


def create_sample_monitor_result(
    test_name: str = "test_api_endpoint",
    test_location: str = "tests/test_api.py::TestAPI::test_api_endpoint",
    response_time_ms: float = 125.5,
    query_count: int = 5,
    with_n1: bool = False,
    with_failures: bool = False,
    with_warnings: bool = False,
) -> MonitorResult:
    """Create a sample MonitorResult for testing.

    Args:
        test_name: Name of the test
        test_location: File location of the test
        response_time_ms: Response time in milliseconds
        query_count: Number of queries
        with_n1: Include N+1 patterns
        with_failures: Include failures
        with_warnings: Include warnings

    Returns:
        MonitorResult instance
    """
    result = MonitorResult(
        test_name=test_name,
        test_location=test_location,
        response_time_ms=response_time_ms,
        query_count=query_count,
        queries=[
            "SELECT * FROM users WHERE id = 1",
            "SELECT * FROM posts WHERE user_id = 1",
            "SELECT * FROM comments WHERE post_id = 1",
            "SELECT * FROM likes WHERE post_id = 1",
            "SELECT * FROM tags WHERE post_id = 1",
        ][:query_count],
        thresholds={
            "response_time_ms": 100,
            "query_count": 10,
            "n_plus_one_threshold": 3,
        },
        n_plus_one_patterns=[],
        failures=[],
        warnings=[],
        used_defaults=False,
    )

    if with_n1:
        result.n_plus_one_patterns = [
            create_n1_pattern(
                normalized_query="SELECT * FROM posts WHERE user_id = ?",
                count=5,
                sample_queries=[
                    "SELECT * FROM posts WHERE user_id = 1",
                    "SELECT * FROM posts WHERE user_id = 2",
                    "SELECT * FROM posts WHERE user_id = 3",
                ],
            ),
            create_n1_pattern(
                normalized_query="SELECT * FROM comments WHERE post_id = ?",
                count=10,
                sample_queries=[
                    "SELECT * FROM comments WHERE post_id = 1",
                    "SELECT * FROM comments WHERE post_id = 2",
                ],
            ),
        ]

    if with_failures:
        result.failures = [
            f"Response time {response_time_ms}ms exceeds threshold 100ms",
            "N+1 pattern detected: 5 similar queries",
        ]

    if with_warnings:
        result.warnings = [
            "Query count approaching threshold (8/10)",
            "Potential N+1 pattern detected",
        ]

    return result


def create_n1_pattern(
    normalized_query: str = "SELECT * FROM table WHERE id = ?",
    count: int = 5,
    sample_queries: List[str] = None,
) -> N1Pattern:
    """Create a sample N+1 pattern.

    Args:
        normalized_query: Normalized SQL query
        count: Number of occurrences
        sample_queries: Sample queries

    Returns:
        N1Pattern instance
    """
    if sample_queries is None:
        sample_queries = [
            "SELECT * FROM table WHERE id = 1",
            "SELECT * FROM table WHERE id = 2",
            "SELECT * FROM table WHERE id = 3",
        ]

    return N1Pattern(
        normalized_query=normalized_query, count=count, sample_queries=sample_queries
    )


def create_sample_results_list(
    num_tests: int = 10, pass_rate: float = 0.7, with_n1_rate: float = 0.3
) -> List[Tuple[str, MonitorResult]]:
    """Create a list of sample test results for summary export.

    Args:
        num_tests: Number of test results to create
        pass_rate: Percentage of tests that should pass (0.0 to 1.0)
        with_n1_rate: Percentage of tests that have N+1 patterns

    Returns:
        List of (test_name, MonitorResult) tuples
    """
    results = []

    for i in range(num_tests):
        test_name = f"tests.test_api.TestAPI.test_endpoint_{i+1}"
        should_pass = i < int(num_tests * pass_rate)
        has_n1 = i < int(num_tests * with_n1_rate)

        # Vary response times and query counts
        response_time = 50 + (i * 25)  # 50, 75, 100, 125, ...
        query_count = 2 + (i * 2)  # 2, 4, 6, 8, ...

        result = create_sample_monitor_result(
            test_name=test_name,
            test_location=f"tests/test_api.py::TestAPI::test_endpoint_{i+1}",
            response_time_ms=response_time,
            query_count=min(query_count, 20),  # Cap at 20
            with_n1=has_n1,
            with_failures=not should_pass,
            with_warnings=False,
        )

        results.append((test_name, result))

    return results


def create_failure_result() -> MonitorResult:
    """Create a MonitorResult that fails all checks.

    Returns:
        MonitorResult instance with multiple failures
    """
    return create_sample_monitor_result(
        test_name="test_slow_endpoint_with_n1",
        test_location="tests/test_api.py::TestAPI::test_slow_endpoint_with_n1",
        response_time_ms=500.0,
        query_count=25,
        with_n1=True,
        with_failures=True,
        with_warnings=True,
    )


def create_perfect_result() -> MonitorResult:
    """Create a MonitorResult that passes all checks.

    Returns:
        MonitorResult instance with no issues
    """
    return create_sample_monitor_result(
        test_name="test_fast_endpoint",
        test_location="tests/test_api.py::TestAPI::test_fast_endpoint",
        response_time_ms=25.0,
        query_count=2,
        with_n1=False,
        with_failures=False,
        with_warnings=False,
    )


def create_xss_test_result() -> MonitorResult:
    """Create a MonitorResult with special HTML characters to test escaping.

    Returns:
        MonitorResult with HTML special characters
    """
    return MonitorResult(
        test_name="test_endpoint_<script>alert('xss')</script>",
        test_location="tests/test_api.py::TestAPI::test_xss_\"quotes\"_&_ampersands",
        response_time_ms=50.0,
        query_count=3,
        queries=[
            "SELECT * FROM users WHERE name = '<script>alert(1)</script>'",
            "SELECT * FROM posts WHERE title = '\"Quoted\" & Special'",
            "SELECT * FROM comments WHERE text = 'Test & <test>'",
        ],
        thresholds={
            "response_time_ms": 100,
            "query_count": 10,
            "n_plus_one_threshold": 3,
        },
        n_plus_one_patterns=[],
        failures=["Test failure with <html> & \"quotes\""],
        warnings=["Warning with <tags> & 'apostrophes'"],
        used_defaults=False,
    )
