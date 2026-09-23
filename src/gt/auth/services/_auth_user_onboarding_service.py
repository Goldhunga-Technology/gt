from sqlalchemy.ext.asyncio import AsyncSession

from gt.auth.models._auth_user_onboarding_model import (
    AuthUserOnboardingModelBase,
    TOnboarding,
)
from gt.auth.repositories._auth_user_onboarding_repository import (
    AuthUserOnboardingRepository,
)
from gt.exceptions import DomainException
from gt.exceptions._base_exceptions import InvalidException


class AuthUserOnboardingService[TOnboarding: AuthUserOnboardingModelBase]:
    """
    Service class for managing user onboarding processes.
    """

    def __init__(
        self,
        repository: AuthUserOnboardingRepository[TOnboarding],
        model: type[TOnboarding],
        user_service=None,
    ):
        self._repository = repository
        self._model = model
        self._user_service = user_service

    async def add_onboarding(
        self,
        user_id: int,
        theme: str,
        referral_source: str | None = None,
    ) -> TOnboarding:
        """
        Upserts the onboarding information for a user.
        """
        try:
            existing = await self._repository.get_by(user_id=user_id)
            if existing:
                raise InvalidException(
                    error="Onboarding already exists for this user.",
                    internal_details=f"User ID: {user_id}",
                )

            onboarding = self._model(
                user_id=user_id,
                theme=theme,
                referral_source=referral_source,
            )
            created = await self._repository.add(onboarding)

            if self._user_service:
                user = await self._user_service.get_user_by(id=user_id)
                if user and not user.is_onboarded:
                    user.is_onboarded = True
                    await self._user_service.update_user(user)

            return created
        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to add onboarding.",
                internal_details=str(e),
            ) from e

    async def get_onboarding_by(self, **kwargs) -> TOnboarding | None:
        """
        Retrieves onboarding information based on provided criteria.
        """
        try:
            return await self._repository.get_by(**kwargs)
        except DomainException:
            raise
        except Exception as e:
            raise DomainException(
                error="Failed to retrieve onboarding.",
                internal_details=str(e),
            ) from e


def get_auth_user_onboarding_service(
    session: AsyncSession,
    model: type[TOnboarding],
    user_service=None,
) -> AuthUserOnboardingService[TOnboarding]:
    """
    Factory function to create an instance of AuthUserOnboardingService.
    """
    repository = AuthUserOnboardingRepository(session=session, model=model)
    return AuthUserOnboardingService(
        repository=repository, model=model, user_service=user_service
    )
