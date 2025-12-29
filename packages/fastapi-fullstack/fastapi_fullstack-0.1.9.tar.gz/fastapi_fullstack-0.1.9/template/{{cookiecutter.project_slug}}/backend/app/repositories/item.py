{%- if cookiecutter.include_example_crud and cookiecutter.use_postgresql %}
"""Item repository (PostgreSQL async).

Contains database operations for Item entity. Business logic
should be handled by ItemService in app/services/item.py.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.item import Item


async def get_by_id(db: AsyncSession, item_id: UUID) -> Item | None:
    """Get item by ID."""
    return await db.get(Item, item_id)


async def get_multi(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> list[Item]:
    """Get multiple items with pagination."""
    query = select(Item)
    if active_only:
        query = query.where(Item.is_active == True)  # noqa: E712
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create(
    db: AsyncSession,
    *,
    title: str,
    description: str | None = None,
) -> Item:
    """Create a new item."""
    item = Item(
        title=title,
        description=description,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def update(
    db: AsyncSession,
    *,
    db_item: Item,
    update_data: dict,
) -> Item:
    """Update an item."""
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.add(db_item)
    await db.flush()
    await db.refresh(db_item)
    return db_item


async def delete(db: AsyncSession, item_id: UUID) -> Item | None:
    """Delete an item."""
    item = await get_by_id(db, item_id)
    if item:
        await db.delete(item)
        await db.flush()
    return item


{%- elif cookiecutter.include_example_crud and cookiecutter.use_sqlite %}
"""Item repository (SQLite sync).

Contains database operations for Item entity. Business logic
should be handled by ItemService in app/services/item.py.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.item import Item


def get_by_id(db: Session, item_id: str) -> Item | None:
    """Get item by ID."""
    return db.get(Item, item_id)


def get_multi(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> list[Item]:
    """Get multiple items with pagination."""
    query = select(Item)
    if active_only:
        query = query.where(Item.is_active == True)  # noqa: E712
    query = query.offset(skip).limit(limit)
    result = db.execute(query)
    return list(result.scalars().all())


def create(
    db: Session,
    *,
    title: str,
    description: str | None = None,
) -> Item:
    """Create a new item."""
    item = Item(
        title=title,
        description=description,
    )
    db.add(item)
    db.flush()
    db.refresh(item)
    return item


def update(
    db: Session,
    *,
    db_item: Item,
    update_data: dict,
) -> Item:
    """Update an item."""
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.add(db_item)
    db.flush()
    db.refresh(db_item)
    return db_item


def delete(db: Session, item_id: str) -> Item | None:
    """Delete an item."""
    item = get_by_id(db, item_id)
    if item:
        db.delete(item)
        db.flush()
    return item


{%- elif cookiecutter.include_example_crud and cookiecutter.use_mongodb %}
"""Item repository (MongoDB).

Contains database operations for Item entity. Business logic
should be handled by ItemService in app/services/item.py.
"""

from datetime import UTC, datetime

from app.db.models.item import Item


async def get_by_id(item_id: str) -> Item | None:
    """Get item by ID."""
    return await Item.get(item_id)


async def get_multi(
    *,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> list[Item]:
    """Get multiple items with pagination."""
    query = Item.find_all()
    if active_only:
        query = Item.find(Item.is_active == True)  # noqa: E712
    return await query.skip(skip).limit(limit).to_list()


async def create(
    *,
    title: str,
    description: str | None = None,
) -> Item:
    """Create a new item."""
    item = Item(
        title=title,
        description=description,
    )
    await item.insert()
    return item


async def update(
    *,
    db_item: Item,
    update_data: dict,
) -> Item:
    """Update an item."""
    for field, value in update_data.items():
        setattr(db_item, field, value)
    db_item.updated_at = datetime.now(UTC)
    await db_item.save()
    return db_item


async def delete(item_id: str) -> Item | None:
    """Delete an item."""
    item = await get_by_id(item_id)
    if item:
        await item.delete()
    return item


{%- else %}
"""Item repository - not configured."""
{%- endif %}
