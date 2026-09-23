from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gt.auth.dependencies._current_user import current_user
from gt.auth.dependencies._guards._require_access_guard import require_access
from gt.auth.interfaces._policy_check_interface import IPolicyCheck
from gt.exceptions import DomainException
from gt.exceptions._base_exceptions import InvalidException, UnauthorizedException


class FakeCheck(IPolicyCheck):
    """Test implementation of the IPolicyCheck port."""

    def __init__(self, *, allow: bool = True):
        self.calls = []
        self.allow = allow

    async def check(self, *, user, session) -> None:
        self.calls.append((user, session))
        if not self.allow:
            raise InvalidException(
                error="Custom check denied.",
                errors={"code": "CUSTOM_DENIED"},
            )


def make_services(*, user_session=None, user=None):
    services = MagicMock()
    services.session.get_session_by = AsyncMock(return_value=user_session)
    services.user.get_user_by = AsyncMock(return_value=user)
    return services


def make_auth(*, user_session=None, user=None):
    auth = MagicMock()
    auth.get_services.return_value = make_services(user_session=user_session, user=user)
    return auth


class TestCurrentUser:
    async def test_returns_user_for_valid_session(self):
        user = MagicMock()
        user.is_active.return_value = True
        user_session = MagicMock()
        user_session.is_active = True
        auth = make_auth(user_session=user_session, user=user)

        result = await current_user(
            auth=auth, session=MagicMock(), session_uuid="valid-uuid"
        )

        assert result is user
        auth.get_services.assert_called_once()

    async def test_raises_for_invalid_session(self):
        auth = make_auth(user_session=None)

        with pytest.raises(InvalidException):
            await current_user(auth=auth, session=MagicMock(), session_uuid="bad-uuid")

    async def test_raises_for_inactive_user(self):
        user = MagicMock()
        user.is_active.return_value = False
        user_session = MagicMock()
        user_session.is_active = True
        auth = make_auth(user_session=user_session, user=user)

        with pytest.raises(InvalidException):
            await current_user(
                auth=auth, session=MagicMock(), session_uuid="valid-uuid"
            )


class TestRequireAccess:
    async def test_unauthenticated_raises(self, auth):
        dependency = require_access(auth=auth)
        request = MagicMock()
        request.cookies = {}

        with pytest.raises(UnauthorizedException):
            await dependency(request, session=MagicMock())

    async def test_returns_none_when_not_required_and_no_session(self, auth):
        dependency = require_access(auth=auth, authenticated=False)
        request = MagicMock()
        request.cookies = {}

        result = await dependency(request, session=MagicMock())

        assert result is None

    async def test_returns_user_when_authenticated(self, auth):
        user = MagicMock()
        request = MagicMock()
        request.cookies = {"session_uuid": "valid-uuid"}

        with patch(
            "gt.auth.dependencies._current_user.current_user",
            new=AsyncMock(return_value=user),
        ):
            dependency = require_access(auth=auth)
            result = await dependency(request, session=MagicMock())

        assert result is user

    async def test_email_verified_policy_is_enforced(self, auth):
        user = MagicMock()
        user.is_email_verified.return_value = False
        request = MagicMock()
        request.cookies = {"session_uuid": "valid-uuid"}

        with patch(
            "gt.auth.dependencies._current_user.current_user",
            new=AsyncMock(return_value=user),
        ):
            dependency = require_access(auth=auth, email_verified=True)
            with pytest.raises(DomainException):
                await dependency(request, session=MagicMock())


class TestCustomPolicyChecks:
    def test_register_check_rejects_builtin_name(self, auth):
        with pytest.raises(ValueError):
            auth.register_check(name="email_verified", check=FakeCheck())

    def test_register_check_rejects_duplicate(self, auth):
        auth.register_check(name="custom", check=FakeCheck())

        with pytest.raises(ValueError):
            auth.register_check(name="custom", check=FakeCheck())

    def test_register_check_rejects_non_port_implementation(self, auth):
        with pytest.raises(TypeError):
            auth.register_check(name="custom", check=object())

    def test_policy_can_reference_registered_check(self, auth):
        auth.register_check(name="custom", check=FakeCheck())
        auth.register_policy(name="member", checks=["custom"])

        @auth.policy("member")
        async def handler():
            return "ok"

        assert handler is not None

    async def test_check_passes(self, auth):
        check = FakeCheck()
        auth.register_check(name="custom", check=check)

        session = MagicMock()
        user = MagicMock()
        request = MagicMock()
        request.cookies = {"session_uuid": "valid-uuid"}

        with patch(
            "gt.auth.dependencies._current_user.current_user",
            new=AsyncMock(return_value=user),
        ):
            dependency = require_access(auth=auth, custom_checks=["custom"])
            result = await dependency(request, session=session)

        assert result is user
        assert check.calls == [(user, session)]

    async def test_denies_when_check_raises(self, auth):
        check = FakeCheck(allow=False)
        auth.register_check(name="custom", check=check)

        request = MagicMock()
        request.cookies = {"session_uuid": "valid-uuid"}

        with patch(
            "gt.auth.dependencies._current_user.current_user",
            new=AsyncMock(return_value=MagicMock()),
        ):
            dependency = require_access(auth=auth, custom_checks=["custom"])
            with pytest.raises(InvalidException):
                await dependency(request, session=MagicMock())
