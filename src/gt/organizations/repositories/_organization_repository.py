from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gt.exceptions import CreateException
from gt.organizations.models import OrganizationModel

TOrganization = TypeVar("TOrganization", bound=OrganizationModel)


class OrganizationRepository[TOrganization: OrganizationModel]:
    """Repository for managing organization persistence."""

    def __init__(self, session: AsyncSession, model: type[TOrganization]):
        """Initialize the repository with a database session and model.

        Args:
            session: Async SQLAlchemy session.
            model: The OrganizationModel class.
        """
        self.session = session
        self.model = model

    async def add(self, organization: TOrganization) -> TOrganization:
        """Add a new organization record to the database.

        Args:
            organization: The organization model instance to persist.

        Returns:
            The persisted organization instance.
        """
        try:
            self.session.add(organization)
            await self.session.flush()
            await self.session.refresh(organization)
            return organization
        except Exception as e:
            raise CreateException(
                error="Failed to add organization to the database.",
                internal_details=str(e),
            ) from e

    async def get_by(self, **kwargs) -> TOrganization | None:
        """Retrieve an organization record by arbitrary filter criteria.

        Args:
            **kwargs: Filter keyword arguments passed to filter_by.

        Returns:
            The matching organization instance or None.
        """
        try:
            stmt = select(self.model).filter_by(**kwargs)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise CreateException(
                error="Failed to retrieve organization from the database.",
                internal_details=str(e),
            ) from e

    async def get_first(self) -> TOrganization | None:
        """Retrieve the first organization record in the database.

        Returns:
            The first organization instance or None when none exist.
        """
        try:
            stmt = select(self.model).limit(1)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise CreateException(
                error="Failed to retrieve organization from the database.",
                internal_details=str(e),
            ) from e

    async def update(self, organization: TOrganization) -> TOrganization:
        """Update an existing organization record in the database.

        Args:
            organization: The organization model instance to update.

        Returns:
            The updated organization instance.
        """
        try:
            await self.session.flush()
            await self.session.refresh(organization)
            return organization
        except Exception as e:
            raise CreateException(
                error="Failed to update organization in the database.",
                internal_details=str(e),
            ) from e

    async def filter_by(self, **kwargs) -> list[TOrganization]:
        """Filter organization records by arbitrary criteria.

        Args:
            **kwargs: Filter keyword arguments passed to filter_by.

        Returns:
            A list of matching organization instances.
        """
        try:
            stmt = select(self.model).filter_by(**kwargs)
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            raise CreateException(
                error="Failed to filter organizations from the database.",
                internal_details=str(e),
            ) from e
