{%- if cookiecutter.use_celery or cookiecutter.use_taskiq %}
"""Background workers."""
{%- else %}
# Background workers not enabled
{%- endif %}
