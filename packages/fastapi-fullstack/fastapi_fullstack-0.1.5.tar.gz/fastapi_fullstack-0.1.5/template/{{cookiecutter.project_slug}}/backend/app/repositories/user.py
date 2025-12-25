{%- if cookiecutter.use_jwt and cookiecutter.use_postgresql %}
"""User repository (PostgreSQL async).

Contains only database operations. Business logic (password hashing,
validation) is handled by UserService in app/services/user.py.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


async def get_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """Get user by ID."""
    return await db.get(User, user_id)


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    """Get user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


{%- if cookiecutter.enable_oauth %}


async def get_by_oauth(db: AsyncSession, provider: str, oauth_id: str) -> User | None:
    """Get user by OAuth provider and ID."""
    result = await db.execute(
        select(User).where(User.oauth_provider == provider, User.oauth_id == oauth_id)
    )
    return result.scalar_one_or_none()
{%- endif %}


async def get_multi(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """Get multiple users with pagination."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


async def create(
    db: AsyncSession,
    *,
    email: str,
    hashed_password: str | None,
    full_name: str | None = None,
    is_active: bool = True,
    is_superuser: bool = False,
    role: str = "user",
{%- if cookiecutter.enable_oauth %}
    oauth_provider: str | None = None,
    oauth_id: str | None = None,
{%- endif %}
) -> User:
    """Create a new user.

    Note: Password should already be hashed by the service layer.
    """
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=is_active,
        is_superuser=is_superuser,
        role=role,
{%- if cookiecutter.enable_oauth %}
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
{%- endif %}
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update(
    db: AsyncSession,
    *,
    db_user: User,
    update_data: dict,
) -> User:
    """Update a user.

    Note: If password needs updating, it should already be hashed.
    """
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user


async def delete(db: AsyncSession, user_id: UUID) -> User | None:
    """Delete a user."""
    user = await get_by_id(db, user_id)
    if user:
        await db.delete(user)
        await db.flush()
    return user


{%- elif cookiecutter.use_jwt and cookiecutter.use_sqlite %}
"""User repository (SQLite sync).

Contains only database operations. Business logic (password hashing,
validation) is handled by UserService in app/services/user.py.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User


def get_by_id(db: Session, user_id: str) -> User | None:
    """Get user by ID."""
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    """Get user by email."""
    result = db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


{%- if cookiecutter.enable_oauth %}


def get_by_oauth(db: Session, provider: str, oauth_id: str) -> User | None:
    """Get user by OAuth provider and ID."""
    result = db.execute(
        select(User).where(User.oauth_provider == provider, User.oauth_id == oauth_id)
    )
    return result.scalar_one_or_none()
{%- endif %}


def get_multi(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """Get multiple users with pagination."""
    result = db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


def create(
    db: Session,
    *,
    email: str,
    hashed_password: str | None,
    full_name: str | None = None,
    is_active: bool = True,
    is_superuser: bool = False,
    role: str = "user",
{%- if cookiecutter.enable_oauth %}
    oauth_provider: str | None = None,
    oauth_id: str | None = None,
{%- endif %}
) -> User:
    """Create a new user.

    Note: Password should already be hashed by the service layer.
    """
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=is_active,
        is_superuser=is_superuser,
        role=role,
{%- if cookiecutter.enable_oauth %}
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
{%- endif %}
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def update(
    db: Session,
    *,
    db_user: User,
    update_data: dict,
) -> User:
    """Update a user.

    Note: If password needs updating, it should already be hashed.
    """
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.add(db_user)
    db.flush()
    db.refresh(db_user)
    return db_user


def delete(db: Session, user_id: str) -> User | None:
    """Delete a user."""
    user = get_by_id(db, user_id)
    if user:
        db.delete(user)
        db.flush()
    return user


{%- elif cookiecutter.use_jwt and cookiecutter.use_mongodb %}
"""User repository (MongoDB).

Contains only database operations. Business logic (password hashing,
validation) is handled by UserService in app/services/user.py.
"""

from app.db.models.user import User


async def get_by_id(user_id: str) -> User | None:
    """Get user by ID."""
    return await User.get(user_id)


async def get_by_email(email: str) -> User | None:
    """Get user by email."""
    return await User.find_one(User.email == email)


{%- if cookiecutter.enable_oauth %}


async def get_by_oauth(provider: str, oauth_id: str) -> User | None:
    """Get user by OAuth provider and ID."""
    return await User.find_one(User.oauth_provider == provider, User.oauth_id == oauth_id)
{%- endif %}


async def get_multi(
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """Get multiple users with pagination."""
    return await User.find_all().skip(skip).limit(limit).to_list()


async def create(
    *,
    email: str,
    hashed_password: str | None,
    full_name: str | None = None,
    is_active: bool = True,
    is_superuser: bool = False,
    role: str = "user",
{%- if cookiecutter.enable_oauth %}
    oauth_provider: str | None = None,
    oauth_id: str | None = None,
{%- endif %}
) -> User:
    """Create a new user.

    Note: Password should already be hashed by the service layer.
    """
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=is_active,
        is_superuser=is_superuser,
        role=role,
{%- if cookiecutter.enable_oauth %}
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
{%- endif %}
    )
    await user.insert()
    return user


async def update(
    *,
    db_user: User,
    update_data: dict,
) -> User:
    """Update a user.

    Note: If password needs updating, it should already be hashed.
    """
    for field, value in update_data.items():
        setattr(db_user, field, value)

    await db_user.save()
    return db_user


async def delete(user_id: str) -> User | None:
    """Delete a user."""
    user = await get_by_id(user_id)
    if user:
        await user.delete()
    return user


{%- else %}
"""User repository - not configured."""
{%- endif %}
