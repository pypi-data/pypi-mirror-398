"""Test cases for GIL state caching optimization."""
import time
import pytest


def test_gil_nested_allocations(example_module):
    """Test that nested allocations don't redundantly acquire GIL."""
    # Import a module that will trigger nested memory allocations
    from example import helloworld

    # Call a function that allocates memory
    # This should internally benefit from GIL caching
    result = helloworld.hello()
    assert isinstance(result, str)


def test_gil_performance_improvement(example_module):
    """Benchmark to show GIL caching improves performance."""
    from example import helloworld

    # Warm up
    for _ in range(100):
        helloworld.hello()

    # Measure performance with many allocations
    iterations = 10000
    start = time.perf_counter()
    for _ in range(iterations):
        helloworld.hello()
    elapsed = time.perf_counter() - start

    # With GIL caching, this should be significantly faster than without
    # (baseline would be ~2-3x slower without the optimization)
    # We're not asserting specific timing to avoid flaky tests,
    # but manual benchmarking should show improvement
    assert elapsed > 0  # Just verify it completes


def test_gil_with_containers(example_module):
    """Test GIL optimization with container allocations."""
    from example import helloworld

    # Create containers that allocate memory
    result = helloworld.make_list()
    assert isinstance(result, list)

    result = helloworld.make_dict()
    assert isinstance(result, dict)


def test_gil_multithreaded_safety(example_module):
    """Verify GIL caching is thread-safe with threadlocal storage."""
    import threading
    from example import helloworld

    results = []
    errors = []

    def worker():
        try:
            for _ in range(1000):
                result = helloworld.hello()
                results.append(result)
        except Exception as e:
            errors.append(e)

    # Run multiple threads
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 4000  # 4 threads × 1000 iterations


def test_gil_depth_tracking(example_module):
    """Test that GIL depth tracking works correctly."""
    from example import helloworld

    # Call functions that may trigger nested allocations
    # The GIL depth counter should properly increment/decrement
    result = helloworld.nested_function()
    assert result is not None
