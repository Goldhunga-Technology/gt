from functools import cached_property
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from gt.auth.settings import AuthSettings

from ..models._auth_user_account_model import AuthUserAccountModelBase
from ..models._auth_user_model import AuthUserModel
from ..models._auth_user_onboarding_model import AuthUserOnboardingModelBase
from ..models._auth_user_session_model import AuthUserSessionModelBase
from ..models._auth_user_tokens_model import AuthUserTokensModelBase
from ._auth_email_service import get_auth_email_service
from ._auth_login_service import get_auth_login_service
from ._auth_oauth_service import get_auth_oauth_service
from ._auth_password_service import get_auth_password_service
from ._auth_user_account_service import get_auth_user_account_service
from ._auth_user_onboarding_service import get_auth_user_onboarding_service
from ._auth_user_service import get_auth_user_service
from ._auth_user_session_service import get_auth_user_session_service
from ._auth_user_tokens_service import get_auth_user_tokens_service


class ServiceRegistry:
    """
    Per-session access to every auth service with the models pre-wired.

    Build one per request via ``auth.get_services(session)`` and access the
    services you need as attributes. Each service is created lazily and
    cached for the lifetime of the registry.
    """

    def __init__(
        self,
        *,
        session: AsyncSession,
        user_model: type[AuthUserModel],
        account_model: type[AuthUserAccountModelBase],
        session_model: type[AuthUserSessionModelBase],
        token_model: type[AuthUserTokensModelBase],
        onboarding_model: type[AuthUserOnboardingModelBase],
        settings: AuthSettings,
    ):
        self._session = session
        self._user_model = user_model
        self._account_model = account_model
        self._session_model = session_model
        self._token_model = token_model
        self._onboarding_model = onboarding_model
        self._settings = settings

    @cached_property
    def user(self):
        """Service for creating, updating and deactivating users."""
        return get_auth_user_service(
            session=self._session,
            user_model=self._user_model,
            account_model=self._account_model,
            session_model=self._session_model,
            token_model=self._token_model,
        )

    @cached_property
    def login(self):
        """Service for login and logout flows."""
        return get_auth_login_service(
            session=self._session,
            user_model=self._user_model,
            account_model=self._account_model,
            session_model=self._session_model,
        )

    @cached_property
    def account(self):
        """Service for user account (credential) operations."""
        return get_auth_user_account_service(
            session=self._session, model=self._account_model
        )

    @cached_property
    def session(self):
        """Service for user session operations."""
        return get_auth_user_session_service(
            session=self._session, model=self._session_model
        )

    @cached_property
    def tokens(self):
        """Service for user token (verification, reset) operations."""
        return get_auth_user_tokens_service(
            session=self._session, model=self._token_model
        )

    @cached_property
    def onboarding(self):
        """Service for user onboarding operations."""
        return get_auth_user_onboarding_service(
            session=self._session,
            model=self._onboarding_model,
            user_service=self.user,
        )

    @cached_property
    def password(self):
        """Service for password reset flows."""
        return get_auth_password_service(
            session=self._session,
            user_model=self._user_model,
            account_model=self._account_model,
            session_model=self._session_model,
            token_model=self._token_model,
        )

    @cached_property
    def email(self):
        """Service for email verification flows."""
        return get_auth_email_service(
            session=self._session,
            user_model=self._user_model,
            account_model=self._account_model,
            session_model=self._session_model,
            token_model=self._token_model,
        )

    def oauth(self, *, provider: Literal["google"] = "google"):
        """Service for OAuth login flows."""
        return get_auth_oauth_service(settings=self._settings, provider=provider)
