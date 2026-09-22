from starlette.status import HTTP_200_OK

from gt.auth.schemas._auth_password_schemas import (
    AuthPasswordResetRequestSchema,
    AuthPasswordResetSchema,
)
from gt.auth.services._auth_password_service import get_auth_password_service
from gt.response import cr

from ..uow import AuthUOW


def create_password_router(*, auth):
    """
    Create a router for password operations.
    """
    session_factory = auth.session_factory
    user_model = auth.user_model
    user_account_model = auth.user_account_model
    user_session_model = auth.user_session_model
    user_tokens_model = auth.user_tokens_model

    password_reset_token_digit = auth.settings.password_reset_token_digit
    password_reset_token_expiry_minutes = (
        auth.settings.password_reset_token_expiry_minutes
    )

    from fastapi import APIRouter

    router = APIRouter()

    @router.post("/forgot-password")
    async def forgot_password(body: AuthPasswordResetRequestSchema):
        """
        Endpoint to request a password reset token for a user.
        """
        async with session_factory() as session:
            password_service = get_auth_password_service(
                session=session,
                user_model=user_model,
                account_model=user_account_model,
                session_model=user_session_model,
                token_model=user_tokens_model,
            )

            async with AuthUOW(session):
                await password_service.request_password_reset(
                    email=body.email,
                    password_reset_token_expiry_minutes=password_reset_token_expiry_minutes,
                    password_reset_token_digit=password_reset_token_digit,
                )

        return cr.success(
            message="If the email exists, a password reset token has been sent.",
            status_code=HTTP_200_OK,
        )

    @router.post("/reset-password")
    async def reset_password(body: AuthPasswordResetSchema):
        """
        Endpoint to reset a user's password using a password reset token.
        """
        async with session_factory() as session:
            password_service = get_auth_password_service(
                session=session,
                user_model=user_model,
                account_model=user_account_model,
                session_model=user_session_model,
                token_model=user_tokens_model,
            )

            async with AuthUOW(session):
                await password_service.reset_password(
                    token=body.token,
                    new_password=body.new_password,
                )

        return cr.success(
            message="Password reset successfully.",
            status_code=HTTP_200_OK,
        )

    return router
