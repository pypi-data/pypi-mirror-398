{%- if cookiecutter.include_example_crud %}
"""Item schemas - example CRUD entity.

This module demonstrates standard Pydantic schemas for a CRUD entity.
You can use it as a template for creating your own schemas.
"""

{%- if cookiecutter.use_postgresql %}
from uuid import UUID
{%- endif %}

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema


class ItemBase(BaseSchema):
    """Base item schema with common fields."""

    title: str = Field(max_length=255, description="Item title")
    description: str | None = Field(default=None, description="Item description")


class ItemCreate(ItemBase):
    """Schema for creating an item."""

    pass


class ItemUpdate(BaseSchema):
    """Schema for updating an item.

    All fields are optional to allow partial updates.
    """

    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None)
    is_active: bool | None = None


class ItemRead(ItemBase, TimestampSchema):
    """Schema for reading an item (API response)."""

{%- if cookiecutter.use_postgresql %}
    id: UUID
{%- else %}
    id: str
{%- endif %}
    is_active: bool = True
{%- else %}
"""Item schemas - not configured."""
{%- endif %}
