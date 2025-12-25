{%- if cookiecutter.enable_session_management and cookiecutter.use_jwt %}
{%- if cookiecutter.use_postgresql %}
"""Session service (PostgreSQL async)."""

import hashlib
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.db.models.session import Session
from app.repositories import session_repo


def _hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def _parse_user_agent(user_agent: str | None) -> tuple[str | None, str | None]:
    """Parse user agent to extract device name and type."""
    if not user_agent:
        return None, None

    user_agent_lower = user_agent.lower()

    # Detect device type
    if "mobile" in user_agent_lower or "android" in user_agent_lower:
        device_type = "mobile"
    elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
        device_type = "tablet"
    else:
        device_type = "desktop"

    # Extract browser/device name
    if "chrome" in user_agent_lower:
        device_name = "Chrome"
    elif "firefox" in user_agent_lower:
        device_name = "Firefox"
    elif "safari" in user_agent_lower:
        device_name = "Safari"
    elif "edge" in user_agent_lower:
        device_name = "Edge"
    else:
        device_name = "Unknown Browser"

    return device_name, device_type


class SessionService:
    """Service for session management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        user_id: UUID,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Session:
        """Create a new session for a user."""
        device_name, device_type = _parse_user_agent(user_agent)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

        return await session_repo.create(
            self.db,
            user_id=user_id,
            refresh_token_hash=_hash_token(refresh_token),
            expires_at=expires_at,
            device_name=device_name,
            device_type=device_type,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def get_user_sessions(self, user_id: UUID) -> list[Session]:
        """Get all active sessions for a user."""
        return await session_repo.get_user_sessions(self.db, user_id, active_only=True)

    async def validate_refresh_token(self, refresh_token: str) -> Session | None:
        """Validate a refresh token and return the session if valid."""
        token_hash = _hash_token(refresh_token)
        session = await session_repo.get_by_refresh_token_hash(self.db, token_hash)

        if session and session.expires_at > datetime.utcnow():
            await session_repo.update_last_used(self.db, session.id)
            return session

        return None

    async def logout_session(self, session_id: UUID, user_id: UUID) -> Session:
        """Logout a specific session."""
        session = await session_repo.get_by_id(self.db, session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError(message="Session not found")

        await session_repo.deactivate(self.db, session_id)
        return session

    async def logout_all_sessions(self, user_id: UUID) -> int:
        """Logout all sessions for a user. Returns count of logged out sessions."""
        return await session_repo.deactivate_all_user_sessions(self.db, user_id)

    async def logout_by_refresh_token(self, refresh_token: str) -> Session | None:
        """Logout session by refresh token."""
        token_hash = _hash_token(refresh_token)
        return await session_repo.deactivate_by_refresh_token_hash(self.db, token_hash)


{%- elif cookiecutter.use_sqlite %}
"""Session service (SQLite sync)."""

import hashlib
from datetime import datetime, timedelta

from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.db.models.session import Session
from app.repositories import session_repo


def _hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def _parse_user_agent(user_agent: str | None) -> tuple[str | None, str | None]:
    """Parse user agent to extract device name and type."""
    if not user_agent:
        return None, None

    user_agent_lower = user_agent.lower()

    # Detect device type
    if "mobile" in user_agent_lower or "android" in user_agent_lower:
        device_type = "mobile"
    elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
        device_type = "tablet"
    else:
        device_type = "desktop"

    # Extract browser/device name
    if "chrome" in user_agent_lower:
        device_name = "Chrome"
    elif "firefox" in user_agent_lower:
        device_name = "Firefox"
    elif "safari" in user_agent_lower:
        device_name = "Safari"
    elif "edge" in user_agent_lower:
        device_name = "Edge"
    else:
        device_name = "Unknown Browser"

    return device_name, device_type


class SessionService:
    """Service for session management."""

    def __init__(self, db: DBSession):
        self.db = db

    def create_session(
        self,
        user_id: str,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Session:
        """Create a new session for a user."""
        device_name, device_type = _parse_user_agent(user_agent)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

        return session_repo.create(
            self.db,
            user_id=user_id,
            refresh_token_hash=_hash_token(refresh_token),
            expires_at=expires_at,
            device_name=device_name,
            device_type=device_type,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def get_user_sessions(self, user_id: str) -> list[Session]:
        """Get all active sessions for a user."""
        return session_repo.get_user_sessions(self.db, user_id, active_only=True)

    def validate_refresh_token(self, refresh_token: str) -> Session | None:
        """Validate a refresh token and return the session if valid."""
        token_hash = _hash_token(refresh_token)
        session = session_repo.get_by_refresh_token_hash(self.db, token_hash)

        if session and session.expires_at > datetime.utcnow():
            session_repo.update_last_used(self.db, session.id)
            return session

        return None

    def logout_session(self, session_id: str, user_id: str) -> Session:
        """Logout a specific session."""
        session = session_repo.get_by_id(self.db, session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError(message="Session not found")

        session_repo.deactivate(self.db, session_id)
        return session

    def logout_all_sessions(self, user_id: str) -> int:
        """Logout all sessions for a user. Returns count of logged out sessions."""
        return session_repo.deactivate_all_user_sessions(self.db, user_id)

    def logout_by_refresh_token(self, refresh_token: str) -> Session | None:
        """Logout session by refresh token."""
        token_hash = _hash_token(refresh_token)
        return session_repo.deactivate_by_refresh_token_hash(self.db, token_hash)


{%- elif cookiecutter.use_mongodb %}
"""Session service (MongoDB)."""

import hashlib
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.db.models.session import Session
from app.repositories import session_repo


def _hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def _parse_user_agent(user_agent: str | None) -> tuple[str | None, str | None]:
    """Parse user agent to extract device name and type."""
    if not user_agent:
        return None, None

    user_agent_lower = user_agent.lower()

    # Detect device type
    if "mobile" in user_agent_lower or "android" in user_agent_lower:
        device_type = "mobile"
    elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
        device_type = "tablet"
    else:
        device_type = "desktop"

    # Extract browser/device name
    if "chrome" in user_agent_lower:
        device_name = "Chrome"
    elif "firefox" in user_agent_lower:
        device_name = "Firefox"
    elif "safari" in user_agent_lower:
        device_name = "Safari"
    elif "edge" in user_agent_lower:
        device_name = "Edge"
    else:
        device_name = "Unknown Browser"

    return device_name, device_type


class SessionService:
    """Service for session management."""

    async def create_session(
        self,
        user_id: str,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Session:
        """Create a new session for a user."""
        device_name, device_type = _parse_user_agent(user_agent)
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

        return await session_repo.create(
            user_id=user_id,
            refresh_token_hash=_hash_token(refresh_token),
            expires_at=expires_at,
            device_name=device_name,
            device_type=device_type,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def get_user_sessions(self, user_id: str) -> list[Session]:
        """Get all active sessions for a user."""
        return await session_repo.get_user_sessions(user_id, active_only=True)

    async def validate_refresh_token(self, refresh_token: str) -> Session | None:
        """Validate a refresh token and return the session if valid."""
        token_hash = _hash_token(refresh_token)
        session = await session_repo.get_by_refresh_token_hash(token_hash)

        if session and session.expires_at > datetime.now(UTC):
            await session_repo.update_last_used(str(session.id))
            return session

        return None

    async def logout_session(self, session_id: str, user_id: str) -> Session:
        """Logout a specific session."""
        session = await session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError(message="Session not found")

        await session_repo.deactivate(session_id)
        return session

    async def logout_all_sessions(self, user_id: str) -> int:
        """Logout all sessions for a user. Returns count of logged out sessions."""
        return await session_repo.deactivate_all_user_sessions(user_id)

    async def logout_by_refresh_token(self, refresh_token: str) -> Session | None:
        """Logout session by refresh token."""
        token_hash = _hash_token(refresh_token)
        return await session_repo.deactivate_by_refresh_token_hash(token_hash)


{%- endif %}
{%- else %}
"""Session service - not configured."""
{%- endif %}
