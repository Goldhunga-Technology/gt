from fastapi import Depends
from starlette.status import HTTP_400_BAD_REQUEST

from gt.auth.uow import AuthUOW
from gt.exceptions._base_exceptions import DomainException
from gt.organizations.schemas import (
    OrganizationMemberAddSchema,
    OrganizationMemberResponseSchema,
    OrganizationMemberUpdateSchema,
)
from gt.response import cr


def create_organization_member_router(*, organizations):
    """
    Create a router for organization member operations.
    """
    session_factory = organizations.session_factory
    organization_member_add_schema = OrganizationMemberAddSchema
    current_user = organizations.current_user

    from fastapi import APIRouter

    router = APIRouter()

    @router.post("/{organization_slug}/members")
    async def add_member(
        organization_slug: str,
        body: organization_member_add_schema,  # type: ignore
        user=Depends(current_user),
    ):
        """
        Endpoint to add a member to an organization.
        """
        async with session_factory() as session:
            services = organizations.get_services(session)
            organization = await services.organization.get_organization_by(
                slug=organization_slug
            )
            if not organization:
                return cr.error(
                    error="Organization not found.",
                    errors={"code": "ORGANIZATION_NOT_FOUND"},
                    status_code=HTTP_400_BAD_REQUEST,
                )
            if organization.owner_id != user.id:
                return cr.error(
                    error="You do not have access to this organization.",
                    errors={"code": "ORGANIZATION_ACCESS_DENIED"},
                )

            async with AuthUOW(session):
                try:
                    member = await services.member.add_member(
                        organization_id=organization.id,
                        organization_uuid=organization.uuid,
                        user_id=body.user_id,
                        status=body.status,
                        role=body.role,
                    )
                except DomainException as e:
                    return cr.error(
                        error=e.error,
                        errors=e.errors,
                    )

        return cr.success(
            data=OrganizationMemberResponseSchema.model_validate(member).model_dump(),
            message="Member added successfully.",
        )

    @router.get("/{organization_slug}/members")
    async def list_members(organization_slug: str, user=Depends(current_user)):
        """
        Endpoint to list all members of an organization.
        """
        async with session_factory() as session:
            services = organizations.get_services(session)
            organization = await services.organization.get_organization_by(
                slug=organization_slug
            )
            if not organization:
                return cr.error(
                    error="Organization not found.",
                    errors={"code": "ORGANIZATION_NOT_FOUND"},
                    status_code=HTTP_400_BAD_REQUEST,
                )

            members = await services.member.list_members(
                organization_id=organization.id
            )

        return cr.success(
            data=[
                OrganizationMemberResponseSchema.model_validate(m).model_dump()
                for m in members
            ],
            message="Members retrieved successfully.",
        )

    @router.patch("/{organization_slug}/members/{member_uuid}")
    async def update_member(
        organization_slug: str,
        member_uuid: str,
        body: OrganizationMemberUpdateSchema,
        user=Depends(current_user),
    ):
        """
        Endpoint to update an organization member's status.
        """
        async with session_factory() as session:
            services = organizations.get_services(session)
            organization = await services.organization.get_organization_by(
                slug=organization_slug
            )
            if not organization:
                return cr.error(
                    error="Organization not found.",
                    errors={"code": "ORGANIZATION_NOT_FOUND"},
                    status_code=HTTP_400_BAD_REQUEST,
                )
            if organization.owner_id != user.id:
                return cr.error(
                    error="You do not have access to this organization.",
                    errors={"code": "ORGANIZATION_ACCESS_DENIED"},
                )

            async with AuthUOW(session):
                member = await services.member.get_member_by(
                    organization_id=organization.id, uuid=member_uuid
                )
                if not member:
                    return cr.error(
                        error="Member not found.",
                        errors={"code": "MEMBER_NOT_FOUND"},
                        status_code=HTTP_400_BAD_REQUEST,
                    )
                try:
                    member = await services.member.update_member(
                        member=member,
                        organization_uuid=organization.uuid,
                        status=body.status,
                        role=body.role,
                    )
                except DomainException as e:
                    return cr.error(
                        error=e.error,
                        errors=e.errors,
                    )

        return cr.success(
            data=OrganizationMemberResponseSchema.model_validate(member).model_dump(),
            message="Member updated successfully.",
        )

    @router.delete("/{organization_slug}/members/{member_uuid}")
    async def remove_member(
        organization_slug: str,
        member_uuid: str,
        user=Depends(current_user),
    ):
        """
        Endpoint to remove a member from an organization.
        """
        async with session_factory() as session:
            services = organizations.get_services(session)
            organization = await services.organization.get_organization_by(
                slug=organization_slug
            )
            if not organization:
                return cr.error(
                    error="Organization not found.",
                    errors={"code": "ORGANIZATION_NOT_FOUND"},
                    status_code=HTTP_400_BAD_REQUEST,
                )
            if organization.owner_id != user.id:
                return cr.error(
                    error="You do not have access to this organization.",
                    errors={"code": "ORGANIZATION_ACCESS_DENIED"},
                )

            async with AuthUOW(session):
                member = await services.member.get_member_by(
                    organization_id=organization.id, uuid=member_uuid
                )
                if not member:
                    return cr.error(
                        error="Member not found.",
                        errors={"code": "MEMBER_NOT_FOUND"},
                        status_code=HTTP_400_BAD_REQUEST,
                    )
                await services.member.remove_member(
                    member, organization_uuid=organization.uuid
                )

        return cr.success(message="Member removed successfully.")

    return router
