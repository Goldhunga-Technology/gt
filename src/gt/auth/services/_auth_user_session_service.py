from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from gt.auth.models._auth_user_session_model import AuthUserSessionModelBase
from gt.auth.repositories._auth_user_session_repository import TSession
from gt.exceptions import DomainException

from ..repositories import AuthUserSessionRepository


class AuthUserSessionService[TSession: AuthUserSessionModelBase]:
    """Service for managing auth user session operations."""

    def __init__(
        self, repository: AuthUserSessionRepository[TSession], model: type[TSession]
    ):
        """Initialize the service with a repository and model.

        Args:
            repository: The AuthUserSessionRepository instance.
            model: The AuthUserSessionModel class.
        """
        self._repository = repository
        self._model = model

    async def create_session(
        self,
        user_id: int,
        expire_minutes: int,
        device: str,
        ip_address: str,
        browser: str,
    ) -> TSession:
        """Create a new user session.

        Args:
            session_record: The session model instance to create.

        Returns:
            The created session instance.

        Raises:
            ConflictException: If a session with the same uuid already exists.
            DomainException: On unexpected failures.
        """
        try:
            session = self._model(
                user_id=user_id,
                expires_at=datetime.now(UTC) + timedelta(minutes=expire_minutes),
                device=device,
                ip_address=ip_address,
                browser=browser,
            )
            return await self._repository.add(session)

        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to create session.",
                internal_details=str(e),
            ) from e

    async def get_session_by(self, **kwargs) -> TSession | None:
        """Retrieve a session by filter criteria.

        Args:
            **kwargs: Filter keyword arguments.

        Returns:
            The matching session instance or None.

        Raises:
            DomainException: On unexpected failures.
        """
        try:
            return await self._repository.get_by(**kwargs)
        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to retrieve session.",
                internal_details=str(e),
            ) from e

    async def list_sessions_by_user(self, user_id: int) -> list[TSession]:
        """List all sessions for a given user.

        Args:
            user_id: The ID of the user.
        """
        try:
            return await self._repository.filter_by(user_id=user_id)
        except Exception as e:
            raise DomainException(
                error="Failed to list sessions for user.",
                internal_details=str(e),
            ) from e

    async def invalidate_user_sessions(self, user_id: int) -> None:
        """Invalidate all active sessions belonging to a user.

        Args:
            user_id: The ID of the user whose sessions should be revoked.

        Raises:
            DomainException: On unexpected failures.
        """
        try:
            sessions = await self.list_sessions_by_user(user_id)
            for session in sessions:
                if session.is_active:
                    session.revoke()
                    await self._repository.update(session)
        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to invalidate user sessions.",
                internal_details=str(e),
            ) from e

    async def invalidate_session(self, session_uuid: str) -> None:
        """Invalidate a session by its UUID.

        Args:
            session_uuid: The UUID of the session to invalidate.

        Raises:
            DomainException: On unexpected failures.
        """
        try:
            session = await self.get_session_by(uuid=session_uuid)
            if not session:
                raise DomainException(
                    error="Session not found.",
                    internal_details=f"No session found with uuid: {session_uuid}",
                )
            if not session.is_active:
                raise DomainException(
                    error="Session is already inactive.",
                    internal_details=f"Session with uuid: {session_uuid} is already inactive.",
                )

            session.revoke()
            await self._repository.update(session)
        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to invalidate session.",
                internal_details=str(e),
            ) from e


def get_auth_user_session_service(
    session: AsyncSession, model: type[TSession]
) -> AuthUserSessionService:
    """Factory function to create an AuthUserSessionService instance.

    Args:
        session: Async SQLAlchemy session.
        model: The AuthUserSessionModel class.

    Returns:
        A configured AuthUserSessionService.
    """
    repository = AuthUserSessionRepository(session=session, model=model)
    return AuthUserSessionService(repository=repository, model=model)
