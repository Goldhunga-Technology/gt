from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK

from gt.auth.dependencies._guards._require_access_guard import require_access
from gt.auth.schemas._auth_email_schemas import AuthEmailVerifySchema
from gt.response import cr

from ..uow import AuthUOW


def create_email_router(*, auth):
    """
    Create a router for email verification operations.
    """
    email_token_digit = auth.settings.email_verification_token_digit
    email_token_expiry_minutes = auth.settings.email_verification_token_expiry_minutes

    router = APIRouter()

    @router.post("/email-verification")
    async def verify_email(
        body: AuthEmailVerifySchema,
        session: AsyncSession = Depends(auth.get_db_session),
        current_user=Depends(require_access(auth=auth, authenticated=True)),
    ):
        """
        Endpoint to verify a user's email address using a verification token.
        """
        email_service = auth.get_services(session).email

        async with AuthUOW(session):
            await email_service.verify_email(
                user=current_user,
                token=body.token,
            )

        return cr.success(
            message="Email verified successfully.",
            status_code=HTTP_200_OK,
        )

    @router.post("/resend-email-verification")
    async def resend_email_verification(
        session: AsyncSession = Depends(auth.get_db_session),
        current_user=Depends(require_access(auth=auth, authenticated=True)),
    ):
        """
        Endpoint to resend the email verification token to the user.
        """
        email_service = auth.get_services(session).email

        async with AuthUOW(session):
            await email_service.resend_verification_email(
                user=current_user,
                email_token_digit=email_token_digit,
                email_token_expiry_minutes=email_token_expiry_minutes,
            )

        return cr.success(
            message="Verification email resent successfully.",
            status_code=HTTP_200_OK,
        )

    return router
