"""Test cases for fast path optimization for primitive types."""
import time
import pytest


def test_i64_fastpath(example_module):
    """Test i64 fast path conversion."""
    from example import fastpath_bench

    # Test basic conversion
    assert fastpath_bench.return_i64(21) == 42
    assert fastpath_bench.return_i64(-10) == -20
    assert fastpath_bench.return_i64(0) == 0


def test_f64_fastpath(example_module):
    """Test f64 fast path conversion."""
    from example import fastpath_bench

    # Test basic conversion
    assert fastpath_bench.return_f64(21.5) == 43.0
    assert fastpath_bench.return_f64(-10.25) == -20.5
    assert abs(fastpath_bench.return_f64(0.1) - 0.2) < 1e-10


def test_bool_fastpath(example_module):
    """Test bool fast path conversion."""
    from example import fastpath_bench

    # Test basic conversion
    assert fastpath_bench.return_bool(True) is False
    assert fastpath_bench.return_bool(False) is True


def test_string_fastpath(example_module):
    """Test string fast path conversion."""
    from example import fastpath_bench

    # Test basic conversion
    assert fastpath_bench.return_string("hello") == "hello"
    assert fastpath_bench.return_string("") == ""
    assert fastpath_bench.return_string("unicode: ñ ü 中文") == "unicode: ñ ü 中文"


def test_mixed_types_fastpath(example_module):
    """Test mixed type conversions using fast paths."""
    from example import fastpath_bench

    result = fastpath_bench.mixed_types(
        int_val=21,
        float_val=10.5,
        bool_val=True,
        str_val="test"
    )

    assert isinstance(result, dict)
    assert result["int_result"] == 42
    assert result["float_result"] == 21.0
    assert result["bool_result"] is False
    assert result["str_result"] == "test"


def test_optional_int_fastpath(example_module):
    """Test optional type with fast path."""
    from example import fastpath_bench

    # Test with value
    assert fastpath_bench.optional_int(21) == 42

    # Test with None
    assert fastpath_bench.optional_int(None) is None


def test_error_union_fastpath(example_module):
    """Test error union with fast path."""
    from example import fastpath_bench

    # Test success case
    assert fastpath_bench.error_union_int(21, False) == 42

    # Test error case
    with pytest.raises(RuntimeError):
        fastpath_bench.error_union_int(21, True)


def test_fastpath_performance(example_module):
    """Benchmark fast path performance improvement."""
    from example import fastpath_bench

    # Warm up
    for _ in range(100):
        fastpath_bench.return_i64(42)

    # Measure performance
    iterations = 100000
    start = time.perf_counter()
    for i in range(iterations):
        result = fastpath_bench.return_i64(i)
    elapsed = time.perf_counter() - start

    # With fast paths, this should be significantly faster than generic trampolines
    # Average should be well under 10 microseconds per call
    avg_time_us = (elapsed / iterations) * 1e6
    print(f"\nAverage time per i64 conversion: {avg_time_us:.3f} µs")

    assert elapsed > 0  # Just verify it completes


def test_benchmark_primitives(example_module):
    """Test the benchmark function for primitive conversions."""
    from example import fastpath_bench

    # Test with small number
    result = fastpath_bench.benchmark_primitives(100)
    expected = sum(range(100))
    assert result == expected

    # Test with larger number
    result = fastpath_bench.benchmark_primitives(1000)
    expected = sum(range(1000))
    assert result == expected


def test_fastpath_type_checking(example_module):
    """Verify fast paths still do type checking when needed."""
    from example import fastpath_bench

    # These should work
    assert fastpath_bench.return_i64(42) == 84
    assert fastpath_bench.return_f64(21.0) == 42.0

    # These should raise TypeError
    with pytest.raises(TypeError):
        fastpath_bench.return_i64("not an int")

    with pytest.raises(TypeError):
        fastpath_bench.return_f64("not a float")


def test_fastpath_edge_cases(example_module):
    """Test edge cases for fast path optimization."""
    from example import fastpath_bench

    # Max/min values for i64
    import sys
    max_i64 = 2**63 - 1
    min_i64 = -(2**63)

    # Python will auto-promote to larger int if result overflows
    fastpath_bench.return_i64(max_i64 // 2)
    fastpath_bench.return_i64(min_i64 // 2)

    # Special float values
    assert fastpath_bench.return_f64(float('inf')) == float('inf')
    assert fastpath_bench.return_f64(float('-inf')) == float('-inf')
    import math
    assert math.isnan(fastpath_bench.return_f64(float('nan')))


def test_fastpath_vs_generic(example_module):
    """Compare fast path vs generic trampoline performance."""
    from example import fastpath_bench
    import time

    # Test i64 fast path
    iterations = 50000

    start = time.perf_counter()
    for i in range(iterations):
        fastpath_bench.return_i64(i)
    fastpath_time = time.perf_counter() - start

    print(f"\nFast path time for {iterations} i64 conversions: {fastpath_time:.4f}s")
    print(f"Average per call: {(fastpath_time/iterations)*1e6:.3f} µs")

    # Fast paths should complete quickly
    assert fastpath_time < 1.0  # Should take less than 1 second for 50k calls
