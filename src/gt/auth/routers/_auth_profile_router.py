from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK

from gt.auth.dependencies._guards._require_access_guard import require_access
from gt.auth.schemas._auth_profile_schemas import (
    AuthDeactivateSchema,
    AuthProfileUpdateSchema,
)
from gt.auth.services._auth_user_service import get_auth_user_service
from gt.response import cr

from ..uow import AuthUOW


def create_profile_router(*, auth):
    """
    Create a router for user profile operations.
    """
    user_model = auth.user_model
    user_tokens_model = auth.user_tokens_model
    account_model = auth.user_account_model
    session_model = auth.user_session_model

    router = APIRouter()

    @router.patch("/profile")
    async def update_profile(
        body: AuthProfileUpdateSchema,
        session: AsyncSession = Depends(auth.get_db_session),
        current_user=Depends(require_access(auth=auth, authenticated=True)),
    ):
        """
        Endpoint to update the current user's profile.
        """
        user_service = get_auth_user_service(
            session=session,
            user_model=user_model,
            account_model=account_model,
            session_model=session_model,
            token_model=user_tokens_model,
        )

        async with AuthUOW(session):
            updated_user = await user_service.update_profile(
                user=current_user,
                **body.model_dump(exclude_unset=True),
            )

        return cr.success(
            data={
                "id": updated_user.id,
                "uuid": updated_user.uuid,
                "full_name": updated_user.full_name,
                "email": updated_user.email,
                "avatar": updated_user.avatar,
                "avatar_bg": updated_user.avatar_bg,
            },
            message="Profile updated successfully.",
            status_code=HTTP_200_OK,
        )

    @router.post("/deactivate")
    async def deactivate_user(
        body: AuthDeactivateSchema,
        session: AsyncSession = Depends(auth.get_db_session),
        current_user=Depends(require_access(auth=auth, authenticated=True)),
    ):
        """
        Endpoint to deactivate the current user's account.
        """
        user_service = get_auth_user_service(
            session=session,
            user_model=user_model,
            account_model=account_model,
            session_model=session_model,
            token_model=user_tokens_model,
        )

        async with AuthUOW(session):
            await user_service.deactivate_user(
                user=current_user,
                password=body.password,
            )

        return cr.success(
            message="User deactivated successfully.",
            status_code=HTTP_200_OK,
        )

    return router
