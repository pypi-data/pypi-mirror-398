"""Example usage of why-slow."""

from pyperf_why import explain


# Example 1: Dynamic List Growth
@explain
def bad_list_building():
    """Inefficient: appending to list in loop."""
    result = []
    for i in range(1000):
        result.append(i * 2)
    return result


# Example 2: Nested Loops
@explain
def nested_loop_example():
    """O(n²) complexity."""
    matrix = []
    for i in range(100):
        row = []
        for j in range(100):
            row.append(i * j)
        matrix.append(row)
    return matrix


# Example 3: Function Calls in Loop
def expensive_operation(x):
    """Some computation."""
    return x ** 2 + x ** 0.5


@explain
def calls_in_loop():
    """Repeated function call overhead."""
    result = []
    for i in range(500):
        result.append(expensive_operation(i))
    return result


# Example 4: Clean Code (No Issues)
@explain
def clean_list_building():
    """Efficient: list comprehension."""
    return [i * 2 for i in range(1000)]


# Example 5: Multiple Issues
@explain
def multiple_problems():
    """This has several performance issues."""
    result = []
    for i in range(100):
        for j in range(100):
            result.append(expensive_operation(i + j))
    return result


if __name__ == "__main__":
    print("=" * 80)
    print("Example 1: Dynamic List Growth")
    print("=" * 80)
    bad_list_building()

    print("\n" + "=" * 80)
    print("Example 2: Nested Loops")
    print("=" * 80)
    nested_loop_example()

    print("\n" + "=" * 80)
    print("Example 3: Function Calls in Loop")
    print("=" * 80)
    calls_in_loop()

    print("\n" + "=" * 80)
    print("Example 4: Clean Code (Should have no/minimal issues)")
    print("=" * 80)
    clean_list_building()

    print("\n" + "=" * 80)
    print("Example 5: Multiple Problems")
    print("=" * 80)
    multiple_problems()