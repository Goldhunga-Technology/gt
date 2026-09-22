from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from gt.auth.models._auth_user_tokens_model import AuthUserTokensModelBase
from gt.auth.repositories._auth_user_tokens_repository import TToken
from gt.exceptions import DomainException

from ..repositories import AuthUserTokensRepository

AUTH_TOKEN_TYPE_LITERAL = Literal["password_reset", "email_verification"]


class AuthUserTokensService[TToken: AuthUserTokensModelBase]:
    """Service for managing auth user token operations."""

    def __init__(
        self, repository: AuthUserTokensRepository[TToken], model: type[TToken]
    ):
        """Initialize the service with a repository and model.

        Args:
            repository: The AuthUserTokensRepository instance.
            model: The AuthUserTokensModel class.
        """
        self._repository = repository
        self._model = model

    async def create_token(
        self,
        user_id: int,
        type: AUTH_TOKEN_TYPE_LITERAL,
        token_hash: str,
        expires_at,
    ) -> TToken:
        """Create a new user token.

        Args:
            user_id: The user ID.
            type: The token type.
            token_hash: The hashed token value.
            expires_at: The expiration datetime.

        Returns:
            The created token instance.

        Raises:
            DomainException: On unexpected failures.
        """
        try:
            token = self._model(
                user_id=user_id,
                type=type,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            return await self._repository.add(token)

        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to create token.",
                internal_details=str(e),
            ) from e

    async def update_token(self, token: TToken) -> TToken:
        """Update an existing token record.

        Args:
            token: The token model instance with modified attributes.

        Returns:
            The updated token instance.

        Raises:
            DomainException: On unexpected failures.
        """
        try:
            return await self._repository.update(token)
        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to update token.",
                internal_details=str(e),
            ) from e

    async def get_token_by(self, **kwargs) -> TToken | None:
        """Retrieve a token by filter criteria.

        Args:
            **kwargs: Filter keyword arguments.

        Returns:
            The matching token instance or None.

        Raises:
            DomainException: On unexpected failures.
        """
        try:
            return await self._repository.get_by(**kwargs)
        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to retrieve token.",
                internal_details=str(e),
            ) from e

    async def get_tokens_by(self, **kwargs) -> list[TToken]:
        """Retrieve tokens matching the filter criteria.

        Args:
            **kwargs: Filter keyword arguments.

        Returns:
            A list of matching token instances.

        Raises:
            DomainException: On unexpected failures.
        """
        try:
            return await self._repository.filter_by(**kwargs)
        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to retrieve tokens.",
                internal_details=str(e),
            ) from e

    async def delete_tokens_by(self, **kwargs) -> None:
        """Delete tokens matching the filter criteria.

        Args:
            **kwargs: Filter keyword arguments.

        Raises:
            DomainException: On unexpected failures.
        """
        try:
            await self._repository.delete_by(**kwargs)
        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to delete tokens.",
                internal_details=str(e),
            ) from e


def get_auth_user_tokens_service(
    session: AsyncSession, model: type[TToken]
) -> AuthUserTokensService:
    """Factory function to create an AuthUserTokensService instance.

    Args:
        session: Async SQLAlchemy session.
        model: The AuthUserTokensModel class.

    Returns:
        A configured AuthUserTokensService.
    """
    repository = AuthUserTokensRepository(session=session, model=model)
    return AuthUserTokensService(repository=repository, model=model)
