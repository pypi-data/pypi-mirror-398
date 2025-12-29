{%- if cookiecutter.use_celery or cookiecutter.use_taskiq or cookiecutter.use_arq %}
"""Background workers."""
{%- else %}
# Background workers not enabled
{%- endif %}
