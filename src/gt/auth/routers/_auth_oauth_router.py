from typing import Literal

from fastapi import APIRouter
from fastapi.param_functions import Path
from fastapi.requests import Request


def create_oauth_router(*, auth):
    """
    Create a router for OAuth-related operations.
    """

    from gt.auth.uow._auth_uow import AuthUOW

    session_factory = auth.session_factory

    router = APIRouter(prefix="/oauth")

    @router.get("/login/{provider}")
    async def oauth_login(
        request: Request,
        provider: Literal["google"] = Path(..., description="OAuth provider name"),
    ):
        """
        Endpoint to initiate the OAuth login process for a given provider.
        """

        async with session_factory() as session:
            oauth_service = auth.get_services(session).oauth(provider=provider)

            async with AuthUOW(session):
                return await oauth_service.authorize_redirect(request=request)

    return router

    @router.get("/callback/{provider}")
    async def oauth_callback(
        request: Request,
        provider: Literal["google"] = Path(..., description="OAuth provider name"),
    ):
        """
        Endpoint to handle the OAuth callback for a given provider.
        """

        async with session_factory() as session:
            oauth_service = auth.get_services(session).oauth(provider=provider)

            async with AuthUOW(session):
                return await oauth_service.handle_callback(request=request)
