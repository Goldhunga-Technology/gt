from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class IPolicyCheck(ABC):
    """
    Interface for custom policy checks evaluated against the current user.

    Implementations must raise a domain/HTTP exception to reject the request,
    or return normally to allow it. This keeps ``gt.auth`` decoupled from the
    resource being checked (e.g. organization membership) — concrete
    implementations live in packages that depend on auth, such as
    ``gt.organizations``.
    """

    @abstractmethod
    async def check(self, *, user: Any, session: AsyncSession) -> None:
        """
        Verify that the current user satisfies this check.

        Args:
            user: The authenticated user, or ``None`` when not authenticated.
            session: The active database session.

        Raises:
            DomainException: When the check fails. Must be raised to reject.
        """
        raise NotImplementedError
