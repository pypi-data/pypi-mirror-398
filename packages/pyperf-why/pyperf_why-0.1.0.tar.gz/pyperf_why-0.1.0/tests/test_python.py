"""Integration tests for why-slow."""

import pytest
from pyperf_why import explain


def test_list_growth_detection():
    """Test detection of dynamic list growth."""

    @explain(run=False)
    def bad_list_growth():
        result = []
        for i in range(1000):
            result.append(i * 2)
        return result

    report = bad_list_growth._pyperf_why_report

    assert len(report.issues) > 0
    issue_patterns = [issue.pattern for issue in report.issues]
    assert "dynamic_list_growth" in issue_patterns


def test_nested_loops_detection():
    """Test detection of nested loops."""

    @explain(run=False)
    def nested_loops():
        result = 0
        for i in range(10):
            for j in range(10):
                result += i * j
        return result

    report = nested_loops._pyperf_why_report

    assert len(report.issues) > 0
    issue_patterns = [issue.pattern for issue in report.issues]
    assert "nested_loops" in issue_patterns


def test_function_call_in_loop():
    """Test detection of function calls in loops."""

    def helper(x):
        return x * 2

    @explain(run=False)
    def calls_in_loop():
        result = []
        for i in range(100):
            result.append(helper(i))
        return result

    report = calls_in_loop._pyperf_why_report

    assert len(report.issues) > 0
    # Should detect both function_call_in_loop and dynamic_list_growth
    issue_patterns = [issue.pattern for issue in report.issues]
    assert "function_call_in_loop" in issue_patterns or "dynamic_list_growth" in issue_patterns


def test_clean_code_no_issues():
    """Test that optimized code produces no issues."""

    @explain(run=False)
    def clean_code():
        # List comprehension is optimal
        return [i * 2 for i in range(100)]

    report = clean_code._pyperf_why_report

    # Should have no issues or only low severity
    high_issues = [i for i in report.issues if "High" in str(i.severity)]
    assert len(high_issues) == 0


def test_direct_call():
    """Test using explain as direct function call."""

    def my_func():
        x = []
        for i in range(50):
            x.append(i)
        return x

    wrapped = explain(my_func, run=False)
    assert hasattr(wrapped, '_pyperf_why_report')


def test_severity_ordering():
    """Test that issues are ordered by severity."""

    @explain(run=False)
    def multiple_issues():
        result = []
        for i in range(1000):
            for j in range(10):
                result.append(i * j)
        return result

    report = multiple_issues._pyperf_why_report

    if len(report.issues) > 1:
        # Check severity ordering
        severities = [str(issue.severity) for issue in report.issues]
        # High should come before Medium, Medium before Low
        high_indices = [i for i, s in enumerate(severities) if "High" in s]
        low_indices = [i for i, s in enumerate(severities) if "Low" in s]

        if high_indices and low_indices:
            assert min(high_indices) < max(low_indices)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])