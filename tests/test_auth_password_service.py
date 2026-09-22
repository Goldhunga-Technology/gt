from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gt.auth.services._auth_password_service import AuthPasswordService
from gt.exceptions._base_exceptions import InvalidException, NotFoundException


def make_user(models):
    return models["user_model"](
        email="user@example.com", full_name="Test User", avatar_bg="#ffffff"
    )


def make_password_service(*, user):
    user_service = MagicMock()
    user_service.get_user_by = AsyncMock(return_value=user)
    user_service.get_password_reset_token = AsyncMock(
        return_value=(MagicMock(), "123456")
    )
    token_service = MagicMock()
    token_service.delete_tokens_by = AsyncMock()
    account_service = MagicMock()
    session_service = MagicMock()
    hash_service = MagicMock()

    service = AuthPasswordService(
        user_service=user_service,
        account_service=account_service,
        session_service=session_service,
        token_service=token_service,
        hash_service=hash_service,
    )
    return (
        service,
        token_service,
        user_service,
        account_service,
        session_service,
    )


def make_reset_token(models, *, expired: bool = False):
    expires_at = (
        datetime.now(UTC) - timedelta(minutes=1)
        if expired
        else datetime.now(UTC) + timedelta(minutes=15)
    )
    return models["token_model"](
        user_id=1,
        type="password_reset",
        token_hash="token-hash",
        expires_at=expires_at,
    )


def make_reset_service(models, *, tokens=None, verify_ok=True, account=None):
    service, token_service, user_service, account_service, session_service = (
        make_password_service(user=make_user(models))
    )
    token_service.get_tokens_by = AsyncMock(return_value=tokens or [])
    token_service.update_token = AsyncMock()
    hash_service = service._hash_service
    hash_service.verify_deterministic_hash = MagicMock(return_value=verify_ok)
    hash_service.hash = MagicMock(return_value="new-hash")
    account_service.get_account_by = AsyncMock(return_value=account)
    account_service.update_account = AsyncMock()
    session_service.invalidate_user_sessions = AsyncMock()
    return service, token_service, user_service, account_service, session_service


class TestAuthPasswordService:
    async def test_request_password_reset_unknown_user(self, models):
        service, _, _, _, _ = make_password_service(user=None)

        with pytest.raises(NotFoundException):
            await service.request_password_reset(
                email="missing@example.com",
                password_reset_token_expiry_minutes=15,
                password_reset_token_digit=6,
            )

    async def test_request_password_reset_success(self, models):
        user = make_user(models)
        service, token_service, user_service, _, _ = make_password_service(user=user)

        with patch(
            "gt.auth.services._auth_password_service.event_bus.publish",
            new=AsyncMock(),
        ) as publish:
            await service.request_password_reset(
                email="User@Example.com",
                password_reset_token_expiry_minutes=15,
                password_reset_token_digit=6,
            )

        user_service.get_user_by.assert_awaited_once_with(email="user@example.com")
        token_service.delete_tokens_by.assert_awaited_once_with(
            user_id=user.id, type="password_reset"
        )
        user_service.get_password_reset_token.assert_awaited_once_with(
            user_id=user.id,
            password_reset_token_expiry_minutes=15,
            password_reset_token_digit=6,
        )
        publish.assert_awaited_once()


class TestResetPassword:
    async def test_reset_password_no_token(self, models):
        service, _, _, _, _ = make_reset_service(models, tokens=[])

        with pytest.raises(InvalidException):
            await service.reset_password(token="123456", new_password="newsecret")

    async def test_reset_password_wrong_token(self, models):
        service, _, _, _, _ = make_reset_service(
            models, tokens=[make_reset_token(models)], verify_ok=False
        )

        with pytest.raises(InvalidException):
            await service.reset_password(token="654321", new_password="newsecret")

    async def test_reset_password_expired_token(self, models):
        service, _, _, _, _ = make_reset_service(
            models, tokens=[make_reset_token(models, expired=True)]
        )

        with pytest.raises(InvalidException):
            await service.reset_password(token="123456", new_password="newsecret")

    async def test_reset_password_missing_account(self, models):
        service, _, _, _, _ = make_reset_service(
            models, tokens=[make_reset_token(models)], account=None
        )

        with pytest.raises(NotFoundException):
            await service.reset_password(token="123456", new_password="newsecret")

    async def test_reset_password_success(self, models):
        token = make_reset_token(models)
        account = MagicMock()
        service, token_service, _, account_service, session_service = (
            make_reset_service(models, tokens=[token], account=account)
        )

        with patch(
            "gt.auth.services._auth_password_service.event_bus.publish",
            new=AsyncMock(),
        ) as publish:
            await service.reset_password(token="123456", new_password="newsecret")

        assert token.used_at is not None
        token_service.update_token.assert_awaited_once_with(token)
        account_service.get_account_by.assert_awaited_once_with(
            user_id=1, type="credentials"
        )
        assert account.hashed_password == "new-hash"
        assert account.last_password_updated_at is not None
        account_service.update_account.assert_awaited_once_with(account)
        session_service.invalidate_user_sessions.assert_awaited_once_with(user_id=1)
        token_service.delete_tokens_by.assert_awaited_once_with(
            user_id=1, type="password_reset"
        )
        publish.assert_awaited_once()
