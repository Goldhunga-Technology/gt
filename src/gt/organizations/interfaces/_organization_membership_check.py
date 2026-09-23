from abc import ABC, abstractmethod


class OrganizationMembershipCheck(ABC):
    """
    Port for checking organization membership.
    """

    @abstractmethod
    async def check_user_belongs_to_organization(self, *, user, session) -> None:
        """
        Reject when the user is not an active member of any organization or
        when no organization has been set up in the database.
        """
        raise NotImplementedError
