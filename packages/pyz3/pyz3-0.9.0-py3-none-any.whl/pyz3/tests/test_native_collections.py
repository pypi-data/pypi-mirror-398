"""
Tests for native high-performance collections using uthash and utarray.
"""

import pytest
import sys
import time


@pytest.fixture(scope="module")
def native_collections():
    """Import the native collections example module."""
    try:
        from example import native_collections_example
        return native_collections_example
    except ImportError as e:
        pytest.skip(f"Native collections example not available: {e}")


class TestNativeDict:
    """Tests for FastDict (uthash-based dictionary)."""

    def test_fast_dict_basic(self, native_collections):
        """Test basic FastDict functionality."""
        result = native_collections.test_fast_dict()

        assert isinstance(result, dict)
        assert "key1" in result
        assert "key2" in result
        assert "key3" in result
        assert "size" in result

        assert result["key1"] == 42
        assert result["key2"] == 100
        assert result["key3"] == 200
        assert result["size"] == 3

    def test_dict_benchmark_small(self, native_collections):
        """Test FastDict performance with small dataset."""
        result = native_collections.benchmark_dict(100)

        assert isinstance(result, dict)
        assert "insert_time_ms" in result
        assert "lookup_time_ms" in result
        assert "size" in result

        assert result["size"] == 100
        assert result["insert_time_ms"] >= 0
        assert result["lookup_time_ms"] >= 0

        print(f"\nSmall dict (100 items):")
        print(f"  Insert time: {result['insert_time_ms']:.3f} ms")
        print(f"  Lookup time: {result['lookup_time_ms']:.3f} ms")

    def test_dict_benchmark_medium(self, native_collections):
        """Test FastDict performance with medium dataset."""
        result = native_collections.benchmark_dict(1000)

        assert isinstance(result, dict)
        assert result["size"] == 1000

        print(f"\nMedium dict (1,000 items):")
        print(f"  Insert time: {result['insert_time_ms']:.3f} ms")
        print(f"  Lookup time: {result['lookup_time_ms']:.3f} ms")

    def test_dict_benchmark_large(self, native_collections):
        """Test FastDict performance with large dataset."""
        result = native_collections.benchmark_dict(10000)

        assert isinstance(result, dict)
        assert result["size"] == 10000

        print(f"\nLarge dict (10,000 items):")
        print(f"  Insert time: {result['insert_time_ms']:.3f} ms")
        print(f"  Lookup time: {result['lookup_time_ms']:.3f} ms")

    def test_dict_vs_python_dict(self, native_collections):
        """Compare FastDict vs Python dict performance."""
        count = 10000

        # Test native dict
        result = native_collections.benchmark_dict(count)
        native_insert = result["insert_time_ms"]
        native_lookup = result["lookup_time_ms"]

        # Test Python dict
        start = time.perf_counter()
        py_dict = {}
        for i in range(count):
            py_dict[f"key{i}"] = i
        py_insert = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        for i in range(count):
            _ = py_dict.get(f"key{i}")
        py_lookup = (time.perf_counter() - start) * 1000

        print(f"\nDict comparison ({count:,} items):")
        print(f"  Native insert: {native_insert:.3f} ms")
        print(f"  Python insert: {py_insert:.3f} ms")
        print(f"  Native lookup: {native_lookup:.3f} ms")
        print(f"  Python lookup: {py_lookup:.3f} ms")

        # Native should be competitive
        assert native_insert >= 0
        assert native_lookup >= 0


class TestNativeArray:
    """Tests for FastArray (utarray-based dynamic array)."""

    def test_fast_array_basic(self, native_collections):
        """Test basic FastArray functionality."""
        result = native_collections.test_fast_array()

        assert isinstance(result, list)
        assert len(result) == 10

        # Check values
        for i, val in enumerate(result):
            assert val == i * 10

    def test_array_benchmark_small(self, native_collections):
        """Test FastArray performance with small dataset."""
        result = native_collections.benchmark_array(100)

        assert isinstance(result, dict)
        assert "push_time_ms" in result
        assert "access_time_ms" in result
        assert "size" in result

        assert result["size"] == 100
        assert result["push_time_ms"] >= 0
        assert result["access_time_ms"] >= 0

        print(f"\nSmall array (100 items):")
        print(f"  Push time: {result['push_time_ms']:.3f} ms")
        print(f"  Access time: {result['access_time_ms']:.3f} ms")

    def test_array_benchmark_medium(self, native_collections):
        """Test FastArray performance with medium dataset."""
        result = native_collections.benchmark_array(1000)

        assert isinstance(result, dict)
        assert result["size"] == 1000

        print(f"\nMedium array (1,000 items):")
        print(f"  Push time: {result['push_time_ms']:.3f} ms")
        print(f"  Access time: {result['access_time_ms']:.3f} ms")

    def test_array_benchmark_large(self, native_collections):
        """Test FastArray performance with large dataset."""
        result = native_collections.benchmark_array(10000)

        assert isinstance(result, dict)
        assert result["size"] == 10000

        print(f"\nLarge array (10,000 items):")
        print(f"  Push time: {result['push_time_ms']:.3f} ms")
        print(f"  Access time: {result['access_time_ms']:.3f} ms")

    def test_array_vs_python_list(self, native_collections):
        """Compare FastArray vs Python list performance."""
        count = 10000

        # Test native array
        result = native_collections.benchmark_array(count)
        native_push = result["push_time_ms"]
        native_access = result["access_time_ms"]

        # Test Python list
        start = time.perf_counter()
        py_list = []
        for i in range(count):
            py_list.append(i)
        py_push = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        for i in range(count):
            _ = py_list[i]
        py_access = (time.perf_counter() - start) * 1000

        print(f"\nArray comparison ({count:,} items):")
        print(f"  Native push: {native_push:.3f} ms")
        print(f"  Python push: {py_push:.3f} ms")
        print(f"  Native access: {native_access:.3f} ms")
        print(f"  Python access: {py_access:.3f} ms")

        # Native should be competitive
        assert native_push >= 0
        assert native_access >= 0


class TestNativeCollectionsIntegration:
    """Integration tests for native collections."""

    def test_dict_with_pyobjects(self, native_collections):
        """Test that native dict can work with Python objects."""
        result = native_collections.dict_with_pyobjects()

        assert isinstance(result, dict)
        assert "message" in result
        assert isinstance(result["message"], str)
        assert "Native dict" in result["message"]

    def test_large_scale_dict(self, native_collections):
        """Test native dict with large scale data."""
        count = 50000

        result = native_collections.benchmark_dict(count)

        assert result["size"] == count
        print(f"\nLarge-scale dict ({count:,} items):")
        print(f"  Insert time: {result['insert_time_ms']:.3f} ms")
        print(f"  Lookup time: {result['lookup_time_ms']:.3f} ms")
        print(f"  Avg insert: {result['insert_time_ms']/count*1000:.3f} µs/op")
        print(f"  Avg lookup: {result['lookup_time_ms']/count*1000:.3f} µs/op")

    def test_large_scale_array(self, native_collections):
        """Test native array with large scale data."""
        count = 50000

        result = native_collections.benchmark_array(count)

        assert result["size"] == count
        print(f"\nLarge-scale array ({count:,} items):")
        print(f"  Push time: {result['push_time_ms']:.3f} ms")
        print(f"  Access time: {result['access_time_ms']:.3f} ms")
        print(f"  Avg push: {result['push_time_ms']/count*1000:.3f} µs/op")
        print(f"  Avg access: {result['access_time_ms']/count*1000:.3f} µs/op")


class TestNativeCollectionsMemory:
    """Memory and stress tests for native collections."""

    def test_dict_stress(self, native_collections):
        """Stress test for dict with many operations."""
        # This should not crash or leak memory
        result = native_collections.benchmark_dict(100000)

        assert result["size"] == 100000
        print(f"\nDict stress test (100,000 items):")
        print(f"  Total time: {result['insert_time_ms'] + result['lookup_time_ms']:.3f} ms")

    def test_array_stress(self, native_collections):
        """Stress test for array with many operations."""
        # This should not crash or leak memory
        result = native_collections.benchmark_array(100000)

        assert result["size"] == 100000
        print(f"\nArray stress test (100,000 items):")
        print(f"  Total time: {result['push_time_ms'] + result['access_time_ms']:.3f} ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
