"""Database module."""
{%- if cookiecutter.use_postgresql or cookiecutter.use_sqlite %}

from app.db.base import Base

__all__ = ["Base"]
{%- endif %}
