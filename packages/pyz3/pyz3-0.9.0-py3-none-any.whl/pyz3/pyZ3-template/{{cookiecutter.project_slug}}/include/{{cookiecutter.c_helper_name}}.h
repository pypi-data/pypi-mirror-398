{% if cookiecutter.include_c_example == "yes" -%}
// C helper functions for {{ cookiecutter.project_name }}

#ifndef {{ cookiecutter.c_helper_name.upper() }}_H
#define {{ cookiecutter.c_helper_name.upper() }}_H

// Example function: add two integers
int {{ cookiecutter.c_helper_name }}_add(int a, int b);

// Example function: multiply two integers
int {{ cookiecutter.c_helper_name }}_multiply(int a, int b);

#endif // {{ cookiecutter.c_helper_name.upper() }}_H
{% endif -%}
