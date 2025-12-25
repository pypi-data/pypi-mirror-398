{% if cookiecutter.include_c_example == "yes" -%}
// C implementation of helper functions for {{ cookiecutter.project_name }}

#include "{{ cookiecutter.c_helper_name }}.h"

int {{ cookiecutter.c_helper_name }}_add(int a, int b) {
    return a + b;
}

int {{ cookiecutter.c_helper_name }}_multiply(int a, int b) {
    return a * b;
}
{% endif -%}
