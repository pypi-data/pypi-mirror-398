{%- if cookiecutter.use_jwt and cookiecutter.use_postgresql %}
"""User service (PostgreSQL async).

Contains business logic for user operations. Uses UserRepository for database access.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError, AuthenticationError, NotFoundError
from app.core.security import get_password_hash, verify_password
from app.db.models.user import User
from app.repositories import user_repo
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for user-related business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> User:
        """Get user by ID.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = await user_repo.get_by_id(self.db, user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": user_id},
            )
        return user

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email. Returns None if not found."""
        return await user_repo.get_by_email(self.db, email)

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Get multiple users with pagination."""
        return await user_repo.get_multi(self.db, skip=skip, limit=limit)

    async def register(self, user_in: UserCreate) -> User:
        """Register a new user.

        Raises:
            AlreadyExistsError: If email is already registered.
        """
        existing = await user_repo.get_by_email(self.db, user_in.email)
        if existing:
            raise AlreadyExistsError(
                message="Email already registered",
                details={"email": user_in.email},
            )

        hashed_password = get_password_hash(user_in.password)
        return await user_repo.create(
            self.db,
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role.value,
        )

    async def authenticate(self, email: str, password: str) -> User:
        """Authenticate user by email and password.

        Raises:
            AuthenticationError: If credentials are invalid or user is inactive.
        """
        user = await user_repo.get_by_email(self.db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError(message="Invalid email or password")
        if not user.is_active:
            raise AuthenticationError(message="User account is disabled")
        return user

    async def update(self, user_id: UUID, user_in: UserUpdate) -> User:
        """Update user.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = await self.get_by_id(user_id)

        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        return await user_repo.update(self.db, db_user=user, update_data=update_data)

    async def delete(self, user_id: UUID) -> User:
        """Delete user.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = await user_repo.delete(self.db, user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": str(user_id)},
            )
        return user

{%- if cookiecutter.enable_oauth %}

    async def get_by_oauth(self, provider: str, oauth_id: str) -> User | None:
        """Get user by OAuth provider and ID."""
        return await user_repo.get_by_oauth(self.db, provider, oauth_id)

    async def link_oauth(self, user_id: UUID, provider: str, oauth_id: str) -> User:
        """Link OAuth account to existing user."""
        user = await self.get_by_id(user_id)
        return await user_repo.update(
            self.db,
            db_user=user,
            update_data={"oauth_provider": provider, "oauth_id": oauth_id},
        )

    async def create_oauth_user(
        self,
        email: str,
        full_name: str | None,
        oauth_provider: str,
        oauth_id: str,
    ) -> User:
        """Create a new user from OAuth data."""
        return await user_repo.create(
            self.db,
            email=email,
            hashed_password=None,
            full_name=full_name,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
        )
{%- endif %}


{%- elif cookiecutter.use_jwt and cookiecutter.use_sqlite %}
"""User service (SQLite sync).

Contains business logic for user operations. Uses UserRepository for database access.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import AlreadyExistsError, AuthenticationError, NotFoundError
from app.core.security import get_password_hash, verify_password
from app.db.models.user import User
from app.repositories import user_repo
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for user-related business logic."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> User:
        """Get user by ID.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = user_repo.get_by_id(self.db, user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": user_id},
            )
        return user

    def get_by_email(self, email: str) -> User | None:
        """Get user by email. Returns None if not found."""
        return user_repo.get_by_email(self.db, email)

    def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Get multiple users with pagination."""
        return user_repo.get_multi(self.db, skip=skip, limit=limit)

    def register(self, user_in: UserCreate) -> User:
        """Register a new user.

        Raises:
            AlreadyExistsError: If email is already registered.
        """
        existing = user_repo.get_by_email(self.db, user_in.email)
        if existing:
            raise AlreadyExistsError(
                message="Email already registered",
                details={"email": user_in.email},
            )

        hashed_password = get_password_hash(user_in.password)
        return user_repo.create(
            self.db,
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role.value,
        )

    def authenticate(self, email: str, password: str) -> User:
        """Authenticate user by email and password.

        Raises:
            AuthenticationError: If credentials are invalid or user is inactive.
        """
        user = user_repo.get_by_email(self.db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError(message="Invalid email or password")
        if not user.is_active:
            raise AuthenticationError(message="User account is disabled")
        return user

    def update(self, user_id: str, user_in: UserUpdate) -> User:
        """Update user.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = self.get_by_id(user_id)

        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        return user_repo.update(self.db, db_user=user, update_data=update_data)

    def delete(self, user_id: str) -> User:
        """Delete user.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = user_repo.delete(self.db, user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": user_id},
            )
        return user

{%- if cookiecutter.enable_oauth %}

    def get_by_oauth(self, provider: str, oauth_id: str) -> User | None:
        """Get user by OAuth provider and ID."""
        return user_repo.get_by_oauth(self.db, provider, oauth_id)

    def link_oauth(self, user_id: str, provider: str, oauth_id: str) -> User:
        """Link OAuth account to existing user."""
        user = self.get_by_id(user_id)
        return user_repo.update(
            self.db,
            db_user=user,
            update_data={"oauth_provider": provider, "oauth_id": oauth_id},
        )

    def create_oauth_user(
        self,
        email: str,
        full_name: str | None,
        oauth_provider: str,
        oauth_id: str,
    ) -> User:
        """Create a new user from OAuth data."""
        return user_repo.create(
            self.db,
            email=email,
            hashed_password=None,
            full_name=full_name,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
        )
{%- endif %}


{%- elif cookiecutter.use_jwt and cookiecutter.use_mongodb %}
"""User service (MongoDB).

Contains business logic for user operations. Uses UserRepository for database access.
"""

from app.core.exceptions import AlreadyExistsError, AuthenticationError, NotFoundError
from app.core.security import get_password_hash, verify_password
from app.db.models.user import User
from app.repositories import user_repo
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for user-related business logic."""

    async def get_by_id(self, user_id: str) -> User:
        """Get user by ID.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": user_id},
            )
        return user

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email. Returns None if not found."""
        return await user_repo.get_by_email(email)

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Get multiple users with pagination."""
        return await user_repo.get_multi(skip=skip, limit=limit)

    async def register(self, user_in: UserCreate) -> User:
        """Register a new user.

        Raises:
            AlreadyExistsError: If email is already registered.
        """
        existing = await user_repo.get_by_email(user_in.email)
        if existing:
            raise AlreadyExistsError(
                message="Email already registered",
                details={"email": user_in.email},
            )

        hashed_password = get_password_hash(user_in.password)
        return await user_repo.create(
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role.value,
        )

    async def authenticate(self, email: str, password: str) -> User:
        """Authenticate user by email and password.

        Raises:
            AuthenticationError: If credentials are invalid or user is inactive.
        """
        user = await user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError(message="Invalid email or password")
        if not user.is_active:
            raise AuthenticationError(message="User account is disabled")
        return user

    async def update(self, user_id: str, user_in: UserUpdate) -> User:
        """Update user.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = await self.get_by_id(user_id)

        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        return await user_repo.update(db_user=user, update_data=update_data)

    async def delete(self, user_id: str) -> User:
        """Delete user.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = await user_repo.delete(user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": user_id},
            )
        return user

{%- if cookiecutter.enable_oauth %}

    async def get_by_oauth(self, provider: str, oauth_id: str) -> User | None:
        """Get user by OAuth provider and ID."""
        return await user_repo.get_by_oauth(provider, oauth_id)

    async def link_oauth(self, user_id: str, provider: str, oauth_id: str) -> User:
        """Link OAuth account to existing user."""
        user = await self.get_by_id(user_id)
        return await user_repo.update(
            db_user=user,
            update_data={"oauth_provider": provider, "oauth_id": oauth_id},
        )

    async def create_oauth_user(
        self,
        email: str,
        full_name: str | None,
        oauth_provider: str,
        oauth_id: str,
    ) -> User:
        """Create a new user from OAuth data."""
        return await user_repo.create(
            email=email,
            hashed_password=None,
            full_name=full_name,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
        )
{%- endif %}


{%- else %}
"""User service - not configured."""
{%- endif %}
