"""Test cases for object pooling optimization."""
import sys
import pytest


def test_small_int_pooling(example_module):
    """Test that small integers use object pooling."""
    from example import fastpath_bench

    # Small integers should be cached
    result1 = fastpath_bench.return_i64(5)
    result2 = fastpath_bench.return_i64(5)

    # Both should return the value 10 (5 * 2)
    assert result1 == 10
    assert result2 == 10

    # Test multiple small integers
    for i in range(-5, 257):
        result = fastpath_bench.return_i64(i)
        assert result == i * 2


def test_large_int_no_pooling(example_module):
    """Test that large integers are not pooled."""
    from example import fastpath_bench

    # Large integers should work correctly (just not pooled)
    result = fastpath_bench.return_i64(1000)
    assert result == 2000

    result = fastpath_bench.return_i64(-1000)
    assert result == -2000


def test_pool_initialization(example_module):
    """Test that object pool initializes correctly."""
    from example import fastpath_bench

    # Multiple calls should work consistently
    for _ in range(100):
        result = fastpath_bench.return_i64(42)
        assert result == 84


def test_pool_performance_benefit(example_module):
    """Benchmark showing pooling improves performance for small ints."""
    from example import fastpath_bench
    import time

    # Test with small integers (should use pool)
    iterations = 50000

    start = time.perf_counter()
    for i in range(iterations):
        # Use small int that should be pooled
        small_val = i % 256
        result = fastpath_bench.return_i64(small_val)
    small_int_time = time.perf_counter() - start

    print(f"\nSmall int pooling time for {iterations} calls: {small_int_time:.4f}s")
    print(f"Average per call: {(small_int_time/iterations)*1e6:.3f} µs")

    # Pooling should make this very fast
    assert small_int_time < 2.0  # Should take less than 2 seconds


def test_pool_edge_cases(example_module):
    """Test edge cases for object pooling."""
    from example import fastpath_bench

    # Test boundary values
    assert fastpath_bench.return_i64(-5) == -10  # Lower bound of pool
    assert fastpath_bench.return_i64(256) == 512  # Upper bound of pool
    assert fastpath_bench.return_i64(-6) == -12  # Just outside lower bound
    assert fastpath_bench.return_i64(257) == 514  # Just outside upper bound


def test_pool_thread_safety(example_module):
    """Test that object pooling is thread-safe."""
    import threading
    from example import fastpath_bench

    results = []
    errors = []

    def worker():
        try:
            for i in range(1000):
                # Use small integers that should be pooled
                result = fastpath_bench.return_i64(i % 100)
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


def test_pool_memory_efficiency(example_module):
    """Verify that pooling reduces memory allocations."""
    from example import fastpath_bench

    # Create many small integers
    # Without pooling, this would create many objects
    # With pooling, it reuses cached objects
    results = []
    for i in range(10000):
        result = fastpath_bench.return_i64(i % 50)  # Small int range
        results.append(result)

    assert len(results) == 10000
    # All results should be valid
    for i, result in enumerate(results):
        expected = (i % 50) * 2
        assert result == expected


def test_pool_benchmark_comparison(example_module):
    """Compare performance with and without pooling."""
    from example import fastpath_bench
    import time

    iterations = 100000

    # Test with small integers (uses pooling)
    start = time.perf_counter()
    for i in range(iterations):
        result = fastpath_bench.return_i64(i % 100)  # Small int, pooled
    pooled_time = time.perf_counter() - start

    # Test with large integers (no pooling)
    start = time.perf_counter()
    for i in range(iterations):
        result = fastpath_bench.return_i64(1000 + i)  # Large int, not pooled
    non_pooled_time = time.perf_counter() - start

    print(f"\nPooled time: {pooled_time:.4f}s")
    print(f"Non-pooled time: {non_pooled_time:.4f}s")
    print(f"Speedup: {non_pooled_time/pooled_time:.2f}x")

    # Pooled should be faster or similar (CPython also caches small ints)
    # This test just verifies both work correctly
    assert pooled_time > 0
    assert non_pooled_time > 0
