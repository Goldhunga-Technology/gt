from collections.abc import AsyncGenerator, Callable

from pydantic.main import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from gt.auth.events import event_bus
from gt.auth.models._auth_user_model import TUser
from gt.organizations.models import (
    OrganizationMemberModelBase,
    OrganizationModel,
    TOrganization,
    TOrganizationMember,
    create_organization_member_model,
    create_organization_model,
)
from gt.organizations.schemas import OrganizationCreateSchema
from gt.organizations.services._service_registry import OrganizationServiceRegistry


class Organizations:
    """
    This class is responsible for wiring organization models, services and
    routers onto the application.
    """

    def __init__(
        self,
        *,
        base: type[DeclarativeBase],
        session_factory: async_sessionmaker[AsyncSession],
        user_model: type[TUser],
        organization_model: type[TOrganization] | None = None,
        organization_member_model: type[TOrganizationMember] | None = None,
        organization_create_schema: type[BaseModel] | None = None,
        current_user: Callable | None = None,
    ):
        """
        Initializes the Organizations class.

        Args:
            base: The declarative base class (SQLAlchemy or SQLModel).
            session_factory: The application's async session factory.
            user_model: The concrete user model class.
            organization_model: An optional custom organization model base.
            organization_member_model: An optional custom organization member model base.
            organization_create_schema: An optional custom create schema.
            current_user: A FastAPI dependency that resolves the current authenticated user.
        """
        self.session_factory = session_factory
        self.user_model = user_model

        ## models
        self.organization_model = create_organization_model(
            base=base,
            user_model=user_model,
            model=organization_model or OrganizationModel,
        )
        self.organization_member_model = create_organization_member_model(
            base=base,
            user_model=user_model,
            organization_model=self.organization_model,
            model=organization_member_model or OrganizationMemberModelBase,
        )

        ## schemas
        self.organization_create_schema = (
            organization_create_schema or OrganizationCreateSchema
        )

        ## dependencies
        self.current_user = current_user

        ## event bus
        self.event_bus = event_bus

    def init_app(self, app):
        """
        Initializes the FastAPI application with organization routes.
        """
        self._register_routers(app)

    def on(self, event_type: type):
        """
        Registers an event handler for a specific event type.

        :param event_type: The type of the event to listen for.
        """

        def decorator(handler):
            self.event_bus.register(event_type, handler)
            return handler

        return decorator

    def get_services(self, session: AsyncSession) -> OrganizationServiceRegistry:
        """
        Builds a per-session OrganizationServiceRegistry with the
        organization models pre-wired.

        Access any organization service as an attribute of the returned
        registry, e.g. ``organizations.get_services(session).organization``
        or ``.member``.
        """
        return OrganizationServiceRegistry(
            session=session,
            organization_model=self.organization_model,
            member_model=self.organization_member_model,
        )

    async def get_db_session(self) -> AsyncGenerator[AsyncSession]:
        """
        Provides a database session for use in the application.
        """
        async with self.session_factory() as session:
            yield session

    def _register_routers(self, app):
        """
        Registers organization-related routers to the FastAPI application.
        """
        from gt.organizations.routers import create_organizations_router

        app.include_router(create_organizations_router(organizations=self))
