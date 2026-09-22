from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gt.auth.models._auth_user_tokens_model import AuthUserTokensModelBase
from gt.exceptions import CreateException

TToken = TypeVar("TToken", bound=AuthUserTokensModelBase)


class AuthUserTokensRepository[TToken: AuthUserTokensModelBase]:
    """Repository for managing auth user token persistence."""

    def __init__(self, session: AsyncSession, model: type[TToken]):
        """Initialize the repository with a database session and model.

        Args:
            session: Async SQLAlchemy session.
            model: The AuthUserTokensModel class.
        """
        self.session = session
        self.model = model

    async def add(self, token: TToken) -> TToken:
        """Add a new token record to the database.

        Args:
            token: The token model instance to persist.

        Returns:
            The persisted token instance.
        """
        try:
            self.session.add(token)
            await self.session.flush()
            await self.session.refresh(token)
            return token
        except Exception as e:
            raise CreateException(
                error="Failed to add token to the database.",
                internal_details=str(e),
            ) from e

    async def update(self, token: TToken) -> TToken:
        """Update an existing token record in the database.

        Args:
            token: The token model instance to update.

        Returns:
            The updated token instance.
        """
        try:
            await self.session.flush()
            await self.session.refresh(token)
            return token
        except Exception as e:
            raise CreateException(
                error="Failed to update token in the database.",
                internal_details=str(e),
            ) from e

    async def get_by(self, **kwargs) -> TToken | None:
        """Retrieve a token record by arbitrary filter criteria.

        Args:
            **kwargs: Filter keyword arguments passed to filter_by.

        Returns:
            The matching token instance or None.
        """
        try:
            stmt = select(self.model).filter_by(**kwargs)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise CreateException(
                error="Failed to retrieve token from the database.",
                internal_details=str(e),
            ) from e

    async def filter_by(self, **kwargs) -> list[TToken]:
        """Filter token records by arbitrary criteria.

        Args:
            **kwargs: Keyword arguments passed to filter_by.

        Returns:
            A list of matching token instances.
        """
        try:
            stmt = select(self.model).filter_by(**kwargs)
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            raise CreateException(
                error="Failed to filter tokens from the database.",
                internal_details=str(e),
            ) from e

    async def delete_by(self, **kwargs) -> None:
        """Delete token records matching the filter criteria.

        Args:
            **kwargs: Keyword arguments passed to filter_by.
        """
        try:
            stmt = select(self.model).filter_by(**kwargs)
            result = await self.session.execute(stmt)
            tokens_to_delete = result.scalars().all()
            for token in tokens_to_delete:
                await self.session.delete(token)
            await self.session.flush()
        except Exception as e:
            raise CreateException(
                error="Failed to delete token(s) from the database.",
                internal_details=str(e),
            ) from e
