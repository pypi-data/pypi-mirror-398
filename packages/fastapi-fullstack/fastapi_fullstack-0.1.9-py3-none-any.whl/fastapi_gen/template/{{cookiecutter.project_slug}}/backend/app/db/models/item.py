{%- if cookiecutter.include_example_crud and cookiecutter.use_postgresql and cookiecutter.use_sqlmodel %}
"""Item database model using SQLModel - example CRUD entity."""

import uuid

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from app.db.base import TimestampMixin


class Item(TimestampMixin, SQLModel, table=True):
    """Item model - example entity for demonstrating CRUD operations.

    This is a simple example model. You can use it as a template
    for creating your own models or remove it if not needed.
    """

    __tablename__ = "items"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    title: str = Field(
        sa_column=Column(String(255), nullable=False, index=True),
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    is_active: bool = Field(default=True)

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, title={self.title})>"


{%- elif cookiecutter.include_example_crud and cookiecutter.use_postgresql %}
"""Item database model - example CRUD entity."""

import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Item(Base, TimestampMixin):
    """Item model - example entity for demonstrating CRUD operations.

    This is a simple example model. You can use it as a template
    for creating your own models or remove it if not needed.
    """

    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, title={self.title})>"


{%- elif cookiecutter.include_example_crud and cookiecutter.use_sqlite and cookiecutter.use_sqlmodel %}
"""Item database model using SQLModel - example CRUD entity."""

import uuid

from sqlalchemy import Column, String, Text
from sqlmodel import Field, SQLModel

from app.db.base import TimestampMixin


class Item(TimestampMixin, SQLModel, table=True):
    """Item model - example entity for demonstrating CRUD operations.

    This is a simple example model. You can use it as a template
    for creating your own models or remove it if not needed.
    """

    __tablename__ = "items"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(String(36), primary_key=True),
    )
    title: str = Field(
        sa_column=Column(String(255), nullable=False, index=True),
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    is_active: bool = Field(default=True)

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, title={self.title})>"


{%- elif cookiecutter.include_example_crud and cookiecutter.use_sqlite %}
"""Item database model - example CRUD entity."""

import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Item(Base, TimestampMixin):
    """Item model - example entity for demonstrating CRUD operations.

    This is a simple example model. You can use it as a template
    for creating your own models or remove it if not needed.
    """

    __tablename__ = "items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, title={self.title})>"


{%- elif cookiecutter.include_example_crud and cookiecutter.use_mongodb %}
"""Item document model for MongoDB - example CRUD entity."""

from datetime import UTC, datetime
from typing import Optional

from beanie import Document
from pydantic import Field


class Item(Document):
    """Item document model - example entity for demonstrating CRUD operations.

    This is a simple example model. You can use it as a template
    for creating your own models or remove it if not needed.
    """

    title: str = Field(max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = None

    class Settings:
        name = "items"
        indexes = [
            "title",
        ]


{%- else %}
"""Item model - not configured."""
{%- endif %}
