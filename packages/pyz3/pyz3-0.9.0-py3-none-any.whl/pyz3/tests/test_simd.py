"""Test cases for SIMD datatype support."""

import pytest
import math


def test_vec4_add(example_module):
    """Test SIMD vector addition."""
    from example import simd_example

    a = [1.0, 2.0, 3.0, 4.0]
    b = [5.0, 6.0, 7.0, 8.0]

    result = simd_example.vec4_add(a, b)

    assert len(result) == 4
    assert result[0] == pytest.approx(6.0)
    assert result[1] == pytest.approx(8.0)
    assert result[2] == pytest.approx(10.0)
    assert result[3] == pytest.approx(12.0)


def test_vec4_dot_product(example_module):
    """Test SIMD dot product."""
    from example import simd_example

    a = [1.0, 2.0, 3.0, 4.0]
    b = [5.0, 6.0, 7.0, 8.0]

    result = simd_example.vec4_dot(a, b)

    # 1*5 + 2*6 + 3*7 + 4*8 = 70
    assert result == pytest.approx(70.0)


def test_vec4_scale(example_module):
    """Test SIMD vector scaling."""
    from example import simd_example

    vec = [1.0, 2.0, 3.0, 4.0]
    scalar = 2.5

    result = simd_example.vec4_scale(vec=vec, scalar=scalar)

    assert len(result) == 4
    assert result[0] == pytest.approx(2.5)
    assert result[1] == pytest.approx(5.0)
    assert result[2] == pytest.approx(7.5)
    assert result[3] == pytest.approx(10.0)


def test_vec4_sum(example_module):
    """Test SIMD vector sum."""
    from example import simd_example

    vec = [1.0, 2.0, 3.0, 4.0]
    result = simd_example.vec4_sum(vec=vec)

    assert result == pytest.approx(10.0)


def test_vec4_min(example_module):
    """Test SIMD vector minimum."""
    from example import simd_example

    vec = [3.0, 1.0, 4.0, 2.0]
    result = simd_example.vec4_min(vec=vec)

    assert result == pytest.approx(1.0)


def test_vec4_max(example_module):
    """Test SIMD vector maximum."""
    from example import simd_example

    vec = [3.0, 1.0, 4.0, 2.0]
    result = simd_example.vec4_max(vec=vec)

    assert result == pytest.approx(4.0)


def test_vec4_distance(example_module):
    """Test SIMD distance calculation."""
    from example import simd_example

    a = [0.0, 0.0, 0.0, 0.0]
    b = [3.0, 4.0, 0.0, 0.0]

    result = simd_example.vec4_distance(a, b)

    # Distance should be 5.0 (3-4-5 triangle)
    assert result == pytest.approx(5.0)


def test_batch_add_same_length(example_module):
    """Test SIMD batch addition."""
    from example import simd_example

    a = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    b = [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]

    result = simd_example.batch_add(a, b)

    assert len(result) == 8
    for val in result:
        assert val == pytest.approx(9.0)


def test_batch_add_different_length(example_module):
    """Test that batch add raises error for different lengths."""
    from example import simd_example

    a = [1.0, 2.0, 3.0]
    b = [4.0, 5.0, 6.0, 7.0]

    with pytest.raises(ValueError, match="same length"):
        simd_example.batch_add(a, b)


def test_vec4_with_tuple(example_module):
    """Test that SIMD works with tuples."""
    from example import simd_example

    a = (1.0, 2.0, 3.0, 4.0)
    b = (5.0, 6.0, 7.0, 8.0)

    result = simd_example.vec4_add(a, b)

    assert len(result) == 4
    assert result[0] == pytest.approx(6.0)


def test_vec4_wrong_length(example_module):
    """Test error handling for wrong vector length."""
    from example import simd_example

    a = [1.0, 2.0, 3.0]  # Only 3 elements instead of 4
    b = [4.0, 5.0, 6.0, 7.0]

    with pytest.raises(ValueError, match="length 4"):
        simd_example.vec4_add(a, b)


def test_vec4_wrong_type(example_module):
    """Test error handling for wrong input type."""
    from example import simd_example

    a = "not a list"
    b = [1.0, 2.0, 3.0, 4.0]

    with pytest.raises(TypeError, match="list or tuple"):
        simd_example.vec4_add(a, b)


def test_vec4_operations_chain(example_module):
    """Test chaining multiple SIMD operations."""
    from example import simd_example

    vec = [1.0, 2.0, 3.0, 4.0]

    # Scale by 2
    scaled = simd_example.vec4_scale(vec=vec, scalar=2.0)

    # Find sum of scaled vector
    result = simd_example.vec4_sum(vec=scaled)

    # (1+2+3+4) * 2 = 20
    assert result == pytest.approx(20.0)


def test_batch_add_large_array(example_module):
    """Test SIMD batch operations on larger arrays."""
    from example import simd_example

    size = 1000
    a = [float(i) for i in range(size)]
    b = [float(i * 2) for i in range(size)]

    result = simd_example.batch_add(a, b)

    assert len(result) == size
    for i, val in enumerate(result):
        expected = a[i] + b[i]
        assert val == pytest.approx(expected)


def test_vec4_zero_vector(example_module):
    """Test SIMD operations with zero vector."""
    from example import simd_example

    zero = [0.0, 0.0, 0.0, 0.0]
    vec = [1.0, 2.0, 3.0, 4.0]

    # Add zero
    result = simd_example.vec4_add(zero, vec)
    assert result == [pytest.approx(v) for v in vec]

    # Dot with zero
    dot_result = simd_example.vec4_dot(zero, vec)
    assert dot_result == pytest.approx(0.0)

    # Sum of zero
    sum_result = simd_example.vec4_sum(vec=zero)
    assert sum_result == pytest.approx(0.0)


def test_vec4_negative_values(example_module):
    """Test SIMD with negative values."""
    from example import simd_example

    a = [-1.0, -2.0, -3.0, -4.0]
    b = [4.0, 3.0, 2.0, 1.0]

    result = simd_example.vec4_add(a, b)

    assert result[0] == pytest.approx(3.0)
    assert result[1] == pytest.approx(1.0)
    assert result[2] == pytest.approx(-1.0)
    assert result[3] == pytest.approx(-3.0)


def test_vec4_performance(example_module):
    """Benchmark SIMD performance."""
    from example import simd_example
    import time

    vec1 = [1.0, 2.0, 3.0, 4.0]
    vec2 = [5.0, 6.0, 7.0, 8.0]

    # Warm up
    for _ in range(100):
        simd_example.vec4_add(vec1, vec2)

    # Benchmark
    iterations = 10000
    start = time.perf_counter()
    for _ in range(iterations):
        simd_example.vec4_add(vec1, vec2)
    elapsed = time.perf_counter() - start

    avg_time_us = (elapsed / iterations) * 1e6
    print(f"\nAverage SIMD vec4_add time: {avg_time_us:.3f} µs")

    # Should be very fast
    assert elapsed < 1.0  # Less than 1 second for 10k operations
