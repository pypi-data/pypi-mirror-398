"""Runtime sampling for function execution."""

import time
from typing import Callable, Optional

from ._pyperf_why_core import RuntimeStats


class IterationCounter:
    """Simple iteration counter using sys.settrace."""

    def __init__(self):
        self.iterations = 0
        self.in_loop = False

    def count(self, frame, event, arg):
        # Simple heuristic: count backward jumps
        if event == 'line':
            # This is a simplified approach
            # In reality, detecting loop iterations from trace is complex
            pass
        return self.count


def sample_runtime(func: Callable) -> Optional[RuntimeStats]:
    """
    Execute function once to gather runtime statistics.

    Only works for functions with no required arguments.
    """
    import inspect

    # Check if function can be called without arguments
    sig = inspect.signature(func)
    params = [p for p in sig.parameters.values() if p.default == inspect.Parameter.empty]

    if params:
        # Can't call without arguments
        return None

    try:
        start = time.perf_counter()
        func()
        end = time.perf_counter()

        execution_time_ms = (end - start) * 1000

        # Iteration counting is complex, skip for v0.1
        # Would need proper tracing or instrumentation
        # Note: RuntimeStats constructor changed - execution_time_ms is now first
        return RuntimeStats(
            execution_time_ms=execution_time_ms,
            total_iterations=None
        )
    except Exception:
        return None
