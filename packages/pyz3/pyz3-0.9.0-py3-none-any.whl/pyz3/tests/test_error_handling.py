"""Test cases for enhanced error handling with stack traces."""

import pytest
import sys


def test_granular_error_types():
    """Test that granular error types are properly defined."""
    from pyz3 import errors_enhanced

    # Check that error types exist
    assert hasattr(errors_enhanced, 'PyError')


def test_error_with_stack_trace():
    """Test capturing error with stack trace."""
    # This will be tested when we have a module that uses enhanced errors
    pass


def test_python_exception_info():
    """Test getting Python exception information."""
    try:
        # Raise a Python exception
        raise ValueError("Test error message")
    except ValueError:
        # Exception is set, we could capture it with getErrorInfo
        exc_type, exc_value, exc_tb = sys.exc_info()

        assert exc_type is ValueError
        assert str(exc_value) == "Test error message"
        assert exc_tb is not None


def test_nested_exceptions():
    """Test handling nested exceptions."""

    def inner():
        raise ValueError("Inner error")

    def middle():
        try:
            inner()
        except ValueError as e:
            raise RuntimeError("Middle error") from e

    def outer():
        try:
            middle()
        except RuntimeError as e:
            raise TypeError("Outer error") from e

    with pytest.raises(TypeError) as exc_info:
        outer()

    # Check exception chaining
    assert exc_info.value.__cause__ is not None
    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_exception_message_formatting():
    """Test that exception messages are properly formatted."""

    def raise_error():
        raise ValueError("Value must be positive, got -5")

    with pytest.raises(ValueError) as exc_info:
        raise_error()

    assert "Value must be positive" in str(exc_info.value)
    assert "-5" in str(exc_info.value)


def test_multiple_error_types():
    """Test different error types."""
    errors = [
        (TypeError, "Wrong type"),
        (ValueError, "Wrong value"),
        (KeyError, "Key not found"),
        (IndexError, "Index out of range"),
        (AttributeError, "Attribute missing"),
        (RuntimeError, "Runtime problem"),
    ]

    for error_type, message in errors:
        with pytest.raises(error_type):
            raise error_type(message)


def test_error_context_preservation():
    """Test that error context is preserved through multiple levels."""

    class CustomError(Exception):
        def __init__(self, message, context=None):
            super().__init__(message)
            self.context = context

    def level_3():
        raise ValueError("Level 3 error")

    def level_2():
        try:
            level_3()
        except ValueError as e:
            raise CustomError("Level 2 error", context=e)

    def level_1():
        try:
            level_2()
        except CustomError as e:
            raise RuntimeError(f"Level 1 error: {e}") from e

    with pytest.raises(RuntimeError) as exc_info:
        level_1()

    # Check that we can trace back through the errors
    assert exc_info.value.__cause__ is not None


def test_error_traceback_information():
    """Test that traceback information is available."""
    import traceback

    def error_function():
        raise ValueError("Test error for traceback")

    try:
        error_function()
    except ValueError:
        tb_lines = traceback.format_exc().split('\n')

        # Should contain file name
        assert any("test_error_handling.py" in line for line in tb_lines)

        # Should contain function name
        assert any("error_function" in line for line in tb_lines)

        # Should contain error message
        assert any("Test error for traceback" in line for line in tb_lines)


def test_assertion_error():
    """Test AssertionError handling."""
    with pytest.raises(AssertionError):
        assert False, "This should fail"


def test_zero_division_error():
    """Test ZeroDivisionError."""
    with pytest.raises(ZeroDivisionError):
        _ = 1 / 0


def test_overflow_error():
    """Test OverflowError."""
    with pytest.raises((OverflowError, ValueError)):
        # Try to create a number too large
        _ = float('1e309') * float('1e309')


def test_unicode_error():
    """Test UnicodeError handling."""
    with pytest.raises(UnicodeDecodeError):
        # Invalid UTF-8 sequence
        b'\xff\xfe'.decode('utf-8')


def test_import_error():
    """Test ImportError."""
    with pytest.raises(ImportError):
        import nonexistent_module_xyz_12345


def test_attribute_error_detailed():
    """Test detailed AttributeError."""

    class TestClass:
        def __init__(self):
            self.existing_attr = "value"

    obj = TestClass()

    # This should work
    _ = obj.existing_attr

    # This should raise AttributeError
    with pytest.raises(AttributeError) as exc_info:
        _ = obj.nonexistent_attr

    assert "nonexistent_attr" in str(exc_info.value)


def test_key_error_detailed():
    """Test detailed KeyError."""
    d = {"a": 1, "b": 2}

    # This should work
    _ = d["a"]

    # This should raise KeyError
    with pytest.raises(KeyError) as exc_info:
        _ = d["nonexistent_key"]

    assert "nonexistent_key" in str(exc_info.value)


def test_index_error_detailed():
    """Test detailed IndexError."""
    lst = [1, 2, 3]

    # This should work
    _ = lst[0]

    # This should raise IndexError
    with pytest.raises(IndexError):
        _ = lst[10]


def test_type_error_detailed():
    """Test detailed TypeError."""
    with pytest.raises(TypeError) as exc_info:
        # Cannot add string and int
        _ = "string" + 5

    # Error message should be descriptive
    assert "str" in str(exc_info.value) or "int" in str(exc_info.value)


def test_value_error_detailed():
    """Test detailed ValueError."""
    with pytest.raises(ValueError) as exc_info:
        int("not a number")

    assert "invalid literal" in str(exc_info.value).lower()


def test_file_not_found_error():
    """Test FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        with open("/nonexistent/path/file.txt"):
            pass


def test_permission_error():
    """Test PermissionError (on Unix-like systems)."""
    import os

    if os.name != 'nt':  # Skip on Windows
        with pytest.raises((PermissionError, OSError)):
            # Try to write to root (requires permissions)
            with open("/root/test_file.txt", 'w'):
                pass


def test_stop_iteration():
    """Test StopIteration."""
    it = iter([1, 2, 3])

    # Exhaust iterator
    next(it)
    next(it)
    next(it)

    # Should raise StopIteration
    with pytest.raises(StopIteration):
        next(it)


def test_error_recovery():
    """Test error recovery and continued execution."""
    results = []

    for i in range(5):
        try:
            if i == 2:
                raise ValueError("Error at 2")
            results.append(i)
        except ValueError:
            results.append(-1)

    assert results == [0, 1, -1, 3, 4]


def test_finally_block_execution():
    """Test that finally blocks always execute."""
    executed = []

    def test_finally():
        try:
            executed.append("try")
            raise ValueError("Test")
        except ValueError:
            executed.append("except")
        finally:
            executed.append("finally")

    test_finally()

    assert executed == ["try", "except", "finally"]


def test_error_message_interpolation():
    """Test error messages with variable interpolation."""
    value = -5
    minimum = 0

    with pytest.raises(ValueError) as exc_info:
        if value < minimum:
            raise ValueError(f"Value {value} is less than minimum {minimum}")

    assert "-5" in str(exc_info.value)
    assert "0" in str(exc_info.value)
