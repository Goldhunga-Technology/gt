from gt.auth.interfaces._policy_check_interface import IPolicyCheck
from gt.exceptions import DomainException


class BelongsToOrganizationCheck(IPolicyCheck):
    """
    Adapter connecting organization membership to the auth policy system.

    Implements the :class:`IPolicyCheck` port so it can be registered with
    ``auth.register_check(name="belongs_to_org", ...)`` and referenced from any
    policy's ``checks`` list. This keeps ``gt.auth`` decoupled from
    organizations — the membership query lives behind the port.
    """

    def __init__(self, organizations):
        """
        Args:
            organizations: An initialized ``gt.organizations.Organizations``
                instance used to resolve membership.
        """
        self._organizations = organizations

    async def check(self, *, user, session) -> None:
        """
        Reject when the current user does not belong to any organization.
        """
        membership_service = self._organizations.get_services(session).member
        membership = await membership_service.get_member_by(user_id=user.id)
        if not membership or not membership.is_active():
            raise DomainException(
                error="User does not belong to any organization.",
                errors={"code": "USER_NOT_IN_ORGANIZATION"},
            )
