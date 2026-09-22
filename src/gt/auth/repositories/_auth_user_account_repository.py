from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gt.auth.models._auth_user_account_model import AuthUserAccountModelBase
from gt.exceptions import CreateException

TAccount = TypeVar("TAccount", bound=AuthUserAccountModelBase)


class AuthUserAccountRepository[TAccount: AuthUserAccountModelBase]:
    """Repository for managing auth user account persistence."""

    def __init__(self, session: AsyncSession, model: type[TAccount]):
        """Initialize the repository with a database session and model.

        Args:
            session: Async SQLAlchemy session.
            model: The AuthUserAccountModel class.
        """
        self.session = session
        self.model = model

    async def add(self, account: TAccount) -> TAccount:
        """Add a new account record to the database.

        Args:
            account: The account model instance to persist.

        Returns:
            The persisted account instance.
        """
        try:
            self.session.add(account)
            await self.session.flush()
            await self.session.refresh(account)
            return account
        except Exception as e:
            raise CreateException(
                error="Failed to add account to the database.",
                internal_details=str(e),
            ) from e

    async def get_by(self, **kwargs) -> TAccount | None:
        """Retrieve an account record by arbitrary filter criteria.

        Args:
            **kwargs: Filter keyword arguments passed to filter_by.

        Returns:
            The matching account instance or None.
        """
        try:
            stmt = select(self.model).filter_by(**kwargs)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise CreateException(
                error="Failed to retrieve account from the database.",
                internal_details=str(e),
            ) from e

    async def update(self, account: TAccount) -> TAccount:
        """Update an existing account record in the database.

        Args:
            account: The account model instance to update.

        Returns:
            The updated account instance.
        """
        try:
            await self.session.flush()
            await self.session.refresh(account)
            return account
        except Exception as e:
            raise CreateException(
                error="Failed to update account in the database.",
                internal_details=str(e),
            ) from e
