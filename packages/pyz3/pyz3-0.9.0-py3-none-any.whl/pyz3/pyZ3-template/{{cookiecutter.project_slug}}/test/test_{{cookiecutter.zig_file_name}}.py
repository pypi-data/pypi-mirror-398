from {{ cookiecutter.package_name }} import {{ cookiecutter.module_name }}


def test_fibonacci():
    impls = [
        {{ cookiecutter.module_name }}.nth_fibonacci_iterative,
        {{ cookiecutter.module_name }}.nth_fibonacci_recursive,
        {{ cookiecutter.module_name }}.nth_fibonacci_recursive_tail,
    ]
    for impl in impls:
        assert impl(9) == 34


def test_fibonacci_iterator():
    fibonacci = {{ cookiecutter.module_name }}.Fibonacci(10)
    expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

    # As iterator
    fibonacci_iter = iter(fibonacci)
    for expected_item in expected:
        actual = next(fibonacci_iter)
        assert actual == expected_item

    # As list
    fibonacci_list = list(fibonacci)
    for actual, expected_item in zip(fibonacci_list, expected):
        assert actual == expected_item
