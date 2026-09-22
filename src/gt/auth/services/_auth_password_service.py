from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from gt.auth.events import (
    PasswordResetCompletedEvent,
    PasswordResetRequestedEvent,
    event_bus,
)
from gt.auth.models._auth_user_model import AuthUserModel, TUser
from gt.auth.models._auth_user_tokens_model import AuthUserTokensModelBase
from gt.auth.repositories._auth_user_account_repository import TAccount
from gt.auth.repositories._auth_user_session_repository import TSession
from gt.auth.repositories._auth_user_tokens_repository import TToken
from gt.auth.services._auth_user_account_service import (
    AuthUserAccountService,
    get_auth_user_account_service,
)
from gt.auth.services._auth_user_service import AuthUserService, get_auth_user_service
from gt.auth.services._auth_user_session_service import (
    AuthUserSessionService,
    get_auth_user_session_service,
)
from gt.auth.services._auth_user_tokens_service import AuthUserTokensService
from gt.auth.services.hash._hash_service import HasherService
from gt.exceptions._base_exceptions import (
    DomainException,
    InvalidException,
    NotFoundException,
)


class AuthPasswordService[
    TUser: AuthUserModel,
    TToken: AuthUserTokensModelBase,
]:
    """
    Service class for handling password operations.
    """

    def __init__(
        self,
        user_service: AuthUserService,
        account_service: AuthUserAccountService[TAccount],
        session_service: AuthUserSessionService[TSession],
        token_service: AuthUserTokensService[TToken],
        hash_service: HasherService,
    ):
        self._user_service = user_service
        self._account_service = account_service
        self._session_service = session_service
        self._token_service = token_service
        self._hash_service = hash_service

    async def request_password_reset(
        self,
        email: str,
        password_reset_token_expiry_minutes: int,
        password_reset_token_digit: int,
    ) -> None:
        """
        Generate a password reset token for the user and publish an event with it.
        """
        try:
            user = await self._user_service.get_user_by(email=email.lower())
            if not user:
                self._hash_service.dummy_verify("")
                raise NotFoundException(
                    error="No user found with the provided email.",
                    errors={"email": "No user found with the provided email."},
                )

            await self._token_service.delete_tokens_by(
                user_id=user.id,
                type="password_reset",
            )

            _, plain_token = await self._user_service.get_password_reset_token(
                user_id=user.id,
                password_reset_token_expiry_minutes=password_reset_token_expiry_minutes,
                password_reset_token_digit=password_reset_token_digit,
            )

            await event_bus.publish(
                PasswordResetRequestedEvent(
                    user_id=user.id,
                    full_name=user.full_name,
                    email=user.email,
                    user_uuid=user.uuid,
                    password_reset_token=plain_token,
                    password_reset_token_expiry_minutes=password_reset_token_expiry_minutes,
                )
            )
        except (
            NotFoundException,
            InvalidException,
            DomainException,
        ):
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to request password reset.",
                internal_details=str(e),
            ) from e

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset a user's password using a valid password reset token.
        """
        try:
            now = datetime.now(UTC)
            tokens = await self._token_service.get_tokens_by(
                type="password_reset",
                used_at=None,
            )

            token_record = None
            for candidate in tokens:
                if (
                    candidate.expires_at >= now
                    and self._hash_service.verify_deterministic_hash(
                        token, candidate.token_hash
                    )
                ):
                    token_record = candidate
                    break

            if not token_record:
                raise InvalidException(
                    error="Invalid or expired password reset token.",
                    errors={"token": "Invalid or expired token."},
                )

            token_record.used_at = now
            await self._token_service.update_token(token_record)

            account = await self._account_service.get_account_by(
                user_id=token_record.user_id,
                type="credentials",
            )
            if not account:
                raise NotFoundException(
                    error="No credentials account found for the user.",
                    errors={"account": "No credentials account found for the user."},
                )

            account.hashed_password = self._hash_service.hash(new_password)
            account.last_password_updated_at = now
            await self._account_service.update_account(account)

            await self._session_service.invalidate_user_sessions(
                user_id=token_record.user_id
            )

            await self._token_service.delete_tokens_by(
                user_id=token_record.user_id,
                type="password_reset",
            )

            user = await self._user_service.get_user_by(id=token_record.user_id)
            if user:
                await event_bus.publish(
                    PasswordResetCompletedEvent(
                        user_id=user.id,
                        email=user.email,
                        user_uuid=user.uuid,
                    )
                )
        except (
            NotFoundException,
            InvalidException,
            DomainException,
        ):
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to reset password.",
                internal_details=str(e),
            ) from e


def get_auth_password_service(
    *,
    session: AsyncSession,
    user_model: type[TUser],
    account_model: type[TAccount],
    session_model: type[TSession],
    token_model: type[TToken],
) -> AuthPasswordService[TUser, TToken]:
    """
    Factory function to create an instance of AuthPasswordService.
    """
    from gt.auth.services._auth_user_tokens_service import get_auth_user_tokens_service

    user_service = get_auth_user_service(
        session=session,
        user_model=user_model,
        account_model=account_model,
        session_model=session_model,
        token_model=token_model,
    )
    account_service = get_auth_user_account_service(
        session=session, model=account_model
    )
    session_service = get_auth_user_session_service(
        session=session, model=session_model
    )
    token_service = get_auth_user_tokens_service(session=session, model=token_model)
    hash_service = HasherService()
    return AuthPasswordService(
        user_service=user_service,
        account_service=account_service,
        session_service=session_service,
        token_service=token_service,
        hash_service=hash_service,
    )
