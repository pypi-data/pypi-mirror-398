{%- if cookiecutter.enable_ai_agent %}
"""System prompts for AI agents.

Centralized location for all agent prompts to make them easy to find and modify.
"""

DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant."""
{%- else %}
"""AI Agent prompts - not configured."""
{%- endif %}
