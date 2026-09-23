import inspect
from collections.abc import AsyncGenerator
from functools import wraps
from typing import Any, Literal

from fastapi import Depends, FastAPI, Request
from pydantic.main import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from gt.auth.dependencies._guards._require_access_guard import require_access
from gt.auth.interfaces._policy_check_interface import IPolicyCheck
from gt.auth.models._auth_user_account_model import create_auth_user_account_model
from gt.auth.models._auth_user_model import create_auth_user_model
from gt.auth.models._auth_user_onboarding_model import (
    TOnboarding,
    create_auth_user_onboarding_model,
)
from gt.auth.models._auth_user_session_model import create_auth_user_session_model
from gt.auth.models._auth_user_tokens_model import create_auth_user_tokens_model
from gt.auth.schemas._auth_onboarding_schemas import AuthOnboardingRegisterSchema
from gt.auth.schemas._auth_schemas import AuthUserRegisterSchema
from gt.auth.settings import AuthSettings
from gt.exceptions._base_exceptions import InvalidException

from .events import event_bus
from .models import AuthUserModel, AuthUserOnboardingModelBase
from .routers import create_auth_router
from .services import ServiceRegistry

_POLICY_CHECKS_LITERAL = Literal["mfa_required", "email_verified", "onboarded"]

_CHECK_TO_GUARD_ARG: dict[_POLICY_CHECKS_LITERAL, Any] = {
    "mfa_required": {"mfa_required": True},
    "email_verified": {"email_verified": True},
    "onboarded": {"onboarded": True},
}


class Auth[TUser: AuthUserModel]:
    """
    This class is responsible for handling authentication and authorization in the application.
    """

    def __init__(
        self,
        *,
        base: type[DeclarativeBase],
        session_factory: async_sessionmaker[AsyncSession],
        settings: AuthSettings | None = None,
        user_model: type[TUser] | None = None,
        user_onboarding_model: type[TOnboarding] | None = None,
        user_register_schema: type[BaseModel] | None = None,
        onboarding_register_schema: type[AuthOnboardingRegisterSchema] | None = None,
    ):
        """
        Initializes the Auth class.
        """
        self.session_factory = session_factory

        ## setting
        self.settings = settings or AuthSettings()

        ## models
        self.user_model = create_auth_user_model(
            base=base, model=user_model or AuthUserModel
        )
        self.user_onboarding_model = create_auth_user_onboarding_model(
            base=base,
            user_model=self.user_model,
            model=user_onboarding_model or AuthUserOnboardingModelBase,
        )
        self.user_account_model = create_auth_user_account_model(
            base=base, UserModel=self.user_model
        )
        self.user_session_model = create_auth_user_session_model(
            base=base, UserModel=self.user_model
        )
        self.user_tokens_model = create_auth_user_tokens_model(
            base=base, UserModel=self.user_model
        )

        ## schemas
        self.onboarding_register_schema = (
            onboarding_register_schema or AuthOnboardingRegisterSchema
        )
        self.user_register_schema = user_register_schema or AuthUserRegisterSchema
        self.event_bus = event_bus

        ## policies
        self._policies: dict[str, Any] = {}
        self._checks: dict[str, IPolicyCheck] = {}

    def init_app(self, app: FastAPI):
        """
        Initializes the FastAPI application with authentication routes and dependencies.
        """
        self._register_routers(app)
        self._register_exceptions(app)
        self._register_middlewares(app)

    ## ----------------------------------------------- Decorators ----------------------------------------------- ##
    def on(self, event_type: type):
        """
        Registers an event handler for a specific event type.

        :param event_type: The type of the event to listen for.
        """

        def decorator(handler):
            self.event_bus.register(event_type, handler)
            return handler

        return decorator

    def policy(self, name: str):
        """
        Decorator to enforce a policy on a route.
        """

        def decorator(func):
            checks = self._policies.get(name, None)
            if checks is None:
                raise ValueError(f"Policy '{name}' is not registered.")

            kwargs = {}
            custom_checks = []
            for c in checks:
                if c in _CHECK_TO_GUARD_ARG:
                    kwargs.update(_CHECK_TO_GUARD_ARG[c])
                elif c in self._checks:
                    custom_checks.append(c)
                else:
                    raise ValueError(f"Unknown policy check '{c}' in policy '{name}'.")

            guard = Depends(
                require_access(auth=self, custom_checks=custom_checks, **kwargs)
            )

            sig = inspect.signature(func)
            guard_param = inspect.Parameter(
                "_policy_guard",
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=guard,
            )
            func.__signature__ = sig.replace(
                parameters=[*sig.parameters.values(), guard_param]
            )

            @wraps(func)
            async def wrapper(*args, **kwargs):
                kwargs.pop("_policy_guard", None)
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    ## ----------------------------------------------- Dependencies ----------------------------------------------- ##

    def current_user(
        self,
    ):
        """
        Dependency function to retrieve the current authenticated user.
        """

        async def dependency(
            request: Request,
            session: AsyncSession = Depends(self.get_db_session),
        ):

            from gt.auth.dependencies._current_user import current_user

            session_uuid = request.cookies.get("session_uuid")
            if not session_uuid:
                raise InvalidException(
                    error="Session UUID cookie is missing. Please log in again.",
                )

            return await current_user(
                auth=self,
                session=session,
                session_uuid=session_uuid,
            )

        return dependency

    def current_session(
        self,
    ):
        """
        Dependency function to retrieve the current authenticated session.
        """

        async def dependency(
            request: Request,
            session: AsyncSession = Depends(self.get_db_session),
        ):

            from gt.auth.dependencies._current_session import current_session

            session_uuid = request.cookies.get("session_uuid")
            if not session_uuid:
                raise InvalidException(
                    error="Session UUID cookie is missing. Please log in again.",
                )

            return await current_session(
                auth=self,
                session=session,
                session_uuid=session_uuid,
            )

        return dependency

    ## ----------------------------------------------- Policies ----------------------------------------------- ##

    def register_policy(self, *, name: str, checks: list[_POLICY_CHECKS_LITERAL]):
        """
        Registers a policy with the given name and checks.
        """
        if name in self._policies:
            raise ValueError(f"Policy '{name}' is already registered.")
        self._policies[name] = checks

    def register_check(self, *, name: str, check: IPolicyCheck):
        """
        Registers a custom policy check under the given name.

        Custom checks implement the :class:`IPolicyCheck` port and can be
        referenced in any policy's ``checks`` list alongside the built-in
        checks (``mfa_required``, ``email_verified``, ``onboarded``).
        """
        if name in _CHECK_TO_GUARD_ARG:
            raise ValueError(f"Policy check '{name}' shadows a built-in check.")
        if name in self._checks:
            raise ValueError(f"Policy check '{name}' is already registered.")
        if not isinstance(check, IPolicyCheck):
            raise TypeError(
                "Policy check must implement the IPolicyCheck interface (port)."
            )
        self._checks[name] = check

    ## ----------------------------------------------- Session Methods ----------------------------------------------- ##

    def get_services(self, session: AsyncSession) -> ServiceRegistry:
        """
        Builds a per-session ServiceRegistry with all auth models pre-wired.

        Access any auth service as an attribute of the returned registry, e.g.
        ``auth.get_services(session).user`` or ``.login``.
        """
        return ServiceRegistry(
            session=session,
            user_model=self.user_model,
            account_model=self.user_account_model,
            session_model=self.user_session_model,
            token_model=self.user_tokens_model,
            onboarding_model=self.user_onboarding_model,
            settings=self.settings,
        )

    async def get_db_session(self) -> AsyncGenerator[AsyncSession]:
        """
        Provides a database session for use in the application.
        """
        async with self.session_factory() as session:
            yield session

    ## ----------------------------------------------- Internal Methods ----------------------------------------------- ##

    def _register_routers(self, app: FastAPI):
        """
        Registers authentication-related routers to the FastAPI application.
        """
        routers = create_auth_router(auth=self)
        app.include_router(routers)

    def _register_exceptions(self, app: FastAPI):
        """
        Registers custom exception handlers to the FastAPI application.
        """
        from gt.exceptions import add_exceptions_handler

        add_exceptions_handler(app)

    def _register_middlewares(self, app: FastAPI):
        """
        Registers custom middlewares to the FastAPI application.
        """
        from starlette.middleware.sessions import SessionMiddleware

        app.add_middleware(
            SessionMiddleware,
            secret_key="secret key",
            same_site="none",
            # https_only=config.APP_URL.startswith("https"),
        )
