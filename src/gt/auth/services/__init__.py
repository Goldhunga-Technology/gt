from ._auth_login_service import AuthLoginService, get_auth_login_service
from ._auth_user_account_service import (
    AuthUserAccountService,
    get_auth_user_account_service,
)
from ._auth_user_onboarding_service import (
    AuthUserOnboardingService,
    get_auth_user_onboarding_service,
)
from ._auth_user_service import AuthUserService, get_auth_user_service
from ._auth_user_session_service import (
    AuthUserSessionService,
    get_auth_user_session_service,
)
from ._auth_user_tokens_service import (
    AuthUserTokensService,
    get_auth_user_tokens_service,
)
from ._service_registry import ServiceRegistry

__all__ = [
    "AuthLoginService",
    "AuthUserAccountService",
    "AuthUserOnboardingService",
    "AuthUserService",
    "AuthUserSessionService",
    "AuthUserTokensService",
    "ServiceRegistry",
    "get_auth_login_service",
    "get_auth_user_account_service",
    "get_auth_user_onboarding_service",
    "get_auth_user_service",
    "get_auth_user_session_service",
    "get_auth_user_tokens_service",
]


def __getattr__(name: str):
    if name in __all__:
        return globals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
