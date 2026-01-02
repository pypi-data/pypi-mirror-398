# pyperf-why

> Explain why Python code is slow, not just where.

`pyperf-why` is a Rust-powered Python diagnostic tool that identifies performance anti-patterns in your code and explains what Python is doing internally that makes it slow.

Unlike traditional profilers that tell you *where* time is spent, `pyperf-why` tells you *why* it's slow and suggests concrete fixes.

## Installation

```bash
pip install pyperf-why
```

## Quick Start

```python
from pyperf_why import explain

@explain
def process_data():
    result = []
    for i in range(1000):
        result.append(i * 2)  # Dynamic list growth
    return result
```

Output:

```
Found 1 performance issue in 'process_data':
  • 1 high severity

🔴 Issue #1: dynamic_list_growth
   Location: line 5

   Why it's slow:
   Python reallocates list memory on each append() call (~1000 times).
   Each reallocation copies the entire list to a new memory location.
   This creates O(n²) memory operations.

   How to fix:
   Use list comprehension: [expr for i in range(n)]
   or pre-allocate: result = [None] * n, then assign values.
```

## What It Detects (v0.1)

1. **Dynamic List Growth** - `list.append()` in loops causing repeated reallocations
2. **Nested Loops** - O(n²) or worse complexity patterns
3. **Function Calls in Loops** - Overhead from repeated function invocation

## Features

- **Rust-powered analysis** - Fast pattern detection
- **Zero dependencies** - Just install and use
- **Human-readable output** - Clear explanations, not cryptic metrics
- **Actionable suggestions** - Concrete fixes, not vague advice

## Usage

### As a decorator

```python
@explain
def my_function():
    # your code here
    pass
```

### Direct call

```python
def my_function():
    # your code here
    pass

report = explain(my_function)
```

### Skip execution

```python
@explain(run=False)  # Don't execute, just analyze structure
def my_function():
    pass
```

## How It Works

1. **Python extracts** - AST, bytecode, and runtime patterns
2. **Rust analyzes** - Pattern matching and heuristic evaluation
3. **Report generated** - Human-readable explanations with fixes

## Philosophy

**Profilers tell you where. pyperf-why tells you why.**

This is a teaching tool as much as a diagnostic tool. It helps developers understand Python's performance characteristics.

## Non-Goals

- Not a profiler replacement (use `cProfile` for hotspot analysis)
- Not a benchmark tool (use `timeit` for precise timing)
- Not an automatic optimizer (suggestions require manual implementation)

## Development

```bash
# Clone the repo
git clone https://github.com/jagadhis/pyperf-why
cd pyperf-why

# Install Rust (if needed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install maturin
pip install maturin

# Build and install
maturin develop

# Run tests
cargo test  # Rust tests
pytest tests/  # Python tests
```

## Roadmap

### v0.1 (Current)
- ✅ List growth detection
- ✅ Nested loops detection
- ✅ Function calls in loops

### v0.2 (Planned)
- Generator vs list comprehension
- Dict/set operations
- String concatenation patterns
- Global variable access
- Import statements in loops

### v0.3 (Future)
- Interactive mode
- CI/CD integration
- VSCode extension

## Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## License

MIT

## Credits

Built with:
- [PyO3](https://github.com/PyO3/pyo3) - Rust ↔ Python bindings
- [maturin](https://github.com/PyO3/maturin) - Build and publish Rust-based Python packages