from typing import Any, Literal, cast

from sqlalchemy.ext.asyncio import AsyncSession

from gt.auth.models._auth_user_account_model import AuthUserAccountModelBase
from gt.auth.repositories._auth_user_account_repository import TAccount
from gt.exceptions import ConflictException, DomainException

from ..repositories import AuthUserAccountRepository
from .hash._hash_service import HasherService

ACCOUNT_TYPE_LITERAL = Literal["credentials", "oauth"]


class AuthUserAccountService[TAccount: AuthUserAccountModelBase]:
    """Service for managing auth user account operations."""

    def __init__(
        self,
        repository: AuthUserAccountRepository[TAccount],
        hash_service: HasherService,
        model: type[TAccount],
    ):
        """Initialize the service with a repository and model.

        Args:
            repository: The AuthUserAccountRepository instance.
            model: The AuthUserAccountModel class.
        """
        self._repository = repository
        self._hash_service = hash_service
        self._model = model

    async def create_account(
        self,
        user_id: int,
        type: ACCOUNT_TYPE_LITERAL,
        password: str | None = None,
        provider: str | None = None,
    ) -> TAccount:
        """Create a new user account.

        Args:
            account: The account model instance to create.

        Returns:
            The created account instance.

        Raises:
            ConflictException: If an account with the same uuid already exists.
            DomainException: On unexpected failures.
        """
        try:
            existing_user = await self._repository.get_by(user_id=user_id, type=type)
            if existing_user:
                raise ConflictException(
                    error=f"User Account with user_id '{user_id}' already exists.",
                )

            hashed_password = None
            if password:
                hashed_password = self._hash_service.hash(password)

            model_cls = cast("type[Any]", self._model)
            account = model_cls(
                user_id=user_id,
                type=type,
                hashed_password=hashed_password,
                provider=provider,
            )

            return await self._repository.add(account)
        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to create account.",
                internal_details=str(e),
            ) from e

    async def get_account_by(self, **kwargs) -> TAccount | None:
        """Retrieve an account by filter criteria.

        Args:
            **kwargs: Filter keyword arguments.

        Returns:
            The matching account instance or None.

        Raises:
            DomainException: On unexpected failures.
        """
        try:
            return await self._repository.get_by(**kwargs)
        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to retrieve account.",
                internal_details=str(e),
            ) from e

    async def update_account(self, account: TAccount) -> TAccount:
        """Update an existing account.

        Args:
            account: The account model instance with modified attributes.

        Returns:
            The updated account instance.

        Raises:
            DomainException: On unexpected failures.
        """
        try:
            return await self._repository.update(account)
        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to update account.",
                internal_details=str(e),
            ) from e


def get_auth_user_account_service(
    session: AsyncSession, model: type[TAccount]
) -> AuthUserAccountService:
    """Factory function to create an AuthUserAccountService instance.

    Args:
        session: Async SQLAlchemy session.
        model: The AuthUserAccountModel class.

    Returns:
        A configured AuthUserAccountService.
    """
    repository = AuthUserAccountRepository(session=session, model=model)
    hasher = HasherService()
    return AuthUserAccountService(
        repository=repository, model=model, hash_service=hasher
    )
