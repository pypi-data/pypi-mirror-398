"""pyperf-why: Explain why Python code is slow, not just where."""

from functools import wraps
from typing import Callable, Optional

from .extractor import extract_patterns
from .formatter import format_report
from .runtime import sample_runtime

try:
    from ._pyperf_why_core import analyze
except ImportError:
    raise ImportError(
        "Could not import Rust extension. "
        "Please build the package with 'maturin develop' or install from PyPI."
    )


def explain(func: Optional[Callable] = None, *, run: bool = True) -> Callable:
    """
    Analyze a function to explain why it's slow.

    Can be used as a decorator or direct function call.

    Args:
        func: Function to analyze
        run: Whether to execute the function for runtime sampling

    Example:
        @explain
        def my_function():
            result = []
            for i in range(1000):
                result.append(i * 2)
            return result

        # Or direct call
        report = explain(my_function)
    """

    def decorator(f: Callable) -> Callable:
        # Extract patterns
        analysis_input = extract_patterns(f)

        # Sample runtime if requested
        if run:
            try:
                runtime_stats = sample_runtime(f)
                analysis_input.runtime_stats = runtime_stats
            except Exception:
                pass  # Continue without runtime stats

        # Analyze with Rust
        report = analyze(analysis_input)

        # Format and print
        formatted = format_report(report)
        print(formatted)

        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        # Attach report to wrapper
        wrapper._pyperf_why_report = report

        return wrapper

    if func is None:
        # Used as @explain() with parentheses
        return decorator
    else:
        # Used as @explain or explain(func)
        return decorator(func)


__version__ = "0.1.0"
__all__ = ["explain"]
